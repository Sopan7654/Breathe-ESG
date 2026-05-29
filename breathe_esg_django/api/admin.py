"""
admin.py — Registers all models in Django Admin for operational visibility.
"""
from django.contrib import admin
from .models import Company, DataSource, RawUpload, NormalizedRecord, ReviewFlag, AuditLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'source_type', 'is_active', 'created_at']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name']


@admin.register(RawUpload)
class RawUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'company', 'data_source', 'row_count', 'status', 'uploaded_by', 'created_at']
    list_filter = ['status']
    search_fields = ['file_name', 'uploaded_by']
    readonly_fields = ['file_hash', 'file_path']


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_type', 'emission_scope', 'activity_date', 'quantity', 'unit', 'status', 'is_locked']
    list_filter = ['status', 'source_type', 'emission_scope', 'is_locked']
    search_fields = ['description', 'category', 'location']
    readonly_fields = ['raw_payload', 'created_at', 'updated_at']


@admin.register(ReviewFlag)
class ReviewFlagAdmin(admin.ModelAdmin):
    list_display = ['rule_code', 'severity', 'normalized_record', 'resolved_at', 'resolved_by', 'created_at']
    list_filter = ['severity', 'rule_code']
    search_fields = ['rule_code', 'description']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'entity_type', 'entity_id', 'performed_by', 'ip_address', 'created_at']
    list_filter = ['action', 'entity_type']
    search_fields = ['performed_by', 'entity_type']
    readonly_fields = ['previous_value', 'new_value', 'changed_fields']
