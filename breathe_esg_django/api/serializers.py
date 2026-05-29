"""
serializers.py — DRF serializers mirroring C# DTOs exactly.
Preserves camelCase field names for frontend compatibility.
"""
from rest_framework import serializers
from .models import NormalizedRecord, RawUpload, AuditLog, ReviewFlag, DataSource


# ---------------------------------------------------------------------------
# ReviewFlag / FlagDto
# ---------------------------------------------------------------------------
class ReviewFlagSerializer(serializers.ModelSerializer):
    id          = serializers.UUIDField()
    ruleCode    = serializers.CharField(source='rule_code')
    severity    = serializers.CharField()
    description = serializers.CharField()
    resolvedAt  = serializers.DateTimeField(source='resolved_at')
    resolvedBy  = serializers.CharField(source='resolved_by')
    createdAt   = serializers.DateTimeField(source='created_at')

    class Meta:
        model = ReviewFlag
        fields = ['id', 'ruleCode', 'severity', 'description', 'resolvedAt', 'resolvedBy', 'createdAt']


# ---------------------------------------------------------------------------
# NormalizedRecord / RecordDto
# ---------------------------------------------------------------------------
class NormalizedRecordSerializer(serializers.ModelSerializer):
    id                  = serializers.UUIDField()
    companyId           = serializers.UUIDField(source='company_id')
    rawUploadId         = serializers.UUIDField(source='raw_upload_id')
    sourceType          = serializers.CharField(source='source_type')
    emissionScope       = serializers.CharField(source='emission_scope')
    activityDate        = serializers.DateField(source='activity_date', format='%Y-%m-%d')
    activityPeriodStart = serializers.DateField(source='activity_period_start', format='%Y-%m-%d')
    activityPeriodEnd   = serializers.DateField(source='activity_period_end', format='%Y-%m-%d')
    quantity            = serializers.DecimalField(max_digits=18, decimal_places=4)
    unit                = serializers.CharField()
    originalQuantity    = serializers.DecimalField(source='original_quantity', max_digits=18, decimal_places=4)
    originalUnit        = serializers.CharField(source='original_unit')
    category            = serializers.CharField()
    location            = serializers.CharField()
    description         = serializers.CharField()
    status              = serializers.CharField()
    reviewedBy          = serializers.CharField(source='reviewed_by')
    reviewedAt          = serializers.DateTimeField(source='reviewed_at')
    reviewNotes         = serializers.CharField(source='review_notes')
    isLocked            = serializers.BooleanField(source='is_locked')
    flags               = ReviewFlagSerializer(source='review_flags', many=True)
    dataSourceName      = serializers.SerializerMethodField()
    fileName            = serializers.SerializerMethodField()
    createdAt           = serializers.DateTimeField(source='created_at')
    updatedAt           = serializers.DateTimeField(source='updated_at')

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'companyId', 'rawUploadId', 'sourceType', 'emissionScope',
            'activityDate', 'activityPeriodStart', 'activityPeriodEnd',
            'quantity', 'unit', 'originalQuantity', 'originalUnit',
            'category', 'location', 'description',
            'status', 'reviewedBy', 'reviewedAt', 'reviewNotes', 'isLocked',
            'flags', 'dataSourceName', 'fileName', 'createdAt', 'updatedAt',
        ]

    def get_dataSourceName(self, obj):
        try:
            return obj.data_source.name
        except Exception:
            return ''

    def get_fileName(self, obj):
        try:
            return obj.raw_upload.file_name
        except Exception:
            return ''


# ---------------------------------------------------------------------------
# Paginated record list response
# ---------------------------------------------------------------------------
class RecordListResponseSerializer(serializers.Serializer):
    items      = NormalizedRecordSerializer(many=True)
    totalCount = serializers.IntegerField()
    page       = serializers.IntegerField()
    pageSize   = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Upload / UploadResponseDto + UploadListItemDto
# ---------------------------------------------------------------------------
class UploadResponseSerializer(serializers.Serializer):
    uploadId     = serializers.UUIDField()
    fileName     = serializers.CharField()
    rowCount     = serializers.IntegerField()
    flaggedCount = serializers.IntegerField()
    status       = serializers.CharField()
    errorSummary = serializers.CharField(allow_null=True)
    createdAt    = serializers.DateTimeField()


