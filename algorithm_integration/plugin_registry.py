"""Local, manifest based algorithm extension point for the offline platform.

Only code installed by the local administrator under integrations/algorithm_plugins
is loaded. API callers choose a registered key and supply dataset IDs; they cannot
submit a Python path or source code for execution.
"""
from __future__ import annotations

import importlib.util
import json
import re
import math
from pathlib import Path

from django.conf import settings


PLUGIN_ROOT = settings.BASE_DIR / "integrations" / "algorithm_plugins"
KEY_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
TYPES = {"number", "integer", "boolean", "string"}
CATEGORIES = {"diagnosis", "health_assessment", "rul"}
BUILTINS = {
    "hier14": {"name": "Hier14 层次时序诊断", "category": "diagnosis"},
    "msfg_teams_rt": {"name": "MSFG + TEAMS-RT 依赖诊断", "category": "diagnosis"},
    "pca_iforest": {"name": "PCA-iForest 偏离诊断", "category": "diagnosis"},
    "health_main_ensemble": {"name": "多模型集成", "category": "rul", "parameters": {"component_id": {"type": "string", "default": "14"}, "threshold": {"type": "number", "default": 0.2, "minimum": 0, "maximum": 1}}},
    "hi_linear": {"name": "线性 HI 趋势外推", "category": "rul", "parameters": {"horizon": {"type": "integer", "default": 100, "minimum": 1, "maximum": 10000}, "threshold": {"type": "number", "default": 0.2, "minimum": 0, "maximum": 1}}},
    "cdpca_ga": {"name": "CDPCA-GA 健康评估", "category": "health_assessment"},
    "ae_gmm": {"name": "AE-GMM 健康评估", "category": "health_assessment"},
    "gcn_rbd": {"name": "GCN + RBD 系统健康评估", "category": "health_assessment"},
}


