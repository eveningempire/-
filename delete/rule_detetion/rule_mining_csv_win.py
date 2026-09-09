
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob
import warnings
from typing import Dict, List, Tuple, Optional

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, _tree
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import numpy as np
from typing import Dict, Optional
from scipy.stats import skew, kurtosis, entropy
from scipy.signal import welch
# =========================
# ======== CONFIG =========
# =========================
class CONFIG:
    # Data layout
    NORMAL_CSV: str = r"C:\Users\megan\Desktop\故障模式挖掘 - 副本\normal\Health_processed_signals.csv"  # single normal file
    FAULT_DIR: str = r"C:\Users\megan\Desktop\故障模式挖掘 - 副本\fault_data"                # many fault CSVs mixed here
    CSV_GLOB: str = "*.csv"

    # Signals
    EXPECTED_SIGNALS: Optional[List[str]] = ["RotorMotorCurrent","RotorMotorVoltage","RotorSpeed","GimbalMotorSpeed","GimbalMotorCurrentA","GimbalMotorCurrentC"]
    IGNORE_COLUMNS: List[str] = ["RotorMotorCurrentA","RotorMotorCurrentB","RotorMotorCurrentC","GimbalMotorCurrentB","FrictionTorque","GimbalMotorAngle","RotorSpeedCommand"]

    # Inject default for w_command when absent
    W_COMMAND_DEFAULT: float = 6000.0

    # Windowing (critical for more samples)
    USE_WINDOWING: bool = True
    WINDOW_SIZE: int = 100     # rows per window
    WINDOW_STEP: int = 20     # stride

    # Model and training
    MODEL_FILE: str = "fault_classifier_dt_csv.joblib"
    SEED: int = 42
    DT_MAX_DEPTH: Optional[int] = 8
    DT_CLASS_WEIGHT: Optional[str] = "balanced"
    DT_MIN_SAMPLES_LEAF: int = 3           # avoid tiny leaves

    # Rule mining
    MIN_LEAF_SUPPORT: int = 5             # at least this many samples reach the leaf
    MIN_LEAF_PURITY: float = 0.8           # dominant class proportion at leaf
    TOPK_RULES_PER_CLASS: int = 5          # export top-K rules per class by support

    # Class inference from fault CSV
    INFER_FROM_FILENAME: bool = True       # else uses 'fault' or 'label' column if present


# =========================
# ===== Feature logic =====
# =========================
def _coerce_numeric_series(s: pd.Series) -> np.ndarray:
    arr = pd.to_numeric(s, errors="coerce").astype("float64").to_numpy()
    return np.nan_to_num(arr, nan=0.0)



