"""
IMS算法（Inductive Monitoring System）
=====================================
> **版本 3 — 连续异常分数修正**

上一版出现“测试分数全 0 / 全 1”问题，根因是：
* 训练阶段计算的 *超盒半径* 刚好覆盖所有训练样本 → 所有训练距离为 **0**。
* 归一化因子 `_max_train_dist` 因此近乎 0，导致推理时一旦越界就被剪成 1。

本版引入 **“半径收缩 + 分位数归一化”** 两步改进，使得异常分数在 0‑1 区间内连续分布，效果更稳健：
1. **半径收缩 (`shrink_ratio`, 默认 0.05)**：将聚类半径整体缩小 5%，让部分训练样本位于超盒边缘之外，从而产生 *非零* 训练距离。
2. **分位数归一化 (`calib_percentile`, 默认 95)**：用训练距离第 95 分位作为 `max_train_dist`，避免极端值主导，使得推理分数有梯度而非跳变。

其余功能（训练/推理数据管道、参数类调用、CSV+PNG 输出）保持不变。
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans

__all__ = [
    "IMSDetector",
    "TrainParams",
    "TestParams",
    "IMSRunner",
]

# ======================================================================
# IMS Detector 核心类
# ======================================================================


class IMSDetector:
    """Inductive Monitoring System（改进实现，支持连续异常分数）."""

    def __init__(
        self,
        n_clusters: int | None = None,
        random_state: int = 42,
        shrink_ratio: float = 0.05,
        calib_percentile: float = 95.0,
    ) -> None:
        """Parameters
        ----------
        n_clusters : int | None
            聚类数；``None`` 时自动估计。
        shrink_ratio : float, default **0.05**
            聚类半径整体收缩比例，用于产生非零训练距离。
        calib_percentile : float, default **95**
            使用训练距离的第 *P* 分位数做归一化上限（避免 0 或极端值）。
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.shrink_ratio = shrink_ratio
        self.calib_percentile = calib_percentile

        # 训练后属性
        self._kmeans: MiniBatchKMeans | None = None
        self._cluster_radii: np.ndarray | None = None
        self._mu: np.ndarray | None = None
        self._sigma: np.ndarray | None = None
        self._max_train_dist: float | None = None
        self._max_train_dim: np.ndarray | None = None

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    @staticmethod
    def _ensure_array(x: Union[np.ndarray, Sequence]) -> np.ndarray:
        return np.asarray(x, dtype=np.float64)

    def _z_norm(self, x: np.ndarray) -> np.ndarray:
        return (x - self._mu) / (self._sigma + 1e-12)

    def _nearest_cluster_idx(self, x: np.ndarray) -> int:
        dists = np.linalg.norm(self._kmeans.cluster_centers_ - x, axis=1)
        return int(np.argmin(dists))

    def _contributions(self, x: np.ndarray, idx: int) -> np.ndarray:
        """>0 表示越界；连续值 = 距离到收缩后超盒边界."""
        center = self._kmeans.cluster_centers_[idx]
        radius = self._cluster_radii[idx]
        delta = np.abs(x - center) - radius
        return np.where(delta > 0, delta, 0.0)

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------
    def fit(self, X: Union[np.ndarray, Sequence]) -> "IMSDetector":
        X = self._ensure_array(X)
        n_samples, _ = X.shape

        # 1) 计算均值/方差 → z‑norm
        self._mu = X.mean(axis=0)
        self._sigma = X.std(axis=0) + 1e-12
        Xn = self._z_norm(X)

        # 2) 聚类 (自动估计 k)
        if self.n_clusters is None:
            self.n_clusters = max(2, int(np.ceil(np.sqrt(n_samples / 2))))
        self._kmeans = MiniBatchKMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            batch_size=min(256, n_samples),
            n_init="auto",
        ).fit(Xn)

        labels = self._kmeans.labels_
        centers = self._kmeans.cluster_centers_
        base_radii = np.zeros_like(centers)
        for idx in range(self.n_clusters):
            pts = Xn[labels == idx]
            base_radii[idx] = (
                np.max(np.abs(pts - centers[idx]), axis=0) if len(pts) else 1e-6
            )
        # 3) 半径收缩
        self._cluster_radii = base_radii * (1.0 - self.shrink_ratio)

        # 4) 训练距离 & 归一化上限
        dists: list[float] = []
        dim_deltas: list[np.ndarray] = []
        for xi in Xn:
            idx = self._nearest_cluster_idx(xi)
            contrib = self._contributions(xi, idx)
            dists.append(np.linalg.norm(contrib))
            dim_deltas.append(np.abs(contrib))

        d_arr = np.asarray(dists)
        dim_arr = np.asarray(dim_deltas)
        self._max_train_dist = float(
            np.percentile(d_arr, self.calib_percentile) + 1e-12
        )
        self._max_train_dim = (
            np.percentile(dim_arr, self.calib_percentile, axis=0) + 1e-12
        )
        return self

    def predict(self, X: Union[np.ndarray, Sequence]) -> Tuple[np.ndarray, np.ndarray]:
        X = self._ensure_array(X)
        Xn = self._z_norm(X)

        overall, per_dim = [], []
        for xi in Xn:
            idx = self._nearest_cluster_idx(xi)
            contrib = self._contributions(xi, idx)
            dist = np.linalg.norm(contrib)
            overall.append(np.clip(dist / self._max_train_dist, 0.0, 1.0))
            per_dim.append(np.clip(contrib / self._max_train_dim, 0.0, 1.0))
        return np.asarray(overall), np.asarray(per_dim)

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def save(self, path: str, compress: int = 3) -> None:
        joblib.dump(self.__dict__, path, compress=compress)

    @classmethod
    def load(cls, path: str) -> "IMSDetector":
        obj = cls.__new__(cls)
        obj.__dict__.update(joblib.load(path))
        return obj


