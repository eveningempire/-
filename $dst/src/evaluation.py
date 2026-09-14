"""评估指标辅助（14 类 ensemble / 子系统切片）。"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from .config import Config


def classification_metrics(
    true_ids: np.ndarray,
    pred_ids: np.ndarray,
    class_names_en: List[str],
) -> dict:
    report = classification_report(
        true_ids,
        pred_ids,
        labels=list(range(len(class_names_en))),
        target_names=class_names_en,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": float((true_ids == pred_ids).mean()),
        "macro_precision": float(report["macro avg"]["precision"]),
        "macro_recall": float(report["macro avg"]["recall"]),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "classification_report": report,
        "confusion_matrix": confusion_matrix(
            true_ids, pred_ids, labels=list(range(len(class_names_en)))
        ).tolist(),
    }


def subsystem_slice_metrics(
    true_ids: np.ndarray,
    pred_ids: np.ndarray,
    class_ids: List[int],
    class_names_en: List[str],
) -> Optional[dict]:
    mask = np.isin(true_ids, class_ids)
    if mask.sum() == 0:
        return None
    local_names = [Config.CLASS_NAMES_EN[c] for c in class_ids]
    local_true = true_ids[mask]
    local_pred = pred_ids[mask]
    # 子集 accuracy：仅在该子集标签上评估
    return {
        "class_ids": class_ids,
        "n_samples": int(mask.sum()),
        "accuracy": float((local_true == local_pred).mean()),
        "classification_report": classification_report(
            local_true,
            local_pred,
            labels=class_ids,
            target_names=local_names,
            output_dict=True,
            zero_division=0,
        ),
    }
