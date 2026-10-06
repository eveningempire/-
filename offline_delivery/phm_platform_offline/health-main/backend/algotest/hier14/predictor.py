"""Hier14 scope_data.csv inference for health platform demo."""

from __future__ import annotations

import json
import os
import pickle
import sys
from functools import lru_cache
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

_ALGO_DIR = os.path.dirname(os.path.abspath(__file__))
_CHECKPOINT_DIR = os.path.join(_ALGO_DIR, "checkpoints")
_DEFAULT_REPO = os.path.abspath(
    os.path.join(_ALGO_DIR, "..", "..", "..", "..", "fault_diagnosis_tcn_transformer")
)

ROW_INTERVAL = 4
FEATURE_CLIP = 5.0
RAW_DT = 0.031
SAMPLE_DT = RAW_DT * ROW_INTERVAL


def _ensure_diag_repo_on_path() -> str:
    repo = os.environ.get("HIER14_REPO", _DEFAULT_REPO)
    if not os.path.isdir(repo):
        raise FileNotFoundError(
            f"Hier14 source repo not found at {repo}. "
            "Set HIER14_REPO to fault_diagnosis_tcn_transformer checkout."
        )
    if repo not in sys.path:
        sys.path.insert(0, repo)
    return repo


@lru_cache(maxsize=1)
def _load_runtime() -> Dict[str, Any]:
    _ensure_diag_repo_on_path()
    import torch
    from src.config_loader import load_config
    from src.models.hierarchical_tcn_transformer import build_model
    from src.residual_features import build_gnc_residual_features_v21
    from src.utils import load_checkpoint

    meta_path = os.path.join(_CHECKPOINT_DIR, "deploy_meta.json")
    scaler_path = os.path.join(_CHECKPOINT_DIR, "scaler.pkl")
    model_path = os.path.join(_CHECKPOINT_DIR, "best_model.pth")
    for path in (meta_path, scaler_path, model_path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Missing Hier14 artifact: {path}")

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    cfg = load_config("hier14")
    cfg.checkpoint_dir = _CHECKPOINT_DIR

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(cfg).to(device)
    load_checkpoint(model, None, model_path, map_location=device)
    model.eval()

    return {
        "meta": meta,
        "scaler": scaler,
        "model": model,
        "device": device,
        "raw_columns": list(cfg.feature_columns),
        "build_residuals": build_gnc_residual_features_v21,
    }


def _prepare_features(df: pd.DataFrame, runtime: Dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    raw_cols = runtime["raw_columns"]
    meta = runtime["meta"]
    cols_56 = meta["active_feature_columns"]

    # Platform uploads commonly use lower-case ``time`` or ``timestamp``;
    # normalize aliases to the training schema before sorting.
    if "Time" not in df.columns:
        for alias in ("time", "timestamp", "Timestamp", "TIME"):
            if alias in df.columns:
                df = df.rename(columns={alias: "Time"})
                break
    if "Time" not in df.columns:
        df = df.copy()
        df.insert(0, "Time", np.arange(len(df), dtype=np.float64))

    work = df.sort_values("Time").reset_index(drop=True)
    missing = [c for c in raw_cols if c not in work.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    work[raw_cols] = work[raw_cols].ffill().bfill()
    work = work.dropna(subset=raw_cols)
    if len(work) < meta["seq_len"] * ROW_INTERVAL:
        raise ValueError(
            f"Not enough rows after cleaning (need >= {meta['seq_len'] * ROW_INTERVAL}, got {len(work)})"
        )

    work = work.iloc[::ROW_INTERVAL].reset_index(drop=True)
    times = work["Time"].to_numpy(dtype=np.float64)
    resid = runtime["build_residuals"](work, sample_dt=SAMPLE_DT)
    feat = pd.concat([work[raw_cols], resid], axis=1)[cols_56].values.astype(np.float32)
    return feat, times


def _slide_windows(feat: np.ndarray, seq_len: int, stride: int) -> np.ndarray:
    if len(feat) < seq_len:
        raise ValueError(f"Feature length {len(feat)} < seq_len {seq_len}")
    if len(feat) == seq_len:
        return feat[np.newaxis, ...]
    windows = []
    for start in range(0, len(feat) - seq_len + 1, stride):
        windows.append(feat[start : start + seq_len])
    if not windows:
        windows.append(feat[-seq_len:])
    return np.stack(windows, axis=0)


def _window_times(
    times: np.ndarray, window_index: int, seq_len: int, stride: int
) -> tuple[float, float]:
    start_idx = window_index * stride
    end_idx = start_idx + seq_len - 1
    end_idx = min(end_idx, len(times) - 1)
    return float(times[start_idx]), float(times[end_idx])


def _rank_class_probs(probs: np.ndarray, class_names: List[str]) -> List[Dict[str, Any]]:
    return sorted(
        [
            {"class_id": i, "name": class_names[i], "prob": float(probs[i])}
            for i in range(len(class_names))
        ],
        key=lambda x: x["prob"],
        reverse=True,
    )


def predict_scope_csv(csv_path: str) -> Dict[str, Any]:
    import torch

    runtime = _load_runtime()
    meta = runtime["meta"]
    seq_len = int(meta["seq_len"])
    stride = int(meta.get("window_stride", 64))
    class_names: List[str] = list(meta["class_names"])

    df = pd.read_csv(csv_path)
    feat, times = _prepare_features(df, runtime)
    windows = _slide_windows(feat, seq_len, stride)
    scaled = runtime["scaler"].transform(windows.reshape(-1, windows.shape[-1]))
    scaled = scaled.reshape(windows.shape).astype(np.float32)
    np.clip(scaled, -FEATURE_CLIP, FEATURE_CLIP, out=scaled)

    device = runtime["device"]
    model = runtime["model"]
    probs_sum = np.zeros(len(class_names), dtype=np.float64)
    window_series: List[Dict[str, Any]] = []
    all_probs: List[np.ndarray] = []

    with torch.no_grad():
        batch_size = 64
        for batch_start in range(0, len(scaled), batch_size):
            batch = torch.from_numpy(scaled[batch_start : batch_start + batch_size]).to(device)
            last_pred, _ = model.encode_last_pred(batch)
            heads = model.forward_heads(last_pred)
            logits = model.to_flat_logits(heads)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            probs_sum += probs.sum(axis=0)
            all_probs.append(probs)

    probs_all = np.concatenate(all_probs, axis=0)
    for i, probs in enumerate(probs_all):
        pred_label = int(probs.argmax())
        time_start, time_end = _window_times(times, i, seq_len, stride)
        window_series.append(
            {
                "window_index": i,
                "time_start": time_start,
                "time_end": time_end,
                "pred_label": pred_label,
                "pred_name": class_names[pred_label],
                "confidence": float(probs[pred_label]),
                "p_normal": float(probs[0]),
                "top3": [
                    {
                        "class_id": int(idx),
                        "name": class_names[int(idx)],
                        "prob": float(probs[int(idx)]),
                    }
                    for idx in probs.argsort()[-3:][::-1]
                ],
            }
        )

    avg_probs = probs_sum / len(scaled)
    last_probs = probs_all[-1]
    last_label = int(last_probs.argmax())

    return {
        "pred_label": last_label,
        "pred_name": class_names[last_label],
        "aggregate_pred_label": int(avg_probs.argmax()),
        "aggregate_pred_name": class_names[int(avg_probs.argmax())],
        "n_windows": int(len(scaled)),
        "seq_len": seq_len,
        "window_stride": stride,
        "sample_dt": SAMPLE_DT,
        "csv_path": os.path.abspath(csv_path),
        "class_probs": _rank_class_probs(last_probs, class_names),
        "aggregate_class_probs": _rank_class_probs(avg_probs, class_names),
        "original_probs": {f"class_{i}": float(last_probs[i]) for i in range(len(class_names))},
        "window_series": window_series,
    }
