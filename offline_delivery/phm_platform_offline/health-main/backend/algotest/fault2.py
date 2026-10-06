import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
import os, json

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import lightgbm as lgb
import joblib

import glob
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)



def extract_features_from_df(df, channels=None, fft_k=5):
    """
    df: DataFrame 包含 Time, P1..P17 等列
    channels: 列名列表,若 None 则自动找 P1..P17
    返回:1D numpy array 特征向量
    """
    if channels is None:
        channels = [f'P{i}' for i in range(1, 18)]

    feats = []
    for ch in channels:
        if ch not in df.columns:
            # 如果某列缺失,补 NaN -> 转为 0
            x = np.zeros(1)
        else:
            x = pd.to_numeric(df[ch], errors='coerce').fillna(0).values

        # 时域特征
        feats.append(np.mean(x))
        feats.append(np.std(x))
        feats.append(np.var(x))
        feats.append(np.max(x))
        feats.append(np.min(x))
        feats.append(np.ptp(x))  # range
        feats.append(np.median(x))
        feats.append(np.percentile(x, 75) - np.percentile(x, 25))  # IQR
        feats.append(skew(x))
        feats.append(kurtosis(x))
        feats.append(np.sqrt(np.mean(x**2)))  # RMS
        feats.append(np.sum(x**2))  # energy
        # 一阶差分
        if len(x) > 1:
            d = np.diff(x)
            feats.append(np.mean(d))
            feats.append(np.std(d))
        else:
            feats.append(0.0)
            feats.append(0.0)

        # 频域:FFT 前 k 大幅值
        if len(x) > 1:
            fftm = np.abs(np.fft.rfft(x))
            # 排除直流成分? 可以保留
            topk = np.sort(fftm)[-fft_k:]
            # 若长度不足,补零
            if len(topk) < fft_k:
                topk = np.pad(topk, (fft_k - len(topk), 0), 'constant')
            feats.extend(topk.tolist())
        else:
            feats.extend([0.0] * fft_k)

    return np.nan_to_num(np.array(feats, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)



def build_dataset_from_folder(folder_path):
    X = []
    y = []

    # 遍历每个子文件夹(文件夹名就是标签)
    folder_list = sorted([d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))])

    for folder_name in folder_list:
         # 检查文件夹名是否是数字
        if not folder_name.isdigit():
            print(f"跳过非数字标签文件夹: {folder_name}")
            continue
        label = int(folder_name)  # 文件夹名就是故障标签
        sub_folder_path = os.path.join(folder_path, folder_name)

        # 遍历子文件夹下的所有 csv 文件
        csv_files = sorted([f for f in os.listdir(sub_folder_path) if f.endswith('.csv')])
        for csv_file in csv_files:
            file_path = os.path.join(sub_folder_path, csv_file)
            df = pd.read_csv(file_path)

            # 这里不再从 flag 提取 label,直接用文件夹名
            feats = extract_features_from_df(df)
            X.append(feats)
            y.append(label)

    X = np.vstack(X)
    y = np.array(y, dtype=int)
    return X, y




# =========================
# 1. 读取并构建特征数据集
# =========================
folder_path = r"D:\pythonpro\datacsv"
X, y = build_dataset_from_folder(folder_path)

# =========================
# 2. 划分训练/测试集 7:3
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# =========================
# 3. 构建 Pipeline(RFE + GBDT)
# =========================
gb_estimator = GradientBoostingClassifier(random_state=42)

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('rfe', RFE(estimator=gb_estimator)),
    ('clf', GradientBoostingClassifier(random_state=42))
])

# =========================
# 4. 定义参数网格(调特征数量 + GBDT 参数)
# =========================
#param_grid = {
#   'rfe__n_features_to_select': [20, 40, 60],   # 特征数按你提取维度调整
#   'clf__n_estimators': [100, 200],
#   'clf__learning_rate': [0.05, 0.1, 0.2],
#   'clf__max_depth': [3, 4],
#  'clf__min_samples_split': [2, 5]
#}

param_grid = {
  'rfe__n_features_to_select': [40],   # 特征数按你提取维度调整
  'clf__n_estimators': [100],
  'clf__learning_rate': [0.1],
  'clf__max_depth': [3],
 'clf__min_samples_split': [5]
}

grid_search = GridSearchCV(
    estimator=pipe,
    param_grid=param_grid,
    scoring='accuracy',
    cv=3,
    n_jobs=-1,
    verbose=2
)

# =========================
# 5. 训练模型
# =========================
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_

print("\n✅ 最优参数组合:")
print(grid_search.best_params_)

# 保存模型
joblib.dump(best_model,  r'D:\pythonpro\health\backend\algotest\fault_gbdt_model.pkl')
print("✅ 模型已保存为 fault_gbdt_model.pkl")

# =========================
# 6. 模型评估
# =========================
y_pred = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)

print("\n=== 评估结果 ===")
print(f"准确率: {accuracy_score(y_test, y_pred):.4f}")
print(f"精确率: {precision_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
print(f"召回率: {recall_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
print(f"F1分数: {f1_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")

print("\n=== 混淆矩阵 ===")
print(confusion_matrix(y_test, y_pred))

print("\n=== 分类报告 ===")
print(classification_report(y_test, y_pred, digits=4))


