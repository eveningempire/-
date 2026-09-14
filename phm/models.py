import uuid

from django.conf import settings
from django.db import models


class TelemetrySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    token_hash = models.CharField(max_length=64)
    columns = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class TelemetrySample(models.Model):
    session = models.ForeignKey(TelemetrySession, on_delete=models.CASCADE, related_name='samples')
    values = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['session', 'id'], name='telemetry_session_cursor')]


class AcceptanceTelemetry(models.Model):
    vehicle_id = models.CharField(max_length=100, db_index=True, default="default")
    values = models.JSONField(default=dict)
    anomaly_fields = models.JSONField(default=dict)
    health_index = models.FloatField(default=1.0)
    status = models.CharField(max_length=20, default="normal", db_index=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)


class StructureNode(models.Model):
    node_key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    node_type = models.CharField(max_length=50, default="component")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    properties = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AlarmRule(models.Model):
    OPERATORS = [("gt", ">"), ("gte", ">="), ("lt", "<"), ("lte", "<="), ("eq", "=")]
    name = models.CharField(max_length=200)
    signal = models.CharField(max_length=100, db_index=True)
    operator = models.CharField(max_length=4, choices=OPERATORS, default="gt")
    threshold = models.FloatField()
    severity = models.CharField(max_length=20, default="warning")
    enabled = models.BooleanField(default=True)
    description = models.TextField(blank=True)


class AuditEvent(models.Model):
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    resource = models.CharField(max_length=200, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