def compute_signal_features(values: np.ndarray,
                            fs: Optional[float] = None   # 采样频率，缺省则不计算频域特征
                           ) -> Dict[str, float]:
    """
    计算一维信号的统计、梯度、时域高阶、可选频域特征。
    新增特征键不会破坏旧代码的读取；下游若不需要可忽略。
    """
    if values.ndim != 1:
        values = values.reshape(-1)

    n = values.size
    if n == 0:   # 全部返回 0
        return {k: 0.0 for k in (
            "mean", "std", "max", "min", "range",
            "skew", "kurt",
            "rms", "ptp", "crest_factor", "impulse_factor", "shape_factor",
            "grad_mean", "grad_std", "grad_max", "grad_min", "grad_range",
            "dom_freq", "spec_entropy", "spec_centroid"
        )}

    # ----------- 时域基础统计 -----------
    v_mean = float(np.mean(values))
    v_std  = float(np.std(values))
    v_max  = float(np.max(values))
    v_min  = float(np.min(values))
    v_rng  = float(v_max - v_min)
    v_rms  = float(np.sqrt(np.mean(values ** 2)))
    v_ptp  = float(np.ptp(values))

    if v_std == 0.0 or n < 3:
        v_skew, v_kurt = 0.0, 0.0
    else:
        v_skew = float(skew(values, bias=False))
        v_kurt = float(kurtosis(values, bias=False))

    # 时域派生因子
    crest_factor   = v_max / v_rms if v_rms else 0.0
    impulse_factor = v_max / (abs(v_mean) + 1e-9)
    shape_factor   = v_rms / (abs(v_mean) + 1e-9)

    # ----------- 一阶梯度统计 -----------
    if n >= 2:
        g = np.gradient(values.astype("float64"))
        g_mean = float(np.mean(g))
        g_std  = float(np.std(g))
        g_max  = float(np.max(g))
        g_min  = float(np.min(g))
        g_rng  = float(g_max - g_min)
    else:
        g_mean = g_std = g_max = g_min = g_rng = 0.0

    # ----------- 频域特征（可选） -----------
    dom_freq = spec_entropy = spec_centroid = 0.0
    if fs is not None and n >= 4:
        f, Pxx = welch(values.astype("float64"), fs=fs, nperseg=min(256, n))
        if Pxx.sum() > 0:
            dom_freq      = float(f[np.argmax(Pxx)])              # 主频
            Pxx_norm      = Pxx / Pxx.sum()
            spec_entropy  = float(entropy(Pxx_norm))              # 谱熵
            spec_centroid = float((f * Pxx).sum() / Pxx.sum())    # 谱质心

    return {
        # 时域基础
        "mean": v_mean, "std": v_std, "max": v_max, "min": v_min, "range": v_rng,
        "skew": v_skew, "kurt": v_kurt,
        # 新增时域高阶
        "rms": v_rms, "ptp": v_ptp,
        "crest_factor": crest_factor,
        "impulse_factor": impulse_factor,
        "shape_factor": shape_factor,
        # 梯度特征
        "grad_mean": g_mean, "grad_std": g_std,
        "grad_max": g_max, "grad_min": g_min, "grad_range": g_rng,
        # 频域特征（若 fs=None 则返回 0）
        "dom_freq": dom_freq,
        "spec_entropy": spec_entropy,
        "spec_centroid": spec_centroid,
    }

FEATURE_SUFFIXES = [
    "mean","std","max","min","range","skew","kurt",
    "grad_mean","grad_std","grad_max","grad_min","grad_range","rms","ptp","crest_factor","impulse_factor","shape_factor"
]

def extract_features_from_df(df: pd.DataFrame, all_signals: List[str]) -> Dict[str, float]:
    df = df.copy()
    df.columns = [str(c) for c in df.columns]
    if CONFIG.IGNORE_COLUMNS:
        df = df.drop(columns=[c for c in CONFIG.IGNORE_COLUMNS if c in df.columns], errors="ignore")

    nrows = len(df)
    feats: Dict[str, float] = {}
    for sig in all_signals:
        if sig == "w_command":
            values = np.full((nrows,), CONFIG.W_COMMAND_DEFAULT, dtype="float64")
        elif sig in df.columns:
            values = _coerce_numeric_series(df[sig])
        else:
            values = np.zeros((nrows,), dtype="float64")
        stats = compute_signal_features(values)
        for suf in FEATURE_SUFFIXES:
            feats[f"{sig}_{suf}"] = stats[suf]
    return feats

