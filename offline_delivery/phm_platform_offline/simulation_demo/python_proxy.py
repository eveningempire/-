"""MATLAB-free deterministic fault-data generator.

This backend starts from the packaged normal baseline and applies documented
synthetic disturbances.  It is intended for UI, pipeline and algorithm tests;
it is deliberately labelled as proxy data and is not a replacement for the
Simulink model.
"""
from __future__ import annotations

import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings
from django.db import transaction

from datasets.models import Dataset
from simulation_dataset import services
from .simulink import output_dir


FAULT_GROUPS = {
    "泵气蚀": ("power", ("FT", "S1", "S2", "P1", "P2")),
    "涡轮转速下降": ("power", ("S3", "S4", "P3", "P4")),
    "管路堵塞": ("power", ("S5", "S6", "P5", "P6")),
    "主阀门卡滞": ("power", ("S7", "S8", "P7", "P8")),
    "燃气泄漏": ("power", ("S9", "S10_X", "S10_Y", "S10_Z", "P9", "P10")),
    "燃烧不稳定": ("power", ("FT", "S11", "P11", "P12")),
    "喷管堵塞": ("power", ("S12", "S13", "P13", "P14")),
    "TVC偏角不足": ("control", ("Pitch", "S14", "P15")),
    "RCS推力不足": ("control", ("Roll", "Yaw", "S15", "P16")),
    "栅格舵偏角不足": ("control", ("Roll", "Pitch", "S16", "P17")),
    "控制器无信号": ("control", ("S17", "P15", "P16")),
    "陀螺仪恒偏差": ("control", ("Roll", "Pitch", "Yaw")),
    "陀螺仪卡死": ("control", ("Roll", "Pitch", "Yaw", "S17")),
}


def proxy_status():
    try:
        path = services.ARCHIVE
        with zipfile.ZipFile(path) as archive:
            baseline = next((name for name in archive.namelist()
                             if name.endswith("/baseline/fc0.csv")), None)
        if not baseline:
            raise ValueError("仿真数据包中缺少正常基线 fc0.csv")
        return {"backend": "python_proxy", "available": True,
                "baseline": baseline, "source": "正常基线 CSV + Python 代理扰动",
                "error": None}
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        return {"backend": "python_proxy", "available": False, "baseline": None,
                "source": "正常基线 CSV + Python 代理扰动", "error": str(exc)}


def _baseline_members():
    with zipfile.ZipFile(services.ARCHIVE) as archive:
        names = set(archive.namelist())
        scope = next((name for name in sorted(names) if name.endswith("/baseline/fc0.csv")), None)
        if not scope:
            raise ValueError("仿真数据包中缺少正常基线 fc0.csv")
        paired = str(Path(scope).with_name(Path(scope).stem + "_P.csv")).replace("\\", "/")
        if paired not in names:
            raise ValueError("正常基线缺少 P_values 配对文件")
        return scope, paired


def _read_member(archive, member):
    with archive.open(member) as stream:
        return pd.read_csv(stream, encoding="utf-8-sig")


def _validate_frame(frame, label):
    if frame.empty or "Time" not in frame:
        raise ValueError(f"正常基线 {label} 缺少 Time 列或没有数据")
    if "FaultFlag" in frame:
        frame = frame.drop(columns=["FaultFlag"])
    frame = frame.apply(pd.to_numeric, errors="raise")
    if not np.isfinite(frame.to_numpy(dtype=float)).all() or np.any(np.diff(frame["Time"].to_numpy()) < 0):
        raise ValueError(f"正常基线 {label} 含无效数值或倒序时间")
    return frame


def _apply_fault(scope, params, fault_mode, start, end, severity):
    for key in scope.columns:
        if key != "Time":
            scope[key] = scope[key].astype(float)
    active = (scope["Time"] >= start) & (scope["Time"] <= end)
    if fault_mode == "无故障" or not active.any():
        return active
    _, columns = FAULT_GROUPS.get(fault_mode, ("generic", ()))
    numeric = [key for key in scope.columns if key not in ("Time", "FaultFlag")]
    selected = [key for key in columns if key in scope.columns]
    if not selected:
        selected = numeric[: min(4, len(numeric))]
    severity = min(1.0, max(0.05, float(severity)))
    time = scope.loc[active, "Time"].to_numpy(dtype=float)
    phase = (time - start) / max(end - start, 1e-9)
    # A smooth deterministic envelope avoids discontinuous spikes at boundaries.
    envelope = np.sin(np.pi * np.clip(phase, 0.0, 1.0)) ** 0.7
    for index, key in enumerate(selected):
        values = scope.loc[active, key].to_numpy(dtype=float)
        scale = max(float(np.nanstd(scope[key].to_numpy(dtype=float))),
                    float(np.nanmedian(np.abs(scope[key].to_numpy(dtype=float)))) * 0.05,
                    1e-6)
        direction = -1.0 if index % 2 else 1.0
        scope.loc[active, key] = values + direction * scale * (0.8 + 1.6 * severity) * envelope
    return active


