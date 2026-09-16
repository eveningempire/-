"""Causal dilated TCN backbone (DOCX 6.2.2a: feature extractor, not a regressor).

Every convolution pads only on the left, so output step ``t`` depends solely
on inputs ``<= t`` (verified by future-poisoning tests).
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


class CausalConvBlock(nn.Module):
    """Left-padded dilated causal conv + GELU + residual."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, dilation: int, dropout: float):
        super().__init__()
        self.pad_left = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size=kernel_size,
            dilation=dilation,
            padding=0,
        )
        self.norm = nn.LayerNorm(out_channels)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(check_dropout(dropout))
        self.residual = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1) if in_channels != out_channels else nn.Identity()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, time, channels]; conv operates on [batch, channels, time]
        # with left padding only, so step t depends solely on inputs <= t.
        conv_input = x.transpose(1, 2)
        padded = nn.functional.pad(conv_input, (self.pad_left, 0))
        out = self.conv(padded).transpose(1, 2)
        out = self.norm(out)
        out = self.dropout(self.activation(out))
        residual = self.residual(conv_input).transpose(1, 2)
        return out + residual


class TCNBackbone(nn.Module):
    """Multi-scale causal feature extractor returning per-timestep features."""

    def __init__(
        self,
        n_features: int,
        channels: int,
        kernel_size: int = 3,
        dilations: tuple[int, ...] = (1, 2, 4),
        feature_dim: int | None = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.blocks = nn.ModuleList()
        in_channels = n_features
        for dilation in dilations:
            self.blocks.append(
                CausalConvBlock(in_channels, check_positive(channels, "channels"), kernel_size, dilation, dropout)
            )
            in_channels = channels
        # DOCX 6.2.2a: the regression layer is replaced by an FC feature
        # reduction layer producing the multi-scale feature interface
        self.feature_dim = int(feature_dim or channels)
        self.feature_reduction = (
            nn.Linear(in_channels, self.feature_dim) if in_channels != self.feature_dim else nn.Identity()
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


class TCNRegressor(nn.Module):
    """TCN backbone -> masked mean pool -> regression head (baseline interface)."""

    def __init__(
        self,
        n_features: int,
        channels: int,
        kernel_size: int = 3,
        dilations: tuple[int, ...] = (1, 2, 4),
        dropout: float = 0.1,
    ):
        super().__init__()
        self.backbone = TCNBackbone(
            n_features=n_features,
            channels=channels,
            kernel_size=kernel_size,
            dilations=dilations,
            dropout=dropout,
        )
        self.head = RegressionHead(self.backbone.feature_dim, dropout=dropout)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        features = self.backbone(x, lengths)
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        return self.head(masked_mean_pool(features, lengths))
