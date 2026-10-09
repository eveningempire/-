"""Build the RUL model's HI input with the delivered, frozen preprocessing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings

HI_NAMES = {"hi_norm", "hi", "health_index", "health", "健康指数"}
HEALTH_MAIN_COMPONENT_NAMES = {
    1: '液氧泵', 2: '液氧涡轮', 3: '煤油管路', 4: '煤油阀门',
    5: '燃气发生器', 6: '燃烧室', 7: '喷管', 8: 'TVC',
    9: 'RCS', 10: '栅格舵', 11: '传感器', 12: '液氧管路',
    13: '液氧阀门', 14: '煤油泵', 15: '煤油涡轮',
}
COMPONENT_SIGNALS = dict(enumerate(
    ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P10", "P9", "P12", "P14", "P15", "P16", "P17"),
    start=1,
))
COMPONENT_FEATURES = {
    **dict.fromkeys((1, 2, 3, 4, 7, 10, 12, 13, 14, 15), ("min", "mean", "rms", "max")),
    5: ("rms", "mean", "max", "min"),
    **dict.fromkeys((6, 8, 9), ("mean", "rms", "max", "min")),
    11: ("max", "rms", "mean", "min"),
}
SOURCE_REFERENCE = "health-main/backend/algorithm/views.py:component_eval; algotest/lifepredict.py"


def _validate_component_dataset(dataset, component, paired=False):
    if not dataset.structure_node_id:
        return
    actual = (dataset.structure_node.name or '').strip()
    aliases = {'氧涡轮': '液氧涡轮'}
    expected = HEALTH_MAIN_COMPONENT_NAMES[component]
    if aliases.get(actual, actual) != expected:
        label = '配套派生数据集' if paired else '数据集'
        raise ValueError(f'{label}已关联 PBS 部件“{actual}”,与所选寿命模型“{expected}”不一致;请先核对部件映射')


def _read(dataset):
    if not dataset.file or not dataset.file.name.lower().endswith(".csv"):
        raise ValueError("寿命预测只接受 CSV 数据集")
    frame = pd.read_csv(dataset.file.path, encoding="utf-8-sig")
    frame.columns = [str(column).strip() for column in frame.columns]
    if frame.columns.duplicated().any():
        raise ValueError("CSV 含重复列名")
    if frame.empty:
        raise ValueError("数据集为空")
    return frame


def _time_column(frame):
    return next((column for column in frame if column.lower() in {"time", "timestamp"}), None)


def _finite_column(frame, column):
    try:
        values = pd.to_numeric(frame[column], errors="raise").to_numpy(dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{column} 列必须为有效数值") from exc
    if not np.isfinite(values).all():
        raise ValueError(f"{column} 列含缺失值或非有限数值")
    return values


def _times(frame, required=False):
    column = _time_column(frame)
    if column is None:
        if required:
            raise ValueError("P 参数转 HI 需要 Time 时间戳列(秒)")
        return np.arange(len(frame), dtype=float), None
    times = _finite_column(frame, column)
    if np.any(np.diff(times) < 0):
        raise ValueError("Time 时间戳必须按时间升序排列")
    return times, column


def _paired_dataset(dataset):
    """Only follow registered task outputs or the imported archive manifest."""
    from datasets.models import Dataset
    from simulation_demo.models import FaultWorkflowTask

    for task in FaultWorkflowTask.objects.filter(dataset_id=dataset.pk, status="completed"):
        exports = task.simulation_output.get("datasets", [])
        raw = next((item for item in exports if item.get("dataset_id") == dataset.pk), None)
        if raw is None or raw.get("path") != dataset.file.name:
            continue
        for item in exports:
            if item.get("component") != "派生参数":
                continue
            candidate = Dataset.objects.filter(pk=item.get("dataset_id"), file=item.get("path")).first()
            if candidate and Path(candidate.file.path).parent == Path(dataset.file.path).parent:
                return candidate

    manifest_path = Path(settings.MEDIA_ROOT) / "datasets" / "simulate_data_+1" / "import_manifest.json"
    if manifest_path.is_file():
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        raw = next((item for item in entries if item.get("dataset_id") == dataset.pk
                    and item.get("file") == dataset.file.name), None)
        if raw:
            original = Path(raw["member"])
            paired_member = original.with_name(original.stem + "_P.csv").as_posix()
            entry = next((item for item in entries if item.get("member") == paired_member), None)
            if entry:
                candidate = Dataset.objects.filter(pk=entry["dataset_id"], file=entry["file"]).first()
                if candidate and Path(candidate.file.path).parent == Path(dataset.file.path).parent:
                    return candidate
    raise ValueError("原始状态量没有可核验的同次仿真派生参数;请选对应的派生参数 CSV(P1～P17)或带 HI 的数据集")


def prepare(dataset, component_id, asset_dir):
    component = int(component_id)
    if component not in COMPONENT_SIGNALS:
        raise ValueError("部件模型编号必须为 1 到 15")
    _validate_component_dataset(dataset, component)
    frame = _read(dataset)
    hi_column = next((column for column in frame if column.lower() in HI_NAMES), None)
    source = dataset
    paired = False
    if hi_column is not None:
        hi = _finite_column(frame, hi_column)
        if np.any((hi < 0) | (hi > 1)):
            raise ValueError("提供的 HI 必须为 0 到 1 的有限数值")
        times, time_column = _times(frame)
        metadata = {"method": "provided_hi", "input_signal": hi_column, "feature_order": [],
                    "window_seconds": None, "step_seconds": None, "time_column": time_column,
                    "clipped_fraction": 0.0, "calibration": "provided_hi"}
    else:
        signal = COMPONENT_SIGNALS[component]
        if signal not in frame:
            if any(column.startswith("P") and column[1:].isdigit() for column in frame):
                raise ValueError(f"所选部件模型需要 {signal} 列")
            source = _paired_dataset(dataset)
            _validate_component_dataset(source, component, paired=True)
            paired_frame = _read(source)
            selected_times, _ = _times(frame, required=True)
            paired_times, _ = _times(paired_frame, required=True)
            if not np.array_equal(selected_times, paired_times):
                raise ValueError("原始状态量与配套派生参数的 Time 时间轴不一致,不能用于寿命预测")
            frame, paired = paired_frame, True
        if signal not in frame:
            raise ValueError(f"配套派生参数缺少模型所需的 {signal} 列")
        values = _finite_column(frame, signal)
        source_times, time_column = _times(frame, required=True)
        starts = np.arange(source_times[0], source_times[-1] - 1e-9, 1.0)
        features, times = [], []
        order = COMPONENT_FEATURES[component]
        # The stored scaler expects the training feature order, not the old
        # inference endpoint's inverse permutation of those feature names.
        for start in starts:
            left, right = np.searchsorted(source_times, (start, start + 2.0), side="left")
            window = values[left:right]
            if not len(window):
                continue
            stats = {"min": np.min(window), "max": np.max(window),
                     "mean": np.mean(window), "rms": np.sqrt(np.mean(np.square(window)))}
            features.append([stats[name] for name in order])
            times.append(float(start + 1.0))
        if not features:
            raise ValueError("没有可用的 2 秒 HI 特征窗口")
        scaler = joblib.load(asset_dir / "scaler.pkl")
        pca = joblib.load(asset_dir / "pca.pkl")
        meta = json.loads((asset_dir / "hi_meta.json").read_text(encoding="utf-8"))
        low, high = float(meta["global_min"]), float(meta["global_max"])
        if not np.isfinite((low, high)).all() or high <= low:
            raise ValueError("训练 HI 归一化元数据无效")
        raw_hi = pca.transform(scaler.transform(np.asarray(features, dtype=float))).reshape(-1)
        raw_hi = (raw_hi - low) / (high - low + 1e-8)
        reverse = signal in {"P5", "P6", "P12"}
        if reverse:
            raw_hi = 1.0 - raw_hi
        if not np.isfinite(raw_hi).all():
            raise ValueError("训练预处理生成了非有限 HI")
        clipped_fraction = float(np.mean((raw_hi < 0) | (raw_hi > 1)))
        hi = np.clip(raw_hi, 0.0, 1.0)
        metadata = {"method": "trained_pca", "input_signal": signal, "feature_order": list(order),
                    "window_seconds": 2.0, "step_seconds": 1.0, "time_column": time_column,
                    "clipped_fraction": clipped_fraction, "raw_hi_range": [float(raw_hi.min()), float(raw_hi.max())],
                    "reversed": reverse, "calibration": "trained_scaler_pca",
                    "normalization_range": [low, high], "reference": SOURCE_REFERENCE,
                    "preprocessing_assets": {name: hashlib.sha256((asset_dir / name).read_bytes()).hexdigest()
                                             for name in ("scaler.pkl", "pca.pkl", "hi_meta.json")},
                    "window_time_kind": "center"}
    metadata.update({"source_dataset_id": source.pk, "source_dataset_name": source.name,
                     "paired_dataset": paired, "source_row_count": len(frame),
                     "hi_count": len(hi), "excluded_feature_columns": ["Time", "FaultFlag"]})
    return {"values": hi.tolist(), "times": np.asarray(times).tolist(), "source": metadata}
