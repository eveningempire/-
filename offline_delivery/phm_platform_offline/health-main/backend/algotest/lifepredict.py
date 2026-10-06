import os
import pandas as pd
import numpy as np
from deap import base, creator, tools, algorithms
import pywt
from PyEMD import EMD
import matplotlib.pyplot as plt
from scipy.stats import kurtosis, skew, entropy, linregress
from scipy.signal import stft
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import joblib
import json
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline


# ---------------------------
# 1) 基本特征提取函数(时域/频域/时频域)
# ---------------------------
def safe_mean(a):
    return float(np.mean(a)) if len(a) > 0 else 0.0

def value_time_correlation(x):
    time = np.arange(len(x))
    return abs(np.corrcoef(time, x)[0, 1])

def monotonicity(x):
    x = np.array(x)
    diffs = np.diff(x)
    signs = np.sign(diffs)
    mono_score = np.sum(signs == -1) / len(signs)  # 递增占比
    return mono_score  # 越接近1说明越单调递增,越接近0说明递减


def robustness_std(x, noise_level=0.05, trials=10):
    x = np.array(x)
    x = (x - np.mean(x)) / (np.std(x) + 1e-6)  # 归一化
    baseline_std = np.std(x)
    deviations = []
    for _ in range(trials):
        noise = np.random.normal(0, noise_level, size=len(x))
        x_noisy = x + noise
        diff = np.linalg.norm(x_noisy - x)
        deviations.append(diff)
    return 1 / (np.mean(deviations) + 1e-6)  # 越大代表鲁棒性越好


def consistency_single_curve(x, window=10):
    """
    单条HI序列的一致性:多个局部斜率方向是否一致
    """
    x = np.array(x)
    n = len(x)
    directions = []
    for i in range(0, n - window + 1, window):
        segment = x[i:i + window]
        time = np.arange(len(segment))
        slope, _, _, _, _ = linregress(time, segment)
        directions.append(np.sign(slope))
    directions = np.array(directions)
    if len(directions) == 0:
        return 1.0
    same_direction_ratio = np.sum(directions == directions[0]) / len(directions)
    return same_direction_ratio


def sum_nature(x):
    return 0.25*value_time_correlation(x)+0.25*monotonicity(x)+0.25*robustness_std(x)+0.25*consistency_single_curve(x, window=10)

def extract_time_features(signal):
    # signal: 1D numpy array
    if len(signal) == 0:
        return [0.0]*15
    s = signal.astype(float)
    mean = np.mean(s)
    std = np.std(s)
    max_val = np.max(s)
    min_val = np.min(s)
    rms = np.sqrt(np.mean(s ** 2)) if len(s)>0 else 0.0
    # 使用 scipy 的峭度/偏度(可能产生 NaN,当数据几乎相同)
    try:
        kurt = float(kurtosis(s))
    except:
        kurt = 0.0
    try:
        skewness = float(skew(s))
    except:
        skewness = 0.0
    crest = max_val / (rms + 1e-12)
    mad = np.mean(np.abs(s - mean))
    iqr = np.percentile(s, 75) - np.percentile(s, 25)
    zcr = float(((s[:-1] * s[1:]) < 0).sum()) / max(1, len(s))
    sig_range = max_val - min_val
    shape_factor = rms / (np.mean(np.abs(s)) + 1e-12)
    impulse_factor = max_val / (np.mean(np.abs(s)) + 1e-12)
    clearance_factor = max_val / (np.mean(np.sqrt(np.abs(s))) + 1e-12)

    feats = [
        mean, std, max_val, min_val, rms, kurt, skewness, crest,
        #mad, iqr, zcr, sig_range, shape_factor, impulse_factor, clearance_factor
    ]
    feats = np.array(feats, dtype=float)
    feats[~np.isfinite(feats)] = 0.0
    return feats.tolist()

