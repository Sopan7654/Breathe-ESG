"""
views/flags.py — Review flags endpoint.

Performance: uses values() to fetch only required columns from both tables
in a single JOIN, never loading full NormalizedRecord model instances.
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import ReviewFlag
from .helpers import get_company_id


class FlagsListView(APIView):
    """GET /api/flags"""

    def get(self, request):
        company_id   = get_company_id(request)
        open_only    = request.query_params.get('openOnly', 'true').lower() not in ('false', '0', 'no')
        severity     = request.query_params.get('severity')
        page         = max(1, int(request.query_params.get('page', 1)))
        page_size    = min(200, int(request.query_params.get('pageSize', 50)))

        # Single query: JOIN review_flags → normalized_records using values()
        # Never loads full model objects — avoids N+1 entirely.
        qs = ReviewFlag.objects.filter(
            normalized_record__company_id=company_id
        ).values(
            'id', 'rule_code', 'severity', 'description',
            'resolved_at', 'created_at',
            'normalized_record_id',
            # JOIN fields from NormalizedRecord
            'normalized_record__description',
            'normalized_record__status',
        )

        if open_only:
            qs = qs.filter(resolved_at__isnull=True)
        if severity:
            qs = qs.filter(severity__iexact=severity)

        total  = qs.count()
        offset = (page - 1) * page_size
        rows   = list(qs.order_by('-created_at')[offset:offset + page_size])

        items_data = [
            {
                'id':                 str(r['id']),
                'normalizedRecordId': str(r['normalized_record_id']),
                'ruleCode':           r['rule_code'],
                'severity':           r['severity'],
                'description':        r['description'],
                'recordDescription':  r['normalized_record__description'] or '',
                'recordStatus':       r['normalized_record__status'],
                'resolvedAt':         r['resolved_at'],
                'createdAt':          r['created_at'],
            }
            for r in rows
        ]

        return Response({
            'items':      items_data,
            'totalCount': total,
            'page':       page,
            'pageSize':   page_size,
        })
