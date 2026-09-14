"""
YAML 配置加载：在 Config / ExpertConfig 类默认值之上叠加 YAML 覆盖项。

用法:
  from src.config_loader import load_config, load_ensemble_configs

  cfg = load_config("gnc")                      # profile -> configs/gnc.yaml
  cfg = load_config("configs/propulsion.yaml")  # 显式路径
  prop_cfg, gnc_cfg, opts = load_ensemble_configs("ensemble")
"""

from __future__ import annotations

import copy
import os
from typing import Any, Dict, Optional, Tuple, Type, Union

import yaml

from .config import Config

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CONFIGS_DIR = os.path.join(_PROJECT_ROOT, "configs")

_PATH_KEYS = frozenset({
    "simulate_data_dir",
    "processed_data_dir",
    "raw_data_path",
    "checkpoint_dir",
    "result_dir",
    "log_dir",
})

_TUPLE_KEYS = frozenset({
    "allowed_class_ids",
    "prefault_normal_slugs",
    "POWER_FAULT_CLASS_IDS",
    "CONTROL_FAULT_CLASS_IDS",
    "tcn_channels",
    "csv_ignore_patterns",
    "csv_ignore_subdirs",
    "hierarchical_loss_weights",
    "class_weight_multipliers_gnc_fine",
})

_PROFILE_BASE_CLASSES: Dict[str, Type[Config]] = {}
_DEFAULT_YAML_BY_PROFILE: Dict[str, str] = {
    "propulsion": "propulsion.yaml",
    "gnc": "gnc.yaml",
    "full14": "full14.yaml",
    "simulate": "full14.yaml",
    "hier14": "hier14.yaml",
    "fault_hier13": "experiments/two_stage/common/configs/fault_hier13.yaml",
    "two_stage_a1": "experiments/two_stage/a1/config.yaml",
    "two_stage_a2": "experiments/two_stage/a2/config.yaml",
    "two_stage_a3": "experiments/two_stage/a3/config.yaml",
    "two_stage_a4": "experiments/two_stage/a4/config.yaml",
    "ensemble": "ensemble.yaml",
}


def _register_profiles() -> None:
    if _PROFILE_BASE_CLASSES:
        return
    from .expert_config import (
        BinaryStage1Config,
        FaultHier13Config,
        GNCExpertConfig,
        GatedTwoStageConfig,
        Hier14Config,
        PropulsionExpertConfig,
        TwoStageDataConfig,
    )

    _PROFILE_BASE_CLASSES.update({
        "propulsion": PropulsionExpertConfig,
        "gnc": GNCExpertConfig,
        "hier14": Hier14Config,
        "fault_hier13": FaultHier13Config,
        "full14": Config,
        "simulate": Config,
        "two_stage_a1": TwoStageDataConfig,
        "two_stage_a2": TwoStageDataConfig,
        "two_stage_a3": BinaryStage1Config,
        "two_stage_a4": GatedTwoStageConfig,
    })


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(_PROJECT_ROOT, path)


def _resolve_config_file(name_or_path: str) -> str:
    if os.path.isfile(name_or_path):
        return os.path.abspath(name_or_path)

    project_candidate = os.path.join(_PROJECT_ROOT, name_or_path)
    if os.path.isfile(project_candidate):
        return project_candidate

    candidate = os.path.join(_CONFIGS_DIR, name_or_path)
    if os.path.isfile(candidate):
        return candidate

    if not name_or_path.endswith(".yaml"):
        candidate_yaml = candidate + ".yaml"
        if os.path.isfile(candidate_yaml):
            return candidate_yaml

    raise FileNotFoundError(f"Config not found: {name_or_path!r}")


