"""
MSFG鍒嗘瀽搴忓垪鍖栧櫒
"""

from rest_framework import serializers
from data_management.serializers import PHMDataSerializer
from .models import (
    MSFGDefinition, MSFGNode, MSFGEdge, MSFGAnalysisResult, TestPointRuleMapping, TestPointRule, TestPointComponentMapping, FaultComponentMapping, TestPointFaultMapping
)


class MSFGDefinitionSerializer(serializers.ModelSerializer):
    """MSFG瀹氫箟搴忓垪鍖栧櫒"""
    
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)
    
    class Meta:
        model = MSFGDefinition
        fields = [
            'id', 'cmg_model', 'cmg_model_name', 'name', 'description',
            'raw_graph_data', 'processed_graph_data', 'detection_matrix',
            'test_names', 'fault_names', 'component_names',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name']


class MSFGNodeSerializer(serializers.ModelSerializer):
    """MSFG鑺傜偣搴忓垪鍖栧櫒"""
    
    msfg_name = serializers.CharField(source='msfg_definition.name', read_only=True)
    
    class Meta:
        model = MSFGNode
        fields = [
            'id', 'msfg_definition', 'msfg_name', 'node_id', 'node_type',
            'name', 'position_x', 'position_y', 'properties', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'msfg_name']


class MSFGEdgeSerializer(serializers.ModelSerializer):
    """MSFG杈瑰簭鍒楀寲鍣?""
    
    msfg_name = serializers.CharField(source='msfg_definition.name', read_only=True)
    source_node_name = serializers.CharField(source='source_node.name', read_only=True)
    target_node_name = serializers.CharField(source='target_node.name', read_only=True)
    
    class Meta:
        model = MSFGEdge
        fields = [
            'id', 'msfg_definition', 'msfg_name', 'edge_id',
            'source_node', 'target_node', 'source_node_name', 'target_node_name',
            'edge_type', 'properties', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'msfg_name', 'source_node_name', 'target_node_name']


class MSFGAnalysisResultSerializer(serializers.ModelSerializer):
    """MSFG鍒嗘瀽缁撴灉搴忓垪鍖栧櫒"""
    
    data_point = PHMDataSerializer(read_only=True)
    msfg_name = serializers.CharField(source='msfg_definition.name', read_only=True)
    cmg_id = serializers.CharField(source='data_point.cmg.cmg_id', read_only=True)
    timestamp = serializers.DateTimeField(source='data_point.timestamp', read_only=True)
    
    class Meta:
        model = MSFGAnalysisResult
        fields = [
            'id', 'data_point', 'msfg_definition', 'msfg_name',
            'cmg_id', 'timestamp', 'test_results', 'fault_results',
            'system_results', 'component_results', 'overall_health_score', 'detected_faults',
            'critical_components', 'analysis_details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'msfg_name', 'cmg_id', 'timestamp']


class TestPointRuleMappingSerializer(serializers.ModelSerializer):
    """瑙勫垯-娴嬭瘯鐐规槧灏勫簭鍒楀寲鍣?""
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)
    rule_id = serializers.CharField(source='rule_definition.rule_id', read_only=True)

    class Meta:
        model = TestPointRuleMapping
        fields = [
            'id', 'cmg_model', 'cmg_model_name', 'rule_definition', 'rule_id',
            'test_name', 'weight', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name', 'rule_id']


class TestPointRuleSerializer(serializers.ModelSerializer):
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)
    msfg_definition_name = serializers.CharField(source='msfg_definition.name', read_only=True)
    # 璁?msfg_definition 瀛楁鍙€夛紝鍦ㄨ鍥句腑鑷姩濉厖
    msfg_definition = serializers.PrimaryKeyRelatedField(
        queryset=MSFGDefinition.objects.all(), 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = TestPointRule
        fields = [
            'id', 'msfg_definition', 'msfg_definition_name', 'cmg_model', 'cmg_model_name', 
            'test_name', 'rule_id', 'rule_expression', 'weight', 'is_online', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name', 'msfg_definition_name']


class TestPointComponentMappingSerializer(serializers.ModelSerializer):
    """娴嬭瘯鐐?閮ㄤ欢鏄犲皠搴忓垪鍖栧櫒"""
    
    msfg_definition_name = serializers.CharField(source='msfg_definition.name', read_only=True)
    component_type_display = serializers.CharField(source='get_component_type_display', read_only=True)
    
    class Meta:
        model = TestPointComponentMapping
        fields = [
            'id', 'msfg_definition', 'msfg_definition_name', 'test_point_name', 
            'component_name', 'component_type', 'component_type_display',
            'importance_weight', 'is_critical', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'msfg_definition_name', 'component_type_display']


class FaultComponentMappingSerializer(serializers.ModelSerializer):
    msfg_definition_name = serializers.CharField(source='msfg_definition.name', read_only=True)

    class Meta:
        model = FaultComponentMapping
        fields = [
            'id', 'msfg_definition', 'msfg_definition_name', 'fault_name',
            'component_name', 'mapping_type', 'weight', 'is_critical', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'msfg_definition_name']


class TestPointFaultMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestPointFaultMapping
        fields = '__all__'

