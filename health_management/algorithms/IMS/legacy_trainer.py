from __future__ import annotations

import glob
import io
import os
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans


def read_csv_with_fallback(path: str, cols: Optional[List[str]]) -> pd.DataFrame:
    """Read CSV with common encodings; optionally select subset columns or numeric-only."""
    df = None
    for enc in ("gbk", "utf-8-sig", "utf-8"):
        try:
            df = pd.read_csv(path, index_col=0, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        raise ValueError(f"Failed to read CSV: {path}")
    if cols:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{os.path.basename(path)} missing columns: {missing}")
        df = df[cols]
    else:
        # Keep numeric columns only
        df = df.select_dtypes(include=[np.number])
    return df


class LegacyIMSDetector:
    """KMeans radius-based detector that matches legacy adapter expectations.

    After fitting, attributes mirror adapter requirements:
    _mu, _sigma, _kmeans, _cluster_radii, _max_train_dist, _max_train_dim
    """

    def __init__(self, n_clusters: Optional[int], shrink_ratio: float, calib_percentile: float, random_state: int = 42) -> None:
        self.n_clusters = n_clusters
        self.shrink_ratio = float(shrink_ratio)
        self.calib_percentile = float(calib_percentile)
        self.random_state = int(random_state)
        self._mu = None
        self._sigma = None
        self._kmeans = None
        self._cluster_radii = None
        self._max_train_dist = None
        self._max_train_dim = None

    def fit(self, X: np.ndarray) -> "LegacyIMSDetector":
        if X.ndim != 2:
            raise ValueError("X must be 2D array")
        self._mu = X.mean(axis=0)
        self._sigma = X.std(axis=0) + 1e-12
        Xn = (X - self._mu) / self._sigma

        n_samples = Xn.shape[0]
        k = self.n_clusters or max(2, int(np.ceil(np.sqrt(max(n_samples, 2) / 2))))
        self._kmeans = MiniBatchKMeans(
            n_clusters=k,
            random_state=self.random_state,
            batch_size=min(256, n_samples),
            n_init="auto",
        ).fit(Xn)

        labels = self._kmeans.labels_
        centers = self._kmeans.cluster_centers_
        base_radii = np.zeros_like(centers)
        for idx in range(k):
            pts = Xn[labels == idx]
            base_radii[idx] = np.max(np.abs(pts - centers[idx]), axis=0) if len(pts) else 1e-6
        self._cluster_radii = base_radii * (1.0 - self.shrink_ratio)

        # Calibrate distances/overflows - 优化阈值计算策略
        dists: list[float] = []
        dim_deltas: list[np.ndarray] = []
        for xi in Xn:
            # nearest center index
            d = np.linalg.norm(np.where(np.abs(xi - centers[np.argmin(np.linalg.norm(centers - xi, axis=1))]) - self._cluster_radii[np.argmin(np.linalg.norm(centers - xi, axis=1))] > 0,
                                        np.abs(xi - centers[np.argmin(np.linalg.norm(centers - xi, axis=1))]) - self._cluster_radii[np.argmin(np.linalg.norm(centers - xi, axis=1))], 0.0))
            dists.append(d)
            idx = int(np.argmin(np.linalg.norm(centers - xi, axis=1)))
            contrib = np.abs(xi - centers[idx]) - self._cluster_radii[idx]
            dim_deltas.append(np.where(contrib > 0, contrib, 0.0))

        d_arr = np.asarray(dists)
        dim_arr = np.asarray(dim_deltas)
        
        # 改进的归一化上限计算：使用百分位数 + 均值-标准差方法的最大值
        # 这样可以更好地容纳正常数据的波动，降低虚警
        percentile_max_dist = np.percentile(d_arr, self.calib_percentile)
        mean_std_max_dist = np.mean(d_arr) + 2.0 * np.std(d_arr)
        self._max_train_dist = float(max(percentile_max_dist, mean_std_max_dist) + 1e-12)
        
        # 维度级别也使用更保守的方法
        percentile_max_dim = np.percentile(dim_arr, self.calib_percentile, axis=0)
        mean_std_max_dim = np.mean(dim_arr, axis=0) + 2.0 * np.std(dim_arr, axis=0)
        self._max_train_dim = np.maximum(percentile_max_dim, mean_std_max_dim) + 1e-12
        
        return self


def train_legacy_ims_from_csv(
    data_dir: str,
    columns: Optional[List[str]] = None,
    n_clusters: Optional[int] = None,
    shrink_ratio: float = 0.20,      # 优化：增加收缩比例至20%以减少虚警
    calib_percentile: float = 99.0,  # 优化：提高百分位数至99%使阈值更保守
) -> Tuple[bytes, List[str]]:
    """Train legacy IMS from CSV directory and return (model_bytes, parameters).

    If columns is None, use numeric columns automatically.
    """
    pattern = os.path.join(data_dir, "**", "*.csv")
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        raise FileNotFoundError(f"No CSV files under {data_dir}")

    arrays: List[np.ndarray] = []
    final_cols: Optional[List[str]] = columns[:] if columns else None
    for fp in files:
        df = read_csv_with_fallback(fp, final_cols)
        if df.empty:
            continue
        if final_cols is None:
            # establish column order on first non-empty file
            final_cols = list(df.columns)
        else:
            # ensure consistent ordering and presence
            df = df[final_cols]
        vals = df.values.astype(np.float64)
        if not np.isfinite(vals).any():
            continue
        arrays.append(vals)
    if not arrays:
        raise ValueError("No usable numeric data found for training")

    X = np.vstack(arrays)
    detector = LegacyIMSDetector(n_clusters=n_clusters, shrink_ratio=shrink_ratio, calib_percentile=calib_percentile).fit(X)

    bio = io.BytesIO()
    joblib.dump(detector.__dict__, bio, compress=3)
    model_bytes = bio.getvalue()

    if final_cols is None:
        final_cols = [f"param_{i+1}" for i in range(X.shape[1])]

    return model_bytes, final_cols


