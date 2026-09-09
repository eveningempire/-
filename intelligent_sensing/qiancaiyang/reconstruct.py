import sys
from typing import List, Optional, Tuple

import cvxpy as cp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# =============================================================================
# Custom Functions (Copied from lib and utils)
# =============================================================================

ROUND_DECIMALS = 2
def set_seed(seed: int = 42):
    import random

    random.seed(seed)
    np.random.seed(seed)


# set_seed(42)


def dct_matrix(N: int) -> np.ndarray:
    """Generate an orthonormal DCT-II basis matrix."""
    k, n = np.meshgrid(np.arange(N), np.arange(N))
    Psi = np.sqrt(2 / N) * np.cos((np.pi * (2 * n + 1) * k) / (2 * N))
    Psi[:, 0] = np.sqrt(1 / N)
    return Psi


def basis_pursuit(y: np.ndarray, Phi_psi: np.ndarray) -> np.ndarray:
    """Solve the Basis Pursuit (BP) problem."""
    x = cp.Variable(Phi_psi.shape[1])
    objective = cp.Minimize(cp.norm1(x))
    constraints = [Phi_psi @ x == y]
    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.ECOS)
    return x.value


def basis_pursuit_denoising(y: np.ndarray, Phi_psi: np.ndarray, lambda_: float) -> np.ndarray:
    """Solve the Basis Pursuit Denoising (BPDN) problem."""
    x = cp.Variable(Phi_psi.shape[1])
    data_term = cp.multiply(0.5, cp.sum_squares(Phi_psi @ x - y))
    reg_term = cp.multiply(lambda_, cp.norm1(x))
    objective = cp.Minimize(data_term + reg_term)
    prob = cp.Problem(objective)
    prob.solve(solver=cp.ECOS)
    return x.value


def omp(y: np.ndarray, Phi_psi: np.ndarray, sparsity: int) -> np.ndarray:
    """Orthogonal Matching Pursuit with fixed sparsity."""
    from sklearn.linear_model import OrthogonalMatchingPursuit
    model = OrthogonalMatchingPursuit(n_nonzero_coefs=sparsity, fit_intercept=False)
    model.fit(Phi_psi, y)
    return model.coef_


def find_main_components_fusion(fft_result, freqs, energy_ratio=0.95, snr_factor=5):
    half_len = len(freqs) // 2
    if half_len > len(fft_result):
        half_len = len(fft_result)
    # breakpoint()
    offset = 1  # 忽略直流分量
    power_spectrum = np.abs(fft_result[offset:half_len]) ** 2
    noise_floor_estimate = np.median(power_spectrum)
    mad_threshold = snr_factor * noise_floor_estimate
    candidate_indices = power_spectrum > mad_threshold

    if not np.any(candidate_indices):
        return np.array([]), np.array([])

    candidate_power = power_spectrum[candidate_indices]
    candidate_freqs = freqs[offset:half_len][candidate_indices]
    candidate_original_indices = np.where(candidate_indices)[0]

    total_candidate_power = np.sum(candidate_power)
    sorted_indices = np.argsort(candidate_power)[::-1]
    sorted_candidate_power = candidate_power[sorted_indices]
    sorted_candidate_freqs = candidate_freqs[sorted_indices]
    sorted_candidate_original_indices = candidate_original_indices[sorted_indices]

    cumulative_energy_ratio = np.cumsum(sorted_candidate_power) / total_candidate_power

    try:
        cutoff_index = np.where(cumulative_energy_ratio >= energy_ratio)[0][0]
    except IndexError:
        sort_order = np.argsort(candidate_freqs)
        return candidate_freqs[sort_order], candidate_original_indices[sort_order]

    final_main_components = sorted_candidate_freqs[: cutoff_index + 1]
    final_main_components_indices = sorted_candidate_original_indices[: cutoff_index + 1]

    sort_order = np.argsort(final_main_components)
    final_main_components = final_main_components[sort_order]
    final_main_components_indices = final_main_components_indices[sort_order]
    final_main_components_indices += offset  # 调整回原始索引

    return final_main_components, final_main_components_indices


