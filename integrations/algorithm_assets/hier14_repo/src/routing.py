"""双专家 L1 路由：推进 / 姿控异常分 → 全局 14 类标签。"""

from __future__ import annotations

from typing import Tuple, Union

import numpy as np
import torch

from .expert_config import GNC_LOCAL_TO_GLOBAL

ArrayLike = Union[np.ndarray, torch.Tensor]


def _to_numpy(probs: ArrayLike) -> np.ndarray:
    if isinstance(probs, torch.Tensor):
        return probs.detach().cpu().numpy()
    return np.asarray(probs)


def subsystem_anomaly_scores(
    prop_probs: ArrayLike,
    gnc_probs: ArrayLike,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    prop_probs: (N, 8) softmax；index 0 = 正常
    gnc_probs: (N, 7) softmax；index 0 = 正常
    """
    pp = _to_numpy(prop_probs)
    gp = _to_numpy(gnc_probs)
    return 1.0 - pp[:, 0], 1.0 - gp[:, 0]


def route_prediction(
    prop_probs: ArrayLike,
    gnc_probs: ArrayLike,
    *,
    anomaly_threshold: float = 0.5,
) -> int:
    """单样本路由，返回全局 class_id 0–13。"""
    preds = route_batch(
        prop_probs[np.newaxis, :],
        gnc_probs[np.newaxis, :],
        anomaly_threshold=anomaly_threshold,
    )
    return int(preds[0])


def route_batch(
    prop_probs: ArrayLike,
    gnc_probs: ArrayLike,
    *,
    anomaly_threshold: float = 0.5,
) -> np.ndarray:
    """
    批量路由。

    规则（ROADMAP §5.2）：
    - 两侧异常分均 < threshold → 0 正常
    - 仅推进高 → 推进 argmax（1–7）
    - 仅姿控高 → 姿控 argmax 映射 8–13
    - 两侧均高 → 异常分更高一侧
    """
    pp = _to_numpy(prop_probs)
    gp = _to_numpy(gnc_probs)
    n = pp.shape[0]
    prop_anom, gnc_anom = subsystem_anomaly_scores(pp, gp)
    prop_high = prop_anom >= anomaly_threshold
    gnc_high = gnc_anom >= anomaly_threshold

    prop_cls = pp.argmax(axis=1)
    gnc_cls = gp.argmax(axis=1)
    gnc_global = np.array([GNC_LOCAL_TO_GLOBAL[int(c)] for c in gnc_cls], dtype=np.int64)

    out = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if not prop_high[i] and not gnc_high[i]:
            out[i] = 0
        elif prop_high[i] and not gnc_high[i]:
            out[i] = int(prop_cls[i])
        elif gnc_high[i] and not prop_high[i]:
            out[i] = int(gnc_global[i])
        else:
            out[i] = int(prop_cls[i]) if prop_anom[i] >= gnc_anom[i] else int(gnc_global[i])
    return out


def routing_decision_stats(
    prop_probs: ArrayLike,
    gnc_probs: ArrayLike,
    *,
    anomaly_threshold: float = 0.5,
) -> dict:
    prop_anom, gnc_anom = subsystem_anomaly_scores(prop_probs, gnc_probs)
    prop_high = prop_anom >= anomaly_threshold
    gnc_high = gnc_anom >= anomaly_threshold
    n = len(prop_anom)
    both_low = (~prop_high) & (~gnc_high)
    prop_only = prop_high & (~gnc_high)
    gnc_only = gnc_high & (~prop_high)
    both_high = prop_high & gnc_high
    return {
        "n_samples": int(n),
        "anomaly_threshold": float(anomaly_threshold),
        "normal_both_low": int(both_low.sum()),
        "propulsion_only": int(prop_only.sum()),
        "gnc_only": int(gnc_only.sum()),
        "both_high": int(both_high.sum()),
    }
