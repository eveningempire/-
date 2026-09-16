"""Kolmogorov–Arnold Network layers (B-spline basis) and the matched MLP ablation.

The KAN enhances features with learnable univariate B-spline functions as in
DOCX 6.1(3).  ``MLPEnhancement`` is the parameter-matched plain-MLP replacement
used for the fairness ablation.

Implementation notes: the knot vector extends the uniform grid by
``spline_order`` steps on each side (efficient-KAN style), so every Cox–de
Boor denominator is a positive knot gap and extreme inputs only fall back to
the bounded SiLU branch — outputs and gradients stay finite.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .common import RegressionHead, check_dropout, check_positive, masked_mean_pool, validate_batch_input


class KANLayer(nn.Module):
    """Efficient B-spline KAN layer: out_o = w_o·SiLU(x) + Σ_{i,k} c_{oik} B_ik(x)."""

    GRID_RANGE = 3.0

    def __init__(
        self,
        in_features: int,
        out_features: int,
        grid_size: int = 5,
        spline_order: int = 3,
    ):
        super().__init__()
        self.in_features = check_positive(in_features, "in_features")
        self.out_features = check_positive(out_features, "out_features")
        self.grid_size = check_positive(grid_size, "grid_size")
        self.spline_order = check_positive(spline_order, "spline_order")

        base = torch.linspace(-self.GRID_RANGE, self.GRID_RANGE, self.grid_size + 1)
        step = (base[1] - base[0]).unsqueeze(0).repeat(self.in_features, 1)
        base = base.unsqueeze(0).repeat(self.in_features, 1)  # [in, G+1]
        offsets = torch.arange(1, self.spline_order + 1, dtype=base.dtype)
        left = base[:, :1] - step * offsets.flip(0).unsqueeze(0)  # k knots: g0-k*step .. g0-step
        right = base[:, -1:] + step * offsets.unsqueeze(0)  # k knots: gN+step .. gN+k*step
        grid = torch.cat([left, base, right], dim=1)  # [in, G + 2k + 1], strictly increasing
        self.register_buffer("grid", grid)
        n_basis = self.grid_size + self.spline_order
        self.base_weight = nn.Parameter(torch.empty(self.out_features, self.in_features))
        self.spline_weight = nn.Parameter(
            torch.empty(self.out_features, self.in_features, n_basis)
        )
        nn.init.kaiming_uniform_(self.base_weight, a=5**0.5)
        nn.init.normal_(
            self.spline_weight,
            mean=0.0,
            std=(1.0 / (self.in_features * n_basis)) ** 0.5,
        )

    def b_spline_basis(self, x_flat: torch.Tensor) -> torch.Tensor:
        """Cox–de Boor recursion; ``x_flat`` is [N, in_features]."""

        grid = self.grid  # [in, M], M = G + 2k + 1
        n_knots = grid.shape[1]
        xi = x_flat.unsqueeze(-1)  # [N, in, 1]
        basis = ((xi >= grid[:, :-1]) & (xi < grid[:, 1:])).to(x_flat.dtype)  # [N, in, M-1]
        for degree in range(1, self.spline_order + 1):
            n_i = n_knots - 1 - degree
            t_i = grid[:, :n_i]
            t_i_d = grid[:, degree : degree + n_i]
            t_i_1 = grid[:, 1 : n_i + 1]
            t_i_d_1 = grid[:, degree + 1 : degree + n_i + 1]
            left = (xi - t_i) / (t_i_d - t_i) * basis[..., :n_i]
            right = (t_i_d_1 - xi) / (t_i_d_1 - t_i_1) * basis[..., 1 : n_i + 1]
            basis = left + right
        return basis  # [N, in, G+k]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() not in (2, 3):
            raise ValueError(
                f"KANLayer expects [batch, features] or [batch, time, features], got {tuple(x.shape)}"
            )
        if x.shape[-1] != self.in_features:
            raise ValueError(f"KANLayer expects {self.in_features} features, got {x.shape[-1]}")
        if not torch.isfinite(x).all():
            raise ValueError("KANLayer input contains NaN/Inf")
        squeeze_time = x.dim() == 2
        if squeeze_time:
            x = x.unsqueeze(1)
        batch, time_steps, _ = x.shape
        flat = x.reshape(batch * time_steps, self.in_features)
        base = F.silu(flat)
        basis = self.b_spline_basis(flat)
        spline = torch.einsum("nik,oik->no", basis, self.spline_weight)
        output = torch.einsum("ni,oi->no", base, self.base_weight) + spline
        output = output.reshape(batch, time_steps, self.out_features)
        if squeeze_time:
            output = output.squeeze(1)
        return output


class KANEnhancer(nn.Module):
    """Per-timestep KAN nonlinear enhancement used between encoder and BiLSTM."""

    def __init__(
        self,
        in_features: int,
        hidden_features: int,
        grid_size: int = 5,
        spline_order: int = 3,
    ):
        super().__init__()
        self.layer = KANLayer(
            in_features=in_features,
            out_features=hidden_features,
            grid_size=grid_size,
            spline_order=spline_order,
        )
        self.residual = in_features == hidden_features

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        del lengths  # per-timestep map: padded positions stay padded (zero) positions
        out = self.layer(x)
        if self.residual:
            out = out + x
        return out


class MLPEnhancement(nn.Module):
    """Plain MLP applied per timestep; the KAN ablation counterpart."""

    def __init__(self, in_features: int, hidden_features: int, dropout: float = 0.0):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_features),
            nn.GELU(),
            nn.Dropout(check_dropout(dropout)),
            nn.Linear(hidden_features, in_features),
        )
        self.residual = True

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        del lengths
        return x + self.net(x)

    @classmethod
    def match_parameters(
        cls, in_features: int, target_parameters: int, lo: int = 2, hi: int = 2048
    ) -> tuple[int, int]:
        """Find hidden_features whose two-layer MLP is closest to the target."""

        def params(hidden: int) -> int:
            return int(
                sum(
                    p.numel()
                    for p in cls(in_features=in_features, hidden_features=hidden).parameters()
                    if p.requires_grad
                )
            )

        left, right = lo, hi
        while left < right:
            mid = (left + right + 1) // 2
            if params(mid) <= target_parameters:
                left = mid
            else:
                right = mid - 1
        below = params(left)
        above_hidden = min(left + 1, hi)
        above = params(above_hidden)
        if abs(above - target_parameters) < abs(below - target_parameters):
            return above_hidden, above
        return left, below


class KANRegressor(nn.Module):
    """Standalone per-window KAN regressor (interface/ablation use)."""

    def __init__(
        self,
        n_features: int,
        hidden_size: int,
        grid_size: int = 5,
        spline_order: int = 3,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.n_features = int(n_features)
        self.enhancer = KANEnhancer(
            in_features=n_features,
            hidden_features=check_positive(hidden_size, "hidden_size"),
            grid_size=grid_size,
            spline_order=spline_order,
        )
        self.dropout = nn.Dropout(check_dropout(dropout))
        self.head = RegressionHead(
            n_features if n_features == hidden_size else hidden_size, dropout=dropout
        )

    def forward(self, x: torch.Tensor, lengths: torch.Tensor | None = None) -> torch.Tensor:
        if lengths is None:
            lengths = torch.full((x.shape[0],), x.shape[1], dtype=torch.int64, device=x.device)
        validate_batch_input(x, n_features=self.n_features, lengths=lengths)
        enhanced = self.enhancer(x, lengths)
        pooled = masked_mean_pool(enhanced, lengths)
        return self.head(self.dropout(pooled))
