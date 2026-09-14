from django.db import models

class LifetimePredictionConfig(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    window_size = models.IntegerField(default=64)
    required_telemetry = models.JSONField(default=list)
    model_path = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']

class LifetimePredictionResult(models.Model):
    class Meta:
        managed = False
    cmg_id = models.CharField(max_length=100)
    rul_value = models.FloatField()
    confidence = models.FloatField(null=True, blank=True)
    prediction_time = models.DateTimeField()
    window_data = models.JSONField()
    telemetry_used = models.JSONField()
