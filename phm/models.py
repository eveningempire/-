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
    monitoring_enabled = models.BooleanField(default=False)


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
    NODE_TYPES = [
        ("vehicle", "运载器"),
        ("system", "分系统"),
        ("subsystem", "子系统"),
        ("product", "单机产品"),
    ]
    node_key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES, default="product")
    pbs_code = models.CharField(max_length=100, unique=True, db_index=True)
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


class RealtimeAlarm(models.Model):
    session = models.ForeignKey(TelemetrySession, on_delete=models.CASCADE, related_name="alarms")
    sample = models.ForeignKey(TelemetrySample, on_delete=models.CASCADE, related_name="alarms")
    signal = models.CharField(max_length=100)
    value = models.FloatField()
    threshold = models.FloatField()
    operator = models.CharField(max_length=4)
    severity = models.CharField(max_length=20, default="warning")
    fault_name = models.CharField(max_length=200)
    isolation_target = models.CharField(max_length=200)
    health_index = models.FloatField(default=1.0)
    acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["sample", "signal", "operator", "threshold"], name="unique_realtime_sample_rule_alarm")]


class FaultEvent(models.Model):
    """A diagnosed fault occurrence that can be replayed from persisted telemetry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(TelemetrySession, on_delete=models.CASCADE, related_name="fault_events")
    alarm = models.OneToOneField(RealtimeAlarm, null=True, blank=True, on_delete=models.SET_NULL, related_name="fault_event")
    name = models.CharField(max_length=200)
    severity = models.CharField(max_length=20, default="warning")
    isolation_target = models.CharField(max_length=200, blank=True)
    start_time = models.FloatField(db_index=True)
    end_time = models.FloatField(null=True, blank=True)
    diagnosis = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class FaultReplay(models.Model):
    STATES = [("paused", "paused"), ("playing", "playing"), ("finished", "finished")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(FaultEvent, on_delete=models.CASCADE, related_name="replays")
    window_start = models.FloatField()
    window_end = models.FloatField()
    current_time = models.FloatField()
    speed = models.FloatField(default=1.0)
    state = models.CharField(max_length=20, choices=STATES, default="paused")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReleaseAssessment(models.Model):
    """Traceable vehicle-level reflight/release assessment record."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle_id = models.CharField(max_length=100, db_index=True)
    mission_name = models.CharField(max_length=200, blank=True)
    subsystem_health = models.JSONField(default=dict)
    subsystem_weights = models.JSONField(default=dict)
    system_health_index = models.FloatField()
    mission_success_probability = models.FloatField()
    release_threshold = models.FloatField(default=0.85)
    decision = models.CharField(max_length=30, db_index=True)
    blockers = models.JSONField(default=list, blank=True)
    algorithm_trace = models.JSONField(default=dict, blank=True)
    created_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
