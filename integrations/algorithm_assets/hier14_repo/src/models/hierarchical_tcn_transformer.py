"""层次化 TCN-Transformer：共享 backbone + coarse / prop / gnc 三头。"""

from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn

from ..fault_hier13_labels import fault_hier13_logits_to_flat
from ..hierarchical_labels import hierarchical_logits_to_flat
from .tcn_transformer import TCNTransformerDiagnosis


class HierarchicalTCNTransformer(TCNTransformerDiagnosis):
    def __init__(self, config):
        super().__init__(config)
        feat_dim = int(config.input_dim)
        dropout = float(config.dropout)

        self.coarse_head = nn.Sequential(
            nn.Linear(feat_dim, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(64, int(getattr(config, "coarse_num_classes", 3))),
        )
        self.prop_fine_head = nn.Sequential(
            nn.Linear(feat_dim, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(64, int(getattr(config, "prop_fine_num_classes", 7))),
        )
        self.gnc_fine_head = nn.Sequential(
            nn.Linear(feat_dim, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(64, int(getattr(config, "gnc_fine_num_classes", 6))),
        )
        del self.fcn

    def encode_last_pred(self, src, tgt=None, return_diagnosis_attn=False):
        x = self.input_norm(self.input_proj(src))
        x = self.tcn_norm(self.tcn(x))
        x = self.pos_encoder(x)

        if return_diagnosis_attn:
            enc_out, diag_attn_time = self.encoder(x, return_diagnosis_attn=True)
        else:
            enc_out = self.encoder(x)
            diag_attn_time = None

        if tgt is None:
            tgt_input = self.input_proj(src[:, -1:, :])
        else:
            tgt_input = self.input_proj(tgt)

        dec_out = self.decoder(tgt_input, enc_out)
        pred_features = self.output_proj(dec_out)
        last_pred = self.head_norm(pred_features[:, -1, :])
        if return_diagnosis_attn:
            return last_pred, diag_attn_time
        return last_pred, None

    def forward_heads(self, last_pred: torch.Tensor) -> Dict[str, torch.Tensor]:
        return {
            "coarse": self.coarse_head(last_pred),
            "prop": self.prop_fine_head(last_pred),
            "gnc": self.gnc_fine_head(last_pred),
        }

    def to_flat_logits(self, heads: Dict[str, torch.Tensor]) -> torch.Tensor:
        coarse_dim = self.coarse_head[-1].out_features
        if coarse_dim == 2:
            return fault_hier13_logits_to_flat(heads["coarse"], heads["prop"], heads["gnc"])
        return hierarchical_logits_to_flat(heads["coarse"], heads["prop"], heads["gnc"])

    def forward(self, src, tgt=None, return_diagnosis_attn=False):
        last_pred, diag_attn_time = self.encode_last_pred(
            src, tgt=tgt, return_diagnosis_attn=return_diagnosis_attn
        )
        heads = self.forward_heads(last_pred)
        if return_diagnosis_attn:
            return self.to_flat_logits(heads), diag_attn_time
        return heads


def build_model(config) -> nn.Module:
    if getattr(config, "use_gated_hier_head", False):
        from experiments.two_stage.a4.model import GatedHierTransformer
        return GatedHierTransformer(config)
    if getattr(config, "use_hierarchical_head", False):
        return HierarchicalTCNTransformer(config)
    return TCNTransformerDiagnosis(config)


def is_hierarchical_model(model: nn.Module) -> bool:
    from experiments.two_stage.a4.model import GatedHierTransformer
    return isinstance(model, (HierarchicalTCNTransformer, GatedHierTransformer))