def extract_rules_topk(clf: DecisionTreeClassifier,
                       feature_names: List[str],
                       label_to_fault: Dict[int, str],
                       min_support: int = 10,
                       min_purity: float = 0.7,
                       topk: int = 3) -> None:
    from sklearn.tree import _tree
    tree = clf.tree_
    leaves = []  # each: dict(path, support, label, purity)

    def recurse(node: int, path: List[str]):
        if tree.feature[node] != _tree.TREE_UNDEFINED:
            fname = feature_names[tree.feature[node]]
            thr = tree.threshold[node]
            recurse(tree.children_left[node],  path + [f"{fname} <= {thr:.4f}"])
            recurse(tree.children_right[node], path + [f"{fname} > {thr:.4f}"])
        else:
            counts = tree.value[node][0]
            support = int(np.sum(counts))
            cls_idx = int(np.argmax(counts))
            label = int(clf.classes_[cls_idx])
            purity = float(counts[cls_idx] / support) if support > 0 else 0.0
            leaves.append({"path": path, "support": support, "label": label, "purity": purity})

    recurse(0, [])

    # 先用用户阈值筛
    rules_by_class: Dict[int, List[dict]] = {}
    for leaf in leaves:
        if leaf["support"] >= min_support and leaf["purity"] >= min_purity:
            rules_by_class.setdefault(leaf["label"], []).append(leaf)

    # 每类按 support->purity 排序取 Top-K
    for lbl in list(rules_by_class.keys()):
        rules_by_class[lbl].sort(key=lambda d: (d["support"], d["purity"]), reverse=True)
        rules_by_class[lbl] = rules_by_class[lbl][:topk]

    # —— 兜底：若某类为空，逐步放宽阈值；仍为空则取“最大支持度”的 1 条 ——
    relaxed_note: Dict[int, str] = {}
    all_labels = set(int(c) for c in clf.classes_)
    for lbl in all_labels:
        if lbl in rules_by_class and len(rules_by_class[lbl]) > 0:
            continue
        # 渐进式放宽：支持度从 min_support 降到 3，纯度从 min_purity 降到 0.6（步长 0.05）
        picked: List[dict] = []
        for s in range(min_support, 2, -1):
            p = min_purity
            while p >= 0.60 and len(picked) < 1:
                cand = [leaf for leaf in leaves
                        if leaf["label"] == lbl and leaf["support"] >= s and leaf["purity"] >= p]
                cand.sort(key=lambda d: (d["support"], d["purity"]), reverse=True)
                if cand:
                    picked = cand[:1]
                    relaxed_note[lbl] = f"(relaxed: support≥{s}, purity≥{p:.2f})"
                    break
                p -= 0.05
            if picked:
                break
        # 仍然没有？那就直接选该类“支持度最大”的 1 条作为代表
        if not picked:
            cand = [leaf for leaf in leaves if leaf["label"] == lbl]
            cand.sort(key=lambda d: (d["support"], d["purity"]), reverse=True)
            if cand:
                picked = cand[:1]
                relaxed_note[lbl] = "(relaxed: best-support fallback)"
        if picked:
            rules_by_class[lbl] = picked

    # 写文件
    lines = []
    for lbl in sorted(all_labels):
        cname = label_to_fault.get(lbl, str(lbl))
        lines.append(f"{cname}:")
        if lbl in rules_by_class and len(rules_by_class[lbl]) > 0:
            for i, leaf in enumerate(rules_by_class[lbl], 1):
                cond = " 且 ".join(leaf["path"]) if leaf["path"] else "(无分裂条件)"
                tag = f" {relaxed_note.get(lbl,'')}" if lbl in relaxed_note else ""
                lines.append(f"  规则{i}[support={leaf['support']}, purity={leaf['purity']:.2f}]{tag}：如果 {cond}，则预测为：{cname}")
        else:
            lines.append("  (该类没有叶子规则，这通常不应出现)")
        lines.append("")
    with open("extracted_rules.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("规则已保存至 extracted_rules.txt")

# =========================
# ===== Data reading ======
# =========================
def make_windows(df: pd.DataFrame, size: int, step: int) -> List[pd.DataFrame]:
    if not CONFIG.USE_WINDOWING or size <= 0 or step <= 0 or len(df) == 0:
        return [df]
    out = []
    for start in range(0, max(1, len(df) - size + 1), step):
        end = start + size
        if end > len(df):
            break
        out.append(df.iloc[start:end])
    return out if out else [df]

def discover_signals(normal_csv: str, fault_dir: str) -> List[str]:
    if CONFIG.EXPECTED_SIGNALS:
        sigs = list(CONFIG.EXPECTED_SIGNALS)
    else:
        sigs = []
        if os.path.isfile(normal_csv):
            sigs.extend(list(pd.read_csv(normal_csv, nrows=5).columns))
        for p in glob.glob(os.path.join(fault_dir, CONFIG.CSV_GLOB))[:20]:
            try:
                sigs.extend(list(pd.read_csv(p, nrows=5).columns))
            except Exception:
                pass
        sigs = sorted(set(sigs))
    if "w_command" not in sigs:
        sigs.append("w_command")
    return sigs

def infer_category(df: pd.DataFrame, path: str) -> str:
    for col in ["fault","label"]:
        if col in df.columns:
            v = df[col].dropna().astype(str)
            if len(v) > 0 and v.iloc[0].strip() != "":
                return v.iloc[0].strip()
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    parts = re.split(r"[_\-]", name)
    return parts[0] if parts and parts[0] else name


# =========================
# === Train & Rule Mine ===
# =========================
def train_and_mine_rules():
    np.random.seed(CONFIG.SEED)

    all_signals = discover_signals(CONFIG.NORMAL_CSV, CONFIG.FAULT_DIR)
    rows: List[Dict[str, float]] = []
    labels: List[int] = []
    label_to_fault: Dict[int, str] = {0: "Normal"}
    fault_to_label: Dict[str, int] = {"Normal": 0}
    curr_label = 0

    # normal windows
    if os.path.isfile(CONFIG.NORMAL_CSV):
        ndf = pd.read_csv(CONFIG.NORMAL_CSV)
        wins = make_windows(ndf, CONFIG.WINDOW_SIZE, CONFIG.WINDOW_STEP)
        print(
            f"[WIN] Normal: len={len(ndf)}, size={CONFIG.WINDOW_SIZE}, step={CONFIG.WINDOW_STEP}, windows={len(wins)}")
        for win in wins:
            rows.append(extract_features_from_df(win, all_signals))
            labels.append(0)
    else:
        warnings.warn(f"[WARN] Normal CSV not found: {CONFIG.NORMAL_CSV}")

    # fault windows
    fpaths = sorted(glob.glob(os.path.join(CONFIG.FAULT_DIR, "**", CONFIG.CSV_GLOB), recursive=True))
    if not fpaths:
        warnings.warn(f"[WARN] No CSV found in {CONFIG.FAULT_DIR}")
    for fp in fpaths:
        try:
            df = pd.read_csv(fp)
        except Exception as e:
            print(f"[×] 读取失败 {fp}: {e}")
            continue
        cat = infer_category(df, fp)
        if cat not in fault_to_label:
            curr_label += 1
            fault_to_label[cat] = curr_label
            label_to_fault[curr_label] = cat

        wins = make_windows(df, CONFIG.WINDOW_SIZE, CONFIG.WINDOW_STEP)
        print(
            f"[WIN] {os.path.basename(fp)}: len={len(df)}, size={CONFIG.WINDOW_SIZE}, step={CONFIG.WINDOW_STEP}, windows={len(wins)}  -> class={cat}")
        for win in wins:
            rows.append(extract_features_from_df(win, all_signals))
            labels.append(fault_to_label[cat])

    if not rows:
        raise RuntimeError("未收集到任何样本。请检查 normal/ 与 fault/。")

    data = pd.DataFrame(rows).fillna(0.0)
    data["label"] = labels

    print("\n每个类别的样本数：")
    for lid, name in label_to_fault.items():
        print(f"- {name}: {int((data['label']==lid).sum())}")

    X = data.drop(columns=["label"])
    y = data["label"].astype(int)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    clf = DecisionTreeClassifier(
        max_depth=CONFIG.DT_MAX_DEPTH,
        class_weight=CONFIG.DT_CLASS_WEIGHT,
        min_samples_leaf=CONFIG.DT_MIN_SAMPLES_LEAF,
        random_state=CONFIG.SEED
    )
    clf.fit(Xs, y)

    # report
    min_count = int(y.value_counts().min())
    if min_count >= 5:
        from sklearn.model_selection import StratifiedKFold
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=CONFIG.SEED)
        from sklearn.model_selection import cross_val_score
        scores = cross_val_score(clf, Xs, y, cv=cv)
        print(f"\n5折交叉验证平均准确率: {scores.mean():.3f} ± {scores.std():.3f}")
    else:
        print(f"\n跳过交叉验证：最小类别样本数={min_count}")

    y_pred = clf.predict(Xs)
    target_names = [label_to_fault[i] for i in sorted(label_to_fault.keys())]
    print("\n分类报告：")
    print(classification_report(y, y_pred, target_names=target_names, zero_division=0))
    print("混淆矩阵：")
    print(confusion_matrix(y, y_pred))

    # persist
    payload = {
        "model": clf,
        "scaler": scaler,
        "features": X.columns.tolist(),
        "all_signals": all_signals,
        "label_to_fault": label_to_fault,
        "fault_to_label": fault_to_label,
        "config": {k: getattr(CONFIG, k) for k in dir(CONFIG) if k.isupper()}
    }
    joblib.dump(payload, CONFIG.MODEL_FILE)
    print(f"\n模型已保存为 {CONFIG.MODEL_FILE}")

    # rules
    extract_rules_topk(
        clf, X.columns.tolist(), label_to_fault,
        min_support=CONFIG.MIN_LEAF_SUPPORT,
        min_purity=CONFIG.MIN_LEAF_PURITY,
        topk=CONFIG.TOPK_RULES_PER_CLASS
    )


