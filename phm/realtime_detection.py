from .models import AlarmRule, FaultEvent, RealtimeAlarm


DEFAULT_RULES = {
    "pressure": {"operator": "lt", "threshold": 0.88, "fault": "推进剂泄漏", "target": "推进剂供给与压力链路", "severity": "critical"},
    "temperature": {"operator": "gt", "threshold": 0.52, "fault": "动力泵效率下降", "target": "动力泵及温控链路", "severity": "warning"},
    "attitude_error": {"operator": "gt", "threshold": 0.08, "fault": "姿态传感器偏置", "target": "姿态传感器链路", "severity": "critical"},
    "control_error": {"operator": "gt", "threshold": 0.10, "fault": "执行器迟滞", "target": "控制执行机构", "severity": "warning"},
}


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
    return alarms
