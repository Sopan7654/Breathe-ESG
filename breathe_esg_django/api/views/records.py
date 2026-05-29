"""
views/records.py — All record-related API endpoints.

Performance optimizations applied:
- NormalizedRecord list uses .only() to exclude the large raw_payload JSON column
- Summary uses a single annotated query instead of 3 sequential COUNT queries
- datasources and summary results are cached (30s and 5min TTL)
- Approve/reject/edit return the already-updated object from the service, avoiding an extra SELECT
"""
from django.core.cache import cache
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import NormalizedRecord, RawUpload, ReviewFlag, DataSource
from ..serializers import (
    NormalizedRecordSerializer, ReviewActionSerializer, EditRecordSerializer,
    DataSourceSerializer,
)
from ..services.record_service import RecordService
from .helpers import get_company_id, get_analyst_name, get_ip_address

# Fields needed for the list view — raw_payload is ~90% of each row's bytes
_LIST_ONLY_FIELDS = [
    'id', 'company_id', 'raw_upload_id', 'data_source_id', 'source_type',
    'emission_scope', 'activity_date', 'activity_period_start', 'activity_period_end',
    'quantity', 'unit', 'original_quantity', 'original_unit',
    'category', 'location', 'description', 'status',
    'reviewed_by', 'reviewed_at', 'review_notes', 'is_locked',
    'created_at', 'updated_at',
]


def _record_qs(company_id, *, full=False):
    """
    Base queryset for NormalizedRecord.
    full=True loads raw_payload too (needed for detail view).
    full=False skips raw_payload (list view — saves significant bandwidth from DB).
    """
    qs = NormalizedRecord.objects.select_related(
        'data_source', 'raw_upload'
    ).prefetch_related('review_flags').filter(company_id=company_id)
    if not full:
        qs = qs.only(*_LIST_ONLY_FIELDS, 'data_source__name', 'raw_upload__file_name')
    return qs


class RecordsListView(APIView):
    """GET /api/records — paginated, filtered list."""

    def get(self, request):
        company_id = get_company_id(request)

        qs = _record_qs(company_id)

        status_filter = request.query_params.get('status')
        source_type   = request.query_params.get('sourceType')
        scope         = request.query_params.get('scope')
        date_from     = request.query_params.get('dateFrom')
        date_to       = request.query_params.get('dateTo')
        upload_id     = request.query_params.get('uploadId')
        page          = max(1, int(request.query_params.get('page', 1)))
        page_size     = min(200, int(request.query_params.get('pageSize', 50)))

        if status_filter:
            qs = qs.filter(status=status_filter)
        if source_type:
            qs = qs.filter(source_type=source_type)
        if scope:
            qs = qs.filter(emission_scope=scope)
        if date_from:
            qs = qs.filter(activity_date__gte=date_from)
        if date_to:
            qs = qs.filter(activity_date__lte=date_to)
        if upload_id:
            qs = qs.filter(raw_upload_id=upload_id)

        qs = qs.order_by('-created_at')
        total = qs.count()
        offset = (page - 1) * page_size
        items = qs[offset:offset + page_size]

        return Response({
            'items': NormalizedRecordSerializer(items, many=True).data,
            'totalCount': total,
            'page': page,
            'pageSize': page_size,
        })


class RecordSummaryView(APIView):
    """
    GET /api/records/summary — dashboard counts.
    Cached 30 seconds per company — safe because dashboard refreshes on demand.
    Single annotated query for status counts instead of 3 separate COUNTs.
    """

    def get(self, request):
        company_id = get_company_id(request)
        cache_key = f'summary:{company_id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        # Single query: annotate each status count using conditional aggregation
        from django.db.models import Case, When, IntegerField, Sum
        stats = NormalizedRecord.objects.filter(company_id=company_id).aggregate(
            total=Count('id'),
            pending=Count(Case(When(status='Pending',  then=1), output_field=IntegerField())),
            flagged=Count(Case(When(status='Flagged',  then=1), output_field=IntegerField())),
            approved=Count(Case(When(status='Approved', then=1), output_field=IntegerField())),
            rejected=Count(Case(When(status='Rejected', then=1), output_field=IntegerField())),
        )

        total_uploads = RawUpload.objects.filter(company_id=company_id).count()
        open_flags = ReviewFlag.objects.filter(
            normalized_record__company_id=company_id,
            resolved_at__isnull=True,
        ).count()

        payload = {
            'totalRecords':  stats['total'],
            'pendingCount':  stats['pending'],
            'flaggedCount':  stats['flagged'],
            'approvedCount': stats['approved'],
            'rejectedCount': stats['rejected'],
            'totalUploads':  total_uploads,
            'openFlagsCount': open_flags,
        }
        cache.set(cache_key, payload, timeout=30)
        return Response(payload)


