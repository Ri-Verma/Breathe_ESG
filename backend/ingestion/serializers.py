"""
Django REST Framework Serializers for ESG data ingestion.
Handles validation, normalization, and nested relationships.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tenant, RawIngestionLog, EmissionRecord, AuditLog


# ============================================================================
# TENANT SERIALIZER
# ============================================================================

class TenantSerializer(serializers.ModelSerializer):
    """Read-only serializer for Tenant info."""
    
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


# ============================================================================
# AUDIT LOG SERIALIZER
# ============================================================================

class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit trail entries."""
    
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'record', 'user', 'user_name', 'action',
            'previous_state', 'new_state', 'timestamp'
        ]
        read_only_fields = ['id', 'user', 'timestamp', 'previous_state', 'new_state']
Log: Tracks every state change. If an analyst edits a flagged fuel entry on the dashboard, this table records which user changed it, when, the old value, and the new value.


# ============================================================================
# RAW INGESTION LOG SERIALIZER
# ============================================================================

class RawIngestionLogSerializer(serializers.ModelSerializer):
    """Serializer for raw ingestion logs (source-of-truth payloads)."""
    
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = RawIngestionLog
        fields = [
            'id', 'tenant', 'tenant_name', 'source_type', 'source_type_display',
            'raw_payload', 'ingested_at'
        ]
        read_only_fields = ['id', 'ingested_at']


# ============================================================================
# EMISSION RECORD SERIALIZER
# ============================================================================

class EmissionRecordSerializer(serializers.ModelSerializer):
    """
    Main serializer for EmissionRecords with nested audit trails.
    Supports read for all, write only for status/value updates.
    """
    
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    audit_trail = AuditLogSerializer(many=True, read_only=True)
    raw_log = RawIngestionLogSerializer(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = EmissionRecord
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'raw_log',
            'scope',
            'scope_display',
            'category',
            'activity_date',
            'original_value',
            'original_unit',
            'normalized_value',
            'normalized_unit',
            'status',
            'status_display',
            'is_locked',
            'audit_trail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant', 'tenant_name', 'raw_log', 'scope', 'scope_display',
            'original_value', 'original_unit', 'is_locked', 'audit_trail',
            'created_at', 'updated_at'
        ]

    def validate_status(self, value):
        """
        Ensure status transitions are valid.
        APPROVED records cannot be modified.
        """
        instance = self.instance
        
        if instance and instance.is_locked and value != instance.status:
            raise serializers.ValidationError(
                "Cannot change status of a locked (APPROVED) record."
            )
        
        return value

    def validate(self, data):
        """
        Cross-field validation.
        """
        instance = self.instance
        
        # If updating, check if locked
        if instance and instance.is_locked:
            # Only allow non-functional field updates like created_at are read-only
            for field in ['normalized_value', 'category', 'activity_date']:
                if field in data and data[field] != getattr(instance, field):
                    raise serializers.ValidationError(
                        f"Cannot modify {field} on a locked record."
                    )
        
        return data


# ============================================================================
# FILE UPLOAD SERIALIZER (For request handling)
# ============================================================================

class FileUploadSerializer(serializers.Serializer):
    """
    Serializer for handling file upload requests.
    Validates file type and tenant association.
    """
    
    file = serializers.FileField(required=True)
    source_type = serializers.ChoiceField(
        choices=['SAP', 'UTILITY', 'TRAVEL'],
        required=True,
        help_text="Type of source: SAP, UTILITY, or TRAVEL"
    )
    
    def validate_file(self, file):
        """Validate file size and extension."""
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit."
            )
        
        # Check extension
        valid_extensions = {'.csv', '.json'}
        file_ext = file.name.rsplit('.', 1)[-1] if '.' in file.name else ''
        if f'.{file_ext}' not in valid_extensions:
            raise serializers.ValidationError(
                "File must be CSV or JSON format."
            )
        
        return file
    
    def validate(self, data):
        """Cross-field validation."""
        source_type = data.get('source_type')
        file_name = data.get('file').name.lower()
        
        # SAP and UTILITY should be CSV
        if source_type in ['SAP', 'UTILITY'] and not file_name.endswith('.csv'):
            raise serializers.ValidationError(
                f"{source_type} source requires CSV file."
            )
        
        # TRAVEL should be JSON
        if source_type == 'TRAVEL' and not file_name.endswith('.json'):
            raise serializers.ValidationError(
                "TRAVEL source requires JSON file."
            )
        
        return data


# ============================================================================
# BULK OPERATION SERIALIZERS
# ============================================================================

class BulkEmissionUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk updates to emission records.
    Used when analyst approves/flags multiple records at once.
    """
    
    record_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of EmissionRecord IDs to update"
    )
    new_status = serializers.ChoiceField(
        choices=['PENDING', 'FLAGGED', 'APPROVED'],
        required=True,
        help_text="New status to apply to all selected records"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes for the audit log"
    )
    
    def validate_record_ids(self, value):
        """Ensure at least one record ID."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one record ID is required.")
        return value


# ============================================================================
# DASHBOARD SUMMARY SERIALIZER
# ============================================================================

class DashboardSummarySerializer(serializers.Serializer):
    """
    Serializer for dashboard summary statistics.
    Provides counts by scope, status, and category.
    """
    
    total_records = serializers.IntegerField()
    by_scope = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of records by scope (1, 2, 3)"
    )
    by_status = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of records by status"
    )
    by_category = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of records by category"
    )
    recent_uploads = AuditLogSerializer(many=True)
