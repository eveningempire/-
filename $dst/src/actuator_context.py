"""执行器工作阶段推导与推理期 logits 调整（telemetry / time 双模式）。"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

# 阶段名称与 one-hot 列
PHASE_NAMES: Tuple[str, ...] = ("ascent", "rcs", "grid_fin", "full")
PHASE_TO_ID: Dict[str, int] = {n: i for i, n in enumerate(PHASE_NAMES)}
ACTUATOR_PHASE_COLUMNS: List[str] = [f"phase_{n}" for n in PHASE_NAMES]

# 局部类 id：0=Normal, 1=TVC, 2=RCS, 3=GridFin, 4=Controller, 5=GyroBias, 6=GyroStuck
PHASE_ALLOWED_CLASSES: Dict[str, Tuple[int, ...]] = {
    "ascent": (0, 1, 5, 6),
    "rcs": (0, 2, 5, 6),
    "grid_fin": (0, 3, 4, 5, 6),
    "full": (0, 1, 2, 3, 4, 5, 6),
}

# 全局 class_id -> 故障窗有效的执行器阶段（telemetry 规则）
FAULT_VALID_PHASES: Dict[int, Tuple[str, ...]] = {
    8: ("ascent",),           # TVC
    9: ("rcs",),              # RCS
    10: ("grid_fin",),        # 栅格舵
    11: ("grid_fin",),        # 控制器
    12: ("ascent", "rcs", "grid_fin", "full"),  # 陀螺恒偏差
    13: ("ascent", "rcs", "grid_fin", "full"),  # 陀螺卡死
}


def valid_phases_for_fault(global_class_id: int) -> Tuple[str, ...]:
    """返回该全局故障类允许的执行器阶段。"""
    return FAULT_VALID_PHASES.get(int(global_class_id), PHASE_NAMES)

DEFAULT_BAND_STATS: Dict = {
    "ft_on_threshold": 1.0e4,
    "rcs_activity_threshold": 0.05,
    "fin_activity_threshold": 0.05,
    "time_ascent_end_s": 120.0,
    "time_rcs_end_s": 280.0,
    "sample_dt": 0.125,
}

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_BAND_STATS_PATH = os.path.join(
    _PROJECT_ROOT, "data", "processed", "actuator_band_stats.json"
)


def load_band_stats(path: Optional[str] = None) -> Dict:
    path = path or DEFAULT_BAND_STATS_PATH
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_BAND_STATS)
        merged.update(data)
        return merged
    return dict(DEFAULT_BAND_STATS)


def _rolling_std(series: pd.Series, sample_dt: float, sec: float = 2.0) -> pd.Series:
    win = max(4, int(round(sec / sample_dt)))
    return series.rolling(win, min_periods=4).std().bfill().ffill().fillna(0.0)


def _fin_activity(df: pd.DataFrame, sample_dt: float) -> pd.Series:
    s14 = _rolling_std(df["S14"], sample_dt)
    s15 = _rolling_std(df["S15"], sample_dt)
    return s14 + s15


def _rcs_activity(df: pd.DataFrame, sample_dt: float) -> pd.Series:
    return _rolling_std(df["S10_Y"], sample_dt)


def derive_actuator_phase_series(
    df: pd.DataFrame,
    mode: str = "telemetry",
    band_stats: Optional[Dict] = None,
    sample_dt: float = 0.125,
) -> pd.Series:
    """
    逐行推导 ActuatorPhase。
    mode: telemetry（默认）| time（仅 exp-5 负对照）
    """
    stats = band_stats or load_band_stats()
    n = len(df)
    phases = np.full(n, "full", dtype=object)

    if mode == "time":
        if "Time" not in df.columns:
            return pd.Series(phases, index=df.index)
        t = df["Time"].values.astype(np.float64)
        t_ascent = float(stats.get("time_ascent_end_s", 120.0))
        t_rcs = float(stats.get("time_rcs_end_s", 280.0))
        phases[t < t_ascent] = "ascent"
        phases[(t >= t_ascent) & (t < t_rcs)] = "rcs"
        phases[t >= t_rcs] = "grid_fin"
        return pd.Series(phases, index=df.index)

    ft_thr = float(stats.get("ft_on_threshold", 1.0e4))
    rcs_thr = float(stats.get("rcs_activity_threshold", 0.05))
    fin_thr = float(stats.get("fin_activity_threshold", 0.05))

    ft = df["FT"].values.astype(np.float64) if "FT" in df.columns else np.zeros(n)
    rcs_act = _rcs_activity(df, sample_dt).values
    fin_act = _fin_activity(df, sample_dt).values

    ascent_mask = ft > ft_thr
    phases[ascent_mask] = "ascent"

    fin_mask = (~ascent_mask) & (fin_act > fin_thr)
    phases[fin_mask] = "grid_fin"

    rcs_mask = (~ascent_mask) & (~fin_mask) & (rcs_act > rcs_thr)
    phases[rcs_mask] = "rcs"

    return pd.Series(phases, index=df.index)


def phase_onehot_frame(
    phase_series: pd.Series,
) -> pd.DataFrame:
    out = pd.DataFrame(index=phase_series.index)
    for name, col in zip(PHASE_NAMES, ACTUATOR_PHASE_COLUMNS):
        out[col] = (phase_series.values == name).astype(np.float32)
    return out


def allowed_classes_for_phase(phase: str) -> Tuple[int, ...]:
    return PHASE_ALLOWED_CLASSES.get(str(phase), PHASE_ALLOWED_CLASSES["full"])


def soft_phase_prior(
    phase: str,
    num_classes: int = 7,
    prior_matrix: Optional[Dict[str, Sequence[float]]] = None,
) -> np.ndarray:
    """返回 log 先验向量（长度 num_classes）。"""
    default = {
        "ascent": [1.2, 1.5, 0.3, 0.3, 0.5, 1.0, 1.0],
        "rcs": [1.2, 0.3, 1.5, 0.4, 0.4, 1.0, 1.0],
        "grid_fin": [1.2, 0.3, 0.3, 1.3, 1.3, 1.0, 1.0],
        "full": [1.0] * num_classes,
    }
    matrix = prior_matrix or default
    probs = np.array(matrix.get(str(phase), matrix["full"]), dtype=np.float64)
    if len(probs) < num_classes:
        probs = np.pad(probs, (0, num_classes - len(probs)), constant_values=1.0)
    probs = probs[:num_classes]
    probs = probs / probs.sum()
    return np.log(probs + 1e-12)


def apply_logit_adjustment(
    logits: np.ndarray,
    phases: Sequence[str],
    mode: str = "soft",
    num_classes: int = 7,
    prior_matrix: Optional[Dict[str, Sequence[float]]] = None,
) -> np.ndarray:
    """
    对 batch logits 应用阶段先验。
    logits: (N, C); phases: 长度 N 的阶段名列表
    mode: soft | hard
    """
    logits = np.asarray(logits, dtype=np.float64).copy()
    n = logits.shape[0]
    if logits.ndim == 1:
        logits = logits.reshape(1, -1)

    for i in range(n):
        phase = phases[i] if i < len(phases) else "full"
        if mode == "soft":
            logits[i] += soft_phase_prior(phase, num_classes, prior_matrix)
        elif mode == "hard":
            allowed = set(allowed_classes_for_phase(phase))
            mask = np.array([c in allowed for c in range(num_classes)])
            logits[i, ~mask] = -1e9
        else:
            raise ValueError(f"unknown mode: {mode}")
    return logits


def dominant_phase_from_onehot(window_phase: np.ndarray) -> str:
    """window_phase: (seq_len, 4) one-hot；取窗口内均值最大阶段。"""
    if window_phase.size == 0:
        return "full"
    mean_v = window_phase.mean(axis=0)
    idx = int(np.argmax(mean_v))
    return PHASE_NAMES[idx] if idx < len(PHASE_NAMES) else "full"


def calibrate_from_baseline_csvs(
    baseline_dir: str,
    sample_dt: float = 0.125,
    row_interval: int = 4,
) -> Dict:
    """从 baseline fc*.csv 标定 FT 阈值与时间 band。"""
    import glob

    pattern = os.path.join(baseline_dir, "fc*.csv")
    paths = sorted(
        p for p in glob.glob(pattern)
        if "_P.csv" not in os.path.basename(p)
    )
    if not paths:
        raise FileNotFoundError(f"未找到 baseline CSV: {pattern}")

    ft_vals, rcs_vals, fin_vals = [], [], []
    time_ft_off, times_all = [], []

    for path in paths:
        df = pd.read_csv(path)
        df = df.sort_values("Time").reset_index(drop=True)
        if row_interval > 1:
            df = df.iloc[::row_interval].reset_index(drop=True)
        ft = df["FT"].values.astype(np.float64)
        t = df["Time"].values.astype(np.float64)
        rcs_vals.extend(_rcs_activity(df, sample_dt).values.tolist())
        fin_vals.extend(_fin_activity(df, sample_dt).values.tolist())

        on_mask = ft > 1.0e3
        if on_mask.any():
            last_on = int(np.where(on_mask)[0][-1])
            if last_on + 1 < len(t):
                time_ft_off.append(float(t[last_on + 1]))
        ft_vals.extend(ft[on_mask].tolist() if on_mask.any() else ft.tolist())
        times_all.extend(t.tolist())

    ft_thr = float(np.percentile(ft_vals, 10)) if ft_vals else 1.0e4
    ft_thr = max(ft_thr, 1.0e3)

    rcs_thr = float(np.percentile(rcs_vals, 75)) if rcs_vals else 0.05
    fin_thr = float(np.percentile(fin_vals, 75)) if fin_vals else 0.05

    t_ascent = float(np.median(time_ft_off)) if time_ft_off else 120.0
    t_max = float(np.max(times_all)) if times_all else 480.0
    t_rcs = t_ascent + 0.45 * (t_max - t_ascent)

    return {
        "ft_on_threshold": ft_thr,
        "rcs_activity_threshold": max(rcs_thr, 1e-4),
        "fin_activity_threshold": max(fin_thr, 1e-4),
        "time_ascent_end_s": t_ascent,
        "time_rcs_end_s": t_rcs,
        "sample_dt": sample_dt,
        "calibrated_from": paths[:3],
    }