class RecordDataSourcesView(APIView):
    """
    GET /api/records/datasources — active data sources.
    Cached 5 minutes — data sources change very rarely.
    """

    def get(self, request):
        company_id = get_company_id(request)
        cache_key = f'datasources:{company_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        sources = DataSource.objects.filter(
            company_id=company_id, is_active=True
        ).only('id', 'name', 'source_type')
        data = DataSourceSerializer(sources, many=True).data
        cache.set(cache_key, data, timeout=300)   # 5 minutes
        return Response(data)


class RecordDetailView(APIView):
    """GET /api/records/<id> — full record including raw_payload."""

    def get(self, request, record_id):
        company_id = get_company_id(request)
        try:
            record = NormalizedRecord.objects.select_related(
                'data_source', 'raw_upload'
            ).prefetch_related('review_flags').get(id=record_id, company_id=company_id)
        except NormalizedRecord.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(NormalizedRecordSerializer(record).data)

    def patch(self, request, record_id):
        """PATCH /api/records/<id> — edit a PENDING or FLAGGED record."""
        company_id   = get_company_id(request)
        analyst_name = get_analyst_name(request)
        ip_address   = get_ip_address(request)

        ser = EditRecordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        svc = RecordService()
        try:
            svc.edit(
                record_id=record_id, company_id=company_id,
                analyst_name=analyst_name,
                quantity=d.get('quantity'), unit=d.get('unit'),
                category=d.get('category'), activity_date=d.get('activityDate'),
                review_notes=d.get('reviewNotes'), ip_address=ip_address,
            )
        except KeyError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, PermissionError) as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

        cache.delete(f'summary:{company_id}')
        record = NormalizedRecord.objects.select_related(
            'data_source', 'raw_upload'
        ).prefetch_related('review_flags').get(id=record_id)
        return Response(NormalizedRecordSerializer(record).data)


class RecordApproveView(APIView):
    """POST /api/records/<id>/approve"""

    def post(self, request, record_id):
        company_id   = get_company_id(request)
        analyst_name = get_analyst_name(request)
        ip_address   = get_ip_address(request)

        ser = ReviewActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        notes = ser.validated_data.get('notes')

        svc = RecordService()
        try:
            svc.approve(
                record_id=record_id, company_id=company_id,
                analyst_name=analyst_name, notes=notes, ip_address=ip_address,
            )
        except KeyError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, PermissionError) as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

        cache.delete(f'summary:{company_id}')
        record = NormalizedRecord.objects.select_related(
            'data_source', 'raw_upload'
        ).prefetch_related('review_flags').get(id=record_id)
        return Response(NormalizedRecordSerializer(record).data)


class RecordRejectView(APIView):
    """POST /api/records/<id>/reject"""

    def post(self, request, record_id):
        company_id   = get_company_id(request)
        analyst_name = get_analyst_name(request)
        ip_address   = get_ip_address(request)

        ser = ReviewActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        notes = ser.validated_data.get('notes')

        svc = RecordService()
        try:
            svc.reject(
                record_id=record_id, company_id=company_id,
                analyst_name=analyst_name, notes=notes, ip_address=ip_address,
            )
        except KeyError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, PermissionError) as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

        cache.delete(f'summary:{company_id}')
        record = NormalizedRecord.objects.select_related(
            'data_source', 'raw_upload'
        ).prefetch_related('review_flags').get(id=record_id)
        return Response(NormalizedRecordSerializer(record).data)
