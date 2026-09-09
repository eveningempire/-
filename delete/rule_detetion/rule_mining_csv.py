
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob
import warnings
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, _tree
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# =========================
# ======== CONFIG =========
# =========================
class CONFIG:
    # Single CSV for normal data
    NORMAL_CSV: str = r"C:\Users\megan\Desktop\故障模式挖掘 - 副本\normal\Health_processed_signals.csv"
    # Folder containing many CSVs for faulty data (all categories mixed here)
    FAULT_DIR: str = r"C:\Users\megan\Desktop\故障模式挖掘 - 副本\fault_data"  # <- user requirement: put all faulty CSVs here
    # CSV glob pattern
    CSV_GLOB: str = "*.csv"
    # Expected signals (if None, will use columns union + inject w_command)
    EXPECTED_SIGNALS: Optional[List[str]] = ["Gimbal_i","GimbalSpeed_rpm","w_command","i","u","w"]
    # How to get class from a fault CSV:
    # 1) if the file has a column named 'fault' or 'label', use its first non-null value;
    # 2) otherwise infer from filename: take prefix before first '_' or '-'.
    INFER_FROM_FILENAME: bool = True
    # Constant value for injected w_command if column missing
    W_COMMAND_DEFAULT: float = 6000.0
    # Model file to save
    MODEL_FILE: str = "fault_classifier_dt_csv.joblib"
    # Random seed
    SEED: int = 42
    # DecisionTree hyperparameters
    DT_MAX_DEPTH: Optional[int] = 10
    DT_CLASS_WEIGHT: Optional[str] = "balanced"  # or None


# =========================
# ===== Feature logic =====
# =========================
def extract_features(data: Dict[str, List[float]], all_signals: List[str]) -> Dict[str, float]:
    """
    Mirror the user's feature extraction:
    - For each signal in all_signals:
        - if signal == 'w_command': create constant vector (CONFIG.W_COMMAND_DEFAULT)
        - if missing: fill zeros with same length as other columns
        - else: use the numeric column values
      Then compute: mean, std, max, min, range, skew, kurtosis, and gradient stats.
    """
    features = {}
    # Determine length using the first column
    first_len = len(next(iter(data.values()))) if data else 0

    for signal in all_signals:
        if signal == "w_command":
            signal_data = np.full(first_len, CONFIG.W_COMMAND_DEFAULT, dtype=np.float64)
        else:
            if signal not in data:
                signal_data = np.zeros(first_len, dtype=np.float64)
            else:
                # coerce to float64 and flatten
                arr = pd.to_numeric(pd.Series(data[signal]), errors="coerce").astype("float64").to_numpy().flatten()
                if np.isnan(arr).any():
                    arr = np.nan_to_num(arr, nan=0.0)
                signal_data = arr

        # basic stats
        features[f"{signal}_mean"] = float(np.mean(signal_data)) if signal_data.size else 0.0
        features[f"{signal}_std"] = float(np.std(signal_data)) if signal_data.size else 0.0
        features[f"{signal}_max"] = float(np.max(signal_data)) if signal_data.size else 0.0
        features[f"{signal}_min"] = float(np.min(signal_data)) if signal_data.size else 0.0
        features[f"{signal}_range"] = float(np.ptp(signal_data)) if signal_data.size else 0.0

        # skew / kurtosis (avoid warnings when variance==0 or too short)
        if signal_data.size < 3 or float(np.std(signal_data)) == 0.0:
            features[f"{signal}_skew"] = 0.0
            features[f"{signal}_kurtosis"] = 0.0
        else:
            features[f"{signal}_skew"] = float(skew(signal_data))
            features[f"{signal}_kurtosis"] = float(kurtosis(signal_data))

        # gradient stats
        if signal_data.size >= 2:
            grad = np.gradient(signal_data)
            features[f"{signal}_grad_mean"] = float(np.mean(grad))
            features[f"{signal}_grad_std"] = float(np.std(grad))
            features[f"{signal}_grad_max"] = float(np.max(grad))
            features[f"{signal}_grad_min"] = float(np.min(grad))
            features[f"{signal}_grad_range"] = float(np.ptp(grad))
        else:
            features[f"{signal}_grad_mean"] = 0.0
            features[f"{signal}_grad_std"] = 0.0
            features[f"{signal}_grad_max"] = 0.0
            features[f"{signal}_grad_min"] = 0.0
            features[f"{signal}_grad_range"] = 0.0

    return features


def discover_signals(normal_csv: str, fault_dir: str, csv_glob: str, expected: Optional[List[str]]) -> List[str]:
    if expected is not None and len(expected) > 0:
        sigs = list(expected)
    else:
        # union of columns from normal + a sample of fault CSVs
        sigs = []
        if os.path.isfile(normal_csv):
            try:
                df = pd.read_csv(normal_csv, nrows=5)
                sigs.extend(list(df.columns))
            except Exception:
                pass
        for path in glob.glob(os.path.join(fault_dir, csv_glob))[:10]:
            try:
                df = pd.read_csv(path, nrows=5)
                sigs.extend(list(df.columns))
            except Exception:
                continue
        sigs = sorted(set(sigs))
    # ensure w_command is present
    if "w_command" not in sigs:
        sigs.append("w_command")
    return sigs


