"""Shared building blocks for RUL models: input validation, masking, heads.

Conventions frozen for the whole project:

- inputs are batches ``[batch, time, feature]`` plus optional integer
  ``lengths`` giving the number of valid (observed) steps per row;
- single-task regressors return ``[batch]``;
- the multitask teacher returns ``{"component": [batch, n_components],
  "system": [batch]}``;
- padded positions must never influence any output (all modules mask).
"""

from __future__ import annotations

from typing import Mapping

import torch
import torch.nn as nn

MIN_TIME_STEPS = 1


def validate_batch_input(
    x: torch.Tensor,
    *,
    n_features: int,
    lengths: torch.Tensor | None = None,
    min_time: int = MIN_TIME_STEPS,
) -> None:
    """Reject malformed, empty, or non-finite batches before any module runs."""

    if x.dim() != 3:
        raise ValueError(f"expected [batch, time, feature] input, got shape {tuple(x.shape)}")
    batch, time_steps, features = x.shape
    if batch == 0:
        raise ValueError("empty batch is rejected")
    if time_steps < min_time:
        raise ValueError(f"time dimension must be >= {min_time}, got {time_steps}")
    if features != n_features:
        raise ValueError(f"feature mismatch: model expects {n_features}, got {features}")
    if not torch.isfinite(x).all():
        raise ValueError("input contains NaN/Inf values")
    if lengths is not None:
        if lengths.shape != (batch,):
            raise ValueError(f"lengths must have shape ({batch},), got {tuple(lengths.shape)}")
        lengths_cpu = lengths.detach().to("cpu")
        if int(lengths_cpu.min()) < 1:
            raise ValueError("every sequence needs at least one valid step (length >= 1)")
        if int(lengths_cpu.max()) > time_steps:
            raise ValueError(
                f"lengths must not exceed the window length {time_steps}, got {int(lengths_cpu.max())}"
            )


def gather_last_valid(outputs: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
    """Gather the hidden state at each row's last valid time step."""

    index = (lengths.to(outputs.device) - 1).view(-1, 1, 1).expand(-1, 1, outputs.shape[-1])
    return outputs.gather(1, index).squeeze(1)


def masked_mean_pool(outputs: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
    """Average the valid time steps of each row, ignoring padding."""

    mask = torch.arange(outputs.shape[1], device=outputs.device).unsqueeze(0)
    mask = (mask < lengths.to(outputs.device).unsqueeze(1)).unsqueeze(-1).to(outputs.dtype)
    summed = (outputs * mask).sum(dim=1)
    return summed / lengths.to(outputs.device).unsqueeze(1).to(outputs.dtype)


class RegressionHead(nn.Module):
    """Dropout + two-layer MLP mapping a pooled representation to one RUL value."""

    def __init__(self, in_features: int, hidden_features: int | None = None, dropout: float = 0.1):
        super().__init__()
        hidden = hidden_features or max(8, in_features // 2)
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features).squeeze(-1)


class SequenceModelConfigError(ValueError):
    """Raised when a model configuration is structurally invalid."""


def check_positive(value: int, name: str) -> int:
    if int(value) < 1:
        raise SequenceModelConfigError(f"{name} must be >= 1, got {value}")
    return int(value)


def check_dropout(value: float) -> float:
    if not 0.0 <= float(value) < 1.0:
        raise SequenceModelConfigError(f"dropout must lie in [0, 1), got {value}")
    return float(value)


def count_trainable_parameters(module: nn.Module) -> int:
    """Exact trainable-parameter count (the regression head is included)."""

    return int(sum(p.numel() for p in module.parameters() if p.requires_grad))


def match_hidden_size_within_budget(
    *,
    model_type: str,
    base_config: Mapping[str, object],
    n_features: int,
    n_components: int,
    target_parameters: int,
    lo: int = 1,
    hi: int = 512,
) -> tuple[int, int]:
    """Search the unidirectional hidden size closest to a target parameter count.

    Returns ``(hidden_size, exact_parameter_count)``.  The parameter count of
    an LSTM grows with the hidden size, so a bisection over integer candidates
    finds the closest feasible value.
    """

    def params(hidden: int) -> int:
        model = build_model_local(
            {"type": model_type, "hidden_size": hidden, **dict(base_config)},
            n_features=n_features,
            n_components=n_components,
        )
        return count_trainable_parameters(model)

    if params(lo) >= target_parameters:
        return lo, params(lo)
    while hi > lo and params(hi) < target_parameters:
        break
    left, right = lo, hi
    while left < right:
        mid = (left + right + 1) // 2
        if params(mid) <= target_parameters:
            left = mid
        else:
            right = mid - 1
    below = (left, params(left))
    above_hidden = min(left + 1, hi)
    above = (above_hidden, params(above_hidden))
    best = min((below, above), key=lambda item: (abs(item[1] - target_parameters), item[0]))
    return best


def build_model_local(config: Mapping[str, object], *, n_features: int, n_components: int):
    from . import build_model

    return build_model(dict(config), n_features=n_features, n_components=n_components)
