"""Bridge to the customer's simulate_core.py and rocket_sim.slx."""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
from pathlib import Path

from django.conf import settings
from django.db import transaction
from datasets.models import Dataset


def _load_core():
    source = settings.BASE_DIR / "integrations" / "algorithm_assets" / "simulation" / "simulate_core.py"
    spec = importlib.util.spec_from_file_location("customer_simulate_core", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载仿真核心: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fault_catalog():
    core = _load_core()
    return {"动力": core.POWER_FAULTS, "控制": core.CONTROL_FAULTS}


def validate_parameters(body):
    if not isinstance(body, dict):
        raise ValueError("参数必须是 JSON 对象")
    backend = body.get("simulation_backend", "project_archive" if body.get("mode", "offline") == "offline" else "simulink")
    if backend == "project_archive":
        from .project_archive import validate_parameters as validate_archive
        return validate_archive(body)
    if backend != "simulink":
        raise ValueError("新任务仅支持一院 Simulink 仿真")
    if "severity" in body:
        raise ValueError("一院仿真程序不支持严重度参数")
    subsystem = body.get("subsystem", "动力")
    fault = body.get("fault_mode", "泵气蚀")
    catalog = fault_catalog()
    if subsystem not in catalog or fault not in catalog[subsystem]:
        raise ValueError("故障类型与一院模型的子系统映射不匹配")
    start = float(body.get("injection_time", 40))
    end = float(body.get("end_time", 480))
    if not all(math.isfinite(t) for t in (start, end)) or not 0 <= start < end <= 480:
        raise ValueError("时间必须满足 0 <= 注入时刻 < 恢复时刻 <= 480 秒")
    flight = body.get("flight_count", 0)
    numeric_flight = float(flight)
    if isinstance(flight, bool) or not math.isfinite(numeric_flight) or not numeric_flight.is_integer() or not 0 <= numeric_flight <= 20:
        raise ValueError("飞行次数必须为 0 到 20 的整数")
    mode = body.get("mode", "offline")
    if mode not in ("offline", "realtime"):
        raise ValueError("任务模式仅支持 offline 或 realtime")
    name = body.get("name") or f"{subsystem}-{fault}"
    if not isinstance(name, str) or len(name) > 200:
        raise ValueError("任务名称最多 200 个字符")
    return {"name": name, "mode": mode, "subsystem": subsystem, "fault_mode": fault,
            "injection_time": start, "end_time": end, "flight_count": int(numeric_flight),
            "simulation_backend": "simulink"}


def model_path():
    path = Path(os.environ.get("SIMULINK_MODEL_PATH") or
                settings.BASE_DIR / "integrations" / "algorithm_assets" / "simulation" / "rocket_sim.slx")
    if not path.is_file() or path.stem != "rocket_sim":
        raise RuntimeError(f"找不到名为 rocket_sim.slx 的模型: {path}")
    return path.resolve()


def runtime_status():
    from .matlab_runtime import engine_status
    detected = engine_status()
    problems = detected.pop('problems')
    try:
        model = str(model_path())
        model_exists = True
    except RuntimeError as exc:
        model, model_exists = "", False
        problems.append(str(exc))
    return {"backend": "simulink", "available": not problems and model_exists,
            **detected, "model": model, "model_exists": model_exists,
            "model_release": "R2023a", "duration": 480, "allow_newer_model": allow_newer_model(),
            "compatibility_warning": None,
            "error": "; ".join(problems) or None}


def allow_newer_model():
    override = os.environ.get("SIMULINK_ALLOW_NEWER_MODEL")
    if override is not None:
        return override.lower() in ("true", "1", "yes")
    return False


def output_dir(task):
    return Path(settings.MEDIA_ROOT) / "simulink_runs" / str(task.id)


def _validate_export(path, header, parameters):
    count, fault_count, first_time, last_time = 0, 0, None, None
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != header:
            raise ValueError(f"仿真 CSV 列不符合约定: {path.name}")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"仿真 CSV 行列数不一致: {path.name}")
            values = [float(row[key]) for key in header]
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"仿真 CSV 含非有限数值: {path.name}")
            timestamp, flag = float(row["Time"]), float(row["FaultFlag"])
            if last_time is not None and timestamp < last_time:
                raise ValueError("仿真 CSV 时间轴倒序")
            expected = int((parameters["power_fault"] != "无故障" or parameters["control_fault"] != "无故障")
                           and parameters["start_time"] <= timestamp <= parameters["end_time"])
            if flag != expected:
                raise ValueError("FaultFlag 与仿真核心的注入区间不一致")
            first_time = timestamp if first_time is None else first_time
            last_time = timestamp
            count += 1
            fault_count += int(flag)
    if not count:
        raise ValueError("仿真 CSV 为空")
    # Keep a bounded preview including label transitions; full data stays in the CSV.
    preview, previous = [], None
    stride = max(1, math.ceil(count / 800))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for index, row in enumerate(csv.DictReader(stream)):
            sample = {key: float(row[key]) for key in header}
            sample["FaultFlag"] = int(sample["FaultFlag"])
            transition = previous is not None and sample["FaultFlag"] != previous["FaultFlag"]
            if transition and (not preview or preview[-1] != previous):
                preview.append(previous)
            if index % stride == 0 or index == count - 1 or transition:
                preview.append(sample)
            previous = sample
    return {"row_count": count, "fault_row_count": fault_count, "time_range": [first_time, last_time],
            "time_column": "Time", "fault_flag_column": "FaultFlag",
            "parameter_columns": header[1:-1], "preview": preview}


