import os
import random
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import mean_squared_error


# ==========================================
# 1. 全局配置与环境设置
# ==========================================
class Config:
    # 模型主要超参数
    LOOKBACK = 100  # 观察窗长度
    MAX_FORECAST_STEPS = 400  # 最大外推步数 (RUL 搜索上限)
    VAL_RATIO = 0.2  # 验证集比例
    BATCH_SIZE = 64  # 离线训练批次大小
    FORCE_RETRAIN = False  # 是否强制重新训练基础模型

    # 架构切换: 'GRU' 或 'CNN'
    MODEL_TYPE = "CNN"
    # 更新方法切换: 'SGD' 或 'OSELM'
    UPDATE_METHOD = "OSELM"

    # --- 在线个体数据变换配置 ---
    ONLINE_CONFIG = {"ENABLED": True, "SCALE": 1.5, "SHIFT": 0.05, "NOISE_STD": 0.02}

    # 在线更新基础参数
    UPDATE_WINDOW = 20
    WINDOW_MIN = 5  # 监控最密频率 (高危期)
    WINDOW_MAX = 30  # 监控最疏频率 (平稳期)
    WINDOW_GROWTH_STEP = 2  # 窗口增长步长 (慢涨)
    ERROR_THRESHOLD_LOW = 0.05  # 触发增长的低误差阈值
    ERROR_THRESHOLD_HIGH = 0.2  # 触发收缩的高误差阈值

    BASE_ONLINE_LR = 0.0001  # 基础学习率
    BASE_ONLINE_EPOCHS = 10  # 基础迭代次数
    MAX_ONLINE_LR = 0.001  # 最大允许学习率
    MAX_ONLINE_EPOCHS = 100  # 最大允许迭代次数

    # 动态参数调整配置
    ERROR_ADAPT_BASE = 0.01  # 误差基准 (用于缩放步长)
    MAX_ADAPT_FACTOR = 10.0  # 最大缩放倍数

    # 预测平滑控制
    FORCE_MEASUREMENT_START = False  # True: 每次更新后从真实测量值开始预测; False: 从上一次预测终点延续

    # --- 趋势分解配置 ---
    TREND_WINDOW = 100

    # OSELM 特有参数
    OSELM_REG = 0.01
    OSELM_EMA_ALPHA = 0.05  # 误差平滑因子
    OSELM_LAMBDA_MIN = 0.9  # 最小允许遗忘因子
    OSELM_TRACE_LIMIT = 1e5

    # 实验组设置
    GROUP = 1

    # 路径设置
    CURRENT_DIR = Path(__file__).parent
    DATA_FILE = CURRENT_DIR / "data" / "current_extract_final.csv"
    CKPT_DIR = CURRENT_DIR / "online_update_model_ckpt"
    FIGS_DIR = CURRENT_DIR / "figs"

    @classmethod
    def setup_dirs(cls):
        os.makedirs(cls.CKPT_DIR / f"base_{cls.MODEL_TYPE}_full_lifecycle", exist_ok=True)
        os.makedirs(cls.FIGS_DIR, exist_ok=True)


def set_seed(seed=42):
    # 1. Python 随机数生成器
    random.seed(seed)

    # 2. 操作系统相关的哈希种子 (影响 hash() 函数的结果，如 set/dict 的顺序)
    os.environ["PYTHONHASHSEED"] = str(seed)

    # 3. Numpy 随机数生成器
    np.random.seed(seed)

    # 4. PyTorch CPU 随机数生成器
    torch.manual_seed(seed)

    # 5. PyTorch GPU (CUDA) 随机数生成器
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # 如果使用多 GPU

        # --- 关键补充：控制 cuDNN 的非确定性行为 ---

        # 强制 cuDNN 使用确定性算法 (可能会降低一点性能)
        torch.backends.cudnn.deterministic = True

        # 禁止 cuDNN 自动寻找最快的算法 (Benchmarking 往往引入随机性)
        torch.backends.cudnn.benchmark = False