def _report(frame):
    frame = frame.copy()
    if "FaultFlag" not in frame:
        raise ValueError("代理输出缺少 FaultFlag")
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("代理输出含非有限数值")
    stride = max(1, math.ceil(len(frame) / 800))
    transitions = np.flatnonzero(np.diff(frame.FaultFlag.to_numpy()))
    indices = sorted(set(range(0, len(frame), stride)) | {len(frame) - 1} |
                     set(transitions) | set(transitions + 1))
    flagged = frame.loc[frame.FaultFlag == 1, "Time"]
    return {"row_count": len(frame), "fault_row_count": int(len(flagged)),
            "time_range": [float(frame.Time.iloc[0]), float(frame.Time.iloc[-1])],
            "recorded_fault_range": [float(flagged.iloc[0]), float(flagged.iloc[-1])] if len(flagged) else None,
            "time_column": "Time", "fault_flag_column": "FaultFlag",
            "parameter_columns": [key for key in frame.columns if key not in ("Time", "FaultFlag")],
            "preview": frame.iloc[indices].to_dict(orient="records")}


def validate_parameters(body):
    if body.get("mode", "offline") != "offline":
        raise ValueError("Python 代理数据生成仅用于离线模式")
    if body.get("simulation_backend", "python_proxy") != "python_proxy":
        raise ValueError("离线代理任务必须使用 python_proxy 后端")
    subsystem = body.get("subsystem", "动力")
    fault = body.get("fault_mode", "泵气蚀")
    from .simulink import fault_catalog
    catalog = fault_catalog()
    if subsystem not in catalog or fault not in catalog[subsystem]:
        raise ValueError("故障类型与子系统映射不匹配")
    start, end = float(body.get("injection_time", 40)), float(body.get("end_time", 480))
    if not all(math.isfinite(t) for t in (start, end)) or not 0 <= start < end <= 480:
        raise ValueError("时间必须满足 0 <= 注入时刻 < 恢复时刻 <= 480 秒")
    flight = float(body.get("flight_count", 0))
    if not math.isfinite(flight) or not flight.is_integer() or not 0 <= flight <= 20:
        raise ValueError("飞行次数必须为 0 到 20 的整数")
    severity = float(body.get("severity", 0.5))
    if not math.isfinite(severity) or not 0 < severity <= 1:
        raise ValueError("代理故障强度必须在 0 到 1 之间")
    name = body.get("name") or f"Python代理-{subsystem}-{fault}"
    if not isinstance(name, str) or len(name) > 200:
        raise ValueError("任务名称最多 200 个字符")
    return {"name": name, "mode": "offline", "simulation_backend": "python_proxy",
            "subsystem": subsystem, "fault_mode": fault, "injection_time": start,
            "end_time": end, "flight_count": int(flight), "severity": severity}


def run_task(task, on_stage=None):
    if on_stage:
        on_stage("preparing")
    directory = output_dir(task)
    directory.mkdir(parents=True, exist_ok=True)
    scope_member, p_member = _baseline_members()
    with zipfile.ZipFile(services.ARCHIVE) as archive:
        scope = _validate_frame(_read_member(archive, scope_member), "scope_data.csv")
        derived = _validate_frame(_read_member(archive, p_member), "P_values.csv")
    if len(scope) != len(derived) or not np.array_equal(scope.Time.to_numpy(), derived.Time.to_numpy()):
        raise ValueError("正常基线原始/派生文件的时间轴不一致")
    if on_stage:
        on_stage("generating")
    active = _apply_fault(scope, task, task.fault_mode, task.injection_time, task.end_time, task.severity)
    _apply_fault(derived, task, task.fault_mode, task.injection_time, task.end_time, task.severity)
    scope["FaultFlag"] = active.astype(int)
    derived["FaultFlag"] = active.astype(int)
    scope_path, p_path = directory / "scope_data.csv", directory / "P_values.csv"
    scope.to_csv(scope_path, index=False, encoding="utf-8-sig")
    derived.to_csv(p_path, index=False, encoding="utf-8-sig")
    if on_stage:
        on_stage("registering")
    reports = [(scope_path, "原始状态量", _report(scope)), (p_path, "派生参数", _report(derived))]
    with transaction.atomic():
        created = []
        for path, component, report in reports:
            dataset = Dataset.objects.create(
                name=(task.name if component == "原始状态量" else f"{task.name}-{component}")[:200],
                file=path.relative_to(Path(settings.MEDIA_ROOT).resolve()).as_posix(), source="simulation",
                fault_type=task.fault_mode, injection_time=task.injection_time,
                launch_number=task.flight_count, system=task.subsystem, component=component)
            created.append({"dataset_id": dataset.pk, "path": dataset.file.name,
                            "url": dataset.file.url, "component": component, **report})
        result = {"backend": "python_proxy", "source": "正常基线 CSV + Python 代理扰动",
                  "model": "python_fault_proxy", "duration": 480, "datasets": created,
                  "parameters": {"fault_mode": task.fault_mode, "severity": task.severity,
                                  "start_time": task.injection_time, "end_time": task.end_time,
                                  "flight_count": task.flight_count},
                  "note": "这是用于演示、算法联调和测试的代理数据，不代表 Simulink 数值结果。"}
        task.dataset_id, task.simulation_output = created[0]["dataset_id"], result
        task.latest_result = {"datasets": [item["dataset_id"] for item in created]}
        task.status = task.current_stage = "completed"
        task.save(update_fields=["dataset_id", "simulation_output", "latest_result", "status", "current_stage", "updated_at"])
    return result
