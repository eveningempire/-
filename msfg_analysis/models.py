from django.db import models
from data_management.models import PHMModel, PHMData

class MSFGDefinition(models.Model):
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.CASCADE, related_name="msfg_definitions")
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    raw_graph_data = models.JSONField(default=dict)
    processed_graph_data = models.JSONField(default=dict)
    detection_matrix = models.JSONField(null=True, blank=True)
    test_names = models.JSONField(default=list)
    fault_names = models.JSONField(default=list)
    component_names = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = [('cmg_model','name')]

class MSFGNode(models.Model):
    msfg_definition = models.ForeignKey(MSFGDefinition, on_delete=models.CASCADE, related_name="nodes")
    node_id = models.CharField(max_length=64)
    node_type = models.CharField(max_length=20)
    name = models.CharField(max_length=128)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    properties = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class MSFGEdge(models.Model):
    msfg_definition = models.ForeignKey(MSFGDefinition, on_delete=models.CASCADE, related_name="edges")
    edge_id = models.CharField(max_length=64)
    source_node = models.ForeignKey(MSFGNode, on_delete=models.CASCADE, related_name="outgoing_edges")
    target_node = models.ForeignKey(MSFGNode, on_delete=models.CASCADE, related_name="incoming_edges")
    edge_type = models.CharField(max_length=64, blank=True)
    properties = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class MSFGAnalysisResult(models.Model):
    data_point = models.ForeignKey(PHMData, on_delete=models.CASCADE, related_name="msfg_results")
    msfg_definition = models.ForeignKey(MSFGDefinition, on_delete=models.CASCADE, related_name="analysis_results")
    test_results = models.JSONField(default=dict)
    fault_results = models.JSONField(default=dict)
    system_results = models.JSONField(default=dict)
    component_results = models.JSONField(default=dict)
    overall_health_score = models.FloatField(default=1.0)
    detected_faults = models.JSONField(default=list)
    critical_components = models.JSONField(default=list)
    analysis_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class TestPointRuleMapping(models.Model):
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.CASCADE, related_name="msfg_testpoint_mappings")
    rule_definition = models.ForeignKey('rule_detection.RuleDefinition', on_delete=models.CASCADE, related_name="msfg_testpoint_mappings")
    test_name = models.CharField(max_length=128)
    weight = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = [('cmg_model','rule_definition')]

class TestPointRule(models.Model):
    msfg_definition = models.ForeignKey(MSFGDefinition, on_delete=models.CASCADE, related_name='test_point_rules')
    test_name = models.CharField(max_length=128)
    rule_expression = models.TextField(blank=True)
    weight = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=True)
