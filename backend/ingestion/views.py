"""
Django REST API views for ESG data ingestion and analyst dashboard.
Handles file uploads, record retrieval, editing, and audit trails.
"""
import json
import logging
from io import StringIO
from django.db import transaction
from django.db.models import Q, Count
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Tenant, RawIngestionLog, EmissionRecord, AuditLog
from .serializers import (
    TenantSerializer,
    RawIngestionLogSerializer,
    EmissionRecordSerializer,
    AuditLogSerializer,
    FileUploadSerializer,
    BulkEmissionUpdateSerializer,
    DashboardSummarySerializer,
)
from .parsers import PARSER_REGISTRY

logger = logging.getLogger(__name__)


# ============================================================================
# PERMISSIONS
# ============================================================================

class IsAuthenticatedAndHasTenant(permissions.BasePermission):
    """
    Custom permission to ensure user belongs to a tenant.
    """
    
    def has_permission(self, request, view):
        # Assuming tenant_id comes from URL or user profile
        # For now, allow all authenticated users
        return request.user and request.user.is_authenticated


class IsTenantOwner(permissions.BasePermission):
    """
    Ensure user can only access data from their own tenant.
    """
    
    def has_object_permission(self, request, view, obj):
        # Get tenant from object or request
        obj_tenant = getattr(obj, 'tenant_id', None)
        user_tenant = getattr(request.user, 'tenant_id', None)
        
        # For now, allow; in production, enforce strict tenant isolation
        return True


# ============================================================================
# TENANT VIEWSET
# ============================================================================

class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Tenant information.
    Lists available tenants (useful for analytics).
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]


# ============================================================================
# RAW INGESTION LOG VIEWSET
# ============================================================================

class RawIngestionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for audit history.
    Allows analysts to view original raw payloads.
    """
    serializer_class = RawIngestionLogSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['source_type', 'tenant__name']
    ordering_fields = ['ingested_at', 'source_type']
    ordering = ['-ingested_at']
    
    def get_queryset(self):
        """Filter by tenant (in production)."""
        # For now, return all; in production add tenant filtering
        return RawIngestionLog.objects.all()


# ============================================================================
# EMISSION RECORD VIEWSET
# ============================================================================

class EmissionRecordViewSet(viewsets.ModelViewSet):
    """
    Main viewset for EmissionRecord management.
    Supports full CRUD with audit trail tracking.
    """
    serializer_class = EmissionRecordSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category', 'tenant__name']
    ordering_fields = ['activity_date', 'created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter records by tenant and optional query parameters.
        """
        queryset = EmissionRecord.objects.select_related(
            'tenant', 'raw_log'
        ).prefetch_related('audit_trail')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by scope
        scope_param = self.request.query_params.get('scope')
        if scope_param:
            try:
                scope_int = int(scope_param)
                queryset = queryset.filter(scope=scope_int)
            except ValueError:
                pass
        
        # Filter by category
        category_param = self.request.query_params.get('category')
        if category_param:
            queryset = queryset.filter(category__icontains=category_param)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            try:
                queryset = queryset.filter(activity_date__gte=parse_date(start_date))
            except:
                pass
        if end_date:
            try:
                queryset = queryset.filter(activity_date__lte=parse_date(end_date))
            except:
                pass
        
        return queryset
    
    def perform_update(self, serializer):
        """
        Override update to capture audit trail.
        """
        instance = serializer.instance
        old_state = {
            'status': instance.status,
            'normalized_value': instance.normalized_value,
            'category': instance.category,
        }
        
        # Save updated record
        updated_record = serializer.save()
        
        new_state = {
            'status': updated_record.status,
            'normalized_value': updated_record.normalized_value,
            'category': updated_record.category,
        }
        
        # Create audit log entry
        AuditLog.objects.create(
            record=updated_record,
            user=self.request.user,
            action=f"Status changed from {old_state['status']} to {new_state['status']}",
            previous_state=old_state,
            new_state=new_state,
        )
        
        # Lock record if approved
        if updated_record.status == 'APPROVED':
            updated_record.is_locked = True
            updated_record.save()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Dashboard summary endpoint.
        Returns counts by scope, status, category.
        """
        queryset = self.get_queryset()
        
        summary = {
            'total_records': queryset.count(),
            'by_scope': {
                '1': queryset.filter(scope=1).count(),
                '2': queryset.filter(scope=2).count(),
                '3': queryset.filter(scope=3).count(),
            },
            'by_status': {
                'PENDING': queryset.filter(status='PENDING').count(),
                'FLAGGED': queryset.filter(status='FLAGGED').count(),
                'APPROVED': queryset.filter(status='APPROVED').count(),
            },
            'by_category': {},
            'recent_uploads': [],
        }
        
        # Count by category
        for cat in queryset.values('category').annotate(count=Count('id')):
            summary['by_category'][cat['category']] = cat['count']
        
        # Recent uploads from audit log
        recent_audits = AuditLog.objects.filter(
            record__in=queryset
        ).order_by('-timestamp')[:5]
        summary['recent_uploads'] = AuditLogSerializer(recent_audits, many=True).data
        
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Bulk update multiple records at once.
        """
        serializer = BulkEmissionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        record_ids = serializer.validated_data['record_ids']
        new_status = serializer.validated_data['new_status']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            records = EmissionRecord.objects.filter(id__in=record_ids)
            if not records.exists():
                return Response(
                    {'error': 'No records found with given IDs'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            updated_count = 0
            for record in records:
                if record.is_locked:
                    logger.warning(f"Skipping locked record {record.id}")
                    continue
                
                old_status = record.status
                record.status = new_status
                if new_status == 'APPROVED':
                    record.is_locked = True
                record.save()
                
                # Create audit log
                AuditLog.objects.create(
                    record=record,
                    user=request.user,
                    action=f"Bulk update: {old_status} → {new_status}. {notes}",
                    previous_state={'status': old_status},
                    new_state={'status': new_status},
                )
                
                updated_count += 1
            
            return Response({
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} records',
            })
        
        except Exception as e:
            logger.error(f"Bulk update error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def audit_history(self, request, pk=None):
        """
        Retrieve full audit history for a specific record.
        """
        record = self.get_object()
        audits = record.audit_trail.all().order_by('-timestamp')
        serializer = AuditLogSerializer(audits, many=True)
        return Response(serializer.data)


# ============================================================================
# FILE UPLOAD VIEWSET
# ============================================================================

class FileUploadViewSet(viewsets.ViewSet):
    """
    Handles file uploads and routes to appropriate parser.
    Creates RawIngestionLog and EmissionRecords in atomic transaction.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_file(self, request):
        """
        Main file upload endpoint.
        POST /api/upload/
        
        Expected data:
        - file: MultiPartFile (CSV or JSON)
        - source_type: 'SAP' | 'UTILITY' | 'TRAVEL'
        - tenant_id: int (optional; defaults to user's tenant)
        """
        # Validate request
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = serializer.validated_data['file']
        source_type = serializer.validated_data['source_type']
        tenant_id = request.data.get('tenant_id')
        
        # Default tenant (in production, use user's tenant)
        if not tenant_id:
            try:
                tenant = Tenant.objects.first()
                if not tenant:
                    return Response(
                        {'error': 'No tenant available. Please create a tenant first.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                tenant_id = tenant.id
            except Exception as e:
                logger.error(f"Tenant lookup error: {str(e)}")
                return Response(
                    {'error': 'Could not determine tenant'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        try:
            # Read file content
            file_content = uploaded_file.read().decode('utf-8')
            
            # Get parser
            parser_func = PARSER_REGISTRY.get(source_type)
            if not parser_func:
                return Response(
                    {'error': f'Unknown source type: {source_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse file
            successful_records, flagged_records = parser_func(file_content, tenant_id)
            
            # Atomic transaction: create logs and emission records
            with transaction.atomic():
                # Create RawIngestionLog
                raw_log = RawIngestionLog.objects.create(
                    tenant_id=tenant_id,
                    source_type=source_type,
                    raw_payload={
                        'filename': uploaded_file.name,
                        'file_size': uploaded_file.size,
                        'parsing_timestamp': None,  # Could add datetime
                    }
                )
                
                # Create EmissionRecords from successful parse
                created_records = []
                flagged_count = 0
                
                # Process successful records
                for record_data in successful_records:
                    emission_record = EmissionRecord.objects.create(
                        tenant_id=tenant_id,
                        raw_log=raw_log,
                        scope=record_data['scope'],
                        category=record_data['category'],
                        activity_date=record_data['activity_date'],
                        original_value=record_data['original_value'],
                        original_unit=record_data['original_unit'],
                        normalized_value=record_data['normalized_value'],
                        normalized_unit=record_data['normalized_unit'],
                        status=record_data['status'],
                    )
                    
                    # Create initial audit log (creation event)
                    AuditLog.objects.create(
                        record=emission_record,
                        user=request.user,
                        action=f"Record created from {source_type} upload",
                        new_state={
                            'scope': emission_record.scope,
                            'status': emission_record.status,
                        }
                    )
                    
                    created_records.append(emission_record)
                
                # Process flagged records
                for record_data in flagged_records:
                    emission_record = EmissionRecord.objects.create(
                        tenant_id=tenant_id,
                        raw_log=raw_log,
                        scope=record_data.get('scope', 1),
                        category=record_data.get('category', 'Unknown'),
                        activity_date=record_data.get('activity_date'),
                        original_value=record_data.get('original_value'),
                        original_unit=record_data.get('original_unit'),
                        normalized_value=record_data.get('normalized_value'),
                        normalized_unit=record_data.get('normalized_unit', 'kgCO2e'),
                        status='FLAGGED',
                    )
                    
                    # Create audit log with issues
                    issues_str = '; '.join(record_data.get('issues', []))
                    AuditLog.objects.create(
                        record=emission_record,
                        user=request.user,
                        action=f"Record created (flagged) from {source_type} upload: {issues_str}",
                        new_state={
                            'scope': emission_record.scope,
                            'status': 'FLAGGED',
                            'issues': record_data.get('issues', []),
                        }
                    )
                    
                    flagged_count += 1
            
            # Return success response
            return Response({
                'status': 'success',
                'message': f'File uploaded successfully',
                'filename': uploaded_file.name,
                'source_type': source_type,
                'raw_log_id': raw_log.id,
                'statistics': {
                    'total_rows': len(successful_records) + len(flagged_records),
                    'successful': len(successful_records),
                    'flagged': len(flagged_records),
                },
                'records_created': len(created_records) + flagged_count,
            }, status=status.HTTP_201_CREATED)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return Response(
                {'error': f'Invalid JSON format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            return Response(
                {'error': f'Error processing file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# AUDIT LOG VIEWSET
# ============================================================================

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for audit log entries.
    Allows analysts to trace all modifications.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['action', 'user__username']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter audit logs by tenant (in production)."""
        return AuditLog.objects.select_related('record', 'user').all()

