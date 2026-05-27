from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    """
    Handles Multi-Tenancy. Every client organization gets a Tenant record.
    All data must link back to this to ensure strict data isolation.
    """
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class RawIngestionLog(models.Model):
    """
    Source-of-Truth Tracking. We never discard the original messy data.
    """
    SOURCE_CHOICES = [
        ('SAP', 'SAP Flat File'),
        ('UTILITY', 'Utility Portal CSV'),
        ('TRAVEL', 'Travel API JSON'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='raw_logs')
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    # Storing the exact row or JSON object before any parsing happens
    raw_payload = models.JSONField() 
    ingested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_type} log for {self.tenant.name} at {self.ingested_at}"

class EmissionRecord(models.Model):
    """
    The Normalized Core. This feeds the analyst dashboard.
    """
    SCOPE_CHOICES = [
        (1, 'Scope 1 (Direct)'),
        (2, 'Scope 2 (Indirect - Energy)'),
        (3, 'Scope 3 (Value Chain)'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('FLAGGED', 'Flagged (Data Issue)'),
        ('APPROVED', 'Approved (Locked for Audit)'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='emissions')
    raw_log = models.ForeignKey(RawIngestionLog, on_delete=models.SET_NULL, null=True)
    
    # Categorization
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=100) # e.g., 'Fuel', 'Electricity', 'Air Travel'
    activity_date = models.DateField()
    
    # The messy original data
    original_value = models.FloatField(null=True, blank=True)
    original_unit = models.CharField(max_length=50, null=True, blank=True)
    
    # The normalized data ready for calculations
    normalized_value = models.FloatField(null=True, blank=True)
    normalized_unit = models.CharField(max_length=50, default='kgCO2e')
    
    # Workflow state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} - {self.status}"

class AuditLog(models.Model):
    """
    The Audit Trail. Tracks every time an analyst modifies an EmissionRecord.
    """
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_trail')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # The analyst who made the change
    action = models.CharField(max_length=255) # e.g., "Updated unit from GAL to L"
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit: {self.action} on {self.timestamp}"