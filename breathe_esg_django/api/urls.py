"""
api/urls.py — All /api/* routes.
Mirrors the C# controller routes exactly.
"""
from django.urls import path
from .views.records import (
    RecordsListView, RecordSummaryView, RecordDataSourcesView,
    RecordDetailView, RecordApproveView, RecordRejectView,
)
from .views.uploads import UploadIngestView
from .views.audits import AuditListView, AuditEntityView
from .views.flags import FlagsListView

urlpatterns = [
    # Records — order matters: summary and datasources before <record_id>
    path('records/summary',      RecordSummaryView.as_view(),     name='records-summary'),
    path('records/datasources',  RecordDataSourcesView.as_view(), name='records-datasources'),
    path('records',              RecordsListView.as_view(),        name='records-list'),
    path('records/<uuid:record_id>',          RecordDetailView.as_view(),  name='record-detail'),
    path('records/<uuid:record_id>/approve',  RecordApproveView.as_view(), name='record-approve'),
    path('records/<uuid:record_id>/reject',   RecordRejectView.as_view(),  name='record-reject'),

    # Uploads
    path('uploads', UploadIngestView.as_view(), name='uploads'),

    # Audits
    path('audits',                        AuditListView.as_view(),   name='audits-list'),
    path('audits/entity/<uuid:entity_id>', AuditEntityView.as_view(), name='audits-entity'),

    # Flags
    path('flags', FlagsListView.as_view(), name='flags-list'),
]
