"""
record_service.py — Business logic for NormalizedRecord lifecycle management.

Mirrors C# RecordService exactly:
- Approve: locks record, resolves all open flags, writes audit entry
- Reject: terminal state, writes audit entry
- Edit: enforces not-locked, tracks changed fields, writes audit entry
- Status transition state machine enforced in Python (not at DB level)
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from django.db import transaction

from ..models import NormalizedRecord, ReviewFlag
from .audit_service import AuditService


# Valid status transitions — mirrors C# AssertValidTransition
VALID_TRANSITIONS = {
    ('Pending',  'Approved'),
    ('Pending',  'Rejected'),
    ('Flagged',  'Approved'),
    ('Flagged',  'Rejected'),
}


def _capture_snapshot(record: NormalizedRecord) -> dict:
    """Before/after snapshot for audit log — mirrors C# CaptureSnapshot."""
    return {
        'status': record.status,
        'quantity': str(record.quantity) if record.quantity is not None else None,
        'unit': record.unit,
        'category': record.category,
        'activityDate': record.activity_date.isoformat() if record.activity_date else None,
        'reviewedBy': record.reviewed_by,
        'reviewNotes': record.review_notes,
        'isLocked': record.is_locked,
    }


class RecordService:
    """
    Orchestrates all state transitions on NormalizedRecord entities.
    All methods raise:
        KeyError  — record not found (→ 404)
        PermissionError  — record is locked (→ 409)
        ValueError  — invalid transition (→ 409)
    """

    def __init__(self):
        self._audit = AuditService()

    def _get_or_raise(self, record_id, company_id) -> NormalizedRecord:
        try:
            return NormalizedRecord.objects.select_related(
                'data_source', 'raw_upload'
            ).prefetch_related('review_flags').get(id=record_id, company_id=company_id)
        except NormalizedRecord.DoesNotExist:
            raise KeyError(f'Record {record_id} not found.')

    def _assert_not_locked(self, record: NormalizedRecord):
        if record.is_locked:
            raise PermissionError('This record has been approved and is immutable.')

    def _assert_valid_transition(self, current: str, target: str):
        if (current, target) not in VALID_TRANSITIONS:
            raise ValueError(
                f'Invalid status transition: {current} → {target}. '
                'Approved and Rejected records are terminal states.'
            )

    @transaction.atomic
    def approve(
        self, record_id, company_id, analyst_name: str,
        notes: Optional[str] = None, ip_address: Optional[str] = None
    ) -> NormalizedRecord:
        record = self._get_or_raise(record_id, company_id)
        self._assert_not_locked(record)
        self._assert_valid_transition(record.status, 'Approved')

        snapshot = _capture_snapshot(record)

        record.status = 'Approved'
        record.is_locked = True
        record.reviewed_by = analyst_name
        record.reviewed_at = datetime.now(timezone.utc)
        record.review_notes = notes

        # Resolve all open flags on approval
        now = datetime.now(timezone.utc)
        ReviewFlag.objects.filter(
            normalized_record=record, resolved_at__isnull=True
        ).update(resolved_at=now, resolved_by=analyst_name)

        record.save()

        # Reload to get updated flags
        record.refresh_from_db()

        self._audit.log(
            company_id=company_id,
            entity_type='NormalizedRecord',
            entity_id=record_id,
            action='APPROVED',
            performed_by=analyst_name,
            previous=snapshot,
            next_value={
                'status': record.status,
                'reviewedBy': record.reviewed_by,
                'reviewNotes': record.review_notes,
                'isLocked': record.is_locked,
            },
            changed_fields=['status', 'isLocked', 'reviewedBy', 'reviewedAt', 'reviewNotes'],
            ip_address=ip_address,
        )

        return record

    @transaction.atomic
    def reject(
        self, record_id, company_id, analyst_name: str,
        notes: Optional[str] = None, ip_address: Optional[str] = None
    ) -> NormalizedRecord:
        record = self._get_or_raise(record_id, company_id)
        self._assert_not_locked(record)
        self._assert_valid_transition(record.status, 'Rejected')

        snapshot = _capture_snapshot(record)

        record.status = 'Rejected'
        record.reviewed_by = analyst_name
        record.reviewed_at = datetime.now(timezone.utc)
        record.review_notes = notes
        record.save()

        self._audit.log(
            company_id=company_id,
            entity_type='NormalizedRecord',
            entity_id=record_id,
            action='REJECTED',
            performed_by=analyst_name,
            previous=snapshot,
            next_value={'status': record.status, 'reviewedBy': record.reviewed_by, 'reviewNotes': record.review_notes},
            changed_fields=['status', 'reviewedBy', 'reviewedAt', 'reviewNotes'],
            ip_address=ip_address,
        )

        return record

    @transaction.atomic
    def edit(
        self, record_id, company_id, analyst_name: str,
        quantity=None, unit=None, category=None,
        activity_date=None, review_notes=None,
        ip_address: Optional[str] = None
    ) -> NormalizedRecord:
        record = self._get_or_raise(record_id, company_id)
        self._assert_not_locked(record)

        if record.status in ('Approved', 'Rejected'):
            raise ValueError('Cannot edit records in terminal states (Approved/Rejected).')

        snapshot = _capture_snapshot(record)
        changed_fields = []

        if quantity is not None and quantity != record.quantity:
            record.quantity = quantity
            changed_fields.append('quantity')
        if unit is not None and unit != record.unit:
            record.unit = unit
            changed_fields.append('unit')
        if category is not None and category != record.category:
            record.category = category
            changed_fields.append('category')
        if activity_date is not None and activity_date != record.activity_date:
            record.activity_date = activity_date
            changed_fields.append('activityDate')
        if review_notes is not None:
            record.review_notes = review_notes
            changed_fields.append('reviewNotes')

        if not changed_fields:
            return record   # No-op — avoid spamming audit log

        record.save()

        self._audit.log(
            company_id=company_id,
            entity_type='NormalizedRecord',
            entity_id=record_id,
            action='UPDATED',
            performed_by=analyst_name,
            previous=snapshot,
            next_value=_capture_snapshot(record),
            changed_fields=changed_fields,
            ip_address=ip_address,
        )

        return record
