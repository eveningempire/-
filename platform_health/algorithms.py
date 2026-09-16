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


def _matrix(rows: Sequence[dict]) -> Tuple[np.ndarray, List[str], np.ndarray]:
    if not rows:
        raise ValueError("数据集没有可评估的行")
    keys = [k for k in rows[0] if k.lower() not in {"time", "hi_norm"}]
    keys = [k for k in keys if any(_finite(row.get(k)) for row in rows)]
    if not keys:
        raise ValueError("数据集没有可评估的数值信号")
    data = np.array([[float(row.get(k, 0.0)) if _finite(row.get(k)) else np.nan for k in keys] for row in rows], dtype=float)
    for col in range(data.shape[1]):
        finite = np.isfinite(data[:, col])
        fill = float(np.nanmedian(data[:, col])) if finite.any() else 0.0
        data[~finite, col] = fill
    time = np.array([float(row.get("time", i)) if _finite(row.get("time", i)) else float(i) for i, row in enumerate(rows)])
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
            spectral_entropy = []
            for col in range(d):
                power = spectrum[:, col] ** 2
                power = power / max(power.sum(), 1e-12)
                spectral_entropy.append(float(-(power * np.log(power + 1e-12)).sum()))
            spectral_entropy = np.asarray(spectral_entropy)
        else:
            freq_energy = np.zeros(d)
            spectral_entropy = np.zeros(d)
        output.append(np.concatenate([window[-1], window.mean(axis=0), std, rms, peak, freq_energy, spectral_entropy]))
    return np.asarray(output, dtype=float)


def _normal(values: np.ndarray, healthy: np.ndarray, invert: bool = False) -> np.ndarray:
    baseline = np.asarray(healthy, dtype=float)
    scale = np.std(baseline, axis=0) + 1e-6
    distance = np.sqrt(np.mean(((values - baseline.mean(axis=0)) / scale) ** 2, axis=1))
    hi = np.exp(-0.18 * np.clip(distance, 0, 20))
    if invert:
        hi = 1.0 - hi
    return np.clip(hi, 0.0, 1.0)


def _ga_weights(features: np.ndarray, scores: np.ndarray) -> np.ndarray:
    """Small deterministic GA-style search over fusion weights."""
    rng = np.random.default_rng(20260914)
    d = features.shape[1]
    population = rng.dirichlet(np.ones(d), size=min(48, max(12, d * 2)))
    target = np.asarray(scores)
    trend = np.linspace(0.0, 1.0, len(target))
    def fitness(weight):
        series = features @ weight
        corr = abs(np.corrcoef(series, trend)[0, 1]) if np.std(series) > 1e-9 else 0.0
        smooth = 1.0 / (1.0 + np.std(np.diff(series))) if len(series) > 1 else 1.0
        agreement = 1.0 / (1.0 + np.mean(np.abs(series - target)))
        return 0.45 * corr + 0.30 * smooth + 0.25 * agreement
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


