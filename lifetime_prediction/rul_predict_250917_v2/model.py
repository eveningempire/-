import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset


class SingleStageWienerModel:
    def __init__(self, mu=1e-4, sigma=0.05, window_size=100):
        """
        单阶段维纳过程模型，带时间窗口参数更新
        mu: 漂移项（初始值）
        sigma: 扩散项（初始值）
        window_size: 参数估计的时间窗口长度
        """
        self.mu = mu
        self.sigma = sigma
        self.window_size = window_size
        self.data = []
        self.time = []
        # 参数历史
        self.mu_hist = []
        self.sigma_hist = []
        self.thre_hist = []

    def online_update(self, t, x):
        """
        在线更新模型参数，基于滑动时间窗口
        t: 当前时刻
        x: 当前观测值
        """
        self.data.append(x)
        self.time.append(t)

        # 使用最近window_size个数据点来更新参数
        if len(self.data) >= 2:  # 至少需要2个点才能计算差分
            # 当数据量小于窗口大小时，在前面用健康状态值1补齐
            if len(self.data) < self.window_size:
                # 创建补齐后的数据：初始健康状态值(1)加上已有数据
                padded_data = [1.0] * (self.window_size - len(self.data)) + self.data
                window_data = padded_data
            else:
                window_data = self.data[-self.window_size :]

            # 计算差分并更新参数
            if len(window_data) > 1:
                diff_data = np.diff(window_data)
                alpha = 0.001
                self.mu = np.clip(np.mean(diff_data), 1e-6, None) * alpha + (1 - alpha) * self.mu_hist[-1]
                self.sigma = np.std(diff_data)

        # 记录参数历史
        self.mu_hist.append(self.mu)
        self.sigma_hist.append(self.sigma)

    def predict(
        self,
        t_current,
        x_current,
        threshold=1.0,
        dt=0.01,
        max_steps=10000,
        n_mc=100,
        method="vectorized",
        accel=0.0,
    ):
        """
        蒙特卡洛外推直到预测值大于等于threshold，返回RUL均值和分布
        支持 method: "vectorized"（向量化）或 "parallel"（并行）
        """
        self.thre_hist.append(threshold)
        if method == "vectorized":
            return self._predict_vectorized_v2(
                t_current, np.mean(self.data[-self.window_size :]), threshold, dt, max_steps, n_mc, accel
            )
        elif method == "parallel":
            return self._predict_parallel(t_current, x_current, threshold, dt, max_steps, n_mc, accel)
        else:
            raise ValueError("method must be 'vectorized' or 'parallel'")

    def _linear_mu(self, t, alpha=0.5):
        """线性增长的漂移系数：mu(t) = alpha*t（从0开始随时间正比例增大）"""
        return alpha * t

    def _predict_vectorized(self, t_current, x_current, threshold, dt, max_steps, n_mc, accel):
        """
        向量化蒙特卡洛模拟
        """
        t = np.full(n_mc, t_current)
        x = np.full(n_mc, x_current)
        alive = np.ones(n_mc, dtype=bool)
        rng = np.random.default_rng()
        for _ in range(max_steps):
            mu = self.mu
            sigma = self.sigma
            update_idx = alive & (x < threshold)
            if not np.any(update_idx):
                break
            x[update_idx] += mu * dt + sigma * np.sqrt(dt) * rng.normal(size=np.sum(update_idx))
            t[update_idx] += dt
            alive = alive & (x < threshold)
        ruls = t - t_current
        return np.mean(ruls), ruls.tolist()

    def _predict_vectorized_v2(self, t_current, x_current, threshold, dt, max_steps, n_mc, accel):
        """
        向量化蒙特卡洛模拟（支持线性增长mu，无显式for循环，效率更高）
        """
        sigma = self.sigma
        rng = np.random.default_rng()
        # 时间步矩阵 shape: (n_mc, max_steps)
        t_steps = np.arange(1, max_steps + 1) * dt
        t_matrix = np.tile(t_steps, (n_mc, 1))
        if accel != 0.0:
            # mu(t) = mu + accel * abs(mu) * t
            mu0 = self.mu
            growth = accel * abs(mu0)
            mu_matrix = mu0 + growth * t_matrix
        else:
            mu_matrix = np.full((n_mc, max_steps), self.mu)
        increments = mu_matrix * dt + sigma * np.sqrt(dt) * rng.normal(size=(n_mc, max_steps))
        x_paths = x_current + np.cumsum(increments, axis=1)
        x_paths = np.hstack([np.full((n_mc, 1), x_current), x_paths])
        crossed = x_paths >= threshold
        first_cross = np.argmax(crossed, axis=1)
        never_crossed = ~np.any(crossed, axis=1)
        first_cross[never_crossed] = max_steps
        ruls = first_cross * dt
        return np.mean(ruls), ruls.tolist()

    def _predict_parallel(self, t_current, x_current, threshold, dt, max_steps, n_mc, accel):
        """
        并行蒙特卡洛模拟（多进程）
        """
        import concurrent.futures

        def single_path(_):
            t = t_current
            x = x_current
            steps = max_steps
            rng = np.random.default_rng()
            while x < threshold and steps > 0:
                mu = self.mu
                sigma = self.sigma
                x += mu * dt + sigma * np.sqrt(dt) * rng.normal()
                t += dt
                steps -= 1
            return t - t_current

        with concurrent.futures.ProcessPoolExecutor() as executor:
            ruls = list(executor.map(single_path, range(n_mc)))
        return np.mean(ruls), ruls


class AutoEncoder(nn.Module):
    def __init__(self, input_dim, latent_dim=8):
        super(AutoEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32), nn.ReLU(), nn.Linear(32, latent_dim), nn.ReLU()
        )
        self.decoder = nn.Sequential(nn.Linear(latent_dim, 32), nn.ReLU(), nn.Linear(32, input_dim))

    def forward(self, x):
        z = self.encoder(x)
        x_recon = self.decoder(z)
        return x_recon, z


def train_ae(model, train_data, epochs=50, batch_size=64, lr=1e-3, device=None):
    model.train()
    if device is None:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    train_data = train_data.to(device)
    loader = DataLoader(TensorDataset(train_data), batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        total_loss = 0
        for batch in loader:
            x = batch[0].to(device)
            x_recon, _ = model(x)
            loss = criterion(x_recon, x)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)
        avg_loss = total_loss / len(train_data)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
    return model


def test_ae(model, test_data, device=None):
    if device is None:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    criterion = nn.MSELoss(reduction="none")
    test_data = test_data.to(device)
    with torch.no_grad():
        x_recon, z = model(test_data)
        recon_error = criterion(x_recon, test_data).mean(dim=1)
        # recon_error 可作为健康指标，也可用 z 作为健康指标
    return recon_error, z
