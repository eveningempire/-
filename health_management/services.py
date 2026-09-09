"""
Service layer for health management algorithms.

This module acts as a bridge between the database models and the algorithm
implementations. It defines higher-level functions that can be invoked
from REST API views or scheduled tasks. Each function encapsulates a
distinct processing step: offline anomaly detection, real-time anomaly
detection, rule evaluation, fault diagnosis, health evaluation and life
prediction.

Note: The core algorithms (IMS, rule logic and multi-signal graph) are
implemented in ``health_management.algorithms``. They are imported here
and called with appropriate arguments.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Dict, Any

from data_management.models import PHM, PHMData
from django.utils import timezone
from .models import (
    AnomalyResult,
    Rule,
    RuleResult,
    DiagnosisGraph,
    DiagnosisResult,
    HealthEvaluation,
    LifePrediction,
)

from .algorithms.rules import evaluate_rule  # type: ignore
from .algorithms.multi_signal import diagnose  # type: ignore
from .algorithms.health import fuse_scores, predict_end_of_life  # type: ignore
from .ims_service import run_ims_detection
from health_management.ims_worker import enqueue_cmgdata_ids


def run_offline_anomaly_detection(cmg: PHM, records: Iterable[PHMData]) -> None:
    """Runs IMS detection for a batch of records using real IMS models.

    This replaces the previous placeholder algorithm. For each record, all
    active IMS models associated with the PHM model are executed and results
    are stored in ``IMSDetectionResult``.
    """
    for rec in records:
        try:
            run_ims_detection(rec)
        except Exception:
            # Best-effort; individual record failures should not break the batch
            continue


def handle_real_time_data(cmg: PHM, records: List[Dict[str, Any]]) -> None:
    """Handles streaming data for a PHM and triggers real-time processing.

    Records should be dictionaries with at least 'timestamp' and
    measurement key/values. This function will create DataRecord entries on
    the fly, run the IMS algorithm per record and update the health state.
    """
    for item in records:
        ts_str = item.get("timestamp")
        if ts_str is None:
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = timezone.make_aware(ts)
        data = {k: v for k, v in item.items() if k != "timestamp"}
        rec = PHMData.objects.create(cmg=cmg, timestamp=ts, data=data)
        # 灏嗘娴嬩换鍔℃彁浜ょ粰鐙珛IMS杩涚▼锛岄伩鍏嶉樆濉?        try:
            enqueue_cmgdata_ids([rec.id])
        except Exception:
            pass


def evaluate_rules_and_diagnosis(cmg: PHM, anomaly: AnomalyResult) -> None:
    """Evaluates all applicable rules and diagnosis graphs for an anomaly."""
    # Fetch rules applicable to this PHM's model
    rules = Rule.objects.filter(cmg_model=cmg.cmg_model)
    for rule in rules:
        triggered, details = evaluate_rule(rule.definition, anomaly.data_point.data)
        RuleResult.objects.create(
            anomaly=anomaly,
            rule=rule,
            is_triggered=triggered,
            details=details,
        )
    # Fetch diagnosis graphs applicable to this PHM model
    graphs = DiagnosisGraph.objects.filter(cmg_model=cmg.cmg_model)
    for graph in graphs:
        diag = diagnose(graph.graph_definition, anomaly.data_point.data)
        DiagnosisResult.objects.create(
            anomaly=anomaly,
            graph=graph,
            diagnosis=diag,
        )


def compute_health_evaluation(cmg: PHM) -> None:
    """Recomputes the health evaluation for a PHM from recent data."""
    # Gather recent anomalies, rule results and diagnoses to compute scores
    anomalies = AnomalyResult.objects.filter(
        data_point__cmg=cmg,
        is_anomaly=True,
    ).order_by("-created_at")[:100]  # use last 100 anomalies for example
    # Convert to a structure expected by the fusion algorithm
    anomaly_scores = [a.score for a in anomalies]
    rule_triggers = [list(a.rule_results.values_list("is_triggered", flat=True)) for a in anomalies]
    diagnoses = [list(a.diagnosis_results.values_list("diagnosis", flat=True)) for a in anomalies]
    score, details = fuse_scores(anomaly_scores, rule_triggers, diagnoses)
    HealthEvaluation.objects.create(
        cmg=cmg,
        timestamp=timezone.now(),
        score=score,
        details=details,
    )
    # Optionally update life prediction after each evaluation
    update_life_prediction(cmg)


def update_life_prediction(cmg: PHM) -> None:
    """Updates the life prediction based on current health evaluations."""
    evaluations = HealthEvaluation.objects.filter(cmg=cmg).order_by("timestamp")
    if evaluations.count() < 2:
        return
    # Use the fuse algorithm to predict when the score will reach zero
    end_of_life = predict_end_of_life([(ev.timestamp, ev.score) for ev in evaluations])
    LifePrediction.objects.create(
        cmg=cmg,
        timestamp=timezone.now(),
        predicted_end_time=end_of_life,
    )
