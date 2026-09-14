"""层次化 14 类标签映射与概率合并（Hier14 单模型）。"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn.functional as F

IGNORE_INDEX = -1

COARSE_NORMAL = 0
COARSE_PROPULSION = 1
COARSE_CONTROL = 2

COARSE_NAMES = ("normal", "propulsion", "control")


def global_to_coarse(global_id: int) -> int:
    gid = int(global_id)
    if gid == 0:
        return COARSE_NORMAL
    if 1 <= gid <= 7:
        return COARSE_PROPULSION
    return COARSE_CONTROL


def global_to_prop_fine(global_id: int) -> int:
    gid = int(global_id)
    if 1 <= gid <= 7:
        return gid - 1
    return IGNORE_INDEX


def global_to_gnc_fine(global_id: int) -> int:
    gid = int(global_id)
    if 8 <= gid <= 13:
        return gid - 8
    return IGNORE_INDEX


def batch_hierarchical_labels(
    global_labels: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """global_labels: (B,) int64 → coarse, prop_fine, gnc_fine。"""
    labels = global_labels.detach().cpu().numpy().astype(np.int64)
    coarse = np.array([global_to_coarse(y) for y in labels], dtype=np.int64)
    prop_fine = np.array([global_to_prop_fine(y) for y in labels], dtype=np.int64)
    gnc_fine = np.array([global_to_gnc_fine(y) for y in labels], dtype=np.int64)
    device = global_labels.device
    return (
        torch.tensor(coarse, dtype=torch.long, device=device),
        torch.tensor(prop_fine, dtype=torch.long, device=device),
        torch.tensor(gnc_fine, dtype=torch.long, device=device),
    )


def hierarchical_probs_to_flat(
    coarse_probs: torch.Tensor,
    prop_probs: torch.Tensor,
    gnc_probs: torch.Tensor,
    eps: float = 1e-8,
) -> torch.Tensor:
    """
    coarse_probs: (B, 3), prop_probs: (B, 7), gnc_probs: (B, 6)
    → full_probs: (B, 14)
    """
    batch_size = coarse_probs.size(0)
    full = torch.zeros(batch_size, 14, device=coarse_probs.device, dtype=coarse_probs.dtype)
    full[:, 0] = coarse_probs[:, COARSE_NORMAL]
    full[:, 1:8] = coarse_probs[:, COARSE_PROPULSION : COARSE_PROPULSION + 1] * prop_probs
    full[:, 8:14] = coarse_probs[:, COARSE_CONTROL : COARSE_CONTROL + 1] * gnc_probs
    full = full.clamp(min=eps)
    row_sum = full.sum(dim=1, keepdim=True).clamp(min=eps)
    return full / row_sum


def hierarchical_logits_to_flat(
    logits_coarse: torch.Tensor,
    logits_prop: torch.Tensor,
    logits_gnc: torch.Tensor,
    eps: float = 1e-8,
) -> torch.Tensor:
    coarse_probs = F.softmax(logits_coarse, dim=1)
    prop_probs = F.softmax(logits_prop, dim=1)
    gnc_probs = F.softmax(logits_gnc, dim=1)
    probs = hierarchical_probs_to_flat(coarse_probs, prop_probs, gnc_probs, eps=eps)
    return torch.log(probs)


def coarse_head_metrics(
    true_global: np.ndarray,
    pred_coarse: np.ndarray,
) -> Dict[str, object]:
    true_coarse = np.array([global_to_coarse(int(y)) for y in true_global])
    pred_coarse = np.asarray(pred_coarse, dtype=np.int64)
    from sklearn.metrics import classification_report, confusion_matrix

    report = classification_report(
        true_coarse,
        pred_coarse,
        labels=[0, 1, 2],
        target_names=list(COARSE_NAMES),
        output_dict=True,
        zero_division=0,
    )
    return {
        "classification_report": report,
        "confusion_matrix": confusion_matrix(
            true_coarse, pred_coarse, labels=[0, 1, 2]
        ).tolist(),
    }