# ==========================================
# 2. 模型定义
# ==========================================
class OSELMSolver:
    def __init__(self, input_dim, output_dim, device):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.device = device
        self.P = None
        self.beta = None

    def initialize(self, H, T, regularization=1.0):
        H_t = H.t()
        self.P = torch.inverse(torch.mm(H_t, H) + regularization * torch.eye(self.input_dim).to(self.device))
        self.beta = torch.mm(torch.mm(self.P, H_t), T)

    def update(self, H, T, forgetting_factor=1.0):
        H_t = H.t()
        batch_size = H.size(0)
        P_Ht = torch.mm(self.P, H_t)
        M = torch.mm(H, P_Ht) + forgetting_factor * torch.eye(batch_size).to(self.device)
        M_inv = torch.inverse(M)
        K = torch.mm(P_Ht, M_inv)
        pred_error = T - torch.mm(H, self.beta)
        self.beta = self.beta + torch.mm(K, pred_error)
        self.P = (self.P - torch.mm(K, torch.mm(H, self.P))) / forgetting_factor
        if random.random() < 0.1:
            self.P = (self.P + self.P.t()) / 2.0

    def predict(self, H):
        return torch.mm(H, self.beta)


SCALE_FACTOR = 1


class CNN1DNet(nn.Module):
    def __init__(self, input_dim=2, hidden_dim=32, output_dim=2):
        super(CNN1DNet, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=input_dim, out_channels=hidden_dim, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(in_channels=hidden_dim, out_channels=hidden_dim, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim * SCALE_FACTOR)
        self.relu = nn.ReLU()
        self.fc = nn.Linear(hidden_dim * SCALE_FACTOR, output_dim)
        self.hidden_dim = hidden_dim

    def forward(self, x, return_features=False):
        # x: (B, L, C) -> (B, C, L)
        x = x.transpose(1, 2)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.pool(x).squeeze(-1)
        out = self.fc1(x)
        out = self.relu(out)
        if return_features:
            return out
        return self.fc(out)


class GRUNet(nn.Module):
    def __init__(self, input_dim=2, hidden_dim=32, output_dim=2, n_layers=2):
        super(GRUNet, self).__init__()
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers
        self.gru = nn.GRU(input_dim, hidden_dim, n_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim * SCALE_FACTOR)
        self.relu = nn.ReLU()
        self.fc = nn.Linear(hidden_dim * SCALE_FACTOR, output_dim)

    def forward(self, x, return_features=False):
        h0 = torch.zeros(self.n_layers, x.size(0), self.hidden_dim).to(x.device)
        out, _ = self.gru(x, h0)
        out = out[:, -1, :]
        out = self.fc1(out)
        out = self.relu(out)
        if return_features:
            return out
        return self.fc(out)


# ==========================================
# 3. 核心业务类：RUL 预测与在线更新
# ==========================================
class RULForecaster:
    def __init__(self, config):
        self.cfg = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.cfg.MODEL_TYPE == "CNN":
            self.model = CNN1DNet().to(self.device)
            self.model_frozen = CNN1DNet().to(self.device)
        else:
            self.model = GRUNet().to(self.device)
            self.model_frozen = GRUNet().to(self.device)

        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self.criterion = nn.L1Loss()
        self.oselm = None
        self.error_smooth = 0.0
        if self.cfg.UPDATE_METHOD == "OSELM":
            self.oselm = OSELMSolver(
                input_dim=self.model.hidden_dim * SCALE_FACTOR, output_dim=2, device=self.device
            )

    def _model_forward(self, x, use_original=False):
        if use_original:
            return self.model_frozen(x)
        if self.cfg.UPDATE_METHOD == "OSELM" and self.oselm.beta is not None:
            features = self.model(x, return_features=True)
            return self.oselm.predict(features)
        else:
            return self.model(x)

    def _decompose_data(self, values):
        series = pd.Series(values.flatten())
        trend = series.rolling(window=self.cfg.TREND_WINDOW, min_periods=1).mean().values
        residual = (values.flatten() - trend).reshape(-1, 1)
        trend_delta = np.diff(trend, prepend=trend[0]).reshape(-1, 1)
        return np.hstack([trend_delta, residual])

    def prepare_data(self):
        df = pd.read_csv(self.cfg.DATA_FILE)
        df = df.dropna(subset=["current"])
        self.df = df
        self.original_values = df["current"].values
        self.data_decomposed = self._decompose_data(self.original_values)
        self.scaler.fit(self.data_decomposed)
        self.data_scaled = self.scaler.transform(self.data_decomposed)
        self.min_orig = torch.tensor(self.scaler.data_min_).float().to(self.device)
        self.range_orig = torch.tensor(self.scaler.data_range_).float().to(self.device)

        if self.cfg.ONLINE_CONFIG["ENABLED"]:
            # 优先从本地加载已生成的在线数据 CSV，实现“数据持久化变换”
            group_id = getattr(self.cfg, "GROUP", 1)
            sim_csv_path = self.cfg.CURRENT_DIR / "data" / f"simulated_online_data_group{group_id}.csv"

            if sim_csv_path.exists():
                # print(f"[Forecaster] 正在加载预存的在线仿真数据: {sim_csv_path.name}")
                sim_df = pd.read_csv(sim_csv_path)
                self.online_original_values = sim_df["online_current"].values
            else:
                # print(f"[Forecaster] 未发现预存数据，正在进行在线个体数据模拟 (Group {group_id})...")
                c = self.cfg.ONLINE_CONFIG
                self.online_original_values = self.original_values * c["SCALE"] + c["SHIFT"]
                noise = np.random.normal(0, c["NOISE_STD"], size=self.online_original_values.shape)
                self.online_original_values += noise

                # 保存至 CSV 供以后直接加载
                sim_csv_path.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame({"online_current": self.online_original_values}).to_csv(sim_csv_path, index=False)
                # print(f"[Forecaster] 在线仿真数据已保存至: {sim_csv_path}")

            online_decomposed = self._decompose_data(self.online_original_values)
            self.online_data_scaled = self.scaler.transform(online_decomposed)
            self.online_res_values = online_decomposed[:, 1]
            self.online_trend_values = self.online_original_values - self.online_res_values
        else:
            self.online_original_values = self.original_values
            self.online_data_scaled = self.data_scaled
            self.online_res_values = self.data_decomposed[:, 1]
            self.online_trend_values = self.online_original_values - self.online_res_values

        self.failure_threshold = self.online_original_values.max()

    def load_or_train_base(self):
        base_dir = self.cfg.CKPT_DIR / f"base_{self.cfg.MODEL_TYPE}_full_lifecycle"
        # 根据当前 device 区分模型文件名
        dev_suffix = "cuda" if "cuda" in str(self.device).lower() else "cpu"
        m_path = base_dir / f"best_{self.cfg.MODEL_TYPE.lower()}_model_{dev_suffix}.pth"
        s_path = base_dir / "scaler.joblib"

        if not self.cfg.FORCE_RETRAIN and m_path.exists():
            print(f"[Forecaster] 正在从硬盘加载基础模型 ({dev_suffix}): {m_path.name}")
            weights = torch.load(m_path, map_location=self.device)
            self.model.load_state_dict(weights)
            self.model_frozen.load_state_dict(weights)
            self.scaler = joblib.load(s_path)
            self.min_orig = torch.tensor(self.scaler.data_min_).float().to(self.device)
            self.range_orig = torch.tensor(self.scaler.data_range_).float().to(self.device)
        else:
            print(f"[Forecaster] 未找到匹配模型或强制训练 ({dev_suffix})，开始离线基础模型训练...")
            joblib.dump(self.scaler, s_path)
            self._train_base(m_path)

        if self.cfg.UPDATE_METHOD == "OSELM":
            self.model.eval()
            with torch.no_grad():
                X, y = self._create_sequences(self.data_scaled)
                X_tensor = torch.from_numpy(X).float().to(self.device)
                y_tensor = torch.from_numpy(y).float().to(self.device)
                H0 = self.model(X_tensor, return_features=True)
                self.oselm.initialize(H0, y_tensor, regularization=self.cfg.OSELM_REG)

    def _train_base(self, m_path):
        X, y = self._create_sequences(self.data_scaled)
        X_train_raw, X_val_raw, y_train_raw, y_val_raw = train_test_split(
            X, y, test_size=self.cfg.VAL_RATIO, random_state=42, shuffle=True
        )
        X_train_t = torch.from_numpy(X_train_raw).float()
        y_train_t = torch.from_numpy(y_train_raw).float()
        X_val_t = torch.from_numpy(X_val_raw).float().to(self.device)
        y_val_t = torch.from_numpy(y_val_raw).float().to(self.device)
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=self.cfg.BATCH_SIZE, shuffle=True)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        best_v = float("inf")
        patience, trigger = 50, 0
        for epoch in range(1, 1001):
            self.model.train()
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                loss = self.criterion(self.model(batch_X), batch_y)
                loss.backward()
                optimizer.step()
            self.model.eval()
            with torch.no_grad():
                v_loss = self.criterion(self.model(X_val_t), y_val_t)
            if v_loss < best_v:
                best_v = v_loss
                torch.save(self.model.state_dict(), m_path)
                trigger = 0
            else:
                trigger += 1
                if trigger >= patience:
                    break
        self.model.load_state_dict(torch.load(m_path))
        self.model_frozen.load_state_dict(torch.load(m_path))

    def _create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.cfg.LOOKBACK):
            X.append(data[i : i + self.cfg.LOOKBACK])
            y.append(data[i + self.cfg.LOOKBACK])
        return np.array(X), np.array(y)

    def predict_rul_batch(self, start_indices, use_original=False):
        self.model.eval()
        self.model_frozen.eval()
        batch_size = len(start_indices)
        windows = [self.online_data_scaled[k - self.cfg.LOOKBACK : k] for k in start_indices]
        B_windows = torch.from_numpy(np.stack(windows)).float().to(self.device)
        B_last_vals = torch.from_numpy(self.online_original_values[start_indices - 1]).float().to(self.device)
        initial_scaled = (
            torch.from_numpy(np.stack([self.online_data_scaled[k - 1] for k in start_indices]))
            .float()
            .to(self.device)
        )
        B_last_res = (initial_scaled[:, 1] + 1) / 2 * self.range_orig[1] + self.min_orig[1]
        B_current_trend = B_last_vals - B_last_res
        B_rul = torch.full((batch_size,), self.cfg.MAX_FORECAST_STEPS, dtype=torch.int).to(self.device)
        B_alive = torch.ones((batch_size,), dtype=torch.bool).to(self.device)
        with torch.no_grad():
            for step in range(1, self.cfg.MAX_FORECAST_STEPS + 1):
                if not B_alive.any():
                    break
                out_scaled = self._model_forward(B_windows, use_original=use_original)
                pred_phys = (out_scaled + 1) / 2 * self.range_orig + self.min_orig
                B_current_trend += pred_phys[:, 0]
                B_next_vals = B_current_trend + pred_phys[:, 1]
                newly_failed = (B_next_vals >= self.failure_threshold) & B_alive
                B_rul[newly_failed] = step
                B_alive[newly_failed] = False
                B_windows = torch.cat((B_windows[:, 1:, :], out_scaled.unsqueeze(1)), dim=1)
        return B_rul.cpu().numpy()

    def get_trajectory(self, start_idx, steps=None, use_original=False, last_val=None, last_res=None):
        if steps is None:
            steps = self.cfg.MAX_FORECAST_STEPS
        self.model.eval()
        self.model_frozen.eval()
        window = self.online_data_scaled[start_idx - self.cfg.LOOKBACK : start_idx]
        win_tensor = torch.from_numpy(window).float().unsqueeze(0).to(self.device)
        if last_val is None:
            c_val = torch.tensor([self.online_original_values[start_idx - 1]]).float().to(self.device)
        else:
            c_val = (
                last_val.clone()
                if torch.is_tensor(last_val)
                else torch.tensor([last_val]).float().to(self.device)
            )
        if last_res is None:
            last_scaled_res = (
                torch.tensor([self.online_data_scaled[start_idx - 1, 1]]).float().to(self.device)
            )
            c_res = (last_scaled_res + 1) / 2 * self.range_orig[1] + self.min_orig[1]
        else:
            c_res = (
                last_res.clone()
                if torch.is_tensor(last_res)
                else torch.tensor([last_res]).float().to(self.device)
            )
        current_trend = c_val - c_res
        traj = []
        with torch.no_grad():
            for _ in range(steps):
                out_scaled = self._model_forward(win_tensor, use_original=use_original)
                pred_phys = (out_scaled + 1) / 2 * self.range_orig + self.min_orig
                current_trend += pred_phys[:, 0]
                next_val = current_trend + pred_phys[:, 1]
                traj.append(next_val.item())
                win_tensor = torch.cat((win_tensor[:, 1:, :], out_scaled.unsqueeze(1)), dim=1)
        return np.array(traj), next_val, pred_phys[:, 1]

    def run_online_simulation(self):
        total_len = len(self.online_original_values)
        indices = np.arange(self.cfg.LOOKBACK + 1, total_len)
        all_predicted_rul = []
        all_original_rul = []
        short_forecast_values = []
        short_forecast_original = []
        dynamic_params_log = []
        window_size_log = []
        last_val_up, last_res_up = None, None
        last_val_orig, last_res_orig = None, None
        curr_ptr = 0
        curr_win = self.cfg.UPDATE_WINDOW
        while curr_ptr < len(indices):
            end_ptr = min(curr_ptr + curr_win, len(indices))
            chunk = indices[curr_ptr:end_ptr]

            # --- 进度显示 ---
            print(f"    -> 观测点 {chunk[0]} / {total_len} | 窗口: {curr_win} pts...", end="\r")

            start_idx = chunk[0]
            forecast_len = len(chunk)
            window_size_log.append(curr_win)
            f_start = None if self.cfg.FORCE_MEASUREMENT_START else last_val_up
            f_res = None if self.cfg.FORCE_MEASUREMENT_START else last_res_up
            short_traj, last_val_up, last_res_up = self.get_trajectory(
                start_idx, steps=forecast_len, last_val=f_start, last_res=f_res
            )
            short_forecast_values.extend(short_traj)
            f_start_orig = None if self.cfg.FORCE_MEASUREMENT_START else last_val_orig
            f_res_orig = None if self.cfg.FORCE_MEASUREMENT_START else last_res_orig
            short_traj_orig, last_val_orig, last_res_orig = self.get_trajectory(
                start_idx, steps=forecast_len, use_original=True, last_val=f_start_orig, last_res=f_res_orig
            )
            short_forecast_original.extend(short_traj_orig)
            all_predicted_rul.extend(self.predict_rul_batch(chunk))
            all_original_rul.extend(self.predict_rul_batch(chunk, use_original=True))
            actual_chunk_vals = self.online_original_values[chunk]
            error = np.mean(np.abs(short_traj - actual_chunk_vals))
            scale_factor = min(max(error / self.cfg.ERROR_ADAPT_BASE, 1.0), self.cfg.MAX_ADAPT_FACTOR)
            current_lr = min(self.cfg.BASE_ONLINE_LR * scale_factor, self.cfg.MAX_ONLINE_LR)
            current_epochs = int(min(self.cfg.BASE_ONLINE_EPOCHS * scale_factor, self.cfg.MAX_ONLINE_EPOCHS))
            dynamic_params_log.append((error, current_lr, current_epochs))
            if self.cfg.UPDATE_METHOD == "OSELM":
                self.error_smooth = (
                    self.cfg.OSELM_EMA_ALPHA * error + (1 - self.cfg.OSELM_EMA_ALPHA) * self.error_smooth
                )
                lmbd = max(
                    min(
                        1.0
                        - (self.error_smooth / (self.cfg.ERROR_ADAPT_BASE * 5))
                        * (1 - self.cfg.OSELM_LAMBDA_MIN),
                        1.0,
                    ),
                    self.cfg.OSELM_LAMBDA_MIN,
                )
                if torch.trace(self.oselm.P).item() > self.cfg.OSELM_TRACE_LIMIT:
                    lmbd = 1.0
                self._fine_tune_oselm(chunk, forgetting_factor=lmbd)
            else:
                self._fine_tune_model(chunk, current_lr, current_epochs)
            if error > self.cfg.ERROR_THRESHOLD_HIGH:
                curr_win = self.cfg.WINDOW_MIN
            elif error < self.cfg.ERROR_THRESHOLD_LOW:
                curr_win = min(curr_win + self.cfg.WINDOW_GROWTH_STEP, self.cfg.WINDOW_MAX)
            curr_ptr = end_ptr
        return (
            indices,
            np.array(all_predicted_rul),
            np.array(all_original_rul),
            np.array(short_forecast_values),
            np.array(short_forecast_original),
            dynamic_params_log,
            window_size_log,
        )

    def _fine_tune_oselm(self, observed_indices, forgetting_factor=1.0):
        self.model.eval()
        start_idx = max(0, observed_indices[0] - self.cfg.LOOKBACK)
        end_idx = observed_indices[-1] + 1
        segment_scaled = self.online_data_scaled[start_idx:end_idx]
        X_up, y_up = self._create_sequences(segment_scaled)
        if len(X_up) == 0:
            return
        X_up = torch.from_numpy(X_up).float().to(self.device)
        y_up = torch.from_numpy(y_up).float().to(self.device)
        with torch.no_grad():
            H_up = self.model(X_up, return_features=True)
            self.oselm.update(H_up, y_up, forgetting_factor=forgetting_factor)

    def _fine_tune_model(self, observed_indices, lr, epochs):
        self.model.train()
        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        start_idx = max(0, observed_indices[0] - self.cfg.LOOKBACK)
        end_idx = observed_indices[-1] + 1
        segment_scaled = self.online_data_scaled[start_idx:end_idx]
        X_up, y_up = self._create_sequences(segment_scaled)
        if len(X_up) == 0:
            return
        X_up = torch.from_numpy(X_up).float().to(self.device)
        y_up = torch.from_numpy(y_up).float().to(self.device)
        for _ in range(epochs):
            optimizer.zero_grad()
            loss = self.criterion(self.model(X_up), y_up)
            loss.backward()
            optimizer.step()
