# src/data_preprocessing.py
"""
仿真 CSV -> 滑窗样本 -> 按样本分层划分 -> 保存 processed numpy。
"""

import json
import os
import pickle
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .config import Config


def _get_residual_builder(config: Config):
    feature_set = getattr(config, "feature_set", None)
    if feature_set == "v2.1":
        from .residual_features import build_gnc_residual_features_v21
        return build_gnc_residual_features_v21
    from .residual_features import build_gnc_residual_features_v2
    return build_gnc_residual_features_v2


def _contiguous_runs(mask: np.ndarray) -> List[Tuple[int, int]]:
    """True 连续段 [start, end) 索引。"""
    runs = []
    n = len(mask)
    i = 0
    while i < n:
        if not mask[i]:
            i += 1
            continue
        start = i
        while i < n and mask[i]:
            i += 1
        runs.append((start, i))
    return runs


class SimulateDataPreprocessor:
    def __init__(self, config: Config):
        self.config = config
        self.scaler_X = StandardScaler()

    def discover_csv_files(self) -> List[Tuple[str, str, int]]:
        """
        返回 [(csv_path, slug, class_id), ...]
        """
        root = self.config.simulate_data_dir
        items = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in self.config.csv_ignore_subdirs
            ]
            slug = os.path.basename(dirpath).lower()
            if slug not in self.config.SLUG_TO_CLASS_ID:
                continue
            class_id = self.config.slug_to_class_id(slug)
            allowed = getattr(self.config, "allowed_class_ids", None)
            if allowed is not None and class_id not in allowed:
                continue
            for fn in filenames:
                if not fn.lower().endswith(".csv"):
                    continue
                if any(p in fn for p in self.config.csv_ignore_patterns):
                    continue
                items.append((os.path.join(dirpath, fn), slug, class_id))
        items.sort(key=lambda x: x[0])
        return items

    def _load_and_clean(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        missing = [c for c in self.config.feature_columns if c not in df.columns]
        if missing:
            raise ValueError(f"{path} 缺少列: {missing}")
        if self.config.fault_flag_column not in df.columns:
            raise ValueError(f"{path} 缺少 {self.config.fault_flag_column}")
        df = df.sort_values(self.config.time_column).reset_index(drop=True)
        df[self.config.feature_columns] = df[self.config.feature_columns].ffill().bfill()
        df = df.dropna(subset=self.config.feature_columns)

        interval = int(getattr(self.config, "row_interval", 1))
        if interval > 1:
            df = df.iloc[::interval].reset_index(drop=True)
        return df

    def _apply_feature_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        sample_dt = float(getattr(self.config, "sample_dt", 0.125))

        if getattr(self.config, "append_gnc_residual_features", False):
            builder = getattr(self.config, "residual_feature_builder", None)
            if builder is None:
                from .residual_features import build_gnc_residual_features_v21
                builder = build_gnc_residual_features_v21
            feat_df = builder(df, sample_dt=sample_dt)
            keep_cols = [self.config.fault_flag_column]
            if self.config.time_column in df.columns:
                keep_cols.append(self.config.time_column)
            if "_actuator_phase" in df.columns:
                keep_cols.append("_actuator_phase")
            raw_cols = list(self.config.feature_columns)
            return pd.concat([df[keep_cols + raw_cols], feat_df], axis=1)

        if not getattr(self.config, "use_residual_features", False):
            return df
        builder = getattr(self.config, "residual_feature_builder", None)
        if builder is None:
            builder = _get_residual_builder(self.config)
        sample_dt = float(getattr(self.config, "sample_dt", 0.125))
        feat_df = builder(df, sample_dt=sample_dt)

        if getattr(self.config, "use_actuator_phase", False):
            from .actuator_context import (
                derive_actuator_phase_series,
                load_band_stats,
                phase_onehot_frame,
            )
            stats = load_band_stats(
                getattr(self.config, "actuator_band_stats_path", None)
            )
            phase_mode = getattr(self.config, "actuator_phase_mode", "telemetry")
            phase_series = derive_actuator_phase_series(
                df, mode=phase_mode, band_stats=stats, sample_dt=sample_dt
            )
            feat_df = pd.concat([feat_df, phase_onehot_frame(phase_series)], axis=1)

        keep_cols = [self.config.fault_flag_column]
        if self.config.time_column in df.columns:
            keep_cols.append(self.config.time_column)
        if "_actuator_phase" in df.columns:
            keep_cols.append("_actuator_phase")
        return pd.concat([df[keep_cols], feat_df], axis=1)

    def _attach_actuator_phase(self, df: pd.DataFrame) -> pd.DataFrame:
        """为飞控阶段过滤附加逐行 ActuatorPhase（telemetry）。"""
        if not getattr(self.config, "filter_fault_windows_by_actuator_phase", False):
            return df
        from .actuator_context import derive_actuator_phase_series, load_band_stats

        sample_dt = float(getattr(self.config, "sample_dt", 0.125))
        stats = load_band_stats(getattr(self.config, "actuator_band_stats_path", None))
        phase_mode = getattr(self.config, "actuator_phase_for_filter", "telemetry")
        df = df.copy()
        df["_actuator_phase"] = derive_actuator_phase_series(
            df, mode=phase_mode, band_stats=stats, sample_dt=sample_dt
        ).values
        return df

    def _phase_valid_for_fault_window(
        self, phases: np.ndarray, start: int, seq_len: int, global_class_id: int
    ) -> bool:
        if global_class_id == 0:
            return True
        from .actuator_context import valid_phases_for_fault

        valid = set(valid_phases_for_fault(global_class_id))
        win_phases = phases[start : start + seq_len]
        mode = getattr(self.config, "actuator_phase_filter_mode", "center")
        if mode == "all":
            return all(str(p) in valid for p in win_phases)
        mid = start + seq_len // 2
        return str(phases[mid]) in valid

    def _model_columns(self) -> List[str]:
        cols = getattr(self.config, "active_feature_columns", None)
        if cols:
            return list(cols)
        return list(self.config.feature_columns)

    def _mature_offset_points(self) -> int:
        """飞控成熟段：FaultFlag==1 后跳过的采样点数。"""
        sec = float(getattr(self.config, "control_fault_mature_sec", 0.0))
        if sec <= 0:
            return 0
        dt = float(getattr(self.config, "sample_dt", 0.125))
        return max(0, int(round(sec / dt)))

    def _is_control_fault(self, class_id: int) -> bool:
        ids = getattr(self.config, "CONTROL_FAULT_CLASS_IDS", tuple(range(8, 14)))
        return int(class_id) in ids

    def _prefault_normal_ranges(self, flag: np.ndarray) -> List[Tuple[int, int]]:
        """故障 CSV 中首次注入前的 Flag==0 连续段（同 fc* 硬负样本）。"""
        seq_len = self.config.seq_len
        target = int(getattr(self.config, "normal_segment_flag_value", 0))
        fault_idx = np.where(flag == 1)[0]
        if len(fault_idx) == 0:
            return []
        first_fault = int(fault_idx[0])
        ranges = []
        for start, end in _contiguous_runs(flag == target):
            eff_end = min(end, first_fault)
            if eff_end - start >= seq_len:
                ranges.append((start, eff_end))
        return ranges

    def _normal_stride(self, source: str = "baseline") -> int:
        """baseline / prefault 正常窗可用不同步长。"""
        if source == "prefault":
            s = getattr(self.config, "prefault_normal_window_stride", None)
            if s is not None:
                return int(s)
        if source == "baseline":
            s = getattr(self.config, "baseline_normal_window_stride", None)
            if s is not None:
                return int(s)
        s = getattr(self.config, "normal_window_stride", None)
        return int(s) if s is not None else int(self.config.window_stride)

    def _cap_windows(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        max_n = getattr(self.config, "prefault_normal_max_windows_per_file", None)
        if max_n is None or int(max_n) <= 0 or len(X) <= int(max_n):
            return X, y
        # 保留靠近注入点的末尾窗口
        return X[-int(max_n) :], y[-int(max_n) :]

    def _should_add_prefault_normal(self, slug: str, class_id: int) -> bool:
        if not getattr(self.config, "include_prefault_normal_from_fault_csv", False):
            return False
        if int(class_id) == 0:
            return False
        slugs = getattr(self.config, "prefault_normal_slugs", None)
        if slugs is not None:
            allowed = {s.strip().lower() for s in slugs}
            if slug.strip().lower() not in allowed:
                return False
        return True

    def _segment_ranges(
        self, flag: np.ndarray, n: int, class_id: int
    ) -> List[Tuple[int, int]]:
        seq_len = self.config.seq_len
        mature_off = self._mature_offset_points() if self._is_control_fault(class_id) else 0

        if class_id == 0:
            if getattr(self.config, "train_on_normal_segment_only", True):
                target = int(getattr(self.config, "normal_segment_flag_value", 0))
                return [
                    (start, end)
                    for start, end in _contiguous_runs(flag == target)
                    if end - start >= seq_len
                ]
            return [(0, n)]

        if self.config.train_on_fault_segment_only:
            ranges = []
            for start, end in _contiguous_runs(flag == 1):
                eff_start = start + mature_off
                if end - eff_start >= seq_len:
                    ranges.append((eff_start, end))
            return ranges

        return [(0, n)]

    def _window_flag_valid(self, class_id: int, window_flag: np.ndarray) -> bool:
        if class_id == 0 and getattr(self.config, "train_on_normal_segment_only", True):
            target = int(getattr(self.config, "normal_segment_flag_value", 0))
            return bool(np.all(window_flag == target))
        if class_id != 0 and self.config.train_on_fault_segment_only:
            return bool(np.all(window_flag == 1))
        return True

    def _windows_from_ranges(
        self,
        df: pd.DataFrame,
        label_class_id: int,
        index_ranges: List[Tuple[int, int]],
        stride: int,
        ctx_t: Optional[list] = None,
        ctx_phase: Optional[list] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        seq_len = self.config.seq_len
        model_cols = self._model_columns()
        feat = df[model_cols].values.astype(np.float32)
        flag = df[self.config.fault_flag_column].values.astype(np.int32)
        n_feat = len(model_cols)
        time_col = self.config.time_column if self.config.time_column in df.columns else None
        times = df[time_col].values.astype(np.float64) if time_col else None
        save_ctx = getattr(self.config, "save_window_context", False)

        from .actuator_context import ACTUATOR_PHASE_COLUMNS, dominant_phase_from_onehot

        phase_cols = ACTUATOR_PHASE_COLUMNS
        phase_idx = [model_cols.index(c) for c in phase_cols if c in model_cols]
        phase_arr = (
            df["_actuator_phase"].values
            if "_actuator_phase" in df.columns
            else None
        )
        filter_phase = bool(getattr(self.config, "filter_fault_windows_by_actuator_phase", False))

        X_list, y_list = [], []
        for start, end in index_ranges:
            for i in range(start, end - seq_len + 1, stride):
                window_flag = flag[i : i + seq_len]
                if not self._window_flag_valid(label_class_id, window_flag):
                    continue
                if (
                    filter_phase
                    and phase_arr is not None
                    and label_class_id != 0
                    and not self._phase_valid_for_fault_window(
                        phase_arr, i, seq_len, label_class_id
                    )
                ):
                    self._phase_skip_count += 1
                    continue
                X_list.append(feat[i : i + seq_len])
                label = int(label_class_id)
                remap = getattr(self.config, "class_id_remap", None)
                if remap is not None:
                    label = int(remap[label])
                y_list.append(label)

                if save_ctx and ctx_t is not None and times is not None:
                    mid = i + seq_len // 2
                    ctx_t.append(float(times[mid]))
                if save_ctx and ctx_phase is not None and len(phase_idx) == len(phase_cols):
                    wp = feat[i : i + seq_len, phase_idx[0] : phase_idx[-1] + 1]
                    ctx_phase.append(dominant_phase_from_onehot(wp))

        if not X_list:
            return (
                np.empty((0, seq_len, n_feat), np.float32),
                np.empty(0, np.int64),
            )
        return np.stack(X_list, axis=0), np.array(y_list, dtype=np.int64)

    def _windows_from_df(
        self,
        df: pd.DataFrame,
        class_id: int,
        ctx_t: Optional[list] = None,
        ctx_phase: Optional[list] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        seq_len = self.config.seq_len
        stride = self.config.window_stride
        if class_id == 0:
            stride = self._normal_stride("baseline")
        model_cols = self._model_columns()
        flag = df[self.config.fault_flag_column].values.astype(np.int32)
        n = len(df)
        n_feat = len(model_cols)

        if n < seq_len:
            return np.empty((0, seq_len, n_feat), np.float32), np.empty(0, np.int64)

        index_ranges = self._segment_ranges(flag, n, class_id)
        return self._windows_from_ranges(
            df, class_id, index_ranges, stride, ctx_t=ctx_t, ctx_phase=ctx_phase
        )

    def _prefault_normal_windows(
        self,
        df: pd.DataFrame,
        ctx_t: Optional[list] = None,
        ctx_phase: Optional[list] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        flag = df[self.config.fault_flag_column].values.astype(np.int32)
        seq_len = self.config.seq_len
        if len(flag) < seq_len:
            return (
                np.empty((0, seq_len, len(self._model_columns())), np.float32),
                np.empty(0, np.int64),
            )
        stride = self._normal_stride("prefault")
        ranges = self._prefault_normal_ranges(flag)
        X, y = self._windows_from_ranges(
            df, 0, ranges, stride, ctx_t=ctx_t, ctx_phase=ctx_phase
        )
        return self._cap_windows(X, y)

    def build_all_samples(self) -> Tuple[np.ndarray, np.ndarray, list]:
        files = self.discover_csv_files()
        if not files:
            raise FileNotFoundError(f"未在 {self.config.simulate_data_dir} 找到仿真 CSV")

        save_ctx = getattr(self.config, "save_window_context", False)
        ctx_t_all: List[float] = []
        ctx_phase_all: List[str] = []
        self._phase_skip_count = 0

        X_parts, y_parts, meta = [], [], []
        for path, slug, class_id in files:
            df = self._load_and_clean(path)
            df = self._attach_actuator_phase(df)
            df = self._apply_feature_transform(df)
            ctx_t = ctx_t_all if save_ctx else None
            ctx_phase = ctx_phase_all if save_ctx else None
            X, y = self._windows_from_df(df, class_id, ctx_t=ctx_t, ctx_phase=ctx_phase)
            if len(X) == 0:
                print(f"  跳过（无有效窗口）: {path}")
            else:
                X_parts.append(X)
                y_parts.append(y)
                meta.append({
                    "path": path, "slug": slug, "class_id": class_id,
                    "n_windows": int(len(X)),
                    "source": "baseline_normal" if class_id == 0 else "fault_segment",
                })
                print(f"  {slug} class={class_id} windows={len(X)} <- {os.path.basename(path)}")

            if self._should_add_prefault_normal(slug, class_id):
                Xn, yn = self._prefault_normal_windows(df, ctx_t=ctx_t, ctx_phase=ctx_phase)
                if len(Xn) > 0:
                    X_parts.append(Xn)
                    y_parts.append(yn)
                    meta.append({
                        "path": path, "slug": slug, "class_id": 0,
                        "n_windows": int(len(Xn)), "source": "prefault_normal",
                    })
                    print(
                        f"  {slug} class=0 (prefault) windows={len(Xn)} "
                        f"<- {os.path.basename(path)}"
                    )

        X_all = np.concatenate(X_parts, axis=0)
        y_all = np.concatenate(y_parts, axis=0)
        self._window_context = None
        if save_ctx:
            self._window_context = {
                "t_center": np.array(ctx_t_all, dtype=np.float64),
                "phase": np.array(ctx_phase_all, dtype=object),
            }
        self._phase_filter_stats = {
            "enabled": bool(getattr(self.config, "filter_fault_windows_by_actuator_phase", False)),
            "mode": getattr(self.config, "actuator_phase_filter_mode", "center"),
            "skipped_windows": int(self._phase_skip_count),
        }
        if self._phase_filter_stats["enabled"] and self._phase_skip_count > 0:
            print(f"  [phase-filter] skipped {self._phase_skip_count} invalid fault windows")
        return X_all, y_all, meta

    def split_samples(self, X: np.ndarray, y: np.ndarray):
        cfg = self.config
        assert abs(cfg.train_ratio + cfg.val_ratio + cfg.test_ratio - 1.0) < 1e-6

        X_tv, X_test, y_tv, y_test = train_test_split(
            X, y,
            test_size=cfg.test_ratio,
            random_state=cfg.random_seed,
            stratify=y,
        )
        val_rel = cfg.val_ratio / (cfg.train_ratio + cfg.val_ratio)
        X_train, X_val, y_train, y_val = train_test_split(
            X_tv, y_tv,
            test_size=val_rel,
            random_state=cfg.random_seed,
            stratify=y_tv,
        )
        return X_train, X_val, X_test, y_train, y_val, y_test

    def normalize(self, X_train, X_val, X_test):
        clip = float(getattr(self.config, "feature_clip", 5.0))
        s = X_train.shape
        self.scaler_X.fit(X_train.reshape(-1, s[-1]))

        def tr(X):
            r = X.shape
            out = self.scaler_X.transform(X.reshape(-1, r[-1])).reshape(r).astype(np.float32)
            if clip > 0:
                np.clip(out, -clip, clip, out=out)
            return out

        X_train, X_val, X_test = tr(X_train), tr(X_val), tr(X_test)
        for name, arr in ("train", X_train), ("val", X_val), ("test", X_test):
            if not np.isfinite(arr).all():
                raise ValueError(f"归一化后 {name} 含 NaN/Inf，请检查原始 CSV")
        return X_train, X_val, X_test

    def preprocess(self):
        print(f"扫描目录: {self.config.simulate_data_dir}")
        ri = getattr(self.config, "row_interval", 1)
        approx_dt = 0.031 * ri
        win_sec = self.config.seq_len * approx_dt
        mature_off = self._mature_offset_points()
        expert = getattr(self.config, "expert_name", "full")
        print(
            f"row_interval={ri}, seq_len={self.config.seq_len}, "
            f"window_stride={self.config.window_stride}, "
            f"baseline_normal_stride={getattr(self.config, 'baseline_normal_window_stride', None)}, "
            f"prefault_normal_stride={getattr(self.config, 'prefault_normal_window_stride', None)}, "
            f"prefault_cap={getattr(self.config, 'prefault_normal_max_windows_per_file', None)}, "
            f"prefault_slugs={getattr(self.config, 'prefault_normal_slugs', None)}, "
            f"approx_window={win_sec:.1f}s, use_cwt={self.config.use_cwt}, "
            f"expert={expert}, input_dim={len(self._model_columns())}, "
            f"control_mature_sec={getattr(self.config, 'control_fault_mature_sec', 0)}, "
            f"control_mature_pts={mature_off}, "
            f"prefault_normal={getattr(self.config, 'include_prefault_normal_from_fault_csv', False)}, "
            f"phase_filter={getattr(self.config, 'filter_fault_windows_by_actuator_phase', False)}"
        )
        X_raw, y_raw, meta = self.build_all_samples()
        print(f"总窗口样本: {len(y_raw)}")

        if self.config.use_cwt:
            raise NotImplementedError("当前训练关闭 CWT，请将 config.use_cwt=False")

        X_train, X_val, X_test, y_train, y_val, y_test = self.split_samples(X_raw, y_raw)

        out = self.config.processed_data_dir
        os.makedirs(out, exist_ok=True)

        ctx = getattr(self, "_window_context", None)
        if ctx is not None and len(ctx["t_center"]) == len(y_raw):
            idx = np.arange(len(y_raw))
            idx_tv, idx_test = train_test_split(
                idx,
                test_size=self.config.test_ratio,
                random_state=self.config.random_seed,
                stratify=y_raw,
            )
            val_rel = self.config.val_ratio / (self.config.train_ratio + self.config.val_ratio)
            idx_train, idx_val = train_test_split(
                idx_tv,
                test_size=val_rel,
                random_state=self.config.random_seed,
                stratify=y_raw[idx_tv],
            )
            t_ctx, ph_ctx = ctx["t_center"], ctx["phase"]
            np.save(os.path.join(out, "t_train.npy"), t_ctx[idx_train])
            np.save(os.path.join(out, "t_val.npy"), t_ctx[idx_val])
            np.save(os.path.join(out, "t_test.npy"), t_ctx[idx_test])
            np.save(os.path.join(out, "phase_train.npy"), ph_ctx[idx_train])
            np.save(os.path.join(out, "phase_val.npy"), ph_ctx[idx_val])
            np.save(os.path.join(out, "phase_test.npy"), ph_ctx[idx_test])

        X_train, X_val, X_test = self.normalize(X_train, X_val, X_test)

        np.save(os.path.join(out, "X_train.npy"), X_train)
        np.save(os.path.join(out, "X_val.npy"), X_val)
        np.save(os.path.join(out, "X_test.npy"), X_test)
        np.save(os.path.join(out, "y_train.npy"), y_train)
        np.save(os.path.join(out, "y_val.npy"), y_val)
        np.save(os.path.join(out, "y_test.npy"), y_test)

        with open(os.path.join(out, "scaler.pkl"), "wb") as f:
            pickle.dump(self.scaler_X, f)
        with open(os.path.join(out, "feature_names.pkl"), "wb") as f:
            pickle.dump(self._model_columns(), f)
        with open(os.path.join(out, "preprocess_meta.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "expert_name": getattr(self.config, "expert_name", "full"),
                    "active_feature_columns": self._model_columns(),
                    "allowed_class_ids": list(
                        getattr(self.config, "allowed_class_ids", range(self.config.num_classes))
                    ),
                    "class_id_remap": getattr(self.config, "class_id_remap", None),
                    "use_residual_features": bool(
                        getattr(self.config, "use_residual_features", False)
                    ),
                    "append_gnc_residual_features": bool(
                        getattr(self.config, "append_gnc_residual_features", False)
                    ),
                    "gnc_residual_version": getattr(self.config, "gnc_residual_version", 1),
                    "feature_set": getattr(self.config, "feature_set", None),
                    "use_actuator_phase": bool(getattr(self.config, "use_actuator_phase", False)),
                    "actuator_band_stats_path": getattr(
                        self.config, "actuator_band_stats_path", None
                    ),
                    "filter_fault_windows_by_actuator_phase": bool(
                        getattr(self.config, "filter_fault_windows_by_actuator_phase", False)
                    ),
                    "actuator_phase_filter_mode": getattr(
                        self.config, "actuator_phase_filter_mode", "center"
                    ),
                    "actuator_phase_for_filter": getattr(
                        self.config, "actuator_phase_for_filter", "telemetry"
                    ),
                    "phase_filter_stats": getattr(self, "_phase_filter_stats", None),
                    "n_total": int(len(y_raw)),
                    "n_train": int(len(y_train)),
                    "n_val": int(len(y_val)),
                    "n_test": int(len(y_test)),
                    "row_interval": getattr(self.config, "row_interval", 1),
                    "seq_len": self.config.seq_len,
                    "window_stride": self.config.window_stride,
                    "normal_window_stride": getattr(self.config, "normal_window_stride", None),
                    "baseline_normal_window_stride": getattr(
                        self.config, "baseline_normal_window_stride", None
                    ),
                    "prefault_normal_window_stride": getattr(
                        self.config, "prefault_normal_window_stride", None
                    ),
                    "prefault_normal_max_windows_per_file": getattr(
                        self.config, "prefault_normal_max_windows_per_file", None
                    ),
                    "prefault_normal_slugs": list(
                        getattr(self.config, "prefault_normal_slugs", ()) or ()
                    ),
                    "include_prefault_normal_from_fault_csv": bool(
                        getattr(self.config, "include_prefault_normal_from_fault_csv", False)
                    ),
                    "train_on_normal_segment_only": getattr(
                        self.config, "train_on_normal_segment_only", True
                    ),
                    "normal_segment_flag_value": int(
                        getattr(self.config, "normal_segment_flag_value", 0)
                    ),
                    "train_on_fault_segment_only": self.config.train_on_fault_segment_only,
                    "control_fault_mature_sec": float(
                        getattr(self.config, "control_fault_mature_sec", 0.0)
                    ),
                    "control_fault_class_ids": list(
                        getattr(self.config, "CONTROL_FAULT_CLASS_IDS", tuple(range(8, 14)))
                    ),
                    "class_names": self.config.CLASS_NAMES,
                    "files": meta,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"划分: train={len(y_train)}, val={len(y_val)}, test={len(y_test)}")
        for cid in range(self.config.num_classes):
            name = self.config.class_name(cid)
            tr = int((y_train == cid).sum())
            va = int((y_val == cid).sum())
            te = int((y_test == cid).sum())
            print(f"  [{cid}] {name}: train={tr}, val={va}, test={te}")

        return X_train, X_val, X_test, y_train, y_val, y_test


def run_preprocessing(config: Config = None):
    config = config or Config()
    preprocessor = SimulateDataPreprocessor(config)
    return preprocessor.preprocess()
