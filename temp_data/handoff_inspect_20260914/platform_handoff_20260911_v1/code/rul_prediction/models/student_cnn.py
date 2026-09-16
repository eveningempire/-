"""Lightweight causal CNN student for edge deployment (DOCX 6.2.3).

Reuses the TCN causal blocks: every convolution pads only on the left, so the
student is streamable and passes the same future-poisoning tests as the
teacher's TCN stage.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import (
    RegressionHead,
    check_dropout,
    check_positive,
    masked_mean_pool,
    validate_batch_input,
)
from .tcn import CausalConvBlock


class CNNFeatureExtractor(nn.Module):
    """Stacked causal conv blocks; returns per-timestep features [B, T, C]."""

    def __init__(
        self,
        n_features: int,
        channels: int = 32,
        kernel_size: int = 5,
        num_blocks: int = 3,
        feature_dim: int | None = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.feature_dim = int(feature_dim or check_positive(channels, "channels"))
        width = check_positive(channels, "channels")
        in_channels = n_features
        blocks: list[CausalConvBlock] = []
        for index in range(check_positive(num_blocks, "num_blocks")):
            blocks.append(
                CausalConvBlock(
                    in_channels=in_channels,
                    out_channels=width,
                    kernel_size=kernel_size,
                    dilation=2**index,
                    dropout=dropout,
                )
            )
            in_channels = width
        self.blocks = nn.ModuleList(blocks)
        self.feature_reduction = (
            nn.Linear(in_channels, self.feature_dim)
            if in_channels != self.feature_dim
            else nn.Identity()
        )

    def forward_features(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        validate_batch_input(x, n_features=self.n_features, lengths=lengths)
        out = x
        for block in self.blocks:
            out = block(out)
        return self.feature_reduction(out)

    forward = forward_features


class StudentCNNRegressor(nn.Module):
    """CNN student: feature extractor -> masked mean pool -> RUL head.

    ``forward`` stores the penultimate features in ``last_features`` for the
    distillation losses.
    """

    def __init__(
        self,
        n_features: int,
        channels: int = 32,
        kernel_size: int = 5,
        num_blocks: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.extractor = CNNFeatureExtractor(
            n_features=n_features,
            channels=channels,
            kernel_size=kernel_size,
            num_blocks=num_blocks,
            dropout=dropout,
        )
        self.feature_dim = self.extractor.feature_dim
        self.head = RegressionHead(self.feature_dim, dropout=check_dropout(dropout))
        self.last_features: torch.Tensor | None = None

    def forward_features(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        return self.extractor(x, lengths)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        features = self.extractor(x, lengths)
        self.last_features = features
        return self.head(masked_mean_pool(features, lengths))
