"""Import unchanged customer simulation pairs without a MATLAB runtime."""
from __future__ import annotations

import math
import shutil
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings
from django.db import transaction

from datasets.models import Dataset
from simulation_dataset import services
from .simulink import output_dir

FAULT_CATEGORIES = {
    "泵气蚀": "bengqixi", "涡轮转速下降": "wolun", "管路堵塞": "guanlu",
    "主阀门卡滞": "zhufa", "燃气泄漏": "ranqi", "燃烧不稳定": "ranshao",
    "喷管堵塞": "penguan", "TVC偏角不足": "tvc", "RCS推力不足": "rcs",
    "栅格舵偏角不足": "geduo", "控制器无信号": "kongzhiqi",
    "陀螺仪恒偏差": "tuoluoyi_piancha", "陀螺仪卡死": "tuoluoyi_kasi",
    "无故障": "baseline",
}
CONTROL_FAULTS = {"TVC偏角不足", "RCS推力不足", "栅格舵偏角不足", "控制器无信号", "陀螺仪恒偏差", "陀螺仪卡死"}


@lru_cache(maxsize=2)
def _selections(archive_name, mtime):
    result = []
    with zipfile.ZipFile(archive_name) as archive:
        members = set(archive.namelist())
        for member in sorted(members):
            parts = member.split("/")
            if len(parts) != 3 or parts[0] != "simulate_data_+1":
                continue
            match = services.NAME_RE.match(parts[2])
            if not match or match.group("processed"):
                continue
            fault = next((name for name, category in FAULT_CATEGORIES.items() if category == parts[1]), None)
            paired = str(Path(member).with_name(Path(member).stem + "_P.csv")).replace("\\", "/")
            if fault is None or paired not in members:
                continue
            for subsystem in (["动力", "控制"] if fault == "无故障" else ["控制" if fault in CONTROL_FAULTS else "动力"]):
                result.append({"subsystem": subsystem, "fault_mode": fault,
                               "flight_count": int(match.group("flight")),
                               "injection_time": int(match.group("time") or 0),
                               "end_time": 480, "member": member, "paired_member": paired})
    return result


def archive_status():
    try:
        path = services.ARCHIVE
        selections = _selections(str(path), path.stat().st_mtime_ns)
        return {"backend": "project_archive", "available": bool(selections), "selections": selections,
                "error": None if selections else "包内项目仿真数据没有可用的原始/派生文件对"}
    except (OSError, zipfile.BadZipFile) as exc:
        return {"backend": "project_archive", "available": False, "selections": [], "error": str(exc)}


def resolve(body):
    status = archive_status()
    if not status["available"]:
        raise ValueError(status["error"])
    try:
        flight = float(body.get("flight_count", 0))
        start = float(body.get("injection_time", 0 if body.get("fault_mode") == "无故障" else 30))
        end = float(body.get("end_time", 480))
    except (TypeError, ValueError):
        raise ValueError("请选择包内已有的飞行次数及故障记录时刻")
    if isinstance(body.get("flight_count"), bool) or not all(math.isfinite(x) for x in (flight, start, end)):
        raise ValueError("飞行次数和记录时刻必须为有效数值")
    choice = next((item for item in status["selections"] if
                   item["subsystem"] == body.get("subsystem", "动力") and
                   item["fault_mode"] == body.get("fault_mode", "泵气蚀") and
                   item["flight_count"] == flight and item["injection_time"] == start and item["end_time"] == end), None)
    if choice is None:
        raise ValueError("包内没有这组故障、飞行次数和时刻的数据；离线导入不能改变原始仿真注入/恢复时刻")
    return choice


def validate_parameters(body):
    if body.get("mode", "offline") != "offline":
        raise ValueError("实时故障注入需要 Simulink/MATLAB Engine；项目存量数据仅用于离线导入")
    if "severity" in body:
        raise ValueError("包内项目数据不支持调整严重度")
    choice = resolve(body)
    name = body.get("name") or f"项目数据-{choice['subsystem']}-{choice['fault_mode']}-fc{choice['flight_count']}"
    if not isinstance(name, str) or len(name) > 200:
        raise ValueError("任务名称最多 200 个字符")
    return {"name": name, "mode": "offline", "simulation_backend": "project_archive",
            **{key: choice[key] for key in ("subsystem", "fault_mode", "flight_count", "injection_time", "end_time")}}


