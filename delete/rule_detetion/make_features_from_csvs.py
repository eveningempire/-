# ===============================================
# make_features_from_csvs.py
# ===============================================
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# ---------- 你的特征函数（已扩充版） ----------
from rule_mining_csv_win import compute_signal_features   # 就是上一步我们改好的函数

# ---------- 配置 ----------
HEALTH_CSV   = Path(r"C:\Users\megan\Desktop\故障模式挖掘 - 副本\normal\Health_processed_signals.csv")
FAULT_DIR    = Path(r"C:\Users\megan\Desktop\故障模式挖掘 - 副本\fault_data")     # 里面放若干 *.csv
CSV_GLOB     = "*.csv"

WINDOWING    = True
WIN_SIZE     = 100           # 与 rule_mining 一致
WIN_STEP     = 20

EXPECTED_SIGNALS = None      # 自动发现所有列
IGNORE_COLUMNS   = []        # 先不忽略

OUT_FEATS  = "features.parquet"
OUT_LABELS = "labels.parquet"

# -------------------------------------------------

def read_one_csv(path: Path, label: str, file_id: str) -> List[Dict]:
    """对单个 CSV 做滑窗并提特征，返回 dict 列表"""
    df = pd.read_csv(path)

    # 信号列筛选
    if EXPECTED_SIGNALS is None:
        sig_cols = [c for c in df.columns if c not in IGNORE_COLUMNS]
    else:
        sig_cols = [c for c in EXPECTED_SIGNALS if c in df.columns]

    records = []
    if WINDOWING:
        start_idx = np.arange(0, len(df) - WIN_SIZE + 1, WIN_STEP)
        for s in start_idx:
            e = s + WIN_SIZE
            feats = {}
            for col in sig_cols:
                feats_col = compute_signal_features(df[col].iloc[s:e].values)
                # 加前缀保持唯一性
                feats.update({f"{col}__{k}": v for k, v in feats_col.items()})
            feats["label"]   = label
            feats["file_id"] = file_id
            records.append(feats)
    else:  # 整个文件当一个样本
        feats = {}
        for col in sig_cols:
            feats_col = compute_signal_features(df[col].values)
            feats.update({f"{col}__{k}": v for k, v in feats_col.items()})
        feats["label"]   = label
        feats["file_id"] = file_id
        records.append(feats)

    return records


def main():
    all_records = []

    # -------- 1) 健康 CSV --------
    print("Processing healthy data …")
    all_records += read_one_csv(
        HEALTH_CSV,
        label="Normal",
        file_id=HEALTH_CSV.stem          # e.g. "Health_processed_signals"
    )

    # -------- 2) 故障 CSVs --------
    print("Processing fault data …")
    for csv_path in tqdm(sorted(FAULT_DIR.glob(CSV_GLOB))):
        # 假设文件名就是故障名，例如  BreakLu_processed_signals.csv
        fault_name = csv_path.stem.split("_")[0]     # "BreakLu"
        all_records += read_one_csv(
            csv_path,
            label=fault_name,
            file_id=csv_path.stem
        )

    # -------- 3) 整理并保存 --------
    df_all = pd.DataFrame(all_records)
    feature_cols = [c for c in df_all.columns if c not in ("label", "file_id")]
    df_feats  = df_all[feature_cols]
    df_labels = df_all[["label", "file_id"]]

    df_feats.to_parquet(OUT_FEATS, index=False)
    df_labels.to_parquet(OUT_LABELS, index=False)

    print(f"Saved {len(df_all)} windows → {OUT_FEATS}, {OUT_LABELS}")


if __name__ == "__main__":
    main()
