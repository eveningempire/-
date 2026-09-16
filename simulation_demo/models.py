import uuid

from django.db import models


class FaultWorkflowTask(models.Model):
    MODES = [("offline", "offline"), ("realtime", "realtime")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    mode = models.CharField(max_length=20, choices=MODES)
    subsystem = models.CharField(max_length=100)
    fault_mode = models.CharField(max_length=100)
    severity = models.FloatField(default=0.5)
    injection_time = models.FloatField(default=20)
    status = models.CharField(max_length=30, default="created")
    current_stage = models.CharField(max_length=30, default="created")
    dataset_id = models.IntegerField(null=True, blank=True)
    latest_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FaultWorkflowEvent(models.Model):
    task = models.ForeignKey(FaultWorkflowTask, on_delete=models.CASCADE, related_name="events")
    sequence = models.PositiveIntegerField()
    timestamp = models.FloatField()
    stage = models.CharField(max_length=30)
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence"]
        unique_together = [("task", "sequence")]