def cdpca_ga(rows: Sequence[dict]) -> Dict:
    data, signals, time = _matrix(rows)
    features = _features(data)
    scaler = StandardScaler().fit(features)
    z = scaler.transform(features)
    components = max(1, min(z.shape[0], z.shape[1], 8))
    pca = PCA(n_components=components, random_state=2026).fit(z)
    projected = pca.transform(z)
    healthy_count = max(3, min(len(rows), int(len(rows) * 0.2)))
    healthy = projected[:healthy_count]
    # Candidate feature HI values and GA fusion weights.
    candidate = np.exp(-0.18 * np.sqrt(np.mean(((projected - healthy.mean(0)) / (healthy.std(0) + 1e-6)) ** 2, axis=1)))
    weights = _ga_weights(projected, candidate)
    fused = np.clip(projected @ weights, -10, 10)
    lo, hi = np.percentile(fused, 5), np.percentile(fused, 95)
    health = np.clip(1.0 - (fused - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    return {"algorithm": "CDPCA-GA", "level": "component", "health_index": float(health[-1]),
            "hi_sequence": [round(float(x), 6) for x in health],
            "time_sequence": [round(float(x), 6) for x in time], "signals": signals,
            "feature_count": int(features.shape[1]), "pca_components": components,
            "explained_variance": round(float(pca.explained_variance_ratio_.sum()), 6),
            "ga_weights": [round(float(x), 6) for x in weights],
            "source": "platform_health.algorithms.cdpca_ga", "status": "development"}


def ae_gmm(rows: Sequence[dict]) -> Dict:
    data, signals, time = _matrix(rows)
    features = _features(data)
    scaler = StandardScaler().fit(features)
    z = scaler.transform(features)
    healthy_count = max(4, min(len(rows), int(len(rows) * 0.2)))
    train = z[:healthy_count]
    latent_dim = max(1, min(8, train.shape[1] // 2, train.shape[0]))
    if train.shape[0] < 5 or train.shape[1] < 2:
        latent = train[:, :latent_dim]
        encoded = z[:, :latent_dim]
        ae_backend = "linear_fallback"
    else:
        hidden = max(latent_dim + 1, min(32, train.shape[1]))
        ae = MLPRegressor(hidden_layer_sizes=(hidden, latent_dim, hidden), activation="relu",
                          solver="lbfgs", max_iter=500, random_state=2026)
        ae.fit(train, train)
        # Extract the encoder half of the trained symmetric autoencoder.
        def encode(values):
            hidden_values = np.maximum(0.0, values @ ae.coefs_[0] + ae.intercepts_[0])
            return np.maximum(0.0, hidden_values @ ae.coefs_[1] + ae.intercepts_[1])
        latent, encoded, ae_backend = encode(train), encode(z), "MLP-autoencoder"
    try:
        gmm = GaussianMixture(n_components=max(1, min(3, len(latent))), covariance_type="full", random_state=2026).fit(latent)
        nll = -gmm.score_samples(encoded)
    except ValueError:
        nll = np.sum((encoded - latent.mean(0)) ** 2, axis=1)
    base = nll[:healthy_count]
    health = np.exp(-np.clip((nll - base.mean()) / (base.std() + 1e-6), 0, 20) / 3.0)
    return {"algorithm": "AE-GMM", "level": "component", "health_index": float(np.clip(health[-1], 0, 1)),
            "hi_sequence": [round(float(np.clip(x, 0, 1)), 6) for x in health],
            "time_sequence": [round(float(x), 6) for x in time], "signals": signals,
            "feature_count": int(features.shape[1]), "latent_dim": int(latent_dim),
            "gmm_components": int(max(1, min(3, len(latent)))), "backend": ae_backend,
            "source": "platform_health.algorithms.ae_gmm", "status": "development"}


def gcn_rbd(component_results: Sequence[Dict], component_ids: Sequence[str]) -> Dict:
    if not component_results:
        raise ValueError("GCN/RBD 至少需要一个部件健康评估结果")
    sequences = [np.asarray(item.get("hi_sequence", [item["health_index"]]), dtype=float) for item in component_results]
    length = min(len(sequence) for sequence in sequences)
    if length < 1:
        raise ValueError("部件健康评估没有有效时间序列")
    values_by_time = np.asarray([sequence[:length] for sequence in sequences], dtype=float)
    values = values_by_time[:, -1]
    n = len(values)
    # Physical adjacency: neighbouring components exchange state; self-loop is required.
    adjacency = np.eye(n) + (np.ones((n, n)) - np.eye(n)) * (1.0 / max(1, n - 1))
    degree = adjacency.sum(axis=1)
    normalized = adjacency / np.sqrt(np.outer(degree, degree))
    gcn_sequence, rbd_sequence, system_sequence = [], [], []
    for column in values_by_time.T:
        hidden = np.maximum(0.0, normalized @ column)
        gcn_hi = float(np.clip(1.0 / (1.0 + np.mean(1.0 - hidden)), 0, 1))
        rbd_hi = float(np.prod(np.clip(column, 0, 1)))
        system_hi = float(np.clip(0.5 * gcn_hi + 0.5 * rbd_hi, 0, 1))
        gcn_sequence.append(gcn_hi)
        rbd_sequence.append(rbd_hi)
        system_sequence.append(system_hi)
    system_hi = system_sequence[-1]
    times = component_results[0].get("time_sequence", list(range(length)))[:length]
    return {"algorithm": "GCN+RBD", "level": "system", "health_index": round(system_hi, 6),
            "hi_sequence": [round(float(x), 6) for x in system_sequence],
            "time_sequence": [round(float(x), 6) for x in times],
            "component_health": {str(k): round(float(v), 6) for k, v in zip(component_ids, values)},
            "component_hi_sequences": {str(k): [round(float(x), 6) for x in seq[:length]] for k, seq in zip(component_ids, values_by_time)},
            "gcn_health_index": round(gcn_sequence[-1], 6), "rbd_serial_health_index": round(rbd_sequence[-1], 6),
            "gcn_hi_sequence": [round(float(x), 6) for x in gcn_sequence],
            "rbd_serial_hi_sequence": [round(float(x), 6) for x in rbd_sequence],
            "adjacency": normalized.round(6).tolist(), "source": "platform_health.algorithms.gcn_rbd",
            "status": "development", "limitations": ["GCN/RBD 当前为无监督结构融合，需冻结训练权重后再作为正式模型"]}
