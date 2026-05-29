"""
models.py — Django ORM models mirroring the C# entity classes exactly.

Design decisions preserved from the original:
- NormalizedRecord.raw_payload is a JSONField (PostgreSQL JSONB under the hood).
- AuditLog is append-only — no update/delete ever occurs in the service layer.
- is_locked = True on Approved; enforced in service layer, not DB constraints.
- Enum values stored as strings for readability in the DB (matches C# HasConversion<string>).
- Seed data (2 companies + 3 data sources) is loaded via a data migration.
"""
import uuid
from django.db import models


# ---------------------------------------------------------------------------
# Enum choices — mirrors C# enums
# ---------------------------------------------------------------------------
class SourceType(models.TextChoices):
    SAP_FUEL            = 'SapFuel',            'SAP Fuel'
    UTILITY_ELECTRICITY = 'UtilityElectricity', 'Utility Electricity'
    CORPORATE_TRAVEL    = 'CorporateTravel',     'Corporate Travel'


class RecordStatus(models.TextChoices):
    PENDING  = 'Pending',  'Pending'
    FLAGGED  = 'Flagged',  'Flagged'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Rejected'


class UploadStatus(models.TextChoices):
    PROCESSING = 'Processing', 'Processing'
    COMPLETED  = 'Completed',  'Completed'
    FAILED     = 'Failed',     'Failed'


class EmissionScope(models.TextChoices):
    SCOPE1 = 'Scope1', 'Scope 1 — Direct combustion'
    SCOPE2 = 'Scope2', 'Scope 2 — Purchased electricity'
    SCOPE3 = 'Scope3', 'Scope 3 — Value chain'


class FlagSeverity(models.TextChoices):
    WARNING = 'Warning', 'Warning'
    ERROR   = 'Error',   'Error'


# ---------------------------------------------------------------------------
# Company — top-level tenant
# ---------------------------------------------------------------------------
class Company(models.Model):
    """
    Top-level tenant. Every other entity is scoped to a Company.
    Companies are seeded manually — no self-registration flow.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=200)
    slug       = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        ordering = ['name']
        verbose_name_plural = 'companies'

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# DataSource — configured data feed for a company
# ---------------------------------------------------------------------------
class DataSource(models.Model):
    """
    Represents a configured data feed. One company may have multiple sources.
    source_type is immutable after creation — changing it would invalidate all
    existing records that were normalized under the original type.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company     = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='data_sources')
    name        = models.CharField(max_length=200)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    config      = models.JSONField(null=True, blank=True)   # Reserved for future: S3, SFTP, API creds
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'data_sources'
        indexes = [models.Index(fields=['company'])]

    def __str__(self):
        return f'{self.name} ({self.source_type})'


