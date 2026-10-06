import sys
from typing import List, Optional, Tuple

import cvxpy as cp
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# =============================================================================
# Custom Functions (Copied from lib and utils)
# =============================================================================


def set_seed(seed: int = 42):
    import random

    random.seed(seed)
    np.random.seed(seed)


def dct_matrix(N: int) -> np.ndarray:
    """Generate an orthonormal DCT-II basis matrix."""
    k, n = np.meshgrid(np.arange(N), np.arange(N))
    Psi = np.sqrt(2 / N) * np.cos((np.pi * (2 * n + 1) * k) / (2 * N))
    Psi[:, 0] = np.sqrt(1 / N)
    return Psi


def basis_pursuit_denoising(y: np.ndarray, Phi_psi: np.ndarray, lambda_: float) -> np.ndarray:
    """Solve the Basis Pursuit Denoising (BPDN) problem."""
    x = cp.Variable(Phi_psi.shape[1])
    data_term = cp.multiply(0.5, cp.sum_squares(Phi_psi @ x - y))
    reg_term = cp.multiply(lambda_, cp.norm1(x))
    objective = cp.Minimize(data_term + reg_term)
    prob = cp.Problem(objective)
    prob.solve(solver=cp.ECOS)
    return x.value


def find_main_components_fusion(fft_result, freqs, energy_ratio=0.95, snr_factor=5):
    half_len = len(freqs) // 2
    if half_len > len(fft_result):
        half_len = len(fft_result)

    power_spectrum = np.abs(fft_result[:half_len]) ** 2
    noise_floor_estimate = np.median(power_spectrum)
    mad_threshold = snr_factor * noise_floor_estimate
    candidate_indices = power_spectrum > mad_threshold

    if not np.any(candidate_indices):
        return np.array([]), np.array([])

    candidate_power = power_spectrum[candidate_indices]
    candidate_freqs = freqs[:half_len][candidate_indices]
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


# =============================================================================
# Main Reconstruction Function
# =============================================================================


def reconstruct_rearranged_signal(
    dc_val, frequencies, amplitudes, phases, fs=128, t_total=20, target_fs=8, snr_db=20, M=100
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

    Returns:
        list: 包含重建过程中关键变量的列表。
    """
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
    dc_est = uniform_downsampled_signal_with_dc.mean()
    uniform_downsampled_signal = uniform_downsampled_signal_with_dc - dc_est

    downsampled_t = t[::downsample_factor]
    variables_to_save = [downsampled_t, uniform_downsampled_signal_with_dc]

    P = np.eye(len(uniform_downsampled_signal))
    np.random.shuffle(P)
    rearranged_signal = P @ uniform_downsampled_signal

    N = len(rearranged_signal)
    N_ori = len(signal)

    Phi = np.random.randn(M, N) / np.sqrt(M)
    y = Phi @ rearranged_signal
    Psi = dct_matrix(N_ori)
    Theta = Phi @ P @ D_uni @ Psi

    x_rec_coeffs = basis_pursuit_denoising(y, Theta, lambda_=0.001)
    x_rec = Psi @ x_rec_coeffs
    x_rec += dc_est

    fft_original = np.fft.fft(signal)
    fft_reconstructed = np.fft.fft(x_rec)
    fft_uniform_ds = np.fft.fft(uniform_downsampled_signal)

    freqs_original = np.fft.fftfreq(len(signal), d=1 / fs)
    freqs_reconstructed = np.fft.fftfreq(len(x_rec), d=1 / fs)
    freqs_uniform_ds = np.fft.fftfreq(len(uniform_downsampled_signal), d=1 / target_fs)

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
        f_round = np.round(freq, 1)
        if f_round in reconstructed_aliasing_dict:
            reconstructed_aliasing_dict[f_round] += mag
        else:
            reconstructed_aliasing_dict[f_round] = mag

    selected_freqs = np.array(frequencies)
    selected_freqs_aliased = np.round(get_aliasing_frequencies(selected_freqs, target_fs), 1)

    selected_magnitudes = []
    for f in selected_freqs_aliased:
        if f in reconstructed_aliasing_dict:
            selected_magnitudes.append(reconstructed_aliasing_dict[f])
        else:
            selected_magnitudes.append(0.0)

    selected_magnitudes = np.array(selected_magnitudes)
    selected_amplitudes = fft_magnitude_to_signal_amplitude(selected_magnitudes, len(signal))
    optimized_phases = optimize_phases_from_downsampled_signal(
        selected_freqs, selected_amplitudes, uniform_downsampled_signal, t, D_uni
    )

    final_reconstructed_signal = np.zeros_like(t)
    for amp, freq, phase in zip(selected_amplitudes, selected_freqs, optimized_phases):
        final_reconstructed_signal += amp * np.cos(2 * np.pi * freq * t + phase)
    final_reconstructed_signal += dc_est

    variables_to_save.extend([t, signal, final_reconstructed_signal])

    fft_final_reconstructed = np.fft.fft(final_reconstructed_signal)
    freqs_final_reconstructed = np.fft.fftfreq(len(final_reconstructed_signal), d=1 / fs)

    variables_to_save.extend(
        [
            freqs_original[: len(freqs_original) // 2],
            np.abs(fft_original[: len(freqs_original) // 2]),
            freqs_final_reconstructed[: len(freqs_final_reconstructed) // 2],
            np.abs(fft_final_reconstructed[: len(freqs_final_reconstructed) // 2]),
        ]
    )

    rmse_error = np.sqrt(np.mean((signal - final_reconstructed_signal) ** 2))
    mae_error = np.mean(np.abs(signal - final_reconstructed_signal))
    cosine_similarity = np.dot(signal, final_reconstructed_signal) / (
        np.linalg.norm(signal) * np.linalg.norm(final_reconstructed_signal)
    )

    variables_to_save.append(
        {
            "rmse": rmse_error,
            "mae": mae_error,
            "cos_sim": cosine_similarity,
        }
    )

    return variables_to_save


if __name__ == "__main__":
    # 示例用法
    dc_val = 1.3
    freqs = [51.3, 23.7, 37.1]
    amps = [1.0, 0.9, 0.8]
    phases = [np.pi / 5, np.pi / 4, np.pi / 3]

    results = reconstruct_rearranged_signal(dc_val, freqs, amps, phases)

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
