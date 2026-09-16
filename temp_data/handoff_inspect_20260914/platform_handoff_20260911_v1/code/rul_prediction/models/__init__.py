"""Model package: shared conventions and the ``build_model`` factory."""

from __future__ import annotations

from typing import Any, Mapping

import torch.nn as nn

from .bilstm import BiLSTMRegressor
from .common import count_trainable_parameters
from .kan import KANLayer, KANRegressor
from .kan_bilstm import KANBiLSTM, MLPBiLSTM
from .lstm import LSTMRegressor
from .student_cnn import CNNFeatureExtractor, StudentCNNRegressor
from .tcn import TCNBackbone, TCNRegressor
from .tcn_lstm_transformer import (
    ChannelAttentionFusion,
    LSTMLocalBranch,
    TeacherTCNLSTMTransformer,
    TransformerGlobalBranch,
)
from .transformer import TransformerBackbone, TransformerRegressor
from .transformer_bilstm import TransformerBiLSTM
from .transformer_kan_bilstm import TransformerKANBiLSTM

SINGLE_TASK_TYPES = frozenset(
    {
        "lstm",
        "bilstm",
        "transformer",
        "kan",
        "tcn",
        "transformer_bilstm",
        "kan_bilstm",
        "mlp_bilstm",
        "transformer_kan_bilstm",
        "transformer_mlp_bilstm",
        "cnn_student",
    }
)
MULTITASK_TYPES = frozenset({"tcn_lstm_transformer_teacher"})

_MODEL_TYPES = SINGLE_TASK_TYPES | MULTITASK_TYPES


def build_model(
    model_config: Mapping[str, Any],
    *,
    n_features: int,
    n_components: int,
) -> nn.Module:
    """Construct a model from its config section; unknown keys are ignored."""

    config = dict(model_config)
    model_type = str(config.get("type", "")).strip()
    if model_type not in _MODEL_TYPES:
        raise ValueError(
            f"unknown model type {model_type!r}; expected one of {sorted(_MODEL_TYPES)}"
        )
    dropout = float(config.get("dropout", 0.1))

    if model_type == "lstm":
        return LSTMRegressor(
            n_features=n_features,
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config.get("num_layers", 1)),
            dropout=dropout,
        )
    if model_type == "bilstm":
        return BiLSTMRegressor(
            n_features=n_features,
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config.get("num_layers", 1)),
            dropout=dropout,
        )
    if model_type == "transformer":
        return TransformerRegressor(
            n_features=n_features,
            d_model=int(config["d_model"]),
            nhead=int(config["nhead"]),
            num_layers=int(config.get("transformer_layers", config.get("num_layers", 1))),
            dropout=dropout,
        )
    if model_type == "kan":
        return KANRegressor(
            n_features=n_features,
            hidden_size=int(config["hidden_size"]),
            grid_size=int(config.get("grid_size", 5)),
            spline_order=int(config.get("spline_order", 3)),
            dropout=dropout,
        )
    if model_type == "tcn":
        return TCNRegressor(
            n_features=n_features,
            channels=int(config["channels"]),
            kernel_size=int(config.get("kernel_size", 3)),
            dropout=dropout,
        )
    if model_type == "transformer_bilstm":
        return TransformerBiLSTM(
            n_features=n_features,
            d_model=int(config["d_model"]),
            nhead=int(config["nhead"]),
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config.get("num_layers", 1)),
            transformer_layers=int(config.get("transformer_layers", 1)),
            dropout=dropout,
        )
    if model_type == "kan_bilstm":
        return KANBiLSTM(
            n_features=n_features,
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config.get("num_layers", 1)),
            grid_size=int(config.get("grid_size", 5)),
            spline_order=int(config.get("spline_order", 3)),
            dropout=dropout,
        )
    if model_type == "mlp_bilstm":
        return MLPBiLSTM(
            n_features=n_features,
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config.get("num_layers", 1)),
            dropout=dropout,
        )
    if model_type in {"transformer_kan_bilstm", "transformer_mlp_bilstm"}:
        return TransformerKANBiLSTM(
            n_features=n_features,
            d_model=int(config["d_model"]),
            nhead=int(config["nhead"]),
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config.get("num_layers", 1)),
            transformer_layers=int(config.get("transformer_layers", 1)),
            enhancer="mlp" if model_type.endswith("mlp_bilstm") else "kan",
            grid_size=int(config.get("grid_size", 5)),
            spline_order=int(config.get("spline_order", 3)),
            dropout=dropout,
        )
    if model_type == "tcn_lstm_transformer_teacher":
        return TeacherTCNLSTMTransformer(
            n_features=n_features,
            n_components=n_components,
            channels=int(config.get("channels", 32)),
            kernel_size=int(config.get("kernel_size", 3)),
            hidden_size=int(config.get("hidden_size", 32)),
            d_model=int(config["d_model"]),
            nhead=int(config["nhead"]),
            transformer_layers=int(config.get("transformer_layers", 3)),
            dropout=dropout,
        )
    if model_type == "cnn_student":
        return StudentCNNRegressor(
            n_features=n_features,
            channels=int(config.get("channels", 32)),
            kernel_size=int(config.get("kernel_size", 5)),
            num_blocks=int(config.get("num_blocks", 3)),
            dropout=dropout,
        )
    raise AssertionError("unreachable model type")


__all__ = [
    "MULTITASK_TYPES",
    "SINGLE_TASK_TYPES",
    "BiLSTMRegressor",
    "CNNFeatureExtractor",
    "ChannelAttentionFusion",
    "KANBiLSTM",
    "KANLayer",
    "KANRegressor",
    "LSTMLocalBranch",
    "LSTMRegressor",
    "MLPBiLSTM",
    "StudentCNNRegressor",
    "TCNBackbone",
    "TCNRegressor",
    "TeacherTCNLSTMTransformer",
    "TransformerBackbone",
    "TransformerBiLSTM",
    "TransformerGlobalBranch",
    "TransformerKANBiLSTM",
    "TransformerRegressor",
    "build_model",
    "count_trainable_parameters",
]
