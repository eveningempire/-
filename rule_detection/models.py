from django.db import models
from data_management.models import PHMModel, PHMData

class FaultDefinition(models.Model):
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.CASCADE, related_name="fault_definitions")
    fault_name = models.CharField(max_length=128)
    fault_level = models.IntegerField(default=1)
    component = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = [('cmg_model','fault_name')]

class RuleDefinition(models.Model):
    SOURCE_CHOICES = [('expert','Expert'),('data_driven','Data driven')]
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.CASCADE, related_name="rule_definitions")
    fault_definition = models.ForeignKey(FaultDefinition, on_delete=models.CASCADE, related_name="rules")
    rule_id = models.CharField(max_length=64)
    rule_expression = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='expert')
    plan_description = models.TextField(blank=True)
    is_online = models.BooleanField(default=True)
    is_new = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)
    related_parameters = models.JSONField(default=list)
    compiled_rule = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = [('cmg_model','rule_id')]

class RuleDetectionResult(models.Model):
    data_point = models.ForeignKey(PHMData, on_delete=models.CASCADE, related_name="rule_results")
    rule_definition = models.ForeignKey(RuleDefinition, on_delete=models.CASCADE, related_name="detection_results")
    fault_definition = models.ForeignKey(FaultDefinition, on_delete=models.CASCADE, related_name="detection_results")
    is_triggered = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    detection_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

class ComponentDefinition(models.Model):
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.CASCADE, related_name="component_definitions")
    component_name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = [('cmg_model','component_name')]
