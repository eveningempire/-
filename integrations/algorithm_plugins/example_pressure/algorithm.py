"""Demonstration only: threshold values are not calibrated for real vehicles."""
import csv
import math


def predict(csv_path, parameters):
    signal = parameters["signal"]
    threshold = parameters["threshold"]
    with open(csv_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or signal not in rows[0]:
        raise ValueError(f"数据中缺少测点 {signal}")
    values = [float(row[signal]) for row in rows]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("测点数据含非有限数值")
    latest = values[-1]
    abnormal = latest < threshold
    label = "压力低于示例阈值" if abnormal else "正常"
    return {
        "pred_name": label,
        "aggregate_pred_name": label,
        "confidence": None,
        "n_windows": 1,
        "seq_len": len(rows),
        "window_stride": len(rows),
        "window_series": [{"window_index": 0, "time_start": 0, "time_end": len(rows) - 1, "pred_name": label, "confidence": None}],
        "evidence": [{"signal": signal, "latest": latest, "threshold": threshold, "rule": "latest < threshold"}],
        "decision_rule": "示例压力阈值规则；阈值需按实际设备标定",
    }
