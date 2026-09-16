"""Pure unidirectional LSTM regressor over completed history windows."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import (
    RegressionHead,
    check_dropout,
    check_positive,
    gather_last_valid,
    validate_batch_input,
)


class LSTMRegressor(nn.Module):
    """1-2 layer LSTM -> last valid hidden state -> dropout -> FC regression head."""

    def __init__(
        self,
        n_features: int,
        hidden_size: int,
        num_layers: int = 1,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.hidden_size = check_positive(hidden_size, "hidden_size")
        self.num_layers = check_positive(num_layers, "num_layers")
        self.dropout = nn.Dropout(check_dropout(dropout))
        self.lstm = nn.LSTM(
            input_size=self.n_features,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            batch_first=True,
            bidirectional=False,
            dropout=self.dropout.p if self.num_layers > 1 else 0.0,
        )
        self.head = RegressionHead(self.hidden_size, dropout=self.dropout.p)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full(
                (x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device
            )
        validate_batch_input(x, n_features=self.n_features, lengths=lengths)
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths.detach().to("cpu"), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)
        last_hidden = h_n[-1]  # [batch, hidden]
        return self.head(self.dropout(last_hidden))
