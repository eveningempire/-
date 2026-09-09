"""
Serializers for the health_management application.

These serializers define how complex objects like anomalies, rules,
diagnoses and health evaluations are converted to and from JSON. They are
used by viewsets defined in views.py.
"""

from __future__ import annotations

from rest_framework import serializers

from data_management.serializers import PHMSerializer, PHMDataSerializer
from data_management.models import PHMModel
from .models import (
    AnomalyResult,
    Rule,
    RuleResult,
    DiagnosisGraph,
    DiagnosisResult,
    HealthEvaluation,
    LifePrediction,
    IMSModel,
    IMSDetectionResult,
)


class AnomalyResultSerializer(serializers.ModelSerializer):
    """Serializes AnomalyResult objects."""

    data_point = PHMDataSerializer(read_only=True)

    class Meta:
        model = AnomalyResult
        fields = ["data_point", "score", "parameter_scores", "is_anomaly", "created_at"]


class RuleSerializer(serializers.ModelSerializer):
    """Serializes Rule objects."""

    cmg_model = serializers.PrimaryKeyRelatedField(queryset=PHMModel.objects.all())

    class Meta:
        model = Rule
        fields = ["id", "cmg_model", "name", "description", "definition", "created_at", "updated_at"]


class RuleResultSerializer(serializers.ModelSerializer):
    """Serializes RuleResult objects."""

    anomaly = serializers.PrimaryKeyRelatedField(queryset=AnomalyResult.objects.all())
    rule = serializers.PrimaryKeyRelatedField(queryset=Rule.objects.all())

    class Meta:
        model = RuleResult
        fields = ["id", "anomaly", "rule", "is_triggered", "details", "created_at"]


class DiagnosisGraphSerializer(serializers.ModelSerializer):
    """Serializes DiagnosisGraph objects."""

    cmg_model = serializers.PrimaryKeyRelatedField(queryset=PHMModel.objects.all())

    class Meta:
        model = DiagnosisGraph
        fields = ["id", "cmg_model", "name", "description", "graph_definition", "created_at", "updated_at"]


class DiagnosisResultSerializer(serializers.ModelSerializer):
    """Serializes DiagnosisResult objects."""

    anomaly = serializers.PrimaryKeyRelatedField(queryset=AnomalyResult.objects.all())
    graph = serializers.PrimaryKeyRelatedField(queryset=DiagnosisGraph.objects.all())

    class Meta:
        model = DiagnosisResult
        fields = ["id", "anomaly", "graph", "diagnosis", "created_at"]


class HealthEvaluationSerializer(serializers.ModelSerializer):
    """Serializes HealthEvaluation objects."""

    cmg = serializers.PrimaryKeyRelatedField(queryset=PHMSerializer.Meta.model.objects.all())

    class Meta:
        model = HealthEvaluation
        fields = ["id", "cmg", "timestamp", "score", "details", "created_at"]


class LifePredictionSerializer(serializers.ModelSerializer):
    """Serializes LifePrediction objects."""

    cmg = serializers.PrimaryKeyRelatedField(queryset=PHMSerializer.Meta.model.objects.all())

    class Meta:
        model = LifePrediction
        fields = ["id", "cmg", "timestamp", "predicted_end_time", "created_at"]


class IMSModelSerializer(serializers.ModelSerializer):
    """Serializes IMSModel objects."""
    
    cmg_model_name = serializers.CharField(source='cmg_model.model_name', read_only=True)

    class Meta:
        model = IMSModel
        fields = [
            'id', 'cmg_model', 'cmg_model_name', 'name', 'parameters', 
            'model_config', 'threshold', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'cmg_model_name']


class IMSDetectionResultSerializer(serializers.ModelSerializer):
    """Serializes IMSDetectionResult objects."""
    
    data_point = PHMDataSerializer(read_only=True)
    ims_model_name = serializers.CharField(source='ims_model.name', read_only=True)
    cmg_id = serializers.CharField(source='data_point.cmg.cmg_id', read_only=True)
    timestamp = serializers.DateTimeField(source='data_point.timestamp', read_only=True)

    class Meta:
        model = IMSDetectionResult
        fields = [
            'id', 'data_point', 'ims_model', 'ims_model_name', 'cmg_id', 'timestamp',
            'is_anomaly', 'anomaly_score', 'parameter_scores', 'detection_details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'ims_model_name', 'cmg_id', 'timestamp']