# ======================================================================
# 数据读取 & 工具
# ======================================================================

def _excel_files(data_dir: str) -> List[str]:
    return sorted(glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True))


def _read_csv(path: str, cols: Optional[List[str]] = None) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, encoding="gbk")
    if cols is not None:
        missing = set(cols) - set(df.columns)
        if missing:
            raise ValueError(f"{path} 缺少列: {missing}")
        df = df[cols]
    return df


def load_training_matrix(data_dir: str, cols: Optional[List[str]] = None) -> np.ndarray:
    arrays: List[np.ndarray] = []
    for fp in _excel_files(data_dir):
        df = _read_csv(fp, cols)
        print(fp)
        arrays.append(df.values.astype(np.float64))
    return np.vstack(arrays)


def train_ims(
    data_dir: str,
    model_path: str,
    cols: Optional[List[str]] = None,
    n_clusters: Optional[int] = None,
    random_state: int = 42,
    shrink_ratio: float = 0.05,
    calib_percentile: float = 95.0,
):
    X = load_training_matrix(data_dir, cols)
    IMSDetector(
        n_clusters=n_clusters,
        random_state=random_state,
        shrink_ratio=shrink_ratio,
        calib_percentile=calib_percentile,
    ).fit(X).save(model_path)
    print(f"[✔] 模型已保存: {model_path}")


def test_ims(
    model_path: str,
    test_csv: str,
    output_csv: str,
    output_png: str,
    cols: Optional[List[str]] = None,
):
    detector = IMSDetector.load(model_path)
    df = _read_csv(test_csv, cols)
    X = df.values.astype(np.float64)
    overall, per_dim = detector.predict(X)

    result_df = pd.DataFrame(per_dim, columns=[f"{c}_score" for c in df.columns])
    result_df.insert(0, "overall_score", overall)
    result_df.to_csv(output_csv, index=False)
    print(f"[✔] CSV 结果已保存: {output_csv}")

    plt.figure(figsize=(10, 3))
    plt.plot(overall, lw=1)
    plt.title("Overall Anomaly Score")
    plt.xlabel("Frame #")
    plt.ylabel("Score (0‑1)")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(output_png, dpi=150)
    plt.close()
    print(f"[✔] 图像已保存: {output_png}")


# ======================================================================
# 参数类 & 运行器
# ======================================================================


@dataclass(slots=True)
class TrainParams:
    data_dir: str
    model_path: str
    cols: Optional[List[str]] = None
    n_clusters: Optional[int] = None
    random_state: int = 42
    shrink_ratio: float = 0.05
    calib_percentile: float = 95.0

    def asdict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TestParams:
    model_path: str
    test_csv: str
    output_csv: str
    output_png: str
    cols: Optional[List[str]] = None

    def asdict(self) -> Dict[str, Any]:
        return asdict(self)


class IMSRunner:
    @staticmethod
    def train(params: TrainParams) -> None:
        train_ims(**params.asdict())

    @staticmethod
    def test(params: TestParams) -> None:
        test_ims(**params.asdict())

if __name__ == "__main__":

    # 重新训练
    #IMSRunner.train(TrainParams(
    #    data_dir=r"C:\Users\megan\Desktop\IMS\Health",  # 健康 CSV 目录
    #    model_path="ims_model.joblib",
     #   cols=["高速转速", "低速转速", "高速电机电压","高速固紧端轴温", "高速滑动端轴温", "高速电机电流","低速A相电流", "低速C相电流"],  # 或 None
     #   shrink_ratio=0.05,  # 可调
     #   calib_percentile=95,
    #))

    # 重新推理
    IMSRunner.test(TestParams(
        model_path="ims_model.joblib",
        test_csv=r"C:\Users\megan\Desktop\IMS\Health\1553数据7.csv",
        cols=["高速转速", "低速转速", "高速电机电压", "高速固紧端轴温", "高速滑动端轴温", "高速电机电流", "低速A相电流","低速C相电流"],  # 或 None
        output_csv="scores.csv",
        output_png="trend.png",
    ))
