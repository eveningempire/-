"""Evaluate inference outputs against labels kept outside model features."""
from collections import Counter, defaultdict

import numpy as np

FAULT_NAMES = {
    "baseline": "正常", "bengqixi": "泵气蚀", "wolun": "涡轮转速下降",
    "guanlu": "管路堵塞", "zhufa": "主阀门卡滞", "ranqi": "燃气泄漏",
    "ranshao": "燃烧不稳定", "penguan": "喷管堵塞", "tvc": "TVC偏角不足",
    "rcs": "RCS推力不足", "geduo": "栅格舵偏角不足", "kongzhiqi": "控制器无信号",
    "tuoluoyi_piancha": "陀螺仪恒偏差", "tuoluoyi_kasi": "陀螺仪卡死",
}


def score_windows(frame, result, expected_fault):
    times = frame["Time"].to_numpy(dtype=float)
    flags = frame["FaultFlag"].to_numpy(dtype=int)
    scores = []
    for window in result.get("window_series", []):
        start, end = float(window["time_start"]), float(window["time_end"])
        left = int(np.searchsorted(times, start, side="left"))
        right = int(np.searchsorted(times, end, side="right"))
        labels = flags[left:right]
        truth = "transition" if not len(labels) or np.any(labels != labels[0]) else expected_fault if labels[0] else "正常"
        predicted = window["pred_name"]
        scores.append({"time_start": start, "time_end": end, "truth": truth,
                       "predicted": predicted, "confidence": window.get("confidence"),
                       "class_correct": None if truth == "transition" else predicted == truth,
                       "binary_correct": None if truth == "transition" else (predicted != "正常") == (truth != "正常")})
    return scores


def summarize(records):
    groups = defaultdict(list)
    for record in records:
        groups[(record["algorithm"], record["data_type"])].append(record)
    output = []
    for (algorithm, data_type), items in groups.items():
        successful = [item for item in items if item["status"] == "success"]
        windows = [window for item in successful for window in item["windows"] if window["truth"] != "transition"]
        normal = [window for window in windows if window["truth"] == "正常"]
        faulty = [window for window in windows if window["truth"] != "正常"]
        by_class = {}
        for fault in FAULT_NAMES.values():
            rows = [window for window in windows if window["truth"] == fault]
            if rows:
                by_class[fault] = {"windows": len(rows), "correct": sum(row["class_correct"] for row in rows),
                                   "detected": sum(row["predicted"] != "正常" for row in rows)}
        baseline = [item for item in successful if item["expected_fault"] == "正常"]
        fault_files = [item for item in successful if item["expected_fault"] != "正常"]
        output.append({"algorithm": algorithm, "data_type": data_type, "files": len(items),
                       "success": len(successful), "errors": len(items)-len(successful),
                       "model_modes": dict(Counter(item.get("model_mode", "unknown") for item in successful)),
                       "homogeneous_windows": len(windows), "normal_windows": len(normal), "fault_windows": len(faulty),
                       "window_class_accuracy": sum(window["class_correct"] for window in windows)/len(windows) if windows and algorithm == "hier14" else None,
                       "window_binary_accuracy": sum(window["binary_correct"] for window in windows)/len(windows) if windows else None,
                       "normal_false_alarm_rate": sum(window["predicted"] != "正常" for window in normal)/len(normal) if normal else None,
                       "fault_detection_recall": sum(window["predicted"] != "正常" for window in faulty)/len(faulty) if faulty else None,
                       "fault_class_accuracy": sum(window["class_correct"] for window in faulty)/len(faulty) if faulty and algorithm == "hier14" else None,
                       "baseline_files": len(baseline),
                       "baseline_aggregate_correct": sum(item["aggregate_predicted"] == "正常" for item in baseline),
                       "fault_files": len(fault_files),
                       "fault_aggregate_correct": sum(item["aggregate_predicted"] == item["expected_fault"] for item in fault_files),
                       "fault_aggregate_detected": sum(item["aggregate_predicted"] != "正常" for item in fault_files),
                       "class_identification_supported": algorithm == "hier14",
                       "per_class": by_class,
                       "confusion": dict(Counter(f'{window["truth"]} -> {window["predicted"]}' for window in windows))})
    return output