def get_aliasing_frequencies(original_freqs, sampling_freq):
    aliased_freqs = np.mod(original_freqs, sampling_freq)
    aliased_freqs = np.where(aliased_freqs > sampling_freq / 2, sampling_freq - aliased_freqs, aliased_freqs)
    return aliased_freqs


def fft_magnitude_to_signal_amplitude(fft_magnitude, signal_length, is_dc=False):
    if is_dc:
        return fft_magnitude / signal_length
    else:
        return 2 * fft_magnitude / signal_length


def optimize_phases_from_downsampled_signal(aliased_freqs, signal_amplitudes, downsampled_signal, t_axis, D):
    def signal_model(t, *phases):
        result = np.zeros_like(t, dtype=float)
        for i, (freq, amp) in enumerate(zip(aliased_freqs, signal_amplitudes)):
            if np.isclose(freq, 0, atol=1e-6):
                result += amp
            else:
                result += amp * np.cos(2 * np.pi * freq * t + phases[i])
        return D @ result

    p0 = np.zeros(len(aliased_freqs))
    try:
        params, _ = curve_fit(
            signal_model,
            t_axis,
            downsampled_signal,
            p0=p0,
            maxfev=10000,
            bounds=(-2 * np.pi, 2 * np.pi),
        )
        return params
    except Exception as e:
        print(f"Phase optimization failed: {e}")
        return p0


