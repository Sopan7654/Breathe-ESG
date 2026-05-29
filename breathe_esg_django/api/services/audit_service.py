"""
audit_service.py — Writes audit log entries.

Called explicitly by UploadService and RecordService at key state transitions —
not via middleware — giving full control over before/after snapshots.
"""
import json
from ..models import AuditLog


class AuditService:
    """
    Creates AuditLog entries with JSON before/after snapshots.
    Mirrors C# AuditService exactly.
    """

    def log(
        self,
        company_id,
        entity_type: str,
        entity_id,
        action: str,
        performed_by: str,
        previous=None,
        next_value=None,
        changed_fields=None,
        ip_address=None,
        user_agent=None,
    ):
        """
        Create an audit log entry.
        previous and next_value: any JSON-serializable object.
        """
        AuditLog.objects.create(
            company_id=company_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            performed_by=performed_by,
            previous_value=previous,
            new_value=next_value,
            changed_fields=changed_fields or [],
            ip_address=ip_address,
            user_agent=user_agent,
        )
