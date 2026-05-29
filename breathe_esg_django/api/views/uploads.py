"""
views/uploads.py — Upload ingestion and listing.

Mirrors C# UploadsController:
  POST /api/uploads  — ingest file (multipart: file + dataSourceId)
  GET  /api/uploads  — paginated list
"""
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import DataSource
from ..serializers import UploadListItemSerializer
from ..services.upload_service import UploadService
from .helpers import get_company_id, get_analyst_name, get_ip_address


class UploadIngestView(APIView):
    """POST /api/uploads — ingest file."""
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        company_id = get_company_id(request)
        analyst_name = get_analyst_name(request)
        ip_address = get_ip_address(request)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if file_obj.size == 0:
            return Response({'error': 'Uploaded file is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Max 50 MB — enforced in settings but double-check here
        if file_obj.size > 50 * 1024 * 1024:
            return Response({'error': 'File exceeds 50 MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

        data_source_id_str = request.data.get('dataSourceId') or request.data.get('data_source_id')
        if not data_source_id_str:
            return Response({'error': 'dataSourceId is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data_source_id = uuid.UUID(str(data_source_id_str))
        except ValueError:
            return Response({'error': 'Invalid dataSourceId format.'}, status=status.HTTP_400_BAD_REQUEST)

        file_bytes = file_obj.read()
        svc = UploadService()

        try:
            raw_upload, record_count, flagged_count = svc.ingest(
                file_bytes=file_bytes,
                file_name=file_obj.name,
                company_id=company_id,
                data_source_id=data_source_id,
                uploaded_by=analyst_name,
                ip_address=ip_address,
            )
        except DataSource.DoesNotExist as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            err_str = str(e)
            if 'duplicate' in err_str:
                return Response({'error': err_str}, status=status.HTTP_409_CONFLICT)
            return Response({'error': err_str}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'uploadId': str(raw_upload.id),
            'fileName': raw_upload.file_name,
            'rowCount': record_count,
            'flaggedCount': flagged_count,
            'status': raw_upload.status,
            'errorSummary': raw_upload.error_summary,
            'createdAt': raw_upload.created_at,
        })

    def get(self, request):
        """GET /api/uploads — paginated list."""
        company_id = get_company_id(request)
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, int(request.query_params.get('pageSize', 20)))

        svc = UploadService()
        items, total = svc.get_uploads(company_id, page, page_size)

        serializer = UploadListItemSerializer(items, many=True)
        return Response({
            'items': serializer.data,
            'totalCount': total,
            'page': page,
            'pageSize': page_size,
        })