def extract_freq_features(signal, fs=1.0):
    s = np.asarray(signal, dtype=float)
    N = len(s)
    if N < 2:
        return [0.0]*7
    # FFT
    spectrum = np.fft.fft(s)
    mag = np.abs(spectrum[:N//2])
    freqs = np.fft.fftfreq(N, d=1.0/fs)[:N//2]
    mag_sum = np.sum(mag) + 1e-12
    centroid = float(np.sum(freqs * mag) / mag_sum) if np.any(mag) else 0.0
    energy = float(np.sum(mag**2))
    max_mag = float(np.max(mag)) if mag.size>0 else 0.0
    dominant_freq = float(freqs[np.argmax(mag)]) if mag.size>0 else 0.0
    mean_sq_freq = float(np.sum((freqs**2) * mag) / mag_sum) if np.any(mag) else 0.0
    bandwidth = float(np.sqrt(np.sum((freqs - centroid)**2 * mag) / mag_sum)) if np.any(mag) else 0.0

    psd = mag**2
    psd_norm = psd / (np.sum(psd) + 1e-12)
    try:
        spec_entropy = float(entropy(psd_norm))
    except:
        spec_entropy = 0.0

    feats = np.array([energy, max_mag, dominant_freq, centroid, mean_sq_freq, bandwidth, spec_entropy], dtype=float)
    feats[~np.isfinite(feats)] = 0.0
    return feats.tolist()

def extract_timefreq_features(signal, fs=1.0):
    s = np.asarray(signal, dtype=float)
    if len(s) < 2:
        return [0.0]*6

    # 小波包能量(取 level=3 的节点能量比的平均)
    try:
        wp = pywt.WaveletPacket(data=s, wavelet='db4', mode='symmetric', maxlevel=3)
        nodes = wp.get_level(3, order='freq')
        wp_energies = [np.sum(np.square(node.data)) for node in nodes] if nodes else [0.0]
        wp_total = np.sum(wp_energies) + 1e-12
        wp_energy_ratio = float(np.mean([e/wp_total for e in wp_energies]))
    except Exception:
        wp_energy_ratio = 0.0

    # STFT 概要统计
    try:
        f, t_seg, Zxx = stft(s, fs=fs, nperseg=min(128, len(s)))
        stft_mag = np.abs(Zxx)
        stft_mean_spec = float(np.mean(np.mean(stft_mag, axis=1))) if stft_mag.size>0 else 0.0
        stft_energy = float(np.mean(np.sum(stft_mag**2, axis=1))) if stft_mag.size>0 else 0.0
    except Exception:
        stft_mean_spec = 0.0
        stft_energy = 0.0

    # HHT (EMD -> 瞬时频率均值与能量熵)
    try:
        emd = EMD()
        imfs = emd(s)
    except Exception:
        imfs = []

    hht_freqs = []
    hht_energies = []
    for imf in imfs:
        imf = np.asarray(imf, dtype=float)
        if imf.size == 0 or np.all(imf == 0):
            continue
        # 用希尔伯特近似求瞬时频率:这里使用相位差近似(简化)
        try:
            analytic = imf + 1j*np.imag(imf)
            phase = np.unwrap(np.angle(analytic))
            inst_freq = np.diff(phase) * fs / (2.0*np.pi)
            if len(inst_freq) > 0:
                hht_freqs.append(np.mean(np.abs(inst_freq)))
        except Exception:
            pass
        hht_energies.append(np.sum(imf**2))

    if len(hht_energies) == 0:
        hht_entropy = 0.0
        hht_freq_mean = 0.0
    else:
        hht_total = np.sum(hht_energies) + 1e-12
        try:
            hht_entropy = float(entropy([e/hht_total for e in hht_energies]))
        except Exception:
            hht_entropy = 0.0
        hht_freq_mean = float(np.mean(hht_freqs)) if len(hht_freqs)>0 else 0.0

    # 局部特征谱 LCS
    lcs_vals = []
    for imf in imfs:
        if len(imf) > 16:
            try:
                _, _, Zxx_imf = stft(imf, fs=fs, nperseg=64)
                local_max = np.max(np.abs(Zxx_imf), axis=0)
                lcs_vals.append(np.mean(local_max))
            except Exception:
                pass
    lcs = float(np.mean(lcs_vals)) if len(lcs_vals)>0 else 0.0

    feats = np.array([wp_energy_ratio, stft_mean_spec, stft_energy, hht_freq_mean, hht_entropy, lcs], dtype=float)
    feats[~np.isfinite(feats)] = 0.0
    return feats.tolist()

def extract_all_features(signal, fs=1.0):
    t = extract_time_features(signal)
    f = extract_freq_features(signal, fs)
    tf = extract_timefreq_features(signal, fs)
    #feats = np.array(t + f + tf, dtype=float)
    feats = np.array(t, dtype=float)
    feats[~np.isfinite(feats)] = 0.0

     # 3. 构造对应的特征名称列表
    FEATURE_NAMES = [ 
        # --- 时域特征 ---
        'mean','std','max','min','rms','kurt','skew','crest',
        #'mad','iqr','zcr','range','shape_factor','impulse_factor','clearance_factor',
        # --- 频域特征 ---
        #'energy','max_mag','dominant_freq','centroid','mean_sq_freq','bandwidth','spec_entropy',
        # --- 时频域特征 ---
       # 'wp_energy_ratio','stft_mean_spec','stft_energy','hht_freq_mean','hht_entropy','lcs'
    ]

    # 4. 生成字典形式便于在线检索
    feats_dict = {name: float(val) for name, val in zip(FEATURE_NAMES, feats)}

    return feats,feats_dict  # numpy array

# ---------------------------
# 2) 窗口化:滑动窗口,每次 step_sec 生成一帧特征
# ---------------------------
def sliding_window_features(df, signal_col='P1', time_col='Time', window_sec=2.0, step_sec=1.0, min_samples_in_window=8):
    """
    对一个 csv DataFrame 执行滑动窗口特征提取
    返回:
      windows_info: list of dict { 'start':, 'end':, 'center':, 'features': ndarray, 'rul': float }
    """
    times = df[time_col].astype(float).values
    sig = df[signal_col].astype(float).values
    rul_series = df['RUL'].astype(float).values if 'RUL' in df.columns else np.full_like(times, np.nan, dtype=float)

    t_min, t_max = float(np.min(times)), float(np.max(times))
    # window start positions: from t_min to t_max - window_sec (inclusive)
    starts = np.arange(t_min, t_max - 1e-9, step_sec)
    result = []

    for s in starts:
        e = s + window_sec
        # select rows in [s, e)
        mask = (times >= s) & (times < e)
        if np.sum(mask) < 1:
            # 如果窗口内没有数据,跳过或可以 pad
            continue
        window_sig = sig[mask]
        window_times = times[mask]
        window_rul = rul_series[mask]
        # 如果样本太少也可以选择跳过或仍然提特征(这里小于 min_samples_in_window 则仍计算但频域可能退化)
        # 估计 fs:取 median sampling rate within window
        if len(window_times) > 1:
            dt = np.diff(window_times)
            median_dt = np.median(dt)
            fs_est = 1.0 / (median_dt + 1e-12)
        else:
            fs_est = 1.0
        feats, _ = extract_all_features(window_sig, fs=fs_est)
        # 把 rul 赋值为窗口末端对应的 RUL(如果没有 RUL 列,用 nan)
        rul_value = float(window_rul[-1]) if len(window_rul)>0 and not np.isnan(window_rul[-1]) else (float(np.nan) if len(window_rul)>0 else float(np.nan))
        result.append({
            'start': float(s),
            'end': float(e),
            'center': float((s+e)/2.0),
            'features': feats,
            'rul': rul_value
        })
    return result

# ---------------------------
# 3) 对一个部件 (文件夹) 的所有 CSV 做批处理:提取所有窗口特征 -> Standardize -> PCA (取前5) -> 加权合成 HI -> 归一化
# ---------------------------
def process_component_folder(component_folder, signal_col='P1', time_col='Time',
                             window_sec=2.0, step_sec=1.0, top_k_pca=5, save_artifacts=True, out_folder=None):
    """
    返回:
      summary: {
         'files': {
             filename: {
                'windows': [{'center':..., 'HI':..., 'rul':...}, ...],
                'raw_features': ndarray (n_windows, n_feats) optional
             }, ...
         },
         'global_min': float,
         'global_max': float,
         'scaler_path': ... (if saved),
         'pca_path': ...
      }
    """
    all_windows = []  # each elem: dict with filename, center, features, rul
    filenames = sorted([f for f in os.listdir(component_folder) if f.endswith('.csv')])
    for fname in filenames:
        fp = os.path.join(component_folder, fname)
        df = pd.read_csv(fp)
        wf = sliding_window_features(df, signal_col=signal_col, time_col=time_col, window_sec=window_sec, step_sec=step_sec)
        for w in wf:
            all_windows.append({
                'file': fname,
                'center': w['center'],
                'features': w['features'],
                'rul': w['rul']
            })

    if len(all_windows) == 0:
        raise ValueError("没有提取到任何窗口特征,请检查 CSV 与列名")

    # 构造矩阵
    X = np.vstack([w['features'] for w in all_windows])  # shape (N_windows, n_features)
    y_rul = np.array([w['rul'] for w in all_windows], dtype=float)

    # 2. 标准化
    #scaler = StandardScaler()
    #X_scaled = scaler.fit_transform(X)

      # ====== 2. PCA 提取前5个主成分 ======

    #pca = PCA(n_components=min(top_k_pca, X.shape[1]))
    #pcs = pca.fit_transform(X)  # (N, 5)

    # ===== 2. 计算每个特征与RUL的相关性 =====

    # FEATURE_NAMES = [ 
    #     # --- 时域特征 ---
    #     'mean','std','max','min','rms','kurt','skew','crest',
    #     'mad','iqr','zcr','range','shape_factor','impulse_factor','clearance_factor',
    #     # --- 频域特征 ---
    #     'energy','max_mag','dominant_freq','centroid','mean_sq_freq','bandwidth','spec_entropy',
    #     # --- 时频域特征 ---
    #     'wp_energy_ratio','stft_mean_spec','stft_energy','hht_freq_mean','hht_entropy','lcs'
    # ]

    FEATURE_NAMES = [ 
        # --- 时域特征 ---
        'mean','std','max','min','rms','kurt','skew','crest',
        #'mad','iqr','zcr','range','shape_factor','impulse_factor','clearance_factor',
    ]
    correlations = []
    for i, fname in enumerate(FEATURE_NAMES):
        corr = np.corrcoef(X[:, i], y_rul)[0, 1]
        correlations.append((fname, corr))

    corr_df = pd.DataFrame(correlations, columns=['feature', 'corr'])
    corr_df['abs_corr'] = corr_df['corr'].abs()
    #这里只读取与剩余寿命正相关的特征
    #corr_df['abs_corr'] = corr_df['corr']
    corr_df = corr_df.sort_values('abs_corr', ascending=False)

    # 选择 top_k_pca 个最相关的特征
    top_features = corr_df.head(top_k_pca-1)
    print("[INFO] Top correlated features:")
    print(top_features)

     # ===== 3. 使用这些特征计算 HI =====
    selected_indices = [FEATURE_NAMES.index(f) for f in top_features['feature']]
    selected_X = X[:, selected_indices]

    print("Selected features order:", [FEATURE_NAMES[i] for i in selected_indices])

    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(selected_X)

    

    # 再用 PCA 压成一维,得到 HI_raw
    pca = PCA(n_components=1)
    HI_raw = pca.fit_transform(X_scaled).ravel()

    # 归一化
    global_min, global_max = HI_raw.min(), HI_raw.max()
    HI_norm = (HI_raw - global_min) / (global_max - global_min + 1e-8)
    #HI_norm = 1 - HI_norm

    #   # 标准化
    # scaler = StandardScaler()
    # X_scaled = scaler.fit_transform(selected_X)

    # # 再用 PCA 压成一维,得到 HI_raw
    # pca = PCA(n_components=1)
    # pcs = pca.fit_transform(X)  # shape (N_samples, 3)


    # # hi_combined 是所有窗口的前5主成分矩阵
    # hi_combined = pcs

    # # 初始化 DEAP
    # creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    # creator.create("Individual", list, fitness=creator.FitnessMax)
    # toolbox = base.Toolbox()
    # toolbox.register("attr_float", np.random.rand)
    # toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, pcs.shape[1])
    # toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # def evaluate(individual):
    #     weights = np.array(individual)
    #     weights /= (np.sum(weights) + 1e-8)
    #     hi_weighted = np.dot(hi_combined, weights)
    #     return (sum_nature(hi_weighted),)

    # toolbox.register("evaluate", evaluate)
    # toolbox.register("mate", tools.cxBlend, alpha=0.5)
    # toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
    # toolbox.register("select", tools.selTournament, tournsize=3)

    # pop = toolbox.population(n=50)
    # for _ in range(40):
    #     offspring = algorithms.varAnd(pop, toolbox, cxpb=0.8, mutpb=0.3)
    #     fits = list(map(toolbox.evaluate, offspring))
    #     for ind, fit in zip(offspring, fits):
    #         ind.fitness.values = fit
    #     pop = toolbox.select(offspring, k=len(pop))

    # best_ind = tools.selBest(pop, k=1)[0]
    # best_weights = np.array(best_ind)
    # best_weights /= (np.sum(best_weights) + 1e-8)

    # # ====== 4. 计算最终 HI 并归一化 ======
    # HI_raw = np.dot(hi_combined, best_weights)
    # global_min = float(np.min(HI_raw))
    # global_max = float(np.max(HI_raw))
    # HI_norm = (HI_raw - global_min) / (global_max - global_min + 1e-12)

    # ====== 5. 组织输出 ======
    #summary = {'files': {}, 'global_min': global_min, 'global_max': global_max}
    model_folder = out_folder
    os.makedirs(model_folder, exist_ok=True)

    joblib.dump(scaler, os.path.join(model_folder, 'scaler.pkl'))
    joblib.dump(pca, os.path.join(model_folder, 'pca.pkl'))

    best_weights = np.array([1])

    meta = {
        'weights': best_weights.tolist(),
        'global_min': global_min,
        'global_max': global_max
    }
    with open(os.path.join(model_folder, 'hi_meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"✅ 已保存 scaler.pkl、pca.pkl、hi_meta.json 到 {model_folder}")

    # ====== 6. 保存 HI 曲线与 RUL 到 CSV ======
    hi_df = pd.DataFrame({
        'RUL': y_rul,
        'HI_raw': HI_raw,
        'HI_norm': HI_norm
    })
    
    # 按 RUL 降序排序
    hi_df = hi_df.sort_values(by='RUL', ascending=False).reset_index(drop=True)

    csv_path = os.path.join(component_folder, 'hi.csv')
    hi_df.to_csv(csv_path, index=False)
    print(f"✅ 已保存 HI 与 RUL 数据到 {csv_path}")

    return hi_df



# ---------------------------
# 4) 在线预测函数(给定新CSV文件路径,加载保存的 scaler/pca/meta, 计算并归一化 HI)
# ---------------------------
def online_predict(csv_path, scaler_path, pca_path, meta_path,
                   signal_col='P1', time_col='Time', window_sec=2.0, step_sec=1.0):
    """
    返回:
      { 'windows': [ {'center':..., 'HI':..., 'HI_raw':..., 'rul':...}, ... ], 'pred_summary': ... }
    """
    scaler = joblib.load(scaler_path)
    pca = joblib.load(pca_path)
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    global_min = float(meta['global_min'])
    global_max = float(meta['global_max'])
    weights = np.array(meta.get('weights', []), dtype=float)
    if weights.size == 0:
        # fallback: equal weights
        weights = np.ones(pca.n_components_) / pca.n_components_

    df = pd.read_csv(csv_path)
    wf = sliding_window_features(df, signal_col=signal_col, time_col=time_col, window_sec=window_sec, step_sec=step_sec)
    if len(wf) == 0:
        return {'windows': []}

    X_local = np.vstack([w['features'] for w in wf])
    Xs = scaler.transform(X_local)
    pcs = pca.transform(Xs)  # shape (n_windows, k)
    HI_raw = np.dot(pcs, weights)
    HI_norm = (HI_raw - global_min) / (global_max - global_min + 1e-12)

    windows_out = []
    for i, w in enumerate(wf):
        windows_out.append({
            'center': w['center'],
            'HI': float(HI_norm[i]),
            'HI_raw': float(HI_raw[i]),
            'rul': float(w['rul']) if not np.isnan(w['rul']) else None
        })

    return {'windows': windows_out, 'global_min': global_min, 'global_max': global_max}

# ---------------------------
# 5) 简单示例/入口(修改路径后运行)
# ---------------------------
if __name__ == "__main__":
    # 修改为你某个部件文件夹路径
    component_folder = r"D:\pythonpro\datacsv\life\10"  # example
    out_folder = r"D:\pythonpro\health\backend\algotest\life\10"
    out = process_component_folder(component_folder,
                                   signal_col='P9',
                                   time_col='Time',
                                   window_sec=2.0,
                                   step_sec=1.0,
                                   top_k_pca=5,
                                   save_artifacts=True,
                                   out_folder=out_folder)
    # ====== 读取保存的 hi.csv ======
hi_csv_path = os.path.join(component_folder, 'hi.csv')
hi_df = pd.read_csv(hi_csv_path)

# ====== 绘制 HI_norm 曲线 ======
plt.figure(figsize=(8, 4))
plt.plot(hi_df['HI_norm'], label='HI_norm', color='blue')
plt.xlabel('Sample Index (Window)')
plt.ylabel('HI_norm')
plt.title('Health Indicator (HI_norm) Curve')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()
    