def run_task(task, on_stage=None):
    params = validate_parameters({"subsystem": task.subsystem, "fault_mode": task.fault_mode,
                                  "simulation_backend": "simulink",
                                  "injection_time": task.injection_time, "end_time": task.end_time,
                                  "flight_count": task.flight_count, "mode": task.mode})
    parameters = {"power_fault": params["fault_mode"] if params["subsystem"] == "动力" else "无故障",
                  "control_fault": params["fault_mode"] if params["subsystem"] == "控制" else "无故障",
                  "flight_count": params["flight_count"], "start_time": params["injection_time"],
                  "end_time": params["end_time"]}
    directory = output_dir(task)
    directory.mkdir(parents=True, exist_ok=True)
    core = _load_core()
    scope_csv, p_csv, _ = core.run_simulation(
        str(model_path()), str(directory / "scope_data.csv"), **parameters,
        write_p_values=True, close_engine=True, on_stage=on_stage,
        allow_newer_model=allow_newer_model(),
    )
    if not p_csv:
        raise ValueError("仿真未生成 P_values.csv")
    exports = []
    for filename, component, header in ((scope_csv, "原始状态量", core.SCOPE_CSV_HEADER),
                                        (p_csv, "派生参数", core.P_CSV_HEADER)):
        path = Path(filename).resolve()
        if path.parent != directory.resolve():
            raise ValueError("仿真输出不在任务目录内")
        exports.append((path, component, _validate_export(path, header, parameters)))
    if any(item[2]["row_count"] != exports[0][2]["row_count"] or
           [row["Time"] for row in item[2]["preview"]] != [row["Time"] for row in exports[0][2]["preview"]]
           for item in exports[1:]):
        raise ValueError("原始 CSV 与派生 CSV 的采样不一致")
    if on_stage:
        on_stage("registering")
    created = []
    with transaction.atomic():
        for path, component, report in exports:
            # Export is already in MEDIA_ROOT; register without duplicating the file.
            dataset = Dataset.objects.create(
                name=(task.name if component == "原始状态量" else f"{task.name}-{component}")[:200], file=path.relative_to(Path(settings.MEDIA_ROOT).resolve()).as_posix(),
                source="simulation", fault_type=params["fault_mode"], injection_time=params["injection_time"],
                degradation=None, launch_number=params["flight_count"], system=params["subsystem"], component=component,
            )
            created.append({"dataset_id": dataset.id, "path": dataset.file.name,
                            "url": dataset.file.url, "component": component, **report})
        result = {"backend": "simulink", "source": "一院项目/simulate/simulate_core.py",
                  "model": "rocket_sim.slx", "duration": 480, "parameters": parameters, "datasets": created,
                  "allow_newer_model": allow_newer_model()}
        result["matlab_release"] = configured_release = runtime_status().get("matlab_release")
        if configured_release:
            result["model_release"] = "R2023a"
        task.simulation_output = result
        task.dataset_id = created[0]["dataset_id"]
        task.latest_result = {"datasets": [item["dataset_id"] for item in created]}
        task.status = "completed"
        task.current_stage = "completed"
        task.save(update_fields=["simulation_output", "dataset_id", "latest_result", "status", "current_stage", "updated_at"])
    return result
