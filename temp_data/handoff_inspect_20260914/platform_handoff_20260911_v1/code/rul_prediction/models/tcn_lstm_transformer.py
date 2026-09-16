"""TCN–LSTM–Transformer multitask teacher with channel-attention fusion (DOCX 6.2.2/6.2.1).

    causal dilated TCN
    -> LSTM local branch + Transformer global branch (3 stacked layers)
    -> channel attention fusion
    -> component RUL heads + system RUL head

Output contract: ``{"component": [batch, n_components], "system": [batch]}``.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import check_dropout, check_positive, gather_last_valid, masked_mean_pool, validate_batch_input
from .tcn import TCNBackbone
from .transformer import PositionalEncoding


class LSTMLocalBranch(nn.Module):
    """LSTM 时序细化分支：local fine-grained dependencies."""

    def __init__(self, in_features: int, hidden_size: int, num_layers: int = 1, dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=in_features,
            hidden_size=check_positive(hidden_size, "hidden_size"),
            num_layers=check_positive(num_layers, "num_layers"),
            batch_first=True,
            dropout=check_dropout(dropout) if num_layers > 1 else 0.0,
        )
        self.output_dim = hidden_size

    def forward_features(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths.detach().to("cpu"), batch_first=True, enforce_sorted=False
        )
        out, _ = self.lstm(packed)
        padded, _ = nn.utils.rnn.pad_packed_sequence(
            out, batch_first=True, total_length=x.shape[1]
        )
        return padded

    forward = forward_features


class TransformerGlobalBranch(nn.Module):
    """Transformer 全局关联分支：3 stacked encoder layers per DOCX 6.2.2b."""

    def __init__(
        self,
        in_features: int,
        d_model: int,
        nhead: int,
        num_layers: int = 3,
        dim_feedforward: int | None = None,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = check_positive(d_model, "d_model")
        if d_model % nhead != 0:
            raise ValueError(f"d_model {d_model} must be divisible by nhead {nhead}")
        self.input_projection = nn.Linear(in_features, self.d_model)
        self.positional_encoding = PositionalEncoding(self.d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=self.d_model,
            nhead=int(nhead),
            dim_feedforward=int(dim_feedforward or 4 * self.d_model),
            dropout=check_dropout(dropout),
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=check_positive(num_layers, "num_layers"))
        self.output_dim = self.d_model

    def forward_features(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        projected = self.positional_encoding(self.input_projection(x) * self.d_model**0.5)
        positions = torch.arange(x.shape[1], device=x.device).unsqueeze(0)
        padding_mask = positions >= lengths.to(x.device).unsqueeze(1)
        return self.encoder(projected, src_key_padding_mask=padding_mask)

    forward = forward_features


class ChannelAttentionFusion(nn.Module):
    """通道注意力融合 (DOCX 6.2.2c): temporal global average pooling -> SE-style weights.

    Returns the fused feature map and the per-sample branch weights
    ``[batch, 2]`` (softmax over the two streams).
    """

    def __init__(self, feature_dim: int, hidden: int = 32, dropout: float = 0.1):
        super().__init__()
        self.feature_dim = int(feature_dim)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.attention = nn.Sequential(
            nn.Linear(2 * self.feature_dim, hidden),
            nn.GELU(),
            nn.Dropout(check_dropout(dropout)),
            nn.Linear(hidden, 2),
        )

    def forward(
        self,
        lstm_features: torch.Tensor,
        transformer_features: torch.Tensor,
        lengths: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if lstm_features.shape[-1] != transformer_features.shape[-1]:
            raise ValueError(
                "dual-stream feature dims must align before fusion: "
                f"{lstm_features.shape[-1]} vs {transformer_features.shape[-1]}"
            )
        batch = lstm_features.shape[0]
        # temporal global average pooling per stream; with lengths supplied the
        # average covers only valid steps, so appended padding cannot shift it
        if lengths is None:
            pooled = torch.cat(
                [
                    self.pool(lstm_features.transpose(1, 2)).squeeze(-1),
                    self.pool(transformer_features.transpose(1, 2)).squeeze(-1),
                ],
                dim=-1,
            )
        else:
            pooled = torch.cat(
                [
                    masked_mean_pool(lstm_features, lengths),
                    masked_mean_pool(transformer_features, lengths),
                ],
                dim=-1,
            )
        weights = torch.softmax(self.attention(pooled), dim=-1)  # [batch, 2]
        fused = (
            weights[:, 0].view(batch, 1, 1) * lstm_features
            + weights[:, 1].view(batch, 1, 1) * transformer_features
        )
        return fused, weights


class TeacherTCNLSTMTransformer(nn.Module):
    """Multitask teacher: TCN -> dual stream -> channel attention -> RUL heads."""

    def __init__(
        self,
        n_features: int,
        n_components: int,
        channels: int = 32,
        kernel_size: int = 3,
        dilations: tuple[int, ...] = (1, 2, 4),
        hidden_size: int = 32,
        d_model: int = 64,
        nhead: int = 4,
        transformer_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.n_components = check_positive(n_components, "n_components")
        self.tcn = TCNBackbone(
            n_features=n_features,
            channels=check_positive(channels, "channels"),
            kernel_size=kernel_size,
            dilations=dilations,
            dropout=dropout,
        )
        tcn_dim = self.tcn.feature_dim
        self.local_branch = LSTMLocalBranch(
            in_features=tcn_dim, hidden_size=check_positive(hidden_size, "hidden_size"), dropout=dropout
        )
        self.global_branch = TransformerGlobalBranch(
            in_features=tcn_dim,
            d_model=check_positive(d_model, "d_model"),
            nhead=nhead,
            num_layers=transformer_layers,
            dropout=dropout,
        )
        # align the local stream to the global feature dim before fusion
        self.local_projection = nn.Linear(self.local_branch.output_dim, self.global_branch.output_dim)
        self.fusion = ChannelAttentionFusion(feature_dim=self.global_branch.output_dim, dropout=dropout)
        fused_dim = self.global_branch.output_dim
        self.feature_dim = fused_dim  # distillation alignment target
        self.component_head = nn.Sequential(
            nn.Linear(fused_dim, fused_dim // 2),
            nn.GELU(),
            nn.Dropout(check_dropout(dropout)),
            nn.Linear(fused_dim // 2, self.n_components),
        )
        self.system_head = nn.Sequential(
            nn.Linear(fused_dim, fused_dim // 2),
            nn.GELU(),
            nn.Dropout(check_dropout(dropout)),
            nn.Linear(fused_dim // 2, 1),
        )

    def forward_features(
        self, x: torch.Tensor, lengths: torch.Tensor | None = None
    ) -> torch.Tensor:
        """Return the fused per-timestep features (distillation interface)."""
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        validate_batch_input(x, n_features=self.n_features, lengths=lengths)
        tcn_features = self.tcn(x, lengths)
        local = self.local_projection(self.local_branch(tcn_features, lengths))
        glob = self.global_branch(tcn_features, lengths)
        fused, _ = self.fusion(local, glob, lengths)
        return fused

    def forward(
        self, x: torch.Tensor, lengths: torch.Tensor | None = None
    ) -> dict[str, torch.Tensor]:
        fused = self.forward_features(x, lengths)
        # last valid fused state drives the heads
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        pooled = gather_last_valid(fused, lengths)
        return {
            "component": self.component_head(pooled),
            "system": self.system_head(pooled).squeeze(-1),
        }
