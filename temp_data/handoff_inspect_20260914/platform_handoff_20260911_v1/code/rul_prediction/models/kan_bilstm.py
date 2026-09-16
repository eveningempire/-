"""KAN–BiLSTM: per-timestep KAN nonlinear enhancement followed by a BiLSTM."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import RegressionHead, check_dropout, check_positive, count_trainable_parameters
from .kan import KANEnhancer, MLPEnhancement


class KANBiLSTM(nn.Module):
    """KAN enhancement -> BiLSTM -> regression head (DOCX 6.1 KAN ablation leg)."""

    def __init__(
        self,
        n_features: int,
        hidden_size: int,
        num_layers: int = 1,
        grid_size: int = 5,
        spline_order: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.enhancer = KANEnhancer(
            in_features=self.n_features,
            hidden_features=self.n_features,  # keep residual alignment with BiLSTM input
            grid_size=grid_size,
            spline_order=spline_order,
        )
        self.hidden_size = check_positive(hidden_size, "hidden_size")
        self.dropout = nn.Dropout(check_dropout(dropout))
        self.lstm = nn.LSTM(
            input_size=self.n_features,
            hidden_size=self.hidden_size,
            num_layers=check_positive(num_layers, "num_layers"),
            batch_first=True,
            bidirectional=True,
        )
        self.head = RegressionHead(2 * self.hidden_size, dropout=self.dropout.p)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        enhanced = self.enhancer(x, lengths)
        packed = nn.utils.rnn.pack_padded_sequence(
            enhanced, lengths.detach().to("cpu"), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)
        joined = torch.cat([h_n[-2], h_n[-1]], dim=-1)
        return self.head(self.dropout(joined))


class MLPBiLSTM(nn.Module):
    """Parameter-matched MLP replaces the KAN enhancer (fairness ablation)."""

    def __init__(
        self,
        n_features: int,
        hidden_size: int,
        num_layers: int = 1,
        grid_size: int = 5,
        spline_order: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        kan = KANEnhancer(
            in_features=self.n_features,
            hidden_features=self.n_features,
            grid_size=grid_size,
            spline_order=spline_order,
        )
        target = count_trainable_parameters(kan)
        matched_hidden, _ = MLPEnhancement.match_parameters(
            in_features=self.n_features, target_parameters=target
        )
        self.enhancer = MLPEnhancement(
            in_features=self.n_features, hidden_features=matched_hidden
        )
        self.hidden_size = check_positive(hidden_size, "hidden_size")
        self.dropout = nn.Dropout(check_dropout(dropout))
        self.lstm = nn.LSTM(
            input_size=self.n_features,
            hidden_size=self.hidden_size,
            num_layers=check_positive(num_layers, "num_layers"),
            batch_first=True,
            bidirectional=True,
        )
        self.head = RegressionHead(2 * self.hidden_size, dropout=self.dropout.p)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        enhanced = self.enhancer(x, lengths)
        packed = nn.utils.rnn.pack_padded_sequence(
            enhanced, lengths.detach().to("cpu"), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)
        joined = torch.cat([h_n[-2], h_n[-1]], dim=-1)
        return self.head(self.dropout(joined))