def add_gaussian_noise(signal, snr_db):
    if snr_db is None:
        return signal
    signal_power = np.mean(signal**2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise = np.random.normal(0, np.sqrt(noise_power), len(signal))
    return signal + noise


def compensate_residual(X_recon_fft, R_f, fs_high, fs_low):
    """
    残差回填：将低采样空间的频域残差 R(f) 映射并补充到高采样空间的频谱中。
    基于 Y(f) = (1/M) * sum(X_aliased) 的性质。
    """
    N_high = len(X_recon_fft)
    N_low = len(R_f)
    
    # 生成高频空间的频率轴
    f_high = np.fft.fftfreq(N_high, 1/fs_high)
    df_low = fs_low / N_low
    
    # 计算每个高频位置对应的混叠索引
    f_aliased = f_high - fs_low * np.round(f_high / fs_low)
    target_indices = np.round(f_aliased / df_low).astype(int) % N_low
    
    # 将残差补偿回高频频谱 (直接回填，不需要再除以 M，因为 Y 已包含 1/M)
    X_compensated = X_recon_fft + R_f[target_indices]
    
    return X_compensated


# =============================================================================
# Five Steps via Modular Functions
# =============================================================================


def estimate_dc_component(samples: np.ndarray) -> Tuple[float, np.ndarray]:
    """步骤1：直流估计"""
    dc_est = samples.mean()
    ac_signal = samples - dc_est
    return dc_est, ac_signal


def perform_sampling_rearrangement(signal: np.ndarray, seed: int = None) -> Tuple[np.ndarray, np.ndarray]:
    """步骤2：采样重排"""
    P = np.eye(len(signal))
    np.random.shuffle(P)
    rearranged_signal = P @ signal
    return rearranged_signal, P


def perceptual_reconstruction(
    rearranged_signal: np.ndarray,
    P: np.ndarray,
    D_uni: np.ndarray,
    N_ori: int,
    fs: int,
    target_fs: int,
    M: int,
    dc_est: float,
    method: str = "bpdn",
    **kwargs,
):
    """步骤3：感知重构"""
    N = len(rearranged_signal)
    Phi = np.random.randn(M, N) / np.sqrt(M)
    y = Phi @ rearranged_signal
    Psi = dct_matrix(N_ori)
    Theta = Phi @ P @ D_uni @ Psi

    # 根据配置选择重建算法
    if method == "bpdn":
        lambda_ = kwargs.get("lambda_", 0.001)
        x_rec_coeffs = basis_pursuit_denoising(y, Theta, lambda_)
    elif method == "bp":
        x_rec_coeffs = basis_pursuit(y, Theta)
    elif method == "omp":
        sparsity = kwargs.get("sparsity", 20)
        x_rec_coeffs = omp(y, Theta, sparsity)
    else:
        raise ValueError(f"未知的重建方法: {method}。可选: 'bpdn', 'bp', 'omp'")

    x_rec = Psi @ x_rec_coeffs
    x_rec += dc_est

    fft_reconstructed = np.fft.fft(x_rec)
    freqs_reconstructed = np.fft.fftfreq(len(x_rec), d=1 / fs)

    energy_ratio = 0.99
    snr_factor = 5

    _, fft_reconstructed_mc_indices = find_main_components_fusion(
        fft_reconstructed, freqs_reconstructed, energy_ratio, snr_factor
    )
    reconstructed_aliasing_freqs = get_aliasing_frequencies(
        freqs_reconstructed[fft_reconstructed_mc_indices], target_fs
    )
    reconstructed_magnitudes = np.abs(fft_reconstructed[fft_reconstructed_mc_indices])

    reconstructed_aliasing_dict = {}
    for freq, mag in zip(reconstructed_aliasing_freqs, reconstructed_magnitudes):
        f_round = np.round(freq, ROUND_DECIMALS)
        if f_round in reconstructed_aliasing_dict:
            reconstructed_aliasing_dict[f_round] += mag
        else:
            reconstructed_aliasing_dict[f_round] = mag

    return reconstructed_aliasing_dict, x_rec, fft_reconstructed, freqs_reconstructed


def frequency_screening(
    reconstructed_aliasing_dict: dict, 
    theoretical_frequencies: list, 
    target_fs: int, 
    original_signal_len: int,
    auto_discover_top_k: int = 0
):
    """
    步骤4：频率筛选（增强版）
    
    Args:
        reconstructed_aliasing_dict: 感知重构得到的混叠频率字典
        theoretical_frequencies: 预设的理论主频率列表
        target_fs: 目标采样率
        original_signal_len: 原始信号长度
        auto_discover_top_k: 自动发现除理论频率外的前K个强分量（设为0则只提取理论频率）
    """
    # 1. 提取理论频率分量
    selected_freqs = list(theoretical_frequencies)
    selected_freqs_aliased = [np.round(get_aliasing_frequencies(f, target_fs), ROUND_DECIMALS) for f in selected_freqs]

    # 2. 自动发现机制：寻找非理论频率的强分量
    if auto_discover_top_k > 0:
        # 排除已经匹配到的理论频率对应的混叠点
        remaining_candidates = {f: mag for f, mag in reconstructed_aliasing_dict.items() 
                              if f not in selected_freqs_aliased}
        # 按能量排序取前K个
        top_k_items = sorted(remaining_candidates.items(), key=lambda x: x[1], reverse=True)[:auto_discover_top_k]
        for f_extra, _ in top_k_items:
            # 注意：这里的发现是“盲发现”，我们假设它就在原位（或需要更复杂的逆映射）
            # 对于真实数据，可以直接将其加入重建列表
            selected_freqs.append(f_extra)
            selected_freqs_aliased.append(f_extra)

    # 3. 提取对应的幅值
    final_amplitudes = []
    final_freqs = []
    for f_orig, f_alias in zip(selected_freqs, selected_freqs_aliased):
        if f_alias in reconstructed_aliasing_dict:
            final_amplitudes.append(fft_magnitude_to_signal_amplitude(reconstructed_aliasing_dict[f_alias], original_signal_len))
            final_freqs.append(f_orig)
    
    return np.array(final_freqs), np.array(final_amplitudes)


def perform_signal_reconstruction(
    selected_freqs, selected_amplitudes, uniform_downsampled_signal, t_high_res, D_uni, dc_est
):
    """步骤5：信号重建"""
    optimized_phases = optimize_phases_from_downsampled_signal(
        selected_freqs, selected_amplitudes, uniform_downsampled_signal, t_high_res, D_uni
    )

    final_reconstructed_signal = np.zeros_like(t_high_res)
    for amp, freq, phase in zip(selected_amplitudes, selected_freqs, optimized_phases):
        final_reconstructed_signal += amp * np.cos(2 * np.pi * freq * t_high_res + phase)
    final_reconstructed_signal += dc_est

    return final_reconstructed_signal


# =============================================================================
# Main Reconstruction Function
# =============================================================================


def reconstruct_rearranged_signal(
    dc_val, frequencies, amplitudes, phases, fs=128, t_total=20, target_fs=8, snr_db=20, M=100, method="bpdn", plot_steps=False, do_compensation=False, **kwargs
):
    """
    重构重排后的信号。

    Args:
        dc_val (float): 直流分量。
        frequencies (list): 三个高频分量的频率。
        amplitudes (list): 三个高频分量的幅值。
        phases (list): 三个高频分量的相位。
        fs (int): 原始采样率。
        t_total (int): 总时长。
        target_fs (int): 目标采样率。
        snr_db (int): 信噪比。
        M (int): 测量数。
        method (str): 重建方法 ('bpdn', 'bp', 'omp')。
        plot_steps (bool): 是否绘制每一步的关键结果。
        **kwargs: 算法特定参数 (如 lambda_, sparsity)。

    Returns:
        list: 包含重建过程中关键变量的列表。
    """
    if plot_steps:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

    set_seed(1)

    t = np.linspace(0, t_total, fs * t_total, endpoint=False)
    signal_clean = dc_val + sum(
        amp * np.cos(2 * np.pi * f * t + phi) for amp, f, phi in zip(amplitudes, frequencies, phases)
    )

    signal = add_gaussian_noise(signal_clean, snr_db)

    downsample_factor = fs // target_fs
    D_uni = np.zeros((len(t) // downsample_factor, len(t)))
    for i in range(len(t) // downsample_factor):
        D_uni[i, i * downsample_factor] = 1

    uniform_downsampled_signal_with_dc = D_uni @ signal
    t_low = t[::downsample_factor]

    variables_to_save = [t_low, uniform_downsampled_signal_with_dc]

    # 步骤1：直流估计
    dc_est, uniform_downsampled_signal = estimate_dc_component(uniform_downsampled_signal_with_dc)
    print(f"  [Step 1] DC Component Estimated: {dc_est:.4f}")
    print(f"  [Step 1] Signal Shape (after DC removal): {uniform_downsampled_signal.shape}")

    if plot_steps:
        plt.figure(figsize=(12, 4))
        plt.plot(t_low, uniform_downsampled_signal_with_dc, label='欠采样信号 (含DC)', color='gray', alpha=0.5)
        plt.plot(t_low, uniform_downsampled_signal, label='去直流后 (AC)', color='blue')
        plt.title("步骤 1: 直流估计与移除")
        plt.xlabel("时间 (s)")
        plt.ylabel("幅值")
        plt.legend()
        # plt.show()

    # 步骤2：采样重排
    rearranged_signal, P = perform_sampling_rearrangement(uniform_downsampled_signal)
    print(f"  [Step 2] Rearrangement Complete.")
    print(f"  [Step 2] Rearranged Signal Shape: {rearranged_signal.shape}, P Shape: {P.shape}")

    if plot_steps:
        plt.figure(figsize=(12, 4))
        plt.plot(rearranged_signal, 'o-', markersize=2, label='重排信号')
        plt.title("步骤 2: 采样重排")
        plt.xlabel("索引")
        plt.ylabel("幅值")
        plt.legend()
        # plt.show()

    # 步骤3：感知重构
    N_ori = len(signal)
    reconstructed_aliasing_dict, x_rec, fft_reconstructed, freqs_reconstructed = perceptual_reconstruction(
        rearranged_signal, P, D_uni, N_ori, fs, target_fs, M, dc_est, method=method, **kwargs
    )
    print("  [Step 3] Perceptual Reconstruction Candidates:")
    print(f"  [Step 3] Reconstructed Signal Shape (x_rec): {x_rec.shape}")

    if plot_steps:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        ax1.plot(t, x_rec, label='感知重构信号 x_rec')
        ax1.set_title("步骤 3: 感知重构 (时域)")
        ax1.legend()
        
        ax2.plot(freqs_reconstructed[:len(freqs_reconstructed)//2], 
                 np.abs(fft_reconstructed[:len(freqs_reconstructed)//2]), label='重构频谱')
        ax2.set_yscale("log")
        ax2.set_title("步骤 3: 感知重构 (频域)")
        ax2.set_xlabel("频率 (Hz)")
        ax2.legend()
        plt.tight_layout()
        # plt.show()

    sorted_cands = sorted(reconstructed_aliasing_dict.items(), key=lambda x: x[1], reverse=True)
    for f_c, mag_c in sorted_cands[:3]:
        print(f"    Freq: {f_c:.4f} Hz, Mag: {mag_c:.4f}")

    # 步骤4：频率筛选
    selected_freqs, selected_amplitudes = frequency_screening(
        reconstructed_aliasing_dict, frequencies, target_fs, len(signal)
    )
    print("  [Step 4] Screened Frequencies & Amplitudes:")
    print(f"  [Step 4] Selected Frequencies Shape: {selected_freqs.shape}")
    for f_s, amp_s in zip(selected_freqs, selected_amplitudes):
        print(f"    Freq: {f_s:.4f} Hz, Amp: {amp_s:.4f}")

    # 步骤5：信号重建
    final_reconstructed_signal = perform_signal_reconstruction(
        selected_freqs, selected_amplitudes, uniform_downsampled_signal, t, D_uni, dc_est
    )
    print("  [Step 5] Signal Reconstruction Complete.")

    # --- 新增：计算低采样频域残差 R(f) ---
    # 1. 获取观测到的低采样信号的 FFT (Y_obs)
    Y_obs = np.fft.fft(uniform_downsampled_signal_with_dc)
    # 2. 将重构出的高分辨率信号通过采样算子 D_uni 折叠回低采样点
    y_recon_at_low = D_uni @ final_reconstructed_signal
    Y_recon = np.fft.fft(y_recon_at_low)
    # 3. 计算频域残差
    R_f = Y_obs - Y_recon
    
    # --- 新增：残差补偿逻辑 ---
    if do_compensation:
        print("  [Step 6] Applying Residual Compensation...")
        X_sparse_fft = np.fft.fft(final_reconstructed_signal)
        X_comp_fft = compensate_residual(X_sparse_fft, R_f, fs, target_fs)
        final_reconstructed_signal = np.fft.ifft(X_comp_fft).real
    
    # 将 R_f 存入结果字典中
    recon_metrics = {
        "rmse": np.sqrt(np.mean((signal - final_reconstructed_signal) ** 2)),
        "mae": np.mean(np.abs(signal - final_reconstructed_signal)),
        "cos_sim": np.dot(signal, final_reconstructed_signal) / (
            np.linalg.norm(signal) * np.linalg.norm(final_reconstructed_signal)
        ),
        "residual_f": R_f,  # 存储残差
        "Y_obs": Y_obs      # 存储观测值供后续分析
    }

    variables_to_save.extend([t, signal, final_reconstructed_signal])

    fft_original = np.fft.fft(signal)
    fft_final_reconstructed = np.fft.fft(final_reconstructed_signal)

    freqs_original = np.fft.fftfreq(len(signal), d=1 / fs)
    freqs_final_reconstructed = np.fft.fftfreq(len(final_reconstructed_signal), d=1 / fs)

    variables_to_save.extend(
        [
            freqs_original[: len(freqs_original) // 2],
            np.abs(fft_original[: len(freqs_original) // 2]),
            freqs_final_reconstructed[: len(freqs_final_reconstructed) // 2],
            np.abs(fft_final_reconstructed[: len(freqs_final_reconstructed) // 2]),
        ]
    )

    variables_to_save.append(recon_metrics)

    return variables_to_save

def run_real_data_experiment(
    signal_data: np.ndarray,
    target_fs: int = 20,
    samples_to_use: int = 200,
    fs_high: int = 160,
    M: int = 100,
    theoretical_freqs: Optional[List[float]] = None,
    method: str = "bpdn",
    plot_steps: bool = False,
    do_compensation: bool = False,
    **kwargs,
):
    if plot_steps:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

    # 如果传入的是 DataFrame 或 Series，取其值并扁平化
    if hasattr(signal_data, "values"):
        signal_data = signal_data.values
    signal_data = signal_data.flatten()

    # Configuration for Real Data
    if samples_to_use < 1 or samples_to_use > len(signal_data):
        samples_to_use = len(signal_data)
    signal_segment = signal_data[:samples_to_use]
    downsample_factor = fs_high // target_fs  # 20

    # Check consistency
    if fs_high % target_fs != 0:
        print("Warning: fs_high is not a multiple of target_fs")

    N_ori = len(signal_segment) * downsample_factor
    t_high = np.linspace(0, len(signal_segment) / target_fs, N_ori, endpoint=False)
    t_low = np.linspace(0, len(signal_segment) / target_fs, len(signal_segment), endpoint=False)

    D_uni = np.zeros((len(signal_segment), N_ori))
    for i in range(len(signal_segment)):
        D_uni[i, i * downsample_factor] = 1

    print("\n--- Step 1: DC Estimation ---")
    dc_est, ac_signal = estimate_dc_component(signal_segment)
    print(f"Estimated DC Component: {dc_est:.4f}")
    print(f"Signal Shape (after DC removal): {ac_signal.shape}")

    if plot_steps:
        plt.figure(figsize=(12, 4))
        plt.plot(t_low, signal_segment, label='原始段', color='gray', alpha=0.5)
        plt.plot(t_low, ac_signal, label='去直流后 (AC)', color='blue')
        plt.title("步骤 1: 直流估计与移除")
        plt.xlabel("时间 (s)")
        plt.ylabel("幅值")
        plt.legend()
        # plt.show()

    print("\n--- Step 2: Sampling Rearrangement ---")
    rearranged_signal, P = perform_sampling_rearrangement(ac_signal, seed=42)
    print(f"Signal rearranged using random permutation matrix P (Shape: {P.shape})")
    print(f"Rearranged Signal Shape: {rearranged_signal.shape}")

    if plot_steps:
        plt.figure(figsize=(12, 4))
        plt.plot(rearranged_signal, 'o-', markersize=2, label='重排信号')
        plt.title("步骤 2: 采样重排")
        plt.xlabel("索引")
        plt.ylabel("幅值")
        plt.legend()
        # plt.show()

    print("\n--- Step 3: Perceptual Reconstruction ---")
    print(f"Solving {method.upper()} with M={M} measurements, N_high={N_ori}...")

    reconstructed_aliasing_dict, x_rec, fft_reconstructed, freqs_reconstructed = perceptual_reconstruction(
        rearranged_signal, P, D_uni, N_ori, fs_high, target_fs, M, dc_est, method=method, **kwargs
    )
    print(f"Reconstructed High-Res Signal Shape (x_rec): {x_rec.shape}")

    if plot_steps:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        ax1.plot(t_high, x_rec, label='感知重构信号 x_rec')
        ax1.set_title("步骤 3: 感知重构 (时域)")
        ax1.legend()
        
        ax2.plot(freqs_reconstructed[:len(freqs_reconstructed)//2], 
                 np.abs(fft_reconstructed[:len(freqs_reconstructed)//2]), label='重构频谱')
        ax2.set_yscale("log")
        ax2.set_title("步骤 3: 感知重构 (频域)")
        ax2.set_xlabel("频率 (Hz)")
        ax2.legend()
        plt.tight_layout()
        # plt.show()

    print("Top Reconstructed Aliased Component Candidates:")
    sorted_candidates = sorted(reconstructed_aliasing_dict.items(), key=lambda x: x[1], reverse=True)
    for f, mag in sorted_candidates[:5]:
        print(f"  Freq: {f:.4f} Hz, Mag: {mag:.4f}")

    print("\n--- Step 4: Frequency Screening ---")
    if theoretical_freqs is None:
        theoretical_freqs = [116.67, 233.33, 350.0]  # Example frequencies in Hz
    print(f"Applying theoretical filter with frequencies: {theoretical_freqs}")

    selected_freqs, selected_amplitudes = frequency_screening(
        reconstructed_aliasing_dict, theoretical_freqs, target_fs, N_ori, auto_discover_top_k=0,
    )
    print("Selected Components for Reconstruction:")
    for f, amp in zip(selected_freqs, selected_amplitudes):
        print(f"  Freq: {f:.4f} Hz, Amp: {amp:.4f}")

    print("\n--- Step 5: Signal Reconstruction ---")
    final_reconstructed_signal = perform_signal_reconstruction(
        selected_freqs, selected_amplitudes, ac_signal, t_high, D_uni, dc_est
    )

    if plot_steps:
        plt.figure(figsize=(12, 5))
        plt.plot(t_high, final_reconstructed_signal, label='最终重建信号 (高频)', alpha=0.8)
        plt.scatter(t_low, signal_segment, color='red', s=20, label='原始采样点 (低频)', zorder=5)
        plt.title("步骤 5: 最终信号重建结果对比")
        plt.xlabel("时间 (s)")
        plt.ylabel("幅值")
        plt.legend()
        # plt.show()

    print("Reconstruction complete.")
    print(f"Final Reconstructed Signal Shape: {final_reconstructed_signal.shape}")

    # 计算频域残差 R(f)
    Y_obs = np.fft.fft(signal_data) # signal_data 是传入的低采样观测序列
    # 将重建信号映射回低采样点
    y_recon_at_low = D_uni @ final_reconstructed_signal
    Y_recon = np.fft.fft(y_recon_at_low)
    R_f = Y_obs - Y_recon

    # --- 新增：残差补偿逻辑 ---
    if do_compensation:
        print("Applying Residual Compensation for Real Data...")
        X_sparse_fft = np.fft.fft(final_reconstructed_signal)
        X_comp_fft = compensate_residual(X_sparse_fft, R_f, fs_high, target_fs)
        final_reconstructed_signal = np.fft.ifft(X_comp_fft).real
        # 更新补偿后的重建频谱观测
        Y_recon = np.fft.fft(D_uni @ final_reconstructed_signal)

        if plot_steps:
            plt.figure(figsize=(12, 5))
            plt.plot(t_high, final_reconstructed_signal, label='补偿后重建信号 (高频)', alpha=0.8)
            plt.scatter(t_low, signal_segment, color='red', s=20, label='原始采样点 (低频)', zorder=5)
            plt.title("补偿后最终信号重建结果对比")
            plt.xlabel("时间 (s)")
            plt.ylabel("幅值")
            plt.legend()
            # plt.show()

    recon_info = {
        "residual_f": R_f,
        "Y_obs": Y_obs,
        "Y_recon": Y_recon,
        "ratio": np.sum(np.abs(R_f)**2) / np.sum(np.abs(Y_obs)**2),
    }

    return final_reconstructed_signal, recon_info

if __name__ == "__main__":
    # 示例用法
    dc_val = 1.3
    freqs = [51.3, 23.7, 37.1]
    amps = [1.0, 0.9, 0.8]
    phases = [np.pi / 5, np.pi / 4, np.pi / 3]

    results = reconstruct_rearranged_signal(dc_val, freqs, amps, phases, plot_steps=True)

    metrics = results[-1]
    print(f"重建完成。")
    print(f"RMSE: {metrics['rmse']:.4f}")
    print(f"MAE: {metrics['mae']:.4f}")
    print(f"Cosine Similarity: {metrics['cos_sim']:.4f}")

    # 可视化部分结果
    t = results[2]
    signal = results[3]
    reconstructed = results[4]

    plt.figure(figsize=(10, 4))
    plt.plot(t[:500], signal[:500], label="Original")
    plt.plot(t[:500], reconstructed[:500], "--", label="Reconstructed")
    plt.legend()
    plt.title("Reconstruction Detail (First 500 samples)")
    plt.show()