def extract_rules_topk2(clf: DecisionTreeClassifier,
                       feature_names: List[str],
                       label_to_fault: Dict[int, str],
                       min_support: int = 10,
                       min_purity: float = 0.7,
                       topk: int = 3) -> None:
    tree = clf.tree_
    leaves = []  # each: dict(path:list[str], support:int, label:int, purity:float)

    def recurse(node: int, path: List[str]):
        if tree.feature[node] != _tree.TREE_UNDEFINED:
            fname = feature_names[tree.feature[node]]
            thr = tree.threshold[node]
            recurse(tree.children_left[node], path + [f"{fname} <= {thr:.4f}"])
            recurse(tree.children_right[node], path + [f"{fname} > {thr:.4f}"])
        else:
            counts = tree.value[node][0]
            support = int(np.sum(counts))
            cls_idx = int(np.argmax(counts))
            label = int(clf.classes_[cls_idx])
            purity = float(counts[cls_idx] / support) if support > 0 else 0.0
            leaves.append({
                "path": path, "support": support, "label": label, "purity": purity
            })

    recurse(0, [])

    # group and filter
    rules_by_class: Dict[int, List[dict]] = {}
    for leaf in leaves:
        if leaf["support"] >= min_support and leaf["purity"] >= min_purity:
            rules_by_class.setdefault(leaf["label"], []).append(leaf)

    # sort by support desc, then purity desc
    for lbl in list(rules_by_class.keys()):
        rules_by_class[lbl].sort(key=lambda d: (d["support"], d["purity"]), reverse=True)
        rules_by_class[lbl] = rules_by_class[lbl][:topk]

    # write file
    lines = []
    for lbl in sorted(set([leaf["label"] for leaf in leaves])):
        cname = label_to_fault.get(lbl, str(lbl))
        lines.append(f"{cname}:")
        if lbl in rules_by_class and len(rules_by_class[lbl]) > 0:
            for i, leaf in enumerate(rules_by_class[lbl], 1):
                cond = " 且 ".join(leaf["path"]) if leaf["path"] else "(无分裂条件)"
                lines.append(f"  规则{i} [support={leaf['support']}, purity={leaf['purity']:.2f}]：如果 {cond}，则预测为：{cname}")
        else:
            lines.append("  (无满足阈值的规则；可降低 MIN_LEAF_SUPPORT/MIN_LEAF_PURITY 或增加样本)")
        lines.append("")
    with open("extracted_rules.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("规则已保存至 extracted_rules.txt")

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    train_and_mine_rules()
