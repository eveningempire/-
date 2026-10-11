import csv
import tempfile
from pathlib import Path

from .models import AlarmRule, FaultEvent, RealtimeAlarm, RealtimeDetectionResult


DEFAULT_RULES = {
    "pressure": {"operator": "lt", "threshold": 0.88, "fault": "推进剂泄漏", "target": "推进剂供给与压力链路", "severity": "critical"},
    "temperature": {"operator": "gt", "threshold": 0.52, "fault": "动力泵效率下降", "target": "动力泵及温控链路", "severity": "warning"},
    "attitude_error": {"operator": "gt", "threshold": 0.08, "fault": "姿态传感器偏置", "target": "姿态传感器链路", "severity": "critical"},
    "control_error": {"operator": "gt", "threshold": 0.10, "fault": "执行器迟滞", "target": "控制执行机构", "severity": "warning"},
}

ALGORITHMS = {"rules", "hier14", "msfg_teams_rt", "pca_iforest"}


def _hit(value, operator, threshold):
    return {"gt": value > threshold, "gte": value >= threshold, "lt": value < threshold, "lte": value <= threshold, "eq": value == threshold}[operator]


def detect_sample(session, sample):
    if not session.monitoring_enabled:
        return []
    values = sample.values
    configured = {}
    for rule in AlarmRule.objects.filter(enabled=True):
        configured.setdefault(rule.signal, []).append({
            "operator": rule.operator, "threshold": rule.threshold,
            "severity": rule.severity, "fault": rule.name,
            "target": rule.description or f"{rule.signal} 信号链路",
        })
    alarms = []
    for signal, raw in values.items():
        if signal == "time":
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        candidates = list(configured.get(signal, []))
        if signal in DEFAULT_RULES:
            candidates.append(DEFAULT_RULES[signal])
        for rule in candidates:
            operator, threshold, severity = rule["operator"], rule["threshold"], rule["severity"]
            if _hit(value, operator, threshold):
                distance = abs(value - threshold) / max(abs(threshold), 1e-6)
                health_index = max(0.0, min(1.0, 1.0 - distance))
                alarm = RealtimeAlarm.objects.create(session=session, sample=sample, signal=signal, value=value, threshold=threshold, operator=operator, severity=severity, fault_name=rule["fault"], isolation_target=rule["target"], health_index=round(health_index, 4))
                timestamp = values.get("time")
                if isinstance(timestamp, (int, float)):
                    FaultEvent.objects.create(
                        session=session, alarm=alarm, name=rule["fault"], severity=severity,
                        isolation_target=rule["target"], start_time=float(timestamp), end_time=float(timestamp),
                        diagnosis={"signal": signal, "value": value, "operator": operator,
                                   "threshold": threshold, "health_index": round(health_index, 4)},
                    )
                alarms.append(alarm)
    # A model is evaluated only after enough samples have accumulated. This
    # prevents calling an offline/windowed model for every point and ensures
    # updated telemetry schemas are sent to the same platform algorithm used
    # by batch diagnosis.
    algorithm = getattr(session, "detection_algorithm", "rules") or "rules"
    if algorithm != "rules":
        count = session.samples.filter(id__lte=sample.id).count()
        window = max(8, int(getattr(session, "algorithm_window_size", 30) or 30))
        stride = max(1, int(getattr(session, "algorithm_stride", 10) or 10))
        if count >= window and (count - window) % stride == 0:
            try:
                result = run_window_algorithm(session, sample.id)
                result_row = RealtimeDetectionResult.objects.create(
                    session=session, sample=sample, algorithm=algorithm,
                    decision=result.get("decision", "uncertain"),
                    confidence=result.get("confidence"),
                    fault_name=result.get("fault_name", ""),
                    window_start=result.get("window_start"), window_end=result.get("window_end"),
                    result=result,
                )
                if result_row.decision == "abnormal":
                    fault = result_row.fault_name or "算法检测异常"
                    alarm = RealtimeAlarm.objects.create(
                        session=session, sample=sample, signal="algorithm", value=float(result_row.confidence or 0),
                        threshold=0.55, operator="gte", severity="critical", fault_name=fault,
                        isolation_target=result.get("isolation_target", "算法输出对象"),
                        health_index=max(0.0, min(1.0, 1.0 - float(result_row.confidence or 0))),
                    )
                    timestamp = sample.values.get("time")
                    FaultEvent.objects.create(
                        session=session, alarm=alarm, name=fault, severity="critical",
                        isolation_target=alarm.isolation_target,
                        start_time=float(result.get("window_start", timestamp)), end_time=float(result.get("window_end", timestamp)),
                        diagnosis={"algorithm": algorithm, "result_id": result_row.id, **result},
                    )
                    alarms.append(alarm)
            except Exception as exc:
                # Persist an explicit error result. A model failure must not
                # turn into a misleading pressure threshold alarm.
                RealtimeDetectionResult.objects.create(
                    session=session, sample=sample, algorithm=algorithm,
                    decision="error", result={"error": str(exc), "algorithm": algorithm},
                )
    return alarms


def run_window_algorithm(session, cursor_id):
    """Run the exact batch adapter against the current rolling CSV window."""
    from fault_diagnosis.views import _run_algorithm, _standardize_result, _quality_for_csv

    window = max(8, int(getattr(session, "algorithm_window_size", 30) or 30))
    samples = list(session.samples.order_by("-id").filter(id__lte=cursor_id)[:window])[::-1]
    if len(samples) < window:
        raise ValueError(f"算法窗口需要至少 {window} 个采样点")
    columns = list(session.columns or samples[0].values)
    # Telemetry uses ``time``; the trained Hier14 adapter consumes ``Time``.
    export_columns = ['Time' if key == 'time' and session.detection_algorithm == 'hier14' else key
                      for key in columns]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", newline="", encoding="utf-8-sig", delete=False) as handle:
        writer = csv.DictWriter(handle, fieldnames=export_columns)
        writer.writeheader()
        writer.writerows({export: sample.values.get(key) for key, export in zip(columns, export_columns)}
                         for sample in samples)
        path = Path(handle.name)
    try:
        quality = _quality_for_csv(path)
        raw = _run_algorithm(session.detection_algorithm, path)
        result = _standardize_result(raw, quality)
    finally:
        path.unlink(missing_ok=True)
    result["window_start"] = float(samples[0].values.get("time", 0))
    result["window_end"] = float(samples[-1].values.get("time", 0))
    result["fault_name"] = result.get("aggregate_pred_name") or result.get("pred_name") or ""
    result["isolation_target"] = "算法输出对象"
    return result
