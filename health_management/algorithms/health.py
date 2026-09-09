"""
Stub implementations for health score fusion and life prediction.

The fusion function combines anomaly scores, rule trigger counts and
diagnosis results into a single health score between 0 and 100. The life
prediction function extrapolates the trend of health scores over time to
estimate when the health will reach zero.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any


def fuse_scores(
    anomaly_scores: List[float],
    rule_triggers: List[List[bool]],
    diagnoses: List[List[Any]],
) -> Tuple[float, Dict[str, Any]]:
    """
    Fuses multiple inputs into a single health score.

    Args:
        anomaly_scores: A list of anomaly scores (higher is worse).
        rule_triggers: A list of lists indicating which rules were triggered.
        diagnoses: A list of diagnosis results (not used in this stub).

    Returns:
        A tuple (score, details) where score is between 0 and 100.
    """
    if not anomaly_scores:
        return 100.0, {"detail": "No anomalies"}
    # Normalize anomaly scores to 0–100 (assuming a maximum possible score of 200)
    normalized = [max(0.0, min(1.0, s / 200.0)) for s in anomaly_scores]
    avg_anomaly = sum(normalized) / len(normalized)
    # Compute rule impact as fraction of triggered rules
    rule_counts = [sum(triggers) for triggers in rule_triggers] if rule_triggers else [0]
    max_rules = max(len(triggers) for triggers in rule_triggers) if rule_triggers else 1
    avg_rule = sum(c / max_rules for c in rule_counts) / len(rule_counts)
    # Combine anomaly and rule contributions equally
    raw_score = (1.0 - (avg_anomaly + avg_rule) / 2.0) * 100.0
    score = max(0.0, min(100.0, raw_score))
    details = {
        "avg_anomaly": avg_anomaly,
        "avg_rule": avg_rule,
        "normalized_anomalies": normalized,
        "rule_counts": rule_counts,
    }
    return score, details


def predict_end_of_life(history: List[Tuple[datetime, float]]) -> datetime:
    """
    Predicts when the health score will reach zero.

    Args:
        history: A list of (timestamp, score) tuples sorted by time.

    Returns:
        A datetime representing the predicted end of life. If there is no
        decreasing trend the prediction will be 10 years in the future.
    """
    if len(history) < 2:
        return datetime.utcnow() + timedelta(days=3650)
    # Simple linear extrapolation on the last two points
    (t0, s0), (t1, s1) = history[-2], history[-1]
    dt = (t1 - t0).total_seconds()
    ds = s1 - s0
    # Guard against zero/negative dt or non-decreasing trend
    if dt <= 0 or ds >= 0:
        return datetime.utcnow() + timedelta(days=3650)
    rate = ds / dt  # score change per second (negative)
    if rate == 0:
        return datetime.utcnow() + timedelta(days=3650)
    seconds_to_zero = (0.0 - s1) / rate
    if seconds_to_zero < 0:
        seconds_to_zero = 0
    return t1 + timedelta(seconds=seconds_to_zero)