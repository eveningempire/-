"""
瑙勫垯妫€娴嬪簭鍒楀寲鍣?"""

from rest_framework import serializers
from data_management.serializers import PHMDataSerializer
from .models import (
    FaultDefinition, RuleDefinition, RuleDetectionResult, 
    ComponentDefinition
)


class FaultDefinitionSerializer(serializers.ModelSerializer):
    """鏁呴殰瀹氫箟搴忓垪鍖栧櫒"""
    
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)
    
    class Meta:
        model = FaultDefinition
        fields = [
            'id', 'cmg_model', 'cmg_model_name', 'fault_name', 'fault_level',
            'component', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name']


class RuleDefinitionSerializer(serializers.ModelSerializer):
    """瑙勫垯瀹氫箟搴忓垪鍖栧櫒"""
    
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)
    fault_name = serializers.CharField(source='fault_definition.fault_name', read_only=True)
    
    class Meta:
        model = RuleDefinition
        fields = [
            'id', 'cmg_model', 'cmg_model_name', 'fault_definition', 'fault_name',
            'rule_id', 'rule_expression', 'source', 'plan_description',
            'is_online', 'is_new', 'is_editable', 'related_parameters',
            'compiled_rule', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name', 'fault_name']


class RuleDetectionResultSerializer(serializers.ModelSerializer):
    """瑙勫垯妫€娴嬬粨鏋滃簭鍒楀寲鍣?""
    
    data_point = PHMDataSerializer(read_only=True)
    rule_definition = RuleDefinitionSerializer(read_only=True)
    fault_definition = FaultDefinitionSerializer(read_only=True)
    rule_id = serializers.CharField(source='rule_definition.rule_id', read_only=True)
    fault_name = serializers.CharField(source='fault_definition.fault_name', read_only=True)
    cmg_id = serializers.CharField(source='data_point.cmg.cmg_id', read_only=True)
    timestamp = serializers.DateTimeField(source='data_point.timestamp', read_only=True)
    
    class Meta:
        model = RuleDetectionResult
        fields = [
            'id', 'data_point', 'rule_definition', 'fault_definition',
            'rule_id', 'fault_name', 'cmg_id', 'timestamp',
            'is_triggered', 'confidence_score', 'detection_details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'rule_id', 'fault_name', 'cmg_id', 'timestamp']


class ComponentDefinitionSerializer(serializers.ModelSerializer):
    """缁勪欢瀹氫箟搴忓垪鍖栧櫒"""
    
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)
    
    class Meta:
        model = ComponentDefinition
        fields = [
            'id', 'cmg_model', 'cmg_model_name', 'component_name',
            'description', 'parameters', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name']