def _load_yaml_file(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _merge_yaml(path: str, seen: Optional[set] = None) -> Dict[str, Any]:
    seen = seen or set()
    abs_path = os.path.abspath(path)
    if abs_path in seen:
        raise ValueError(f"Circular extends in config: {abs_path}")
    seen.add(abs_path)

    data = _load_yaml_file(abs_path)
    extends = data.pop("extends", None)
    if not extends:
        return copy.deepcopy(data)

    base_path = extends if os.path.isabs(extends) else os.path.join(os.path.dirname(abs_path), extends)
    merged = _merge_yaml(base_path, seen)
    for key, value in data.items():
        if key in ("profile", "description"):
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = copy.deepcopy(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _flatten_sections(data: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for key, value in data.items():
        if key in ("profile", "description", "extends"):
            continue
        if key in ("paths", "preprocessing", "training", "model", "routing", "ensemble") and isinstance(value, dict):
            flat.update(value)
        else:
            flat[key] = value
    return flat


def _normalize_overrides(overrides: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in overrides.items():
        if key in _PATH_KEYS and isinstance(value, str):
            normalized[key] = _resolve_path(value)
        elif key in _TUPLE_KEYS and isinstance(value, list):
            normalized[key] = tuple(value)
        else:
            normalized[key] = value
    return normalized


def _infer_base_class(overrides: Dict[str, Any]) -> Type[Config]:
    _register_profiles()
    profile = overrides.get("profile")
    if isinstance(profile, str) and profile in _PROFILE_BASE_CLASSES:
        return _PROFILE_BASE_CLASSES[profile]

    expert_name = overrides.get("expert_name")
    if expert_name == "propulsion":
        return _PROFILE_BASE_CLASSES["propulsion"]
    if expert_name == "gnc":
        return _PROFILE_BASE_CLASSES["gnc"]
    if expert_name == "hier14":
        return _PROFILE_BASE_CLASSES["hier14"]
    if expert_name == "fault_hier13":
        return _PROFILE_BASE_CLASSES["fault_hier13"]
    return Config


def _finalize_config_class(config_cls: Type[Config], overrides: Dict[str, Any]) -> Type[Config]:
    if "sample_dt" not in overrides:
        raw_dt = getattr(config_cls, "raw_dt", 0.031)
        row_interval = getattr(config_cls, "row_interval", 4)
        config_cls.sample_dt = raw_dt * row_interval

    if "input_dim" not in overrides:
        if hasattr(config_cls, "active_feature_columns"):
            config_cls.input_dim = len(config_cls.active_feature_columns)
        elif hasattr(config_cls, "feature_columns"):
            config_cls.input_dim = len(config_cls.feature_columns)

    if "num_classes" not in overrides and hasattr(config_cls, "CLASS_NAMES"):
        config_cls.num_classes = len(config_cls.CLASS_NAMES)

    return config_cls


def build_config_class(
    base_cls: Type[Config],
    overrides: Optional[Dict[str, Any]] = None,
) -> Type[Config]:
    overrides = _normalize_overrides(_flatten_sections(overrides or {}))
    class_name = f"{base_cls.__name__}FromYAML"
    config_cls = type(class_name, (base_cls,), {})
    for key, value in overrides.items():
        setattr(config_cls, key, value)
    return _finalize_config_class(config_cls, overrides)


def load_config(name_or_path: Optional[str] = None, base_cls: Optional[Type[Config]] = None) -> Type[Config]:
    """
    加载 YAML 并返回动态 Config 子类（类属性访问，与现有代码兼容）。

    name_or_path:
      - None / profile 名: gnc, propulsion, full14, simulate
      - 相对/绝对 YAML 路径
    """
    _register_profiles()

    if name_or_path is None:
        name_or_path = "full14"

    if name_or_path in _DEFAULT_YAML_BY_PROFILE and not os.path.sep in name_or_path:
        yaml_name = _DEFAULT_YAML_BY_PROFILE[name_or_path]
        yaml_path = _resolve_config_file(yaml_name)
        inferred_base = base_cls or _PROFILE_BASE_CLASSES.get(name_or_path, Config)
    else:
        yaml_path = _resolve_config_file(name_or_path)
        merged = _merge_yaml(yaml_path)
        inferred_base = base_cls or _infer_base_class(merged)

    merged = _merge_yaml(yaml_path)
    return build_config_class(inferred_base, merged)


def load_ensemble_configs(
    name_or_path: Optional[str] = None,
) -> Tuple[Type[Config], Type[Config], Dict[str, Any]]:
    """加载双专家 ensemble 配置，返回 (propulsion_cfg, gnc_cfg, routing_opts)。"""
    yaml_path = _resolve_config_file(name_or_path or "ensemble")
    merged = _merge_yaml(yaml_path)
    ensemble_block = merged.get("ensemble", {})
    if not isinstance(ensemble_block, dict):
        ensemble_block = {}

    prop_yaml = ensemble_block.get("propulsion_config", merged.get("propulsion_config", "configs/propulsion.yaml"))
    gnc_yaml = ensemble_block.get("gnc_config", merged.get("gnc_config", "configs/gnc.yaml"))

    prop_cfg = load_config(prop_yaml)
    gnc_cfg = load_config(gnc_yaml)

    routing = merged.get("routing", {})
    if not isinstance(routing, dict):
        routing = {}

    opts = {
        "anomaly_threshold": float(routing.get("anomaly_threshold", 0.5)),
        "result_dir": _resolve_path(routing.get("result_dir", merged.get("result_dir", "results/ensemble"))),
    }
    return prop_cfg, gnc_cfg, opts


def add_config_argument(parser, default: Optional[str] = None, help_suffix: str = "") -> None:
    help_text = (
        "YAML 配置文件或 profile 名 (propulsion|gnc|full14|hier14|fault_hier13|two_stage_a1|two_stage_a2|ensemble)"
    )
    if help_suffix:
        help_text = f"{help_text}; {help_suffix}"
    parser.add_argument("--config", "-c", type=str, default=default, help=help_text)


def config_from_args(args, default: Optional[str] = None) -> Type[Config]:
    return load_config(getattr(args, "config", None) or default)
