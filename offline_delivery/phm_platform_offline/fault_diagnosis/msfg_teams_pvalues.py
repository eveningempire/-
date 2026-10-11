"""MSFG + TEAMS-RT on P_values.csv (health-main / 一院 route).

Pipeline: expert P1–P17 anomaly rules → abstract test vector T → D_power / D_control
→ teams_rt_fault_rows → 13 Simulink fault names.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from datasets.models import Dataset

FAULT_ALL: List[str] = [
    "泵气蚀",
    "涡轮转速下降",
    "管路堵塞",
    "主阀门卡滞",
    "燃气泄漏",
    "燃烧不稳定",
    "喷管堵塞",
    "TVC偏角不足",
    "RCS推力不足",
    "栅格舵偏角不足",
    "控制器无信号",
    "陀螺仪恒偏差",
    "陀螺仪卡死",
]

D_POWER: List[List[int]] = [
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 0, 0, 1],
    [0, 0, 1, 0, 0, 0, 1],
    [0, 0, 1, 1, 0, 0, 1],
    [0, 0, 0, 0, 1, 0, 1],
    [0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 1],
]

D_CONTROL: List[List[int]] = [
    [1, 0, 0, 0, 1],
    [0, 0, 1, 0, 1],
    [0, 1, 0, 0, 1],
    [0, 0, 1, 1, 1],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
]

POWER_TEST_NAMES = [f"动力测点{i + 1}" for i in range(7)]
CONTROL_TEST_NAMES = [f"控制测点{i + 1}" for i in range(5)]

P_RULES: Dict[str, dict] = {}
for key, (relation, threshold, duration) in {
    "P1": ("<=", 0.8, 1.0),
    "P2": ("<=", 0.8, 1.0),
    "P3": ("<=", 0.8, 1.0),
    "P4": ("<=", 0.9, 1.0),
    "P5": (">=", 0.1, 1.0),
    "P6": (">=", 1.2, 1.0),
    "P7": ("<=", 0.9, 1.0),
    "P8": ("<=", 0.8, 1.0),
    "P9": ("<=", 0.8, 1.0),
    "P10": ("<=", 0.8, 1.0),
    "P11": ("<=", 0.5, 1.0),
    "P12": (">=", 0.2, 1.0),
    "P13": ("<=", 0.5, 1.0),
    "P14": ("<=", 0.8, 1.0),
    "P15": ("<=", 0.9, 1.0),
    "P16": ("<=", 0.8, 1.0),
    "P17": ("<=", 0.8, 1.0),
}.items():
    P_RULES[key] = {"relation": relation, "threshold": threshold, "duration": duration}


def teams_rt_fault_rows(d_matrix: Sequence[Sequence[int]], test_vector: Sequence[int]) -> dict:
    """TEAMS-RT (rows=faults, cols=tests). T=1 means test failed (health-main fault1)."""
    d = np.array(d_matrix, dtype=int)
    t = np.array(test_vector, dtype=int)
    num_faults, num_tests = d.shape
    unknown = set(range(num_faults))
    good: set[int] = set()
    bad: set[int] = set()
    suspected: set[int] = set()

    for t_idx in range(num_tests):
        if t[t_idx] == 0:
            for fault in np.where(d[:, t_idx] == 1)[0]:
                if fault in unknown:
                    unknown.remove(fault)
                    good.add(fault)

    bad_candidates: set[int] = set()
    for t_idx in range(num_tests):
        if t[t_idx] == 1:
            related = [f for f in np.where(d[:, t_idx] == 1)[0] if f in unknown]
            if len(related) == 1:
                bad_candidates.add(related[0])
    for fault in bad_candidates:
        if fault in unknown:
            unknown.remove(fault)
            bad.add(fault)

    for t_idx in range(num_tests):
        if t[t_idx] == 1:
            related = [f for f in np.where(d[:, t_idx] == 1)[0] if f in unknown]
            for fault in related:
                unknown.remove(fault)
                suspected.add(fault)

    return {
        "Good": sorted(f + 1 for f in good),
        "Bad": sorted(f + 1 for f in bad),
        "Suspected": sorted(f + 1 for f in suspected),
        "Unknown": sorted(f + 1 for f in unknown),
    }


def _read_p_values(csv_path: Path) -> Tuple[List[dict], float]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 8:
        raise ValueError("P_values 诊断至少需要 8 行数据")
    time_key = next((k for k in rows[0] if k.strip().lower() in {"time", "timestamp", "t"}), None)
    if not time_key:
        raise ValueError("P_values CSV 缺少 Time 列")
    times = []
    for row in rows:
        try:
            times.append(float(row[time_key]))
        except (TypeError, ValueError):
            times.append(math.nan)
    finite = [t for t in times if math.isfinite(t)]
    if len(finite) < 2:
        dt = 0.1
    else:
        diffs = [finite[i + 1] - finite[i] for i in range(len(finite) - 1) if finite[i + 1] > finite[i]]
        dt = float(np.median(diffs)) if diffs else 0.1
        if not math.isfinite(dt) or dt <= 0:
            dt = 0.1
    missing = [f"P{i}" for i in range(1, 18) if f"P{i}" not in rows[0]]
    if missing:
        raise ValueError(f"P_values CSV 缺少列: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")
    return rows, dt


def detect_p_anomalies(rows: List[dict], dt: float) -> Tuple[Dict[str, int], List[dict]]:
    evidence = []
    status_map: Dict[str, int] = {}
    for name, rule in P_RULES.items():
        values = []
        for row in rows:
            try:
                value = float(row[name])
                if not math.isfinite(value):
                    raise ValueError
                values.append(value)
            except (TypeError, ValueError):
                values = []
                break
        if not values:
            status_map[name] = 0
            evidence.append({"signal": name, "status": 0, "threshold": rule["threshold"], "relation": rule["relation"], "failed": False})
            continue
        relation, threshold, duration_limit = rule["relation"], rule["threshold"], rule["duration"]
        if relation == "<=":
            mask = [v <= threshold for v in values]
        else:
            mask = [v >= threshold for v in values]
        consecutive = 0.0
        status = 0
        for flag in mask:
            if flag:
                consecutive += dt
                if consecutive >= duration_limit:
                    status = 1
                    break
            else:
                consecutive = 0.0
        status_map[name] = status
        evidence.append({
            "signal": name,
            "status": status,
            "threshold": threshold,
            "relation": relation,
            "latest": round(float(values[-1]), 6),
            "failed": bool(status),
        })
    return status_map, evidence


def build_test_vectors(p_status: Dict[str, int]) -> Tuple[List[int], List[int]]:
    """Map P1–P17 anomaly flags to health-main abstract tests (Home.vue anomaly_handle)."""
    power = [0, 0, 0, 0, 0, 0, 0]
    control = [0, 0, 0, 0, 0]

    def on(parameter: str):
        return p_status.get(parameter, 0) == 1

    if on("P1"):
        power[0] = power[6] = 1
    if on("P2"):
        power[0] = power[1] = power[6] = 1
    if on("P3"):
        power[2] = power[6] = 1
    if on("P4"):
        power[2] = power[3] = power[6] = 1
    if on("P5"):
        power[4] = power[6] = 1
    if on("P6"):
        power[5] = power[6] = 1
    if on("P7"):
        power[6] = 1
    if on("P8"):
        control[0] = control[4] = 1
    if on("P9"):
        control[1] = control[4] = 1
    if on("P10"):
        control[2] = control[4] = 1
    if on("P11"):
        control[2] = control[3] = control[4] = 1
    if on("P12"):
        control[4] = 1
    if on("P13"):
        control[4] = 1
    if on("P14") or on("P15") or on("P16") or on("P17"):
        power[6] = 1
    return power, control


def resolve_p_values_path(csv_path: Path, dataset: Optional[Dataset] = None) -> Path:
    path = Path(csv_path).resolve()
    name_lower = path.name.lower()
    if "p_values" in name_lower or name_lower.endswith("p_values.csv"):
        return path
    if dataset is not None:
        if dataset.component == "派生参数":
            return path
        sibling_name = f"{dataset.name}-派生参数"[:200]
        sibling = Dataset.objects.filter(name=sibling_name, source=dataset.source).exclude(pk=dataset.pk).first()
        if sibling and sibling.file:
            return Path(sibling.file.path).resolve()
        sibling = Dataset.objects.filter(component="派生参数", source=dataset.source, name__startswith=dataset.name.split("-")[0]).order_by("-id").first()
        if sibling and sibling.file:
            return Path(sibling.file.path).resolve()
    alt = path.parent / "P_values.csv"
    if alt.is_file():
        return alt.resolve()
    raise ValueError(
        "MSFG+TEAMS（一院）需要 P_values.csv；请选择「派生参数」数据集，"
        "或与 scope_data 同任务的派生 CSV（名称通常为「任务名-派生参数」）。"
    )


def _indices_to_names(indices: Sequence[int], offset: int) -> List[str]:
    names = []
    for index in indices:
        pos = index - 1 + offset
        if 0 <= pos < len(FAULT_ALL):
            names.append(FAULT_ALL[pos])
    return names


def _pick_label(bad: List[str], suspected: List[str], p_abnormal: bool) -> Tuple[str, float]:
    if bad:
        return bad[0], 1.0
    if suspected:
        return suspected[0], 0.75
    if p_abnormal:
        return "诊断不确定", 0.5
    return "正常", 1.0


def msfg_teams_pvalues(csv_path, dataset: Optional[Dataset] = None):
    resolved = resolve_p_values_path(Path(csv_path), dataset)
    rows, dt = _read_p_values(resolved)
    p_status, p_evidence = detect_p_anomalies(rows, dt)
    power_t, control_t = build_test_vectors(p_status)
    p_abnormal = any(p_status.values())

    power_result = teams_rt_fault_rows(D_POWER, power_t)
    control_result = teams_rt_fault_rows(D_CONTROL, control_t)

    bad = _indices_to_names(power_result["Bad"], 0) + _indices_to_names(control_result["Bad"], 7)
    suspected = _indices_to_names(power_result["Suspected"], 0) + _indices_to_names(control_result["Suspected"], 7)
    good = _indices_to_names(power_result["Good"], 0) + _indices_to_names(control_result["Good"], 7)
    unknown = _indices_to_names(power_result["Unknown"], 0) + _indices_to_names(control_result["Unknown"], 7)

    label, confidence = _pick_label(bad, suspected, p_abnormal)
    abnormal = label not in {"正常", "诊断不确定"} or (label == "诊断不确定" and p_abnormal)

    combined_d = [row + [0] * len(CONTROL_TEST_NAMES) for row in D_POWER]
    for row in D_CONTROL:
        combined_d.append([0] * len(POWER_TEST_NAMES) + row)
    tests = POWER_TEST_NAMES + CONTROL_TEST_NAMES
    faults = FAULT_ALL[:]

    if not p_abnormal and not bad and not suspected:
        class_probs = [{"name": "正常", "prob": 1.0}]
    else:
        ranked = bad + [n for n in suspected if n not in bad]
        if not ranked:
            ranked = ["诊断不确定"]
        class_probs = [{"name": n, "prob": (1.0 if n in bad else 0.75)} for n in ranked[:6]]
        if label not in ranked and label != "正常":
            class_probs = [{"name": label, "prob": confidence}] + class_probs

    time_start = rows[0].get("Time", rows[0].get("time", 0))
    time_end = rows[-1].get("Time", rows[-1].get("time", len(rows) - 1))

    return {
        "algorithm": "MSFG + TEAMS-RT 依赖诊断",
        "pred_name": label if abnormal or label == "诊断不确定" else "正常",
        "aggregate_pred_name": label if abnormal or label == "诊断不确定" else "正常",
        "confidence": confidence,
        "n_windows": 1,
        "seq_len": len(rows),
        "window_stride": len(rows),
        "sample_dt": round(dt, 6),
        "window_series": [{
            "window_index": 0,
            "time_start": time_start,
            "time_end": time_end,
            "pred_name": label if abnormal or label == "诊断不确定" else "正常",
            "confidence": confidence,
        }],
        "class_probs": class_probs[:5] if len(class_probs) > 6 else class_probs,
        "aggregate_class_probs": class_probs[:5] if len(class_probs) > 6 else class_probs,
        "evidence": p_evidence,
        "p_anomaly_tests": {"power": power_t, "control": control_t},
        "diagnostic_sets": {
            "good": good,
            "bad": bad,
            "suspect": suspected,
            "unknown": unknown,
        },
        "d_matrix": {"tests": tests, "faults": faults, "values": combined_d},
        "input_csv": str(resolved),
        "model_mode": "operational-msfg-teams-yiyuan-p-values",
    }
