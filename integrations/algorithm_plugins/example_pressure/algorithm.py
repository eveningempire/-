"""Offline plugin loading demonstration.

This is an interface and asset-loading example, not a calibrated vehicle model.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path


_ASSET = Path(__file__).with_name("weights.json")


def _number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("输入数据包含非有限数值")
    return number


def predict(csv_path: str, parameters: dict) -> dict:
    asset = json.loads(_ASSET.read_text(encoding="utf-8"))
    signal = str(parameters.get("signal") or asset.get("default_signal", "pressure"))
    threshold = float(parameters.get("threshold", asset.get("default_threshold", 0.8)))
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 8:
        raise ValueError("示例算法至少需要 8 行 CSV 数据")
    if not rows or signal not in rows[0]:
        raise ValueError(f"CSV 中不存在测点列: {signal}")
    values = [_number(row[signal]) for row in rows]
    latest = values[-1]
    abnormal = latest < threshold
    label = asset.get("fault_label", "压力异常") if abnormal else asset.get("normal_label", "正常")
    confidence = min(0.99, 0.55 + abs(latest - threshold) / max(abs(threshold), 1.0))
    time_key = "time" if "time" in rows[0] else "Time" if "Time" in rows[0] else None
    start_time = rows[0].get(time_key) if time_key else 0
    end_time = rows[-1].get(time_key) if time_key else len(rows) - 1
    return {
        "pred_name": label,
        "aggregate_pred_name": label,
        "confidence": round(confidence, 4),
        "evidence": {"signal": signal, "latest_value": latest, "threshold": threshold},
        "window_series": [{
            "window_index": 0,
            "time_start": start_time,
            "time_end": end_time,
            "pred_name": label,
            "confidence": round(confidence, 4)
        }],
        "decision_rule": "示例规则：最新测点值低于阈值时标记为压力异常",
        "asset_loaded": _ASSET.name
    }
