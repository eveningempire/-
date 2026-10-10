"""Operational adapters for PCA-iForest anomaly detection."""
from __future__ import annotations

import csv
import math

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from datasets.schema import column_role, timestamp_value


def _read_numeric(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 8:
        raise ValueError("诊断至少需要 8 行 CSV 数据")
    numeric = {}
    for key in rows[0]:
        if column_role(key) != "parameter":
            continue
        values = []
        try:
            for row in rows:
                value = float(row[key])
                if not math.isfinite(value):
                    raise ValueError
                values.append(value)
        except (TypeError, ValueError, KeyError):
            continue
        numeric[key] = np.asarray(values, dtype=float)
    if not numeric:
        raise ValueError("CSV 中没有可诊断的数值信号")
    return rows, numeric


def _window_matrix(signals, window_size, stride):
    keys = list(signals)
    length = len(next(iter(signals.values())))
    starts = list(range(0, max(1, length - window_size + 1), stride))
    if not starts or starts[-1] + window_size < length:
        starts.append(max(0, length - window_size))
    features = []
    for start in starts:
        row = []
        for key in keys:
            segment = signals[key][start : start + window_size]
            row.extend([np.mean(segment), np.std(segment), np.min(segment), np.max(segment), segment[-1] - segment[0]])
        features.append(row)
    return np.asarray(features, dtype=float), starts, keys


def pca_iforest(csv_path):
    rows, signals = _read_numeric(csv_path)
    window_size = max(8, min(30, len(rows) // 5))
    stride = max(2, window_size // 2)
    matrix, starts, keys = _window_matrix(signals, window_size, stride)
    if len(matrix) < 4:
        raise ValueError("PCA–iForest 至少需要形成 4 个滑动窗口")
    baseline_count = max(3, min(len(matrix) // 2, max(3, int(len(matrix) * 0.4))))
    scaler = StandardScaler().fit(matrix[:baseline_count])
    scaled = scaler.transform(matrix)
    components = max(1, min(3, scaled.shape[1], baseline_count - 1))
    pca = PCA(n_components=components, random_state=42).fit(scaled[:baseline_count])
    embedded = pca.transform(scaled)
    forest = IsolationForest(n_estimators=200, contamination="auto", random_state=42).fit(embedded[:baseline_count])
    raw_scores = -forest.score_samples(embedded)
    reference = raw_scores[:baseline_count]
    threshold = float(np.mean(reference) + 3 * max(np.std(reference), 1e-6))
    anomaly = raw_scores > threshold
    denomin = max(float(raw_scores.max() - raw_scores.min()), 1e-9)
    scores = (raw_scores - raw_scores.min()) / denomin
    windows = []
    for index, start in enumerate(starts):
        end = min(len(rows) - 1, start + window_size - 1)
        windows.append({
            "window_index": index,
            "time_start": timestamp_value(rows[start], start),
            "time_end": timestamp_value(rows[end], end),
            "pred_name": "异常" if anomaly[index] else "正常",
            "confidence": round(float(scores[index] if anomaly[index] else 1 - scores[index]), 6),
            "anomaly_score": round(float(raw_scores[index]), 6),
        })
    latest = windows[-1]
    aggregate = "异常" if anomaly[max(baseline_count, len(anomaly) // 2) :].mean() >= 0.3 else "正常"
    loadings = np.abs(pca.components_[0]).reshape(len(keys), 5).mean(axis=1)
    evidence = sorted(
        (
            {"signal": key, "pca_loading": round(float(loadings[i]), 6), "latest_mean": round(float(np.mean(signals[key][-window_size:])), 6)}
            for i, key in enumerate(keys)
        ),
        key=lambda item: item["pca_loading"],
        reverse=True,
    )
    abnormal_prob = float(np.clip(scores[-1], 0, 1))
    probs = [{"name": "异常", "prob": abnormal_prob}, {"name": "正常", "prob": 1 - abnormal_prob}]
    explained = float(np.nan_to_num(pca.explained_variance_ratio_, nan=0.0).sum())
    return {
        "algorithm": "PCA–iForest 异常检测",
        "pred_name": latest["pred_name"],
        "aggregate_pred_name": aggregate,
        "confidence": latest["confidence"],
        "n_windows": len(windows),
        "seq_len": window_size,
        "window_stride": stride,
        "sample_dt": None,
        "window_series": windows,
        "class_probs": probs,
        "aggregate_class_probs": probs,
        "evidence": evidence,
        "explained_variance": round(explained, 6),
        "baseline_windows": baseline_count,
        "anomaly_threshold": round(threshold, 6),
        "model_mode": "operational-pca-iforest",
    }
