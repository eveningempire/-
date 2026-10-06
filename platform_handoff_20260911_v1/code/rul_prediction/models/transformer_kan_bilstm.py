"""Transformer–KAN–BiLSTM and its parameter-matched MLP ablation (DOCX 6.1).

Pipeline (frozen interpretation: the window is completed history):

    input projection -> positional encoding -> Transformer encoder
    -> KAN nonlinear enhancement (or matched MLP ablation)
    -> BiLSTM -> last valid forward/backward states -> regression head
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import RegressionHead, check_dropout, check_positive
from .kan import KANEnhancer, MLPEnhancement
from .transformer import TransformerBackbone


class TransformerKANBiLSTM(nn.Module):
    """Full 6.1 stack; ``enhancer='mlp'`` gives the parameter-matched ablation."""

    def __init__(
        self,
        n_features: int,
        d_model: int,
        nhead: int,
        hidden_size: int,
        num_layers: int = 1,
        transformer_layers: int = 1,
        enhancer: str = "kan",
        grid_size: int = 5,
        spline_order: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        if enhancer not in {"kan", "mlp"}:
            raise ValueError(f"enhancer must be 'kan' or 'mlp', got {enhancer!r}")
        self.n_features = int(n_features)
        self.enhancer_type = enhancer
        self.backbone = TransformerBackbone(
            n_features=n_features,
            d_model=check_positive(d_model, "d_model"),
            nhead=nhead,
            num_layers=transformer_layers,
            dropout=dropout,
        )
        self.hidden_size = check_positive(hidden_size, "hidden_size")
        self.dropout = nn.Dropout(check_dropout(dropout))
        if enhancer == "kan":
            self.enhancer: KANEnhancer | MLPEnhancement = KANEnhancer(
                in_features=self.backbone.d_model,
                hidden_features=self.backbone.d_model,
                grid_size=grid_size,
                spline_order=spline_order,
            )
        else:
            target = int(
                sum(
                    p.numel()
                    for p in KANEnhancer(
                        in_features=self.backbone.d_model,
                        hidden_features=self.backbone.d_model,
                        grid_size=grid_size,
                        spline_order=spline_order,
                    ).parameters()
                    if p.requires_grad
                )
            )
            hidden, _ = MLPEnhancement.match_parameters(
                in_features=self.backbone.d_model, target_parameters=target
            )
            self.enhancer = MLPEnhancement(
                in_features=self.backbone.d_model, hidden_features=hidden
            )
        self.lstm = nn.LSTM(
            input_size=self.backbone.d_model,
            hidden_size=self.hidden_size,
            num_layers=check_positive(num_layers, "num_layers"),
            batch_first=True,
            bidirectional=True,
        )
        self.head = RegressionHead(2 * self.hidden_size, dropout=self.dropout.p)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        encoded = self.backbone(x, lengths)
        enhanced = self.enhancer(encoded, lengths)
        packed = nn.utils.rnn.pack_padded_sequence(
            enhanced, lengths.detach().to("cpu"), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)
        joined = torch.cat([h_n[-2], h_n[-1]], dim=-1)
        return self.head(self.dropout(joined))