def infer_category_from_df_or_name(df: pd.DataFrame, path: str) -> str:
    # 1) try from columns 'fault' or 'label'
    for col in ["fault", "label"]:
        if col in df.columns:
            val = df[col].dropna().astype(str)
            if len(val) > 0 and val.iloc[0].strip() != "":
                return val.iloc[0].strip()
    # 2) from filename prefix (before first '_' or '-')
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    parts = re.split(r"[_\-]", name)
    return parts[0] if parts and parts[0] else name


# =========================
# ===== Train & Rules =====
# =========================
def train_and_mine_rules():
    np.random.seed(CONFIG.SEED)

    # Discover signals
    all_signals = discover_signals(CONFIG.NORMAL_CSV, CONFIG.FAULT_DIR, CONFIG.CSV_GLOB, CONFIG.EXPECTED_SIGNALS)

    rows: List[Dict[str, float]] = []
    labels: List[int] = []
    # dynamic label maps
    label_to_fault: Dict[int, str] = {}
    fault_to_label: Dict[str, int] = {}

    # Normal = label 0
    curr_label = 0
    label_to_fault[curr_label] = "Normal"
    fault_to_label["Normal"] = curr_label

    # --- Load normal CSV ---
    if not os.path.isfile(CONFIG.NORMAL_CSV):
        warnings.warn(f"[WARN] Normal CSV not found: {CONFIG.NORMAL_CSV}")
    else:
        df = pd.read_csv(CONFIG.NORMAL_CSV)
        sample = df.to_dict(orient="list")
        feat = extract_features(sample, all_signals)
        rows.append(feat)
        labels.append(0)

    # --- Load fault CSVs (mixed categories in one folder) ---
    fault_files = sorted(glob.glob(os.path.join(CONFIG.FAULT_DIR, CONFIG.CSV_GLOB)))
    if not fault_files:
        warnings.warn(f"[WARN] No CSV files found in fault dir: {CONFIG.FAULT_DIR}")
    for fpath in fault_files:
        try:
            df = pd.read_csv(fpath)
        except Exception as e:
            print(f"[×] 读取失败 {fpath}: {e}")
            continue
        # determine category
        fault_name = infer_category_from_df_or_name(df, fpath)
        if fault_name not in fault_to_label:
            curr_label += 1
            fault_to_label[fault_name] = curr_label
            label_to_fault[curr_label] = fault_name
        feat = extract_features(df.to_dict(orient="list"), all_signals)
        rows.append(feat)
        labels.append(fault_to_label[fault_name])

    if not rows:
        raise RuntimeError("未收集到任何样本，请检查 normal/ 与 fault/ 下的 CSV 文件。")

    # build DataFrame
    data = pd.DataFrame(rows).fillna(0.0)
    data["label"] = labels

    # print class counts
    print("\n每个类别的样本数：")
    for lid, name in label_to_fault.items():
        cnt = int((data["label"] == lid).sum())
        print(f"- {name}: {cnt}")

    # split X/y & scale
    X = data.drop(columns=["label"])
    y = data["label"].astype(int)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    # train tree
    clf = DecisionTreeClassifier(max_depth=CONFIG.DT_MAX_DEPTH,
                                 class_weight=CONFIG.DT_CLASS_WEIGHT,
                                 random_state=CONFIG.SEED)
    clf.fit(Xs, y)

    # CV (only when min per-class >= 5)
    min_class_count = int(y.value_counts().min())
    if min_class_count >= 5:
        scores = cross_val_score(clf, Xs, y, cv=5)
        print(f"\n交叉验证平均准确率: {scores.mean():.3f}")
    else:
        print(f"\n跳过交叉验证：最小类别样本数仅为 {min_class_count}，不满足5折要求")

    # in-sample report
    y_pred = clf.predict(Xs)
    target_names = [label_to_fault[i] for i in sorted(label_to_fault.keys())]
    print("\n分类报告：")
    print(classification_report(y, y_pred, target_names=target_names, zero_division=0))
    print("混淆矩阵：")
    print(confusion_matrix(y, y_pred))

    # persist payload (include label maps and signals)
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

    # mine rules (one representative rule per class: the leaf with largest sample count)
    extract_rules(clf, X.columns.tolist(), label_to_fault)


def extract_rules(clf: DecisionTreeClassifier, feature_names: List[str], label_to_fault: Dict[int, str]) -> None:
    tree = clf.tree_
    rules_per_class: Dict[str, str] = {}
    sample_counts: Dict[str, int] = {}

    def recurse(node: int, path: List[str]):
        if tree.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_names[tree.feature[node]]
            thr = tree.threshold[node]
            left = path + [f"{name} <= {thr:.2f}"]
            right = path + [f"{name} > {thr:.2f}"]
            recurse(tree.children_left[node], left)
            recurse(tree.children_right[node], right)
        else:
            value = tree.value[node][0]
            class_idx = int(np.argmax(value))
            label = int(clf.classes_[class_idx])
            fault_name = label_to_fault.get(label, str(label))
            rule_text = "如果 " + " 且 ".join(path) + f"，则预测为：{fault_name}"
            count = int(np.sum(value))
            # keep the leaf with the most samples for this class
            if (fault_name not in rules_per_class) or (count > sample_counts.get(fault_name, 0)):
                rules_per_class[fault_name] = rule_text
                sample_counts[fault_name] = count

    recurse(0, [])

    # write to file
    with open("extracted_rules.txt", "w", encoding="utf-8") as f:
        for cls_name, rule in rules_per_class.items():
            f.write(f"{cls_name}:\n{rule}\n\n")
    print("规则已保存至 extracted_rules.txt")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    train_and_mine_rules()
