"""Pure BiLSTM regressor over completed history windows.

The DOCX describes a bidirectional reader of ``X_t=[x_t,...,x_{t+L-1}]``; per
the frozen interpretation the input here is always the completed history
window ``[x_{t-L+1},...,x_t]``.  The backward LSTM scans only *inside* that
window (via ``pack_padded_sequence``), so it can never see past the decision
point or padded positions.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import (
    RegressionHead,
    check_dropout,
    check_positive,
    validate_batch_input,
)


class BiLSTMRegressor(nn.Module):
    """BiLSTM -> concatenation of last-layer forward/backward final states -> head."""

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
            bidirectional=True,
            dropout=self.dropout.p if self.num_layers > 1 else 0.0,
        )
        self.head = RegressionHead(2 * self.hidden_size, dropout=self.dropout.p)

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
        # h_n: [num_layers*2, batch, hidden]; last layer = rows -2 (forward) and -1 (backward)
        forward_last = h_n[-2]
        backward_last = h_n[-1]
        joined = torch.cat([forward_last, backward_last], dim=-1)
        return self.head(self.dropout(joined))
