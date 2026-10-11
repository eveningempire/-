"""Three-level health assessment algorithms used by the platform endpoint.

The handoff bundle supplies frozen component-HI artifacts, while this module
bridges raw CSV telemetry to the bundle contract and provides the paper's
transparent CDPCA-GA, AE-GMM and GCN/RBD evaluation paths.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from datasets.schema import column_role, timestamp_value


def _matrix(rows: Sequence[dict]) -> Tuple[np.ndarray, List[str], np.ndarray]:
    if not rows:
        raise ValueError("数据集没有可评估的行")
    keys = [k for k in rows[0] if column_role(k) == "parameter" and k.lower() != "hi_norm"]
    keys = [k for k in keys if any(_finite(row.get(k)) for row in rows)]
    if not keys:
        raise ValueError("数据集没有可评估的数值信号")
    data = np.array([[float(row.get(k, 0.0)) if _finite(row.get(k)) else np.nan for k in keys] for row in rows], dtype=float)
    for col in range(data.shape[1]):
        finite = np.isfinite(data[:, col])
        fill = float(np.nanmedian(data[:, col])) if finite.any() else 0.0
        data[~finite, col] = fill
    time = np.array([timestamp_value(row, float(i)) for i, row in enumerate(rows)])
    if not np.isfinite(time).all() or np.any(np.diff(time) < 0):
        raise ValueError("时间戳必须为有限数值并按时间升序排列")
    return data, keys, time


def _finite(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _features(data: np.ndarray) -> np.ndarray:
    """Extract compact time/frequency features for each rolling sample."""
    n, d = data.shape
    width = max(8, min(32, n // 5 if n >= 10 else n))
    output = []
    for i in range(n):
        window = data[max(0, i - width + 1): i + 1]
        centered = window - window.mean(axis=0, keepdims=True)
        rms = np.sqrt(np.mean(window ** 2, axis=0))
        std = window.std(axis=0)
        peak = np.max(np.abs(centered), axis=0)
        if len(window) > 1:
            spectrum = np.abs(np.fft.rfft(centered, axis=0))
            freq_energy = np.mean(spectrum[1:] ** 2, axis=0) if spectrum.shape[0] > 1 else np.zeros(d)
            power = spectrum ** 2
            power = power / np.maximum(power.sum(axis=0, keepdims=True), 1e-12)
            spectral_entropy = -(power * np.log(power + 1e-12)).sum(axis=0)
        else:
            freq_energy = np.zeros(d)
            spectral_entropy = np.zeros(d)
        output.append(np.concatenate([window[-1], window.mean(axis=0), std, rms, peak, freq_energy, spectral_entropy]))
    return np.asarray(output, dtype=float)


def _assessment_input(rows, reference_rows=None, reference_info=None, baseline_end=None):
    """Separate normal flight evolution from deviations; never read fault labels."""
    data, signals, time = _matrix(rows)
    features = _features(data)
    if reference_rows is not None:
        normal, normal_signals, normal_time = _matrix(reference_rows)
        if set(signals) != set(normal_signals):
            raise ValueError("正常基线与待评估数据的参数列不一致")
        if time[0] < normal_time[0] or time[-1] > normal_time[-1]:
            raise ValueError("正常基线的时间范围不能覆盖待评估数据")
        # Adaptive Simulink sample grids differ. Align the signals before
        # extracting windows so both windows represent the same timestamps.
        _, last = np.unique(normal_time[::-1], return_index=True)
        keep = np.sort(len(normal_time) - 1 - last)
        normal = normal[:, [normal_signals.index(key) for key in signals]]
        aligned = np.column_stack([np.interp(time, normal_time[keep], normal[keep, i])
                                   for i in range(len(signals))])
        train = _features(normal)
        expected = _features(aligned)
        metadata = {"kind": "normal_dataset", "time_aligned": True,
                    "sample_count": len(normal), **(reference_info or {})}
    else:
        count = min(len(rows), max(1, int(len(rows) * 0.2)))
        if baseline_end is not None and math.isfinite(float(baseline_end)):
            before = int(np.searchsorted(time, float(baseline_end), side="left"))
            if before == 0:
                raise ValueError("注入前没有参考样本，需提供正常基线后再评估")
            count = min(count, before)
        train = features[:count]
        expected = np.repeat(train.mean(axis=0, keepdims=True), len(features), axis=0)
        metadata = {"kind": "initial_segment", "time_aligned": False,
                    "sample_count": count, "time_range": [float(time[0]), float(time[count-1])],
                    "assumption": "初始参考段假定正常；未消除后续工况变化"}
    return features, train, expected, signals, time, metadata


def _deviation(values, expected, normal, time_aligned=False):
    """Sign-invariant distance beyond normal variation, in standard deviations."""
    scale = np.maximum(np.std(normal, axis=0), 1e-6)
    # Aligned expected values already remove normal flight evolution; its
    # full-trajectory range is not an acceptable residual tolerance.
    tolerance = 0.0 if time_aligned else np.percentile(np.abs(normal - normal.mean(axis=0)), 95, axis=0)
    return np.maximum(np.abs(values - expected) - tolerance, 0.0) / scale


def _ga_weights(features: np.ndarray, scores: np.ndarray) -> np.ndarray:
    """Small deterministic GA-style search over fusion weights."""
    rng = np.random.default_rng(20260914)
    d = features.shape[1]
    population = rng.dirichlet(np.ones(d), size=min(48, max(12, d * 2)))
    target = np.asarray(scores)
    def fitness(weight):
        series = features @ weight
        smooth = 1.0 / (1.0 + np.std(np.diff(series))) if len(series) > 1 else 1.0
        agreement = 1.0 / (1.0 + np.mean(np.abs(series - target)))
        return 0.10 * smooth + 0.90 * agreement
    for _ in range(18):
        order = np.argsort([fitness(x) for x in population])[::-1]
        elite = population[order[:max(4, len(population) // 5)]]
        children = [*elite]
        while len(children) < len(population):
            a, b = elite[rng.integers(len(elite))], elite[rng.integers(len(elite))]
            child = (a + b) / 2.0
            child += rng.normal(0, 0.04, d)
            child = np.clip(child, 1e-6, None)
            children.append(child / child.sum())
        population = np.asarray(children)
    return population[np.argmax([fitness(x) for x in population])]


def cdpca_ga(rows: Sequence[dict], reference_rows=None, reference_info=None, baseline_end=None) -> Dict:
    features, train, expected, signals, time, reference = _assessment_input(
        rows, reference_rows, reference_info, baseline_end)
    scaler = StandardScaler().fit(train)
    z = scaler.transform(features)
    normal_z = scaler.transform(train)
    expected_z = scaler.transform(expected)
    # A constant/one-row reference has no identifiable PCA subspace.
    if len(train) > 1 and np.any(np.var(normal_z, axis=0) > 1e-12):
        components = max(1, min(normal_z.shape[0]-1, normal_z.shape[1], 8))
        pca = PCA(n_components=components, random_state=2026).fit(normal_z)
        projected, normal = pca.transform(z), pca.transform(normal_z)
        distances = _deviation(projected, pca.transform(expected_z), normal, reference['time_aligned'])
        variance = float(pca.explained_variance_ratio_.sum())
    else:
        components, variance = 0, 0.0
        distances = np.empty((len(rows), 0))
    # Retain the full-feature distance: faults in discarded/constant PCA
    # directions must not disappear from the assessment.
    full_distance = np.sqrt(np.mean(_deviation(z, expected_z, normal_z, reference['time_aligned']) ** 2, axis=1))
    distances = np.column_stack([distances, full_distance])
    candidates = np.exp(-0.18 * np.clip(distances, 0, 100))
    target = candidates[:, -1]
    weights = _ga_weights(candidates, target)
    health = np.clip(0.5 * target + 0.5 * (candidates @ weights), 0.0, 1.0)
    return {"algorithm": "CDPCA-GA", "level": "component", "health_index": float(health[-1]),
            "hi_sequence": [round(float(x), 6) for x in health],
            "time_sequence": [round(float(x), 6) for x in time], "signals": signals,
            "feature_count": int(features.shape[1]), "pca_components": components,
            "explained_variance": round(variance, 6), "reference": reference,
            "hi_definition": "1 表示接近正常参考，偏离越大健康指数越低；允许恢复",
            "fusion_features": [f"PC{i+1}_health" for i in range(components)] + ["full_feature_health"],
            "ga_weights": [round(float(x), 6) for x in weights],
            "source": "platform_health.algorithms.cdpca_ga", "status": "development"}


def ae_gmm(rows: Sequence[dict], reference_rows=None, reference_info=None, baseline_end=None) -> Dict:
    features, normal, expected, signals, time, reference = _assessment_input(
        rows, reference_rows, reference_info, baseline_end)
    scaler = StandardScaler().fit(normal)
    z, train = scaler.transform(features), scaler.transform(normal)
    expected_z = scaler.transform(expected)
    latent_dim = max(1, min(8, train.shape[1] // 2, train.shape[0]))
    if train.shape[0] < 5 or train.shape[1] < 2:
        latent = train[:, :latent_dim]
        encoded = z[:, :latent_dim]
        expected_encoded = expected_z[:, :latent_dim]
        ae_backend = "linear_fallback"
    else:
        hidden = max(latent_dim + 1, min(32, train.shape[1]))
        ae = MLPRegressor(hidden_layer_sizes=(hidden, latent_dim, hidden), activation="relu",
                          solver="lbfgs", max_iter=500, random_state=2026)
        fit_indices = np.unique(np.linspace(0, len(train)-1, min(1024, len(train))).astype(int))
        ae.fit(train[fit_indices], train[fit_indices])
        # Extract the encoder half of the trained symmetric autoencoder.
        def encode(values):
            hidden_values = np.maximum(0.0, values @ ae.coefs_[0] + ae.intercepts_[0])
            return np.maximum(0.0, hidden_values @ ae.coefs_[1] + ae.intercepts_[1])
        latent, encoded, ae_backend = encode(train), encode(z), "MLP-autoencoder"
        expected_encoded = encode(expected_z)
    try:
        fit_latent = latent[np.unique(np.linspace(0, len(latent)-1, min(1024, len(latent))).astype(int))]
        gmm_components = max(1, min(3, len(np.unique(fit_latent, axis=0))))
        gmm = GaussianMixture(n_components=gmm_components, covariance_type="full", random_state=2026).fit(fit_latent)
        nll = -gmm.score_samples(encoded)
        base = -gmm.score_samples(latent)
        expected_nll = -gmm.score_samples(expected_encoded)
    except ValueError:
        gmm_components = 0
        nll = np.sum((encoded - latent.mean(0)) ** 2, axis=1)
        base = np.sum((latent - latent.mean(0)) ** 2, axis=1)
        expected_nll = np.sum((expected_encoded - latent.mean(0)) ** 2, axis=1)
    expected_nll = expected_nll if reference_rows is not None else base.mean()
    health = np.exp(-np.clip((nll - expected_nll) / (base.std() + 1e-6), 0, 20) / 3.0)
    # The encoder may suppress an out-of-distribution deviation; keep a
    # direct residual-distance bound so it cannot become healthier.
    distance = np.sqrt(np.mean(_deviation(scaler.transform(features), scaler.transform(expected),
                                         scaler.transform(normal), reference['time_aligned']) ** 2, axis=1))
    health = np.minimum(health, np.exp(-0.18 * np.clip(distance, 0, 100)))
    return {"algorithm": "AE-GMM", "level": "component", "health_index": float(np.clip(health[-1], 0, 1)),
            "hi_sequence": [round(float(np.clip(x, 0, 1)), 6) for x in health],
            "time_sequence": [round(float(x), 6) for x in time], "signals": signals,
            "feature_count": int(features.shape[1]), "latent_dim": int(latent_dim),
            "gmm_components": gmm_components, "backend": ae_backend,
            "training_sample_count": min(1024, len(train)),
            "reference": reference, "hi_definition": "1 表示接近正常参考，偏离越大健康指数越低；允许恢复",
            "source": "platform_health.algorithms.ae_gmm", "status": "development"}


def gcn_rbd(component_results: Sequence[Dict], component_ids: Sequence[str]) -> Dict:
    if not component_results:
        raise ValueError("GCN/RBD 至少需要一个部件健康评估结果")
    sequences = [np.asarray(item.get("hi_sequence", [item["health_index"]]), dtype=float) for item in component_results]
    time_axes = [np.asarray(item.get("time_sequence", np.arange(len(seq))), dtype=float)
                 for item, seq in zip(component_results, sequences)]
    for times, seq in zip(time_axes, sequences):
        if (not len(seq) or len(times) != len(seq) or not np.isfinite(times).all()
                or not np.isfinite(seq).all() or np.any(np.diff(times) < 0)):
            raise ValueError("部件健康评估需要有效且按时间升序排列的时间序列")
    start, end = max(times[0] for times in time_axes), min(times[-1] for times in time_axes)
    if start > end:
        raise ValueError("部件数据集没有重叠的时间范围，不能融合系统健康状况")
    times = np.unique(np.concatenate([axis[(axis >= start) & (axis <= end)] for axis in time_axes]))
    values_by_time = np.asarray([np.interp(times, axis, seq) for axis, seq in zip(time_axes, sequences)])
    values = values_by_time[:, -1]
    n = len(values)
    # Physical adjacency: neighbouring components exchange state; self-loop is required.
    adjacency = np.eye(n) + (np.ones((n, n)) - np.eye(n)) * (1.0 / max(1, n - 1))
    degree = adjacency.sum(axis=1)
    normalized = adjacency / np.sqrt(np.outer(degree, degree))
    gcn_sequence, rbd_sequence, system_sequence = [], [], []
    for column in values_by_time.T:
        hidden = np.maximum(0.0, normalized @ column)
        gcn_hi = float(np.clip(np.mean(hidden), 0, 1))
        rbd_hi = float(np.prod(np.clip(column, 0, 1)))
        system_hi = float(np.clip(0.5 * gcn_hi + 0.5 * rbd_hi, 0, 1))
        gcn_sequence.append(gcn_hi)
        rbd_sequence.append(rbd_hi)
        system_sequence.append(system_hi)
    system_hi = system_sequence[-1]
    return {"algorithm": "GCN + RBD 系统健康评估", "level": "system", "health_index": round(system_hi, 6),
            "hi_sequence": [round(float(x), 6) for x in system_sequence],
            "time_sequence": [round(float(x), 6) for x in times],
            "component_health": {str(k): round(float(v), 6) for k, v in zip(component_ids, values)},
            "component_hi_sequences": {str(k): [round(float(x), 6) for x in seq] for k, seq in zip(component_ids, values_by_time)},
            "time_alignment": "timestamp_interpolation_on_common_range",
            "hi_definition": "1 表示接近正常参考，部件健康下降时系统健康下降；允许恢复",
            "gcn_health_index": round(gcn_sequence[-1], 6), "rbd_serial_health_index": round(rbd_sequence[-1], 6),
            "gcn_hi_sequence": [round(float(x), 6) for x in gcn_sequence],
            "rbd_serial_hi_sequence": [round(float(x), 6) for x in rbd_sequence],
            "adjacency": normalized.round(6).tolist(), "source": "platform_health.algorithms.gcn_rbd",
            "status": "development", "limitations": ["GCN/RBD 当前为无监督结构融合,需冻结训练权重后再作为正式模型"]}
