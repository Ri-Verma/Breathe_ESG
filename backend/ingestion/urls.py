"""
URL routing for ESG ingestion API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet,
    RawIngestionLogViewSet,
    EmissionRecordViewSet,
    AuditLogViewSet,
    FileUploadViewSet,
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'raw-logs', RawIngestionLogViewSet, basename='raw-log')
router.register(r'emissions', EmissionRecordViewSet, basename='emission')
router.register(r'audits', AuditLogViewSet, basename='audit')
router.register(r'upload', FileUploadViewSet, basename='file-upload')

urlpatterns = [
    path('', include(router.urls)),
]