def _report(path):
    frame = pd.read_csv(path, encoding="utf-8-sig")
    if frame.empty or "Time" not in frame or "FaultFlag" not in frame:
        raise ValueError("项目 CSV 缺少时间/故障标记或没有数据")
    numbers = frame.to_numpy(dtype=float)
    if not np.isfinite(numbers).all() or np.any(np.diff(frame.Time.to_numpy()) < 0):
        raise ValueError("项目 CSV 含无效数值或倒序时间")
    if not frame.FaultFlag.isin([0, 1]).all():
        raise ValueError("项目 CSV 故障标记必须为 0 或 1")
    stride = max(1, math.ceil(len(frame) / 800))
    transitions = np.flatnonzero(np.diff(frame.FaultFlag.to_numpy()))
    indices = sorted(set(range(0, len(frame), stride)) | {len(frame)-1} | set(transitions) | set(transitions+1))
    flagged = frame.loc[frame.FaultFlag == 1, "Time"]
    return {"row_count": len(frame), "fault_row_count": len(flagged),
            "time_range": [float(frame.Time.iloc[0]), float(frame.Time.iloc[-1])],
            "recorded_fault_range": [float(flagged.iloc[0]), float(flagged.iloc[-1])] if len(flagged) else None,
            "time_column": "Time", "fault_flag_column": "FaultFlag",
            "parameter_columns": [key for key in frame.columns if key not in ("Time", "FaultFlag")],
            "preview": frame.iloc[indices].to_dict(orient="records")}, frame


def run_task(task, on_stage=None):
    choice = resolve({key: getattr(task, key) for key in ("subsystem", "fault_mode", "flight_count", "injection_time", "end_time")})
    directory = output_dir(task)
    directory.mkdir(parents=True, exist_ok=True)
    if on_stage:
        on_stage("importing")
    exports = []
    with zipfile.ZipFile(services.ARCHIVE) as archive:
        for member, filename, component in ((choice["member"], "scope_data.csv", "原始状态量"),
                                             (choice["paired_member"], "P_values.csv", "派生参数")):
            path = directory / filename
            with archive.open(member) as source, path.open("wb") as target:
                shutil.copyfileobj(source, target)
            report, frame = _report(path)
            exports.append((path, component, member, report, frame))
    if not np.array_equal(exports[0][4][["Time", "FaultFlag"]].to_numpy(), exports[1][4][["Time", "FaultFlag"]].to_numpy()):
        raise ValueError("原始/派生文件的时间轴或故障标记不一致")
    if on_stage:
        on_stage("registering")
    with transaction.atomic():
        created = []
        for path, component, member, report, _ in exports:
            dataset = Dataset.objects.create(name=(task.name if component == "原始状态量" else f"{task.name}-{component}")[:200],
                file=path.resolve().relative_to(Path(settings.MEDIA_ROOT).resolve()).as_posix(),
                source="simulation", fault_type=task.fault_mode, injection_time=task.injection_time,
                launch_number=task.flight_count, system=task.subsystem, component=component)
            created.append({"dataset_id": dataset.pk, "path": dataset.file.name, "url": dataset.file.url,
                            "component": component, "archive_member": member, **report})
        result = {"backend": "project_archive", "source": "包内甲方项目仿真数据/simulate_data_+1",
                  "archive_member": choice["member"], "duration": 480, "datasets": created,
                  "parameters": {"power_fault": task.fault_mode if task.subsystem == "动力" else "无故障",
                                 "control_fault": task.fault_mode if task.subsystem == "控制" else "无故障",
                                 "flight_count": task.flight_count, "start_time": task.injection_time, "end_time": task.end_time},
                  "note": "原始文件按字节导入，时刻取自已有仿真记录；未调用 MATLAB 或重新求解模型。"}
        task.dataset_id, task.simulation_output = created[0]["dataset_id"], result
        task.latest_result = {"datasets": [item["dataset_id"] for item in created]}
        task.status = task.current_stage = "completed"
        task.save(update_fields=["dataset_id", "simulation_output", "latest_result", "status", "current_stage", "updated_at"])
    return result
