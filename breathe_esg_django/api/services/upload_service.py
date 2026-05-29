"""
upload_service.py — Orchestrates the full ingestion pipeline for a single file upload.

10-STEP PIPELINE (mirrors C# UploadService exactly):
1. Validate data source belongs to company
2. Read file bytes + compute SHA-256 hash
3. Reject duplicate uploads (same hash + company)
4. Persist file to disk under UPLOADS_DIR/<company_id>/
5. Create RawUpload record (status: Processing)
6. Parse rows using the appropriate parser
7. Build validation engine with per-source rules (DuplicateTripRule is stateful)
8. Normalize + validate each row
9. Bulk-insert NormalizedRecords + ReviewFlags
10. Update RawUpload status → Completed (or Failed on exception) + emit audit log

All steps are wrapped in try/except — failures update RawUpload.error_summary
rather than leaving the upload record in an unknown state.
"""
import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.db import transaction

from ..models import (
    DataSource, RawUpload, NormalizedRecord, ReviewFlag, UploadStatus, RecordStatus,
)
from ..parsers import SapCsvParser, UtilityCsvParser, TravelJsonParser
from ..normalization import SapNormalizationStrategy, UtilityNormalizationStrategy, TravelNormalizationStrategy
from ..validation import (
    ValidationEngine,
    NegativeValueRule, FutureDateRule, MissingActivityDateRule, MissingUnitRule,
    UnrealisticFuelQuantityRule, MissingMeterIdRule, MissingBillingPeriodRule,
    MissingDistanceRule, InvalidAirportCodeRule, DuplicateTripRule,
)
from .audit_service import AuditService


def _compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_validation_engine(source_type: str) -> ValidationEngine:
    """Shared rules + source-specific rules — mirrors C# BuildValidationEngine."""
    rules = [
        NegativeValueRule(),
        FutureDateRule(),
        MissingActivityDateRule(),
        MissingUnitRule(),
    ]
    if source_type == 'SapFuel':
        rules.append(UnrealisticFuelQuantityRule())
    elif source_type == 'UtilityElectricity':
        rules.append(MissingMeterIdRule())
        rules.append(MissingBillingPeriodRule())
    elif source_type == 'CorporateTravel':
        rules.append(MissingDistanceRule())
        rules.append(InvalidAirportCodeRule())
        rules.append(DuplicateTripRule())   # Stateful — new instance per upload

    return ValidationEngine(rules)


def _get_parser(source_type: str):
    parsers = {
        'SapFuel': SapCsvParser(),
        'UtilityElectricity': UtilityCsvParser(),
        'CorporateTravel': TravelJsonParser(),
    }
    parser = parsers.get(source_type)
    if not parser:
        raise ValueError(f'Source type {source_type} has no registered parser.')
    return parser


def _get_normalizer(source_type: str):
    normalizers = {
        'SapFuel': SapNormalizationStrategy(),
        'UtilityElectricity': UtilityNormalizationStrategy(),
        'CorporateTravel': TravelNormalizationStrategy(),
    }
    normalizer = normalizers.get(source_type)
    if not normalizer:
        raise ValueError(f'Source type {source_type} has no registered normalization strategy.')
    return normalizer


