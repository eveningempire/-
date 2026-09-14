"""构建 14 类统一 test 窗口（双特征：推进 13d + 姿控 v2.1 27d）。"""

from __future__ import annotations

import os
import pickle
from typing import Tuple

import numpy as np
from sklearn.model_selection import train_test_split

from .data_preprocessing import SimulateDataPreprocessor
from .expert_config import (
    EnsembleDataConfig,
    PROPULSION_FEATURE_COLUMNS,
    PropulsionExpertConfig,
    GNCExpertConfig,
)
from .residual_features import GNC_RESIDUAL_COLUMNS_V21, build_gnc_residual_features_v21


def _normalize(X: np.ndarray, scaler, clip: float) -> np.ndarray:
    r = X.shape
    out = scaler.transform(X.reshape(-1, r[-1])).reshape(r).astype(np.float32)
    if clip > 0:
        np.clip(out, -clip, clip, out=out)
    return out


def build_ensemble_test_arrays(
    prop_cfg: PropulsionExpertConfig = None,
    gnc_cfg: GNCExpertConfig = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    从 simulate CSV 构建与专家相同 random_seed 划分的 test 子集。
    返回 X_prop_test, X_gnc_test, y_global_test。
    """
    prop_cfg = prop_cfg or PropulsionExpertConfig()
    gnc_cfg = gnc_cfg or GNCExpertConfig()
    data_cfg = EnsembleDataConfig()
    data_cfg.random_seed = prop_cfg.random_seed
    data_cfg.test_ratio = prop_cfg.test_ratio
    data_cfg.val_ratio = prop_cfg.val_ratio
    data_cfg.train_ratio = prop_cfg.train_ratio
    data_cfg.seq_len = prop_cfg.seq_len
    data_cfg.window_stride = prop_cfg.window_stride
    data_cfg.row_interval = prop_cfg.row_interval
    data_cfg.sample_dt = prop_cfg.sample_dt

    prep = SimulateDataPreprocessor(data_cfg)
    files = prep.discover_csv_files()
    if not files:
        raise FileNotFoundError(f"未在 {data_cfg.simulate_data_dir} 找到仿真 CSV")

    sample_dt = float(data_cfg.sample_dt)
    seq_len = data_cfg.seq_len
    prop_cols = list(PROPULSION_FEATURE_COLUMNS)
    gnc_cols = list(GNC_RESIDUAL_COLUMNS_V21)

    X_prop_parts, X_gnc_parts, y_parts = [], [], []

    for path, slug, class_id in files:
        df = prep._load_and_clean(path)
        df = prep._attach_actuator_phase(df)
        gnc_feat = build_gnc_residual_features_v21(df, sample_dt=sample_dt)

        (Xp, Xg), yw = _windows_for_file(prep, df, gnc_feat, class_id, prop_cols, gnc_cols)
        if len(yw) > 0:
            X_prop_parts.append(Xp)
            X_gnc_parts.append(Xg)
            y_parts.append(yw)

        if prep._should_add_prefault_normal(slug, class_id):
            Xp, Xg, yn = _prefault_windows(prep, df, gnc_feat, prop_cols, gnc_cols)
            if len(yn) > 0:
                X_prop_parts.append(Xp)
                X_gnc_parts.append(Xg)
                y_parts.append(yn)

    X_prop_all = np.concatenate(X_prop_parts, axis=0)
    X_gnc_all = np.concatenate(X_gnc_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)

    _, X_prop_test, _, y_test = train_test_split(
        X_prop_all,
        y_all,
        test_size=data_cfg.test_ratio,
        random_state=data_cfg.random_seed,
        stratify=y_all,
    )
    _, X_gnc_test, _, _ = train_test_split(
        X_gnc_all,
        y_all,
        test_size=data_cfg.test_ratio,
        random_state=data_cfg.random_seed,
        stratify=y_all,
    )

    clip = float(getattr(prop_cfg, "feature_clip", 5.0))
    with open(os.path.join(prop_cfg.processed_data_dir, "scaler.pkl"), "rb") as f:
        prop_scaler = pickle.load(f)
    with open(os.path.join(gnc_cfg.processed_data_dir, "scaler.pkl"), "rb") as f:
        gnc_scaler = pickle.load(f)

    X_prop_test = _normalize(X_prop_test, prop_scaler, clip)
    X_gnc_test = _normalize(X_gnc_test, gnc_scaler, clip)
    return X_prop_test, X_gnc_test, y_test


def _windows_for_file(prep, df, gnc_feat, class_id, prop_cols, gnc_cols):
    seq_len = prep.config.seq_len
    stride = prep.config.window_stride if class_id != 0 else prep._normal_stride("baseline")
    flag = df[prep.config.fault_flag_column].values.astype(np.int32)
    n = len(df)
    phase_arr = df["_actuator_phase"].values if "_actuator_phase" in df.columns else None
    filter_phase = bool(getattr(prep.config, "filter_fault_windows_by_actuator_phase", False))

    prop_arr = df[prop_cols].values.astype(np.float32)
    gnc_arr = gnc_feat[gnc_cols].values.astype(np.float32)

    Xp_list, Xg_list, y_list = [], [], []
    for start, end in prep._segment_ranges(flag, n, class_id):
        for i in range(start, end - seq_len + 1, stride):
            window_flag = flag[i : i + seq_len]
            if not prep._window_flag_valid(class_id, window_flag):
                continue
            if (
                filter_phase
                and phase_arr is not None
                and class_id != 0
                and not prep._phase_valid_for_fault_window(phase_arr, i, seq_len, class_id)
            ):
                continue
            Xp_list.append(prop_arr[i : i + seq_len])
            Xg_list.append(gnc_arr[i : i + seq_len])
            y_list.append(class_id)
    if not Xp_list:
        return (np.empty((0, seq_len, len(prop_cols)), np.float32),
                np.empty((0, seq_len, len(gnc_cols)), np.float32)), np.empty(0, np.int64)
    return (np.stack(Xp_list), np.stack(Xg_list)), np.array(y_list, dtype=np.int64)


def _prefault_windows(prep, df, gnc_feat, prop_cols, gnc_cols):
    flag = df[prep.config.fault_flag_column].values.astype(np.int32)
    seq_len = prep.config.seq_len
    if len(flag) < seq_len:
        return (
            np.empty((0, seq_len, len(prop_cols)), np.float32),
            np.empty((0, seq_len, len(gnc_cols)), np.float32),
            np.empty(0, np.int64),
        )
    stride = prep._normal_stride("prefault")
    prop_arr = df[prop_cols].values.astype(np.float32)
    gnc_arr = gnc_feat[gnc_cols].values.astype(np.float32)
    Xp_list, Xg_list, y_list = [], [], []
    for start, end in prep._prefault_normal_ranges(flag):
        for i in range(start, end - seq_len + 1, stride):
            window_flag = flag[i : i + seq_len]
            if not prep._window_flag_valid(0, window_flag):
                continue
            Xp_list.append(prop_arr[i : i + seq_len])
            Xg_list.append(gnc_arr[i : i + seq_len])
            y_list.append(0)
    if not Xp_list:
        return (
            np.empty((0, seq_len, len(prop_cols)), np.float32),
            np.empty((0, seq_len, len(gnc_cols)), np.float32),
            np.empty(0, np.int64),
        )
    Xp = np.stack(Xp_list)
    Xg = np.stack(Xg_list)
    y = np.array(y_list, dtype=np.int64)
    max_n = getattr(prep.config, "prefault_normal_max_windows_per_file", None)
    if max_n is not None and int(max_n) > 0 and len(y) > int(max_n):
        Xp, Xg, y = Xp[-int(max_n) :], Xg[-int(max_n) :], y[-int(max_n) :]
    return Xp, Xg, y
