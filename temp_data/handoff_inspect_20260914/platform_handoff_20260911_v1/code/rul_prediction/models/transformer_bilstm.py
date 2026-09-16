"""Transformer–BiLSTM: Transformer encoder followed by a BiLSTM decoder."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import RegressionHead, check_dropout, check_positive
from .transformer import TransformerBackbone


class TransformerBiLSTM(nn.Module):
    """input projection -> positional encoding -> Transformer -> BiLSTM -> head."""

    def __init__(
        self,
        n_features: int,
        d_model: int,
        nhead: int,
        hidden_size: int,
        num_layers: int = 1,
        transformer_layers: int = 1,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.backbone = TransformerBackbone(
            n_features=n_features,
            d_model=check_positive(d_model, "d_model"),
            nhead=nhead,
            num_layers=transformer_layers,
            dropout=dropout,
        )
        self.hidden_size = check_positive(hidden_size, "hidden_size")
        self.dropout = nn.Dropout(check_dropout(dropout))
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
        features = self.backbone(x, lengths)
        packed = nn.utils.rnn.pack_padded_sequence(
            features, lengths.detach().to("cpu"), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)
        joined = torch.cat([h_n[-2], h_n[-1]], dim=-1)
        return self.head(self.dropout(joined))
