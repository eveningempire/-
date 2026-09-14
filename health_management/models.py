"""
Models for the health_management application.

These models store outputs of anomaly detection, rule judgement, fault
diagnosis and health assessment. They link back to the raw data records
produced by the data_management app and allow users to query detailed
results at a later time. The actual algorithms run in services.py; these
models persist their outputs.
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone

from data_management.models import PHM, PHMData, PHMModel


class AnomalyResult(models.Model):
    """Stores the outcome of an anomaly detection process.

    Each anomaly result corresponds to a single data record. The
    ``score`` field captures the model's overall anomaly score for the
    record; higher values imply greater deviation from normal behaviour.
    Parameter-level scores can be stored in ``parameter_scores`` for
    per-channel diagnostics. The ``is_anomaly`` flag indicates whether
    the record crossed the configured threshold.
    """

    data_point = models.OneToOneField(
        PHMData,
        on_delete=models.CASCADE,
        related_name="anomaly_result",
        primary_key=True,
    )
    score = models.FloatField(help_text="Overall anomaly score")
    parameter_scores = models.JSONField(
        blank=True, default=dict, help_text="Per-parameter anomaly scores"
    )
    is_anomaly = models.BooleanField(default=False, help_text="Whether this record is anomalous")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anomaly result"
        verbose_name_plural = "Anomaly results"

    def __str__(self) -> str:
        return f"AnomalyResult({self.data_point})"


class Rule(models.Model):
    """Represents a rule that can be applied to anomaly points.

    Rules are defined at the PHM model level. They contain a name and a
    definition, represented as a JSON structure that describes how to
    evaluate the rule given raw telemetry values. The details of rule
    evaluation live in services.py.
    """

    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="PHM model this rule applies to",
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, help_text="Human readable description of the rule")
    definition = models.JSONField(help_text="Machine readable rule definition")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rule"
        verbose_name_plural = "Rules"

    def __str__(self) -> str:
        return self.name


class RuleResult(models.Model):
    """Stores the result of evaluating a rule against an anomaly point."""

    anomaly = models.ForeignKey(AnomalyResult, on_delete=models.CASCADE, related_name="rule_results")
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="results")
    is_triggered = models.BooleanField()
    details = models.JSONField(blank=True, default=dict, help_text="Additional context about the evaluation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rule result"
        verbose_name_plural = "Rule results"
        unique_together = ("anomaly", "rule")

    def __str__(self) -> str:
        return f"RuleResult({self.rule.name}, triggered={self.is_triggered})"


class DiagnosisGraph(models.Model):
    """Defines a multi-signal flow graph used for fault diagnosis.

    The graph structure is stored as a JSON object. The exact format is
    domain specific and should be interpreted by the algorithms defined
    elsewhere. Each graph is tied to a particular PHM model.
    """

    cmg_model = models.ForeignKey(
        PHMModel,
        on_delete=models.CASCADE,
        related_name="diagnosis_graphs",
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    graph_definition = models.JSONField(help_text="Definition of the multi-signal flow graph")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diagnosis graph"
        verbose_name_plural = "Diagnosis graphs"

    def __str__(self) -> str:
        return self.name


class DiagnosisResult(models.Model):
    """Stores the result of running a diagnosis graph on an anomaly point."""

    anomaly = models.ForeignKey(AnomalyResult, on_delete=models.CASCADE, related_name="diagnosis_results")
    graph = models.ForeignKey(DiagnosisGraph, on_delete=models.CASCADE, related_name="results")
    diagnosis = models.JSONField(help_text="Structured diagnosis result")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Diagnosis result"
        verbose_name_plural = "Diagnosis results"
        unique_together = ("anomaly", "graph")

    def __str__(self) -> str:
        return f"DiagnosisResult({self.graph.name})"


class HealthEvaluation(models.Model):
    """Stores a health score computed from multiple inputs.

    The ``score`` field is a number between 0 and 100 where higher values
    indicate better health. ``details`` can store the raw scores and
    weights used in the fusion process.
    """

    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE, related_name="health_evaluations")
    timestamp = models.DateTimeField()
    score = models.FloatField()
    details = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Health evaluation"
        verbose_name_plural = "Health evaluations"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"HealthEvaluation({self.cmg}, score={self.score})"


class LifePrediction(models.Model):
    """Stores a predicted end-of-life timestamp for a PHM based on health scores."""

    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE, related_name="life_predictions")
    timestamp = models.DateTimeField(help_text="When the prediction was computed")
    predicted_end_time = models.DateTimeField(help_text="Predicted time when the PHM's health reaches zero")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Life prediction"
        verbose_name_plural = "Life predictions"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"LifePrediction({self.cmg}, end={self.predicted_end_time:%Y-%m-%d %H:%M:%S})"


class IMSModel(models.Model):
    cmg_model = models.ForeignKey(PHMModel, on_delete=models.CASCADE, related_name="ims_models")
    name = models.CharField(max_length=128)
    parameters = models.JSONField(default=list)
    model_config = models.JSONField(default=dict)
    model_data = models.BinaryField(default=b"")
    threshold = models.FloatField(default=0.5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class IMSDetectionResult(models.Model):
    data_point = models.OneToOneField(PHMData, on_delete=models.CASCADE, related_name="ims_result")
    ims_model = models.ForeignKey(IMSModel, on_delete=models.CASCADE, related_name="detection_results")
    is_anomaly = models.BooleanField(default=False)
    anomaly_score = models.FloatField(default=0.0)
    parameter_scores = models.JSONField(default=dict)
    detection_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