# ---------------------------------------------------------------------------
# RawUpload — immutable record of a file upload event
# ---------------------------------------------------------------------------
class RawUpload(models.Model):
    """
    Immutable record of a file upload event.
    The original file is stored on disk and never deleted — it is the audit anchor.
    SHA-256 hash is computed at upload time to detect re-uploads of identical files.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company          = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='raw_uploads')
    data_source      = models.ForeignKey(DataSource, on_delete=models.RESTRICT, related_name='raw_uploads')
    file_name        = models.CharField(max_length=500)
    file_path        = models.TextField()   # Relative path under UPLOADS_DIR
    file_hash        = models.CharField(max_length=64, db_index=True)   # SHA-256 hex
    file_size_bytes  = models.BigIntegerField(default=0)
    uploaded_by      = models.CharField(max_length=200, blank=True)
    row_count        = models.IntegerField(default=0)
    status           = models.CharField(max_length=20, choices=UploadStatus.choices, default=UploadStatus.PROCESSING)
    error_summary    = models.TextField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'raw_uploads'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['file_hash']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name


# ---------------------------------------------------------------------------
# NormalizedRecord — the canonical record after normalization
# ---------------------------------------------------------------------------
class NormalizedRecord(models.Model):
    """
    The canonical record after normalization.
    Represents a single activity event — one fuel fill, one billing period, one trip leg.

    KEY DESIGN DECISIONS (preserved from C#):
    1. Single unified table across all source types (source-agnostic dashboard).
    2. Both original and normalized values preserved for auditor verification.
    3. raw_payload (JSONB) stores the entire parsed source row for re-normalization.
    4. is_locked = True on APPROVED — enforced in service layer.
    5. activity_period_start/end support utility billing periods that span months.
    """
    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company              = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='normalized_records')
    raw_upload           = models.ForeignKey(RawUpload, on_delete=models.RESTRICT, related_name='normalized_records')
    data_source          = models.ForeignKey(DataSource, on_delete=models.RESTRICT, related_name='normalized_records')

    # Denormalized for fast dashboard filtering without join to DataSource
    source_type          = models.CharField(max_length=30, choices=SourceType.choices)

    # GHG Protocol scope — assigned deterministically in normalization pipeline
    emission_scope       = models.CharField(max_length=10, choices=EmissionScope.choices)

    activity_date        = models.DateField(null=True, blank=True)
    activity_period_start = models.DateField(null=True, blank=True)
    activity_period_end   = models.DateField(null=True, blank=True)

    quantity             = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    unit                 = models.CharField(max_length=50, null=True, blank=True)
    original_quantity    = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    original_unit        = models.CharField(max_length=100, null=True, blank=True)

    category             = models.CharField(max_length=200, null=True, blank=True)
    location             = models.CharField(max_length=500, null=True, blank=True)
    description          = models.CharField(max_length=1000, null=True, blank=True)

    # Full raw source row as JSON — enables re-normalization without re-upload
    raw_payload          = models.JSONField(default=dict)

    status               = models.CharField(max_length=20, choices=RecordStatus.choices, default=RecordStatus.PENDING)
    reviewed_by          = models.CharField(max_length=200, null=True, blank=True)
    reviewed_at          = models.DateTimeField(null=True, blank=True)
    review_notes         = models.CharField(max_length=2000, null=True, blank=True)
    is_locked            = models.BooleanField(default=False)

    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'normalized_records'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['status']),
            models.Index(fields=['source_type']),
            models.Index(fields=['activity_date']),
            models.Index(fields=['emission_scope']),
            models.Index(fields=['company', 'status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.source_type} | {self.activity_date} | {self.quantity} {self.unit}'


# ---------------------------------------------------------------------------
# ReviewFlag — data quality flag attached to a NormalizedRecord
# ---------------------------------------------------------------------------
class ReviewFlag(models.Model):
    """
    Flags are NEVER deleted — resolved_at/resolved_by capture when an analyst cleared them.
    Multiple flags per record are allowed (e.g., NEGATIVE_VALUE + FUTURE_DATE).
    rule_code is a stable string identifier used to group flags in analytics.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record   = models.ForeignKey(
        NormalizedRecord, on_delete=models.CASCADE, related_name='review_flags'
    )
    rule_code           = models.CharField(max_length=100)
    severity            = models.CharField(max_length=10, choices=FlagSeverity.choices)
    description         = models.CharField(max_length=1000)
    resolved_at         = models.DateTimeField(null=True, blank=True)
    resolved_by         = models.CharField(max_length=200, null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_flags'
        indexes = [models.Index(fields=['normalized_record'])]

    def __str__(self):
        return f'{self.rule_code} — {self.severity}'


# ---------------------------------------------------------------------------
# AuditLog — append-only audit trail
# ---------------------------------------------------------------------------
class AuditLog(models.Model):
    """
    Append-only audit trail. Never updated, never deleted.
    Stores before/after JSON snapshots of changed entities.
    changed_fields lists which field names changed — for UI diffing without JSON parsing.
    entity_type + entity_id allow this table to serve multiple entity types.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company        = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name='audit_logs')
    entity_type    = models.CharField(max_length=100)   # e.g., "NormalizedRecord", "RawUpload"
    entity_id      = models.UUIDField()
    action         = models.CharField(max_length=50)     # e.g., "CREATED", "APPROVED"
    performed_by   = models.CharField(max_length=200)
    previous_value = models.JSONField(null=True, blank=True)
    new_value      = models.JSONField(null=True, blank=True)
    changed_fields = models.JSONField(default=list)      # ["Status", "IsLocked", ...]
    ip_address     = models.GenericIPAddressField(null=True, blank=True)
    user_agent     = models.CharField(max_length=500, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['entity_id', 'entity_type']),
            models.Index(fields=['company']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} {self.entity_type} by {self.performed_by}'
