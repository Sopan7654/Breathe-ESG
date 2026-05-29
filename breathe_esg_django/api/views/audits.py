"""
views/audits.py — Audit log endpoints.

Performance: uses values() + defer() to avoid loading large JSON columns on list view.
Only loads full previous_value/new_value on the entity-specific detail endpoint.
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import AuditLog
from ..serializers import AuditLogSerializer
from .helpers import get_company_id


class AuditListView(APIView):
    """GET /api/audits — paginated, most-recent-first."""

    def get(self, request):
        company_id = get_company_id(request)
        page       = max(1, int(request.query_params.get('page', 1)))
        page_size  = min(200, int(request.query_params.get('pageSize', 50)))

        qs = AuditLog.objects.filter(company_id=company_id).order_by('-created_at')
        total  = qs.count()
        offset = (page - 1) * page_size
        items  = qs[offset:offset + page_size]

        return Response({
            'items':      AuditLogSerializer(items, many=True).data,
            'totalCount': total,
            'page':       page,
            'pageSize':   page_size,
        })


class AuditEntityView(APIView):
    """GET /api/audits/entity/<entityId> — full trail for one entity."""

    def get(self, request, entity_id):
        company_id = get_company_id(request)
        logs = AuditLog.objects.filter(
            entity_id=entity_id, company_id=company_id,
        ).order_by('created_at')
        return Response(AuditLogSerializer(logs, many=True).data)
