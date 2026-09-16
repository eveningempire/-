"""Transformer encoder backbone over completed history windows.

Every position inside the window is a past observation (<= decision point), so
full self-attention over the window is causal.  Padded positions are hidden by
the key-padding mask and never influence valid outputs.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn

from .common import (
    RegressionHead,
    check_dropout,
    check_positive,
    masked_mean_pool,
    validate_batch_input,
)


class PositionalEncoding(nn.Module):
    """Fixed sinusoidal positional encoding added to the projected inputs."""

    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        position = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32)
            * (-math.log(10000.0) / d_model)
        )
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)[:, : d_model // 2]
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.shape[1]]


class TransformerBackbone(nn.Module):
    """input projection -> positional encoding -> Transformer encoder.

    Returns per-timestep features ``[batch, time, d_model]`` with padding
    neutralised through the key-padding mask.
    """

    def __init__(
        self,
        n_features: int,
        d_model: int,
        nhead: int,
        num_layers: int,
        dim_feedforward: int | None = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.d_model = check_positive(d_model, "d_model")
        if d_model % nhead != 0:
            raise ValueError(f"d_model {d_model} must be divisible by nhead {nhead}")
        self.input_projection = nn.Linear(self.n_features, self.d_model)
        self.positional_encoding = PositionalEncoding(self.d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=int(nhead),
            dim_feedforward=int(dim_feedforward or 4 * self.d_model),
            dropout=check_dropout(dropout),
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=check_positive(num_layers, "num_layers"))

    def forward_features(
        self, x: torch.Tensor, lengths: torch.Tensor | None = None
    ) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full(
                (x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device
            )
        validate_batch_input(x, n_features=self.n_features, lengths=lengths)
        projected = self.positional_encoding(self.input_projection(x) * math.sqrt(self.d_model))
        positions = torch.arange(x.shape[1], device=x.device).unsqueeze(0)
        padding_mask = positions >= lengths.to(x.device).unsqueeze(1)
        return self.encoder(projected, src_key_padding_mask=padding_mask)

    forward = forward_features


class TransformerRegressor(nn.Module):
    """TransformerBackbone -> masked mean pooling -> regression head."""

    def __init__(
        self,
        n_features: int,
        d_model: int,
        nhead: int,
        num_layers: int,
        dim_feedforward: int | None = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.backbone = TransformerBackbone(
            n_features=n_features,
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
        )
        self.head = RegressionHead(d_model, dropout=dropout)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        features = self.backbone(x, lengths)
        if lengths is None:
            lengths = torch.full(
                (x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device
            )
        return self.head(masked_mean_pool(features, lengths))
