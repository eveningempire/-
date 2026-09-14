# src/visualization.py

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch

# Use default Latin fonts (no CJK required)
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
})


def _time_axis_labels(seq_len: int, sample_dt: float, max_ticks: int = 9):
    step = max(1, seq_len // max_ticks)
    idx = np.arange(0, seq_len, step)
    labels = [f"{i * sample_dt:.1f}" for i in idx]
    return idx, labels


def plot_confusion_matrix(cm, class_names, save_path=None, title="Confusion Matrix"):
    n = len(class_names)
    fig_w = max(10, n * 0.65)
    fig_h = max(8, n * 0.55)
    plt.figure(figsize=(fig_w, fig_h))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_time_attention_heatmap(
    attention_matrix,
    save_path=None,
    title="Diagnosis head: time-time attention",
    sample_dt=0.125,
):
    """
    Diagnosis attention head: (seq_len, seq_len).
    Row = query time step; column = key time step the model attends to.
    """
    seq_len = attention_matrix.shape[0]
    tick_idx, tick_labels = _time_axis_labels(seq_len, sample_dt)

    plt.figure(figsize=(9, 7))
    sns.heatmap(
        attention_matrix,
        cmap="hot",
        cbar_kws={"label": "Attention weight"},
        xticklabels=False,
        yticklabels=False,
    )
    plt.xticks(tick_idx + 0.5, tick_labels, rotation=0)
    plt.yticks(tick_idx + 0.5, tick_labels, rotation=0)
    plt.title(title)
    plt.xlabel("Key time — attended history (s)")
    plt.ylabel("Query time — current step (s)")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_feature_time_attention(
    importance_matrix,
    feature_names,
    save_path=None,
    title="Input attribution: feature vs time",
    sample_dt=0.125,
    feature_labels=None,
):
    """
    importance_matrix: (num_features, seq_len), values in [0, 1] after row min-max normalization.
    Row = telemetry feature; column = time index in the window.
    """
    if importance_matrix is None:
        print("Warning: feature-time matrix is None, skip plot.")
        return

    seq_len = importance_matrix.shape[1]
    tick_idx, tick_labels = _time_axis_labels(seq_len, sample_dt)
    ylabels = feature_labels or feature_names

    plt.figure(figsize=(12, max(7, len(feature_names) * 0.22)))
    sns.heatmap(
        importance_matrix,
        cmap="RdYlBu_r",
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Normalized attribution (row min-max)"},
        xticklabels=False,
        yticklabels=ylabels,
    )
    plt.xticks(tick_idx + 0.5, tick_labels, rotation=0)
    plt.title(title)
    plt.xlabel("Time within window (s)")
    plt.ylabel("Telemetry feature")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_diagnosis_panel(
    time_attn,
    feat_time_imp,
    feature_names,
    save_path,
    title,
    sample_dt=0.125,
    feature_labels=None,
):
    """Side-by-side: diagnosis time attention + feature-time attribution (min-max normalized per row)."""
    seq_len = time_attn.shape[0]
    tick_idx, tick_labels = _time_axis_labels(seq_len, sample_dt)
    ylabels = feature_labels or feature_names

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))

    sns.heatmap(
        time_attn,
        ax=axes[0],
        cmap="hot",
        cbar_kws={"label": "Attention weight"},
        xticklabels=False,
        yticklabels=False,
    )
    axes[0].set_xticks(tick_idx + 0.5)
    axes[0].set_xticklabels(tick_labels)
    axes[0].set_yticks(tick_idx + 0.5)
    axes[0].set_yticklabels(tick_labels)
    axes[0].set_title("Diagnosis head: which past times matter")
    axes[0].set_xlabel("Key time (s)")
    axes[0].set_ylabel("Query time (s)")

    sns.heatmap(
        feat_time_imp,
        ax=axes[1],
        cmap="RdYlBu_r",
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Normalized attribution (row min-max)"},
        xticklabels=False,
        yticklabels=ylabels,
    )
    axes[1].set_xticks(tick_idx + 0.5)
    axes[1].set_xticklabels(tick_labels)
    axes[1].set_title("Feature contribution over time (y-axis: feature [ratio%])")
    axes[1].set_xlabel("Time within window (s)")
    axes[1].set_ylabel("Feature (contribution %)")

    fig.suptitle(title, fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


@torch.enable_grad()
def compute_integrated_gradients(
    model,
    src,
    target_class: int,
    device,
    baseline=None,
    n_steps: int = 50,
):
    """
    Integrated Gradients attribution for the predicted class logit.
    
    IG satisfies the completeness axiom: sum of attributions = F(x) - F(baseline).
    This directly measures "which input features drove the current prediction".
    
    Args:
        model: TCNTransformerDiagnosis model
        src: (1, seq_len, input_dim) input tensor (CPU or device)
        target_class: int, class index to explain
        device: torch device
        baseline: (1, seq_len, input_dim) baseline input, defaults to zeros
        n_steps: int, number of interpolation steps (more = more accurate)
    
    Returns:
        (num_features, seq_len) numpy array of attributions
    """
    model.eval()
    src_dev = src.to(device)
    
    # Baseline: zeros (standard for StandardScaler-normalized inputs)
    if baseline is None:
        baseline = torch.zeros_like(src_dev)
    else:
        baseline = baseline.to(device)
    
    # Interpolation path: baseline -> input
    alphas = torch.linspace(0, 1, n_steps + 1).to(device)
    
    # Accumulate gradients along the path
    grads_sum = torch.zeros_like(src_dev)
    
    for alpha in alphas:
        x_interp = baseline + alpha * (src_dev - baseline)
        x_interp = x_interp.detach().requires_grad_(True)
        
        model.zero_grad(set_to_none=True)
        logits, _ = model(x_interp, return_diagnosis_attn=True)
        score = logits[0, target_class]
        score.backward()
        
        if x_interp.grad is not None:
            grads_sum += x_interp.grad.detach()
    
    # Average gradients and multiply by (input - baseline)
    avg_grads = grads_sum / (n_steps + 1)
    attributions = avg_grads * (src_dev - baseline)
    
    return attributions.squeeze(0).cpu().numpy().T.astype(np.float32)


def normalize_feature_attribution(feat_imp: np.ndarray) -> tuple:
    """
    对 (num_features, seq_len) 归因矩阵做归一化。
    
    全局 min-max 归一化：除以全局最大值，使最大值 = 1。
    - 保留特征间的贡献差异：重要特征整行更亮
    - 不重要的特征整行暗淡
    - 色标范围 [0, 1]，对比度明显
    
    Returns:
        (normalized_matrix, feat_ratios):
        - normalized_matrix: (num_features, seq_len)，全局归一化到 [0, 1]
        - feat_ratios: (num_features,)，每个特征占总贡献的比例
    """
    abs_imp = np.abs(feat_imp)
    
    # 全局归一化：除以最大值，使最亮的 cell = 1
    global_max = abs_imp.max()
    if global_max > 1e-12:
        normalized = abs_imp / global_max
    else:
        normalized = abs_imp
    
    # 特征贡献占比（用原始 abs_imp 计算）
    feat_total = abs_imp.sum(axis=1)
    total = feat_total.sum()
    feat_ratios = feat_total / (total + 1e-12) if total > 1e-12 else feat_total
    
    return normalized, feat_ratios


@torch.enable_grad()
def compute_feature_time_importance(model, src, target_class: int, device):
    """
    Gradient x input attribution for the predicted (or true) class logit.
    src: (1, seq_len, input_dim)
    Returns (num_features, seq_len) numpy array.
    
    Note: This is a simple approximation. For more accurate attributions,
    use compute_integrated_gradients() instead.
    """
    model.eval()
    x = src.detach().to(device).float().requires_grad_(True)
    logits, _ = model(x, return_diagnosis_attn=True)
    score = logits[0, int(target_class)]
    model.zero_grad(set_to_none=True)
    if x.grad is not None:
        x.grad.zero_()
    score.backward()

    attr = (x.grad.abs() * x.detach().abs()).squeeze(0).cpu().numpy()
    return attr.T.astype(np.float32)


def summarize_top_attribution(
    feat_time_imp,
    feature_names,
    feature_physics: dict,
    sample_dt: float,
    top_k: int = 5,
):
    """Return human-readable lines for the evidence report."""
    lines = []
    # 先按特征总贡献排序，再在每个特征内找时间峰值
    n_feat, seq_len = feat_time_imp.shape
    feat_total = feat_time_imp.sum(axis=1)
    top_feat_idx = np.argsort(feat_total)[-top_k:][::-1]
    
    for f in top_feat_idx:
        name = feature_names[f]
        phys = feature_physics.get(name, name)
        ratio = feat_total[f]
        # 找该特征贡献最大的时间点
        t_peak = int(np.argmax(feat_time_imp[f]))
        peak_val = feat_time_imp[f, t_peak]
        t_sec = t_peak * sample_dt
        lines.append(
            f"  - {name} ({phys}): ratio={ratio:.1%}, peak @ t={t_sec:.2f}s ({peak_val:.4f})"
        )
    return lines


def write_heatmap_guide(save_path: str, sample_dt: float, window_sec: float):
    text = f"""# How to read diagnosis heatmaps

Window length: ~{window_sec:.1f} s (after downsampling, dt={sample_dt:.3f} s per point).

## 1. Time-time attention (diagnosis head, left panel)

- **Axes**: row = query time, column = key time (seconds within the window).
- **Color**: brighter = the diagnosis head pays more attention to that (query, key) pair.
- **Meaning**: shows *when* the model looks at *which past moments* inside the 16 s segment.
- **Typical use**: a bright column at the end means the fault signature is recent; a band along the diagonal means gradual evolution; off-diagonal bright spots mean the model links a later query to an earlier key instant (delayed effect).

## 2. Feature-time attribution (right panel, Integrated Gradients + Feature Normalization)

- **Axes**: row = telemetry channel (X, Vx, FT, S1, ...), column = time (s).
- **Color**: brighter = stronger influence of that feature at that time.
- **Method**: Integrated Gradients — accumulates gradients along the path from baseline (zeros) to input. Then **normalized per feature** so each row's total brightness reflects that feature's contribution ratio (all features sum to 1).
- **Meaning**: 
  - **Across rows (features)**: which feature is most important overall? Brighter rows = higher contribution ratio.
  - **Within a row (time)**: when does this feature matter most? Brighter columns = key time steps.
- **Physics mapping**: links the decision to **measurable channels** (thrust FT, attitude Roll/Pitch/Yaw, actuator states S1–S17, etc.).
- **Note**: compare brightness **across features** directly — this is the key advantage over raw attribution plots.

## 3. Mapping to rocket physics

| Group | Features | Fault relevance |
|-------|----------|-----------------|
| Trajectory | X, Y, H, Vx, Vy, Vz | Indirect — motion response to propulsion / control faults |
| Propulsion | FT, S1–S9, S11–S17 | Direct — pump, valve, combustion, nozzle faults |
| Attitude | Roll, Pitch, Yaw | Control loop — TVC, RCS, grid fin, gyro faults |
| Actuator cmds | S10_X/Y/Z | TVC / thrust vectoring |

Always read attribution together with the true/predicted fault class on the figure title.
"""
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)


def generate_evidence_report(
    sample_idx,
    true_class_id,
    pred_class_id,
    time_attn_matrix,
    feat_time_imp,
    feat_ratios,
    feature_names,
    class_names_en,
    feature_physics,
    sample_dt,
    save_path=None,
):
    lines = [
        f"=== Evidence report — sample {sample_idx} ===",
        f"True class:  [{true_class_id}] {class_names_en[true_class_id]}",
        f"Pred class:  [{pred_class_id}] {class_names_en[pred_class_id]}",
        "",
        "--- Feature contribution ranking ---",
    ]
    top_feat_idx = np.argsort(feat_ratios)[-8:][::-1]
    for f in top_feat_idx:
        if feat_ratios[f] < 1e-6:
            continue
        name = feature_names[f]
        phys = feature_physics.get(name, name)
        lines.append(f"  {name} ({phys}): {feat_ratios[f]:.1%}")

    lines.append("\n--- Top feature-time peaks ---")
    lines.extend(
        summarize_top_attribution(
            feat_time_imp, feature_names, feature_physics, sample_dt, top_k=8
        )
    )

    lines.append("\n=== End ===")
    report_text = "\n".join(lines)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(report_text)
    return report_text