def _validate_manifest(folder: Path, data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("manifest.json 必须是对象")
    key = data.get("key")
    if not isinstance(key, str) or not KEY_RE.fullmatch(key) or key != folder.name or key in BUILTINS:
        raise ValueError("算法 key 必须与目录名一致，且不能覆盖内置算法")
    if data.get("category") not in CATEGORIES:
        raise ValueError("category 必须是 diagnosis、health_assessment 或 rul")
    entrypoint = data.get("entrypoint", "algorithm.py:predict")
    if not isinstance(entrypoint, str) or not re.fullmatch(r"[a-zA-Z_]\w*\.py:[a-zA-Z_]\w*", entrypoint):
        raise ValueError("entrypoint 格式应为 module.py:function")
    module_name, function_name = entrypoint.split(":", 1)
    module = (folder / module_name).resolve()
    if not module.is_file() or module.parent != folder.resolve():
        raise ValueError("入口模块必须是算法目录内的 Python 文件")
    parameters = data.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("parameters 必须是对象")
    for name, definition in parameters.items():
        if not isinstance(name, str) or not KEY_RE.fullmatch(name):
            raise ValueError(f"参数名无效: {name}")
        if not isinstance(definition, dict) or definition.get("type") not in TYPES:
            raise ValueError(f"参数 {name} 缺少有效 type")
        kind = definition["type"]
        if "default" in definition:
            default = definition["default"]
            type_ok = (type(default) is bool if kind == "boolean" else type(default) is int if kind == "integer" else type(default) in (int, float) if kind == "number" else isinstance(default, str))
            if not type_ok:
                raise ValueError(f"参数 {name} 的 default 类型与 type 不符")
        for bound in ("minimum", "maximum"):
            if bound in definition and (kind not in {"number", "integer"} or type(definition[bound]) not in (int, float)):
                raise ValueError(f"参数 {name} 的 {bound} 无效")
            if bound in definition and not math.isfinite(definition[bound]):
                raise ValueError(f"参数 {name} 的 {bound} 必须是有限数值")
        if "minimum" in definition and "maximum" in definition and definition["minimum"] > definition["maximum"]:
            raise ValueError(f"参数 {name} 的范围无效")
        if "enum" in definition and (not isinstance(definition["enum"], list) or not definition["enum"]):
            raise ValueError(f"参数 {name} 的 enum 必须是非空数组")
    # Validate declared defaults without requiring values supplied at runtime.
    for name, definition in parameters.items():
        if "default" in definition:
            validate_parameters({name: {**definition, "required": False}}, {})
    minimum = data.get("min_rows", 1)
    if not isinstance(minimum, int) or not 1 <= minimum <= 1000000:
        raise ValueError("min_rows 必须为 1 到 1000000 的整数")
    return {
        "key": key,
        "name": str(data.get("name") or key),
        "version": str(data.get("version") or "1.0"),
        "category": data["category"],
        "description": str(data.get("description") or ""),
        "input_format": "csv",
        "min_rows": minimum,
        "parameters": parameters,
        "entrypoint": entrypoint,
        "source": "plugin",
        "folder": folder,
        "module": module,
        "function": function_name,
    }


def discover() -> tuple[list[dict], list[dict]]:
    algorithms = []
    errors = []
    if not PLUGIN_ROOT.is_dir():
        return algorithms, errors
    for folder in sorted(PLUGIN_ROOT.iterdir()):
        if not folder.is_dir() or folder.is_symlink() or folder.name.startswith("_"):
            continue
        manifest = folder / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8-sig"))
            algorithms.append(_validate_manifest(folder, data))
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            errors.append({"folder": folder.name, "error": str(exc)})
    return algorithms, errors


def public_record(record: dict) -> dict:
    return {key: value for key, value in record.items() if key not in {"folder", "module", "function"}}


def list_algorithms(category: str | None = None) -> tuple[list[dict], list[dict]]:
    plugins, errors = discover()
    builtins = [dict(key=key, source="builtin", version="1.1", input_format="csv", **{"parameters": {}, **value}) for key, value in BUILTINS.items()]
    records = builtins + [public_record(plugin) for plugin in plugins]
    return [item for item in records if category is None or item["category"] == category], errors


def get_algorithm(key: str) -> dict:
    if key in BUILTINS:
        return dict(key=key, source="builtin", version="1.1", input_format="csv", **{"parameters": {}, **BUILTINS[key]})
    plugins, _ = discover()
    for plugin in plugins:
        if plugin["key"] == key:
            return plugin
    raise ValueError(f"算法 {key!r} 未注册或清单无效")


def validate_parameters(schema: dict, supplied: object) -> dict:
    if not isinstance(supplied, dict):
        raise ValueError("parameters 必须是对象")
    unknown = set(supplied) - set(schema)
    if unknown:
        raise ValueError(f"未知参数: {', '.join(sorted(unknown))}")
    values = {}
    for name, definition in schema.items():
        value = supplied.get(name, definition.get("default"))
        if value is None:
            if definition.get("required"):
                raise ValueError(f"缺少必填参数: {name}")
            continue
        kind = definition["type"]
        if kind == "boolean":
            valid = type(value) is bool
        elif kind == "integer":
            valid = type(value) is int
        elif kind == "number":
            valid = type(value) in (int, float)
        else:
            valid = isinstance(value, str)
        if not valid:
            raise ValueError(f"参数 {name} 类型应为 {kind}")
        if kind in {"number", "integer"}:
            if not math.isfinite(value):
                raise ValueError(f"参数 {name} 必须是有限数值")
            if "minimum" in definition and value < definition["minimum"]:
                raise ValueError(f"参数 {name} 低于最小值 {definition['minimum']}")
            if "maximum" in definition and value > definition["maximum"]:
                raise ValueError(f"参数 {name} 超过最大值 {definition['maximum']}")
        if "enum" in definition and value not in definition["enum"]:
            raise ValueError(f"参数 {name} 不在允许值中")
        values[name] = value
    return values


def run_plugin(record: dict, csv_path: str | Path, parameters: object = None) -> dict:
    params = validate_parameters(record["parameters"], parameters or {})
    from datasets.batch_processing import inspect_file
    quality = inspect_file(csv_path)
    if quality["format"] != "csv":
        raise ValueError("当前算法插件只接受 CSV 数据集")
    if quality["row_count"] < record["min_rows"]:
        raise ValueError(f"样本不足: 至少需要 {record['min_rows']} 行")
    spec = importlib.util.spec_from_file_location(f"phm_plugin_{record['key']}", record["module"])
    if spec is None or spec.loader is None:
        raise ValueError("无法加载插件入口模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    function = getattr(module, record["function"], None)
    if not callable(function):
        raise ValueError(f"入口函数 {record['function']} 不存在")
    result = function(str(csv_path), params)
    if not isinstance(result, dict):
        raise ValueError("插件必须返回 JSON 对象")
    if record["category"] == "diagnosis" and not (result.get("pred_name") or result.get("aggregate_pred_name")):
        raise ValueError("诊断插件必须返回 pred_name 或 aggregate_pred_name")
    if record["category"] == "rul" and ("rul_value" not in result or "unit" not in result):
        raise ValueError("寿命预测插件必须返回 rul_value 和 unit")
    if record["category"] == "health_assessment" and "health_index" not in result:
        raise ValueError("健康评估插件必须返回 health_index")
    # Check serializability before constructing an HTTP response.
    json.dumps(result, allow_nan=False)
    result.setdefault("algorithm", record["name"])
    result.setdefault("model_mode", f"plugin:{record['key']}@{record['version']}")
    json.dumps(result, allow_nan=False)
    return result
