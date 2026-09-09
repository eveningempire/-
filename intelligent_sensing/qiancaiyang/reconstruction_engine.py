import numpy as np
from scipy.interpolate import interp1d

class SignalReconstructor:
    """
    信号重建引擎
    集成基础插值与基于谱先验的引导重建算法
    """
    
    @staticmethod
    def linear_reconstruct(t_observed, y_observed, t_target):
        """线性插值重建"""
        return np.interp(t_target, t_observed, y_observed)

    @staticmethod
    def cubic_reconstruct(t_observed, y_observed, t_target):
        """三次样条插值重建"""
        f = interp1d(t_observed, y_observed, kind='cubic', fill_value="extrapolate")
        return f(t_target)

    def __init__(self, ref_data=None, ref_time=None, top_k=6):
        """
        初始化重建引擎
        
        参数:
            ref_data: 1Hz高采样率段的信号数据 (用于提取谱指纹)
            ref_time: 对应的时间戳
            top_k: 提取的主频点数量
        """
        self.ref_freqs = []
        self.ref_full_spectrum = None
        self.ref_start_time = 0
        
        if ref_data is not None and ref_time is not None:
            self.set_reference_segment(ref_data, ref_time, top_k)

    def set_reference_segment(self, data, time, top_k=6):
        """从参考段提取频谱分布特征"""
        if len(data) < 2:
            # 如果参考数据太少，无法计算FFT，则设置一个基本的直流分量先验
            self.ref_freqs = [0.01, 0.05] # 预设一些可能的波动频率
            self.ref_full_spectrum = (np.array([0, 0.01, 0.05]), np.array([1.0, 0.1, 0.1]))
            self.ref_start_time = time[0] if len(time) > 0 else 0
            return

        self.ref_start_time = time[0]
        n = len(data)
        # 获取基础频谱
        dt = (time[1]-time[0]) if n > 1 else 1.0
        freqs = np.fft.rfftfreq(n, d=dt)
        fft_vals = np.fft.rfft(data)
        mags = np.abs(fft_vals) / n
        self.ref_full_spectrum = (freqs, mags)
        
        # 提取 Top_K 主频
        mask = freqs > 0.002
        valid_freqs = freqs[mask]
        valid_mags = mags[mask]
        
        # 寻峰
        peaks = []
        for i in range(1, len(valid_mags)-1):
            if valid_mags[i] > valid_mags[i-1] and valid_mags[i] > valid_mags[i+1]:
                peaks.append(i)
        
        if len(peaks) > 0:
            peak_indices = np.array(peaks)
            top_idx = peak_indices[np.argsort(valid_mags[peak_indices])[::-1][:top_k]]
            self.ref_freqs = valid_freqs[top_idx]
        else:
            self.ref_freqs = valid_freqs[np.argsort(valid_mags)[::-1][:top_k]]

    def guided_spectral_reconstruct(self, t_observed, y_observed, t_target):
        """
        基于谱先验的引导式拟合重建 (核心优化算法)
        """
        if self.ref_full_spectrum is None:
            raise ValueError("引导式重建需要先通过 set_reference_segment 设置 1Hz 参考段")

        # 1. 扩充候选频率 (Top-K + 强背景分量)
        candidate_freqs = list(self.ref_freqs)
        fs_ref, mags_ref = self.ref_full_spectrum
        sort_idx = np.argsort(mags_ref)[::-1]
        for idx in sort_idx:
            f_cand = fs_ref[idx]
            if f_cand > 0.002 and not any(np.isclose(f_cand, f, atol=1e-4) for f in candidate_freqs):
                candidate_freqs.append(f_cand)
            if len(candidate_freqs) >= 25: break

        # 2. 构建谱加权岭回归
        A = self._build_design_matrix(t_observed, candidate_freqs)
        
        # 计算惩罚权重 (幅度越小惩罚越大)
        alphas = [0.001] # DC
        for f in candidate_freqs:
            w = mags_ref[np.argmin(np.abs(fs_ref - f))]
            alpha = 1.0 / (w + 1e-6)
            alphas.extend([alpha, alpha])
        
        reg = np.diag(alphas) * 0.001
        coeffs = np.linalg.solve(A.T @ A + reg, A.T @ y_observed)

        # 3. 目标生成与残差修正
        A_target = self._build_design_matrix(t_target, candidate_freqs)
        y_model = A_target @ coeffs
        
        # 确保 100% 映射采样点
        y_obs_pred = A @ coeffs
        residuals = y_observed - y_obs_pred
        y_res_interp = np.interp(t_target, t_observed, residuals)
        
        return y_model + y_res_interp

    def _build_design_matrix(self, t, freqs):
        A_list = [np.ones_like(t)]
        for f in freqs:
            A_list.append(np.cos(2 * np.pi * f * t))
            A_list.append(np.sin(2 * np.pi * f * t))
        return np.vstack(A_list).T

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    print("--- 信号重建模块测试周期 ---")
    
    # 1. 模拟理想连续信号 (作为真值)
    t_full = np.linspace(0, 300, 3000)
    y_true = 0.82 + 0.1 * np.cos(2*np.pi*0.025*t_full) + 0.15 * np.cos(2*np.pi*0.3*t_full)
    
    # 2. 模拟采样
    # 高采样率参考段 (0-60s)
    t_ref = t_full[t_full <= 60]
    y_ref = y_true[t_full <= 60]
    
    # 极低采样率段 (60-300s, 每64秒采一个点)
    t_sparse = np.arange(60, 301, 64)
    y_sparse = 0.82 + 0.1 * np.cos(2*np.pi*0.025*t_sparse) + 0.15 * np.cos(2*np.pi*0.3*t_sparse)
    
    # 目标重建时间轴
    t_target = t_full[t_full > 60]
    y_target_true = y_true[t_full > 60]

    # 3. 使用引擎进行重建
    engine = SignalReconstructor(y_ref, t_ref)
    
    res_linear = engine.linear_reconstruct(t_sparse, y_sparse, t_target)
    res_cubic = engine.cubic_reconstruct(t_sparse, y_sparse, t_target)
    res_guided = engine.guided_spectral_reconstruct(t_sparse, y_sparse, t_target)

    # 4. 可视化
    plt.figure(figsize=(14, 6))
    plt.plot(t_target, y_target_true, 'k--', alpha=0.3, label="True Signal (Target Region)")
    plt.plot(t_target, res_linear, label="Linear", alpha=0.8)
    plt.plot(t_target, res_cubic, label="Cubic Spline", alpha=0.8)
    plt.plot(t_target, res_guided, 'r', linewidth=2, label="Guided Spectral (Ours)")
    plt.scatter(t_sparse, y_sparse, color='blue', marker='x', s=100, label="Observed Points (1/64Hz)")
    
    plt.title("Comparison of Reconstruction Methods on Sparse Data")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