class UploadService:

    def __init__(self):
        self._audit = AuditService()

    def ingest(self, file_bytes: bytes, file_name: str, company_id, data_source_id, uploaded_by: str, ip_address=None):
        """
        Full ingestion pipeline. Returns (raw_upload, record_count, flagged_count).
        Raises:
            DataSource.DoesNotExist → 400/404
            ValueError('duplicate') → 409
        """
        # 1. Validate data source
        try:
            data_source = DataSource.objects.get(id=data_source_id, company_id=company_id)
        except DataSource.DoesNotExist:
            raise DataSource.DoesNotExist(f'DataSource {data_source_id} not found for company {company_id}')

        source_type = data_source.source_type

        # 2. SHA-256 hash
        file_hash = _compute_sha256(file_bytes)

        # 3. Reject duplicates
        existing = RawUpload.objects.filter(file_hash=file_hash, company_id=company_id).first()
        if existing:
            raise ValueError(
                f'duplicate: File already ingested on {existing.created_at:%Y-%m-%d} '
                f'(upload ID: {existing.id}). Reject duplicate upload.'
            )

        # 4. Persist file to disk
        uploads_dir = Path(settings.UPLOADS_DIR) / str(company_id)
        uploads_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f'{uuid.uuid4()}_{Path(file_name).name}'
        file_path = uploads_dir / unique_name
        file_path.write_bytes(file_bytes)

        # 5. Create RawUpload record
        raw_upload = RawUpload.objects.create(
            company_id=company_id,
            data_source=data_source,
            file_name=file_name,
            file_path=str(file_path.relative_to(settings.UPLOADS_DIR.parent)),
            file_hash=file_hash,
            file_size_bytes=len(file_bytes),
            uploaded_by=uploaded_by,
            status=UploadStatus.PROCESSING,
        )

        try:
            # 6. Parse
            parser = _get_parser(source_type)
            parsed_rows = parser.parse(file_bytes, file_name)

            # 7. Build validation engine
            validation_engine = _build_validation_engine(source_type)

            # 8. Normalize + validate
            normalizer = _get_normalizer(source_type)
            normalized_records = []
            all_flags = []
            parse_errors = []

            for row in parsed_rows:
                if row.has_parse_error:
                    parse_errors.append(row.parse_error)
                    continue

                record_data = normalizer.normalize(row)
                engine_result = validation_engine.validate(record_data)

                record_id = uuid.uuid4()
                record_data.update({
                    'id': record_id,
                    'company_id': company_id,
                    'data_source': data_source,
                    'raw_upload': raw_upload,
                    'status': engine_result.final_status,
                })

                normalized_records.append(NormalizedRecord(**{
                    k: v for k, v in record_data.items()
                    if k not in ('id',)  # id is set separately
                }))
                normalized_records[-1].id = record_id

                for flag_data in engine_result.flags:
                    all_flags.append(ReviewFlag(
                        normalized_record_id=record_id,
                        **flag_data,
                    ))

            # 9. Bulk save
            if normalized_records:
                with transaction.atomic():
                    NormalizedRecord.objects.bulk_create(normalized_records)
                    if all_flags:
                        ReviewFlag.objects.bulk_create(all_flags)

            # 10. Update upload record
            flagged_count = sum(1 for r in normalized_records if r.status == 'Flagged')
            raw_upload.row_count = len(normalized_records)
            raw_upload.status = UploadStatus.COMPLETED
            if parse_errors:
                raw_upload.error_summary = f'{len(parse_errors)} parse error(s): {"; ".join(parse_errors[:3])}'
            raw_upload.save()

            # Audit log
            self._audit.log(
                company_id=company_id,
                entity_type='RawUpload',
                entity_id=raw_upload.id,
                action='CREATED',
                performed_by=uploaded_by,
                previous=None,
                next_value={
                    'fileName': raw_upload.file_name,
                    'rowCount': raw_upload.row_count,
                    'flaggedCount': flagged_count,
                },
                ip_address=ip_address,
            )

            return raw_upload, len(normalized_records), flagged_count

        except Exception as exc:
            raw_upload.status = UploadStatus.FAILED
            raw_upload.error_summary = str(exc)
            raw_upload.save()
            raise

    def get_uploads(self, company_id, page: int = 1, page_size: int = 20):
        """Returns (queryset_page, total_count)."""
        qs = RawUpload.objects.select_related('data_source').filter(
            company_id=company_id
        ).order_by('-created_at')
        total = qs.count()
        offset = (page - 1) * page_size
        items = list(qs[offset:offset + page_size])
        return items, total