class UploadListItemSerializer(serializers.ModelSerializer):
    id             = serializers.UUIDField()
    fileName       = serializers.CharField(source='file_name')
    dataSourceName = serializers.SerializerMethodField()
    sourceType     = serializers.SerializerMethodField()
    rowCount       = serializers.IntegerField(source='row_count')
    status         = serializers.CharField()
    uploadedBy     = serializers.CharField(source='uploaded_by')
    errorSummary   = serializers.CharField(source='error_summary', allow_null=True)
    createdAt      = serializers.DateTimeField(source='created_at')

    class Meta:
        model = RawUpload
        fields = ['id', 'fileName', 'dataSourceName', 'sourceType',
                  'rowCount', 'status', 'uploadedBy', 'errorSummary', 'createdAt']

    def get_dataSourceName(self, obj):
        try:
            return obj.data_source.name
        except Exception:
            return ''

    def get_sourceType(self, obj):
        try:
            return obj.data_source.source_type
        except Exception:
            return ''


class UploadListResponseSerializer(serializers.Serializer):
    items      = UploadListItemSerializer(many=True)
    totalCount = serializers.IntegerField()
    page       = serializers.IntegerField()
    pageSize   = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Audit / AuditLogDto
# ---------------------------------------------------------------------------
class AuditLogSerializer(serializers.ModelSerializer):
    id            = serializers.UUIDField()
    entityType    = serializers.CharField(source='entity_type')
    entityId      = serializers.UUIDField(source='entity_id')
    action        = serializers.CharField()
    performedBy   = serializers.CharField(source='performed_by')
    previousValue = serializers.JSONField(source='previous_value', allow_null=True)
    newValue      = serializers.JSONField(source='new_value', allow_null=True)
    changedFields = serializers.JSONField(source='changed_fields')
    ipAddress     = serializers.IPAddressField(source='ip_address', allow_null=True)
    createdAt     = serializers.DateTimeField(source='created_at')

    class Meta:
        model = AuditLog
        fields = ['id', 'entityType', 'entityId', 'action', 'performedBy',
                  'previousValue', 'newValue', 'changedFields', 'ipAddress', 'createdAt']


class AuditListResponseSerializer(serializers.Serializer):
    items      = AuditLogSerializer(many=True)
    totalCount = serializers.IntegerField()
    page       = serializers.IntegerField()
    pageSize   = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Flags / FlagListItemDto
# ---------------------------------------------------------------------------
class FlagListItemSerializer(serializers.Serializer):
    id                = serializers.UUIDField()
    normalizedRecordId = serializers.UUIDField()
    ruleCode          = serializers.CharField()
    severity          = serializers.CharField()
    description       = serializers.CharField()
    recordDescription = serializers.CharField()
    recordStatus      = serializers.CharField()
    resolvedAt        = serializers.DateTimeField(allow_null=True)
    createdAt         = serializers.DateTimeField()


# ---------------------------------------------------------------------------
# Dashboard summary / DashboardSummaryDto
# ---------------------------------------------------------------------------
class DashboardSummarySerializer(serializers.Serializer):
    totalRecords  = serializers.IntegerField()
    pendingCount  = serializers.IntegerField()
    flaggedCount  = serializers.IntegerField()
    approvedCount = serializers.IntegerField()
    rejectedCount = serializers.IntegerField()
    totalUploads  = serializers.IntegerField()
    openFlagsCount = serializers.IntegerField()


# ---------------------------------------------------------------------------
# DataSource / DataSourceDto
# ---------------------------------------------------------------------------
class DataSourceSerializer(serializers.ModelSerializer):
    id         = serializers.UUIDField()
    name       = serializers.CharField()
    sourceType = serializers.CharField(source='source_type')

    class Meta:
        model = DataSource
        fields = ['id', 'name', 'sourceType']


# ---------------------------------------------------------------------------
# Request body DTOs
# ---------------------------------------------------------------------------
class ReviewActionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class EditRecordSerializer(serializers.Serializer):
    quantity     = serializers.DecimalField(max_digits=18, decimal_places=4, required=False, allow_null=True)
    unit         = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    category     = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    activityDate = serializers.DateField(required=False, allow_null=True)
    reviewNotes  = serializers.CharField(required=False, allow_null=True, allow_blank=True)
