"""Operational adapters for the project-route MSFG/TEAMS-RT and PCA-iForest methods."""
from __future__ import annotations

import csv
import importlib.util
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


SIGNAL_TESTS = {
    "pressure": {"name": "推进压力测点", "fault": "推进剂供给泄漏", "direction": "low"},
    "temperature": {"name": "动力温度测点", "fault": "动力泵效率下降", "direction": "high"},
    "bus_voltage": {"name": "电源母线电压测点", "fault": "电源母线欠压", "direction": "low"},
    "battery_capacity": {"name": "电池容量测点", "fault": "蓄电池容量衰减", "direction": "low"},
    "attitude_error": {"name": "姿态误差测点", "fault": "姿态传感器偏置", "direction": "abs"},
    "control_error": {"name": "控制误差测点", "fault": "控制执行器迟滞", "direction": "abs"},
}


def _read_numeric(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 8:
        raise ValueError("诊断至少需要 8 行 CSV 数据")
    numeric = {}
    for key in rows[0]:
        values = []
        try:
            for row in rows:
                value = float(row[key])
                if not math.isfinite(value): raise ValueError
                values.append(value)
        except (TypeError, ValueError, KeyError):
            continue
        numeric[key] = np.asarray(values, dtype=float)
    signals = {key: numeric[key] for key in SIGNAL_TESTS if key in numeric}
    if not signals:
        excluded = {"time", "timestamp", "rul", "hi", "hi_norm", "health_index"}
        signals = {key: value for key, value in numeric.items() if key.strip().lower() not in excluded}
    if not signals:
        raise ValueError("CSV 中没有可诊断的数值信号")
    return rows, signals


@lru_cache(maxsize=1)
def _teams_module():
    path = Path(__file__).resolve().parent.parent / "integrations" / "algorithm_assets" / "algorithms" / "legacy_reference" / "teamsrt.py"
    spec = importlib.util.spec_from_file_location("phm_teamsrt_runtime", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def msfg_teams_rt(csv_path):
    rows, signals = _read_numeric(csv_path)
    keys = list(signals)
    faults = [SIGNAL_TESTS.get(key, {}).get("fault", f"{key}异常") for key in keys]
    tests = [SIGNAL_TESTS.get(key, {}).get("name", key) for key in keys]
    matrix = np.eye(len(keys), dtype=int)
    test_results, evidence = [], []
    baseline_count = max(5, min(len(rows) // 3, 30))
    for key in keys:
        values = signals[key]; baseline = values[:baseline_count]
        center, spread = float(np.mean(baseline)), float(np.std(baseline))
        latest = float(np.mean(values[-min(5, len(values)):]))
        robust_scale = max(spread, abs(center) * 0.03, 1e-6)
        z_score = (latest - center) / robust_scale
        direction = SIGNAL_TESTS.get(key, {}).get("direction", "abs")
        failed = z_score < -3 if direction == "low" else z_score > 3 if direction == "high" else abs(z_score) > 3
        test_results.append(1 if failed else 0)
        evidence.append({"signal": key, "test": tests[len(evidence)], "baseline": round(center, 6), "latest": round(latest, 6), "z_score": round(z_score, 4), "failed": failed})
    teams = _teams_module().dmatrixDiag(matrix, np.asarray(test_results), faults, tests)
    candidates = []
    for fault, detail in teams.get("faultprocess", {}).items():
        candidates.append({"name": fault, "state": detail.get("state"), "probability": round(float(detail.get("probability", 0)), 6), "testsource": detail.get("testsource", [])})
    candidates.sort(key=lambda item: (item["state"] == "b", item["probability"]), reverse=True)
    top = candidates[0] if candidates else {"name": "正常", "probability": 1.0}
    abnormal = any(test_results)
    label = top["name"] if abnormal else "正常"
    confidence = top["probability"] if abnormal else 1.0
    class_probs = [{"name": item["name"], "prob": item["probability"]} for item in candidates] or [{"name": "正常", "prob": 1.0}]
    return {"algorithm": "MSFG + TEAMS-RT", "pred_name": label, "aggregate_pred_name": label, "confidence": confidence,
            "n_windows": 1, "seq_len": len(rows), "window_stride": len(rows), "sample_dt": None,
            "window_series": [{"window_index": 0, "time_start": rows[0].get("time", 0), "time_end": rows[-1].get("time", len(rows)-1), "pred_name": label, "confidence": confidence}],
            "class_probs": class_probs, "aggregate_class_probs": class_probs,
            "evidence": evidence, "diagnostic_sets": {"good": teams.get("g", []), "bad": teams.get("b", []), "suspect": teams.get("s", []), "unknown": teams.get("u", [])},
            "d_matrix": {"tests": tests, "faults": faults, "values": matrix.tolist()}, "model_mode": "operational-msfg-teams-rt"}


def _window_matrix(signals, window_size, stride):
    keys = list(signals); length = len(next(iter(signals.values())))
    starts = list(range(0, max(1, length - window_size + 1), stride))
    if not starts or starts[-1] + window_size < length: starts.append(max(0, length - window_size))
    features = []
    for start in starts:
        row = []
        for key in keys:
            segment = signals[key][start:start + window_size]
            row.extend([np.mean(segment), np.std(segment), np.min(segment), np.max(segment), segment[-1] - segment[0]])
        features.append(row)
    return np.asarray(features, dtype=float), starts, keys


def pca_iforest(csv_path):
    rows, signals = _read_numeric(csv_path)
    window_size = max(8, min(30, len(rows) // 5)); stride = max(2, window_size // 2)
    matrix, starts, keys = _window_matrix(signals, window_size, stride)
    if len(matrix) < 4: raise ValueError("PCA–iForest 至少需要形成 4 个滑动窗口")
    baseline_count = max(3, min(len(matrix) // 2, max(3, int(len(matrix) * .4))))
    scaler = StandardScaler().fit(matrix[:baseline_count]); scaled = scaler.transform(matrix)
    components = max(1, min(3, scaled.shape[1], baseline_count - 1))
    pca = PCA(n_components=components, random_state=42).fit(scaled[:baseline_count]); embedded = pca.transform(scaled)
    forest = IsolationForest(n_estimators=200, contamination="auto", random_state=42).fit(embedded[:baseline_count])
    raw_scores = -forest.score_samples(embedded)
    reference = raw_scores[:baseline_count]; threshold = float(np.mean(reference) + 3 * max(np.std(reference), 1e-6))
    anomaly = raw_scores > threshold
    denomin = max(float(raw_scores.max() - raw_scores.min()), 1e-9)
    scores = (raw_scores - raw_scores.min()) / denomin
    windows = []
    for index, start in enumerate(starts):
        windows.append({"window_index": index, "time_start": rows[start].get("time", start), "time_end": rows[min(len(rows)-1, start+window_size-1)].get("time", min(len(rows)-1,start+window_size-1)), "pred_name": "异常" if anomaly[index] else "正常", "confidence": round(float(scores[index] if anomaly[index] else 1-scores[index]), 6), "anomaly_score": round(float(raw_scores[index]), 6)})
    latest = windows[-1]; aggregate = "异常" if anomaly[max(baseline_count, len(anomaly)//2):].mean() >= .3 else "正常"
    loadings = np.abs(pca.components_[0]).reshape(len(keys), 5).mean(axis=1)
    evidence = sorted(({"signal": key, "pca_loading": round(float(loadings[i]), 6), "latest_mean": round(float(np.mean(signals[key][-window_size:])), 6)} for i, key in enumerate(keys)), key=lambda item: item["pca_loading"], reverse=True)
    abnormal_prob = float(np.clip(scores[-1], 0, 1)); probs = [{"name": "异常", "prob": abnormal_prob}, {"name": "正常", "prob": 1-abnormal_prob}]
    explained = float(np.nan_to_num(pca.explained_variance_ratio_, nan=0.0).sum())
    return {"algorithm": "PCA–iForest", "pred_name": latest["pred_name"], "aggregate_pred_name": aggregate, "confidence": latest["confidence"], "n_windows": len(windows), "seq_len": window_size, "window_stride": stride, "sample_dt": None, "window_series": windows, "class_probs": probs, "aggregate_class_probs": probs, "evidence": evidence, "explained_variance": round(explained, 6), "baseline_windows": baseline_count, "anomaly_threshold": round(threshold, 6), "model_mode": "operational-pca-iforest"}
