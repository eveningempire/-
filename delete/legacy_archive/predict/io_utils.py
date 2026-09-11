# _*_ coding : utf-8 _*_
# @Time : 2024/12/1 11:20
# @Author : Conearth
# @Email : mathlover2015@163.com
# @Organization : Beihang University
# @File : io
# @Project : 演示验证平台
# @Description : For test


import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import math
from scipy.optimize import curve_fit
import scipy.io
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, TensorDataset
import torch.nn.functional as F
from tqdm import tqdm
from scipy.signal import savgol_filter
import pandas as pd
from scipy.interpolate import interp1d
from datetime import datetime
from matplotlib import pyplot as plt
from datetime import datetime
import os

# 20250316 Kaimol修改：解决降采样率问题


os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'

# 寿命预测系统的io函数
# 如果是训练模式， pack函数返回一个字符串：模型保存在xx位置
# 如果是测试模式， pack函数返回测试结果，依次为：label_test, output, rmse, mae
def ioooo(train_or_test, algorithm, train_data_dir=None, train_model_save_dir=None, test_data_dir=None,
          test_model_load_dir=None, epochs=1):
    # 移除trainingSampleRateoutput和testingSampleRateoutput参数以及downsample相关处理
    if train_or_test == 'train':
        if algorithm == 'Transformer':
            out = pack(train_or_test=train_or_test, train_data_path=train_data_dir, train_algorithm='Transformer',
                       model_save_path=train_model_save_dir, test_data_path=test_data_dir, test_algorithm='Transformer',
                       model_test_path=test_model_load_dir, epochs=epochs)
            return *out, '天'
        elif algorithm == 'Transformer Physics':
            out = pack(train_or_test=train_or_test, train_data_path=train_data_dir, train_algorithm='Transformer Physics',
                       model_save_path=train_model_save_dir, test_data_path=test_data_dir,test_algorithm='Transformer Physics',
                       model_test_path=test_model_load_dir, epochs=epochs)
            return *out, '天'

    elif train_or_test == 'test':
        # 使用前端传递的算法类型参数进行测试
        out = pack(train_or_test=train_or_test, train_data_path=train_data_dir, train_algorithm=None,
                   model_save_path=train_model_save_dir, test_data_path=test_data_dir, test_algorithm=algorithm,
                   model_test_path=test_model_load_dir, epochs=epochs)
        return *out, '天'
    else:
        raise NotImplementedError(f"不支持的算法类型: {algorithm}")

def ioooo2(train_or_test, algorithm, train_data_dir=None, train_model_save_dir=None, test_data_dir=None,
          test_model_load_dir=None, epochs=1):
    # 移除trainingSampleRateoutput和testingSampleRateoutput参数以及downsample相关处理
    if train_or_test == 'train':
        if algorithm == 'Transfer':
            solver = SimplePredictSolver(train_data_path=train_data_dir, train_model_save_path=train_model_save_dir,
                                         test_data_path=test_data_dir, test_model_load_path=test_model_load_dir, epochs=epochs)
            # 训练时，首先确保训练数据被正确加载和归一化
            solver.initialize_data()
            out = solver.train()
            return *out, '机动次'  # 训练模式直接返回字符串
        elif algorithm == 'Transfer Physics':
            solver = FusionPredictSolver(train_data_path=train_data_dir, train_model_save_path=train_model_save_dir,
                                         test_data_path=test_data_dir, test_model_load_path=test_model_load_dir, epochs=epochs)
            # 训练时，首先确保训练数据被正确加载和归一化
            solver.initialize_data()
            out = solver.train()
            return *out, '机动次'  # 训练模式直接返回字符串
    elif train_or_test == 'test':
        if algorithm == 'Transfer':
            # 测试模式下只传递测试相关参数
            solver = SimplePredictSolver(test_data_path=test_data_dir, test_model_load_path=test_model_load_dir, epochs=epochs)
            out = solver.test()
            return *out, '机动次'
        elif algorithm == 'Transfer Physics':
            # 测试模式下只传递测试相关参数
            solver = FusionPredictSolver(test_data_path=test_data_dir, test_model_load_path=test_model_load_dir, epochs=epochs)
            out = solver.test()
            return *out, '机动次'
        else:
            raise NotImplementedError(f"不支持的算法类型: {algorithm}")
    else:
        raise NotImplementedError(f"不支持的操作类型: {train_or_test}")


def map_and_interpolate(model_output, total_days):
    """
    将模型输出数据插值扩展到 [total_days, 1] 并将数据范围映射到 [0, total_days]。

    参数：
        model_output (list or array): 输入数据，形状为 [cycle, 1]，其中每个值是归一化的剩余寿命。
        total_days (int): 总天数，用于扩展数据到 [total_days, 1]。

    返回：
        interpolated_array (ndarray): 插值并映射后的数组，形状为 [total_days, 1]。
    """
    # 提取原始数据长度和归一化的剩余寿命
    length = len(model_output)
    normalized_lifetimes = np.array([item[0] for item in model_output])  # 转为一维数组

    # 原始横坐标 (cycle): 从 0 到 length - 1
    original_x = np.linspace(0, length - 1, num=length)

    # 目标横坐标 (day): 从 0 到 total_days - 1
    target_x = np.linspace(0, length - 1, num=total_days)

    # 插值方法，将原始数据插值到 total_days 个点
    interpolator = interp1d(original_x, normalized_lifetimes, kind='linear')
    interpolated_values = interpolator(target_x)

    # 将插值结果从 [0, 1] 映射到 [0, total_days]
    mapped_values = interpolated_values * total_days

    # 返回结果形状为 [total_days, 1]
    interpolated_array = mapped_values.reshape(-1, 1)

    return interpolated_array



def compute_derivative(time_series):
    """
    对输入的时间序列计算数值导数，使用中心差分法。
    :param time_series: 输入的时间序列, 形状为 (batch_size, sequence_length)
    :return: 导数序列, 形状与输入相同
    """
    # 在时间维度（第二维）上使用中心差分法
    time_series_diff = (time_series[:, 2:] - time_series[:, :-2]) / 2.0

    # 保持维度一致性，补齐导数序列的边界
    first_diff = (time_series[:, 1] - time_series[:, 0]).unsqueeze(1)
    last_diff = (time_series[:, -1] - time_series[:, -2]).unsqueeze(1)

    # 将首位导数拼接回原序列
    derivative = torch.cat([first_diff, time_series_diff, last_diff], dim=1)

    return derivative


class Encoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, seq_len):
        super(Encoder, self).__init__()

        self.seq_len = seq_len
        self.hidden_dim = hidden_dim

        # 一维卷积，用于提取序列的局部特征，保持维度不变
        self.conv1 = nn.Conv1d(input_dim, hidden_dim, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=7, padding=3)

        # Transformer 层，用于时序特征学习
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=4,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=6)

        # 将全连接层改为输出与序列相同形状的补偿项
        self.fc_combine = nn.Linear(hidden_dim, 32)  # 生成 [batch, length, 8] 的补偿项
        self.fc_combine2 = nn.Linear(32, 10)  # 生成 [batch, length, 8] 的补偿项

        self.com_conv1 = nn.Conv2d(in_channels=2, out_channels=16, kernel_size=(3, 3), padding=(1, 1), stride=(2, 1))
        self.nor1 = nn.BatchNorm2d(16)
        self.com_conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=(7, 5), padding=(3, 2), stride=(2, 1))
        self.nor2 = nn.BatchNorm2d(32)
        self.com_conv3 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=(15, 8), padding=(7, 0), stride=(2, 1))
        self.nor3 = nn.BatchNorm2d(64)
        self.com_fc1 = nn.Linear(64 * 250, 256)  # 考虑卷积后的维度减少
        self.com_fc2 = nn.Linear(256, 1)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape

        # Step 1: 物理信息网络部分 - 卷积操作提取局部特征
        x_conv = x.permute(0, 2, 1)  # (batch_size, input_dim, seq_len) for Conv1d
        x_conv = torch.sigmoid(self.conv1(x_conv))
        x_conv = torch.sigmoid(self.conv2(x_conv))
        x_conv = x_conv.permute(0, 2, 1)  # (batch_size, seq_len, hidden_dim)
        ##x_conv = torch.cat((x_conv, x[:, :, 2].unsqueeze(-1)), dim =-1)

        # Step 1: 时序学习网络部分 - Transformer 提取全局时序特征
        x_transformed = self.transformer_encoder(x_conv)

        # Step 2: 全连接层组合各系数并输出补偿项
        # 通过原序列提取出电流 I 和轴温 T
        I = x[:, :, 0]  # 输入中的电流序列
        T = x[:, :, 1]  # 输入中的轴温序列
        dTdt = compute_derivative(T)
        dIdt = compute_derivative(I)
        # 公式计算: 导数项 + 温度项 + 电流项 + 电流轴温混合项
        derivative_term = dTdt  # 温度导数项
        derivative_term2 = (dTdt) ** 2  # 温度导数项2
        tempture_term = T  # 温度项
        current_term = (I ** 2)  # 电流项
        quadratic_term1 = (I ** 2) * (T ** 2)  # 混合项1
        quadratic_term2 = (I ** 2) * (T)  # 混合项2

        # 公式计算：补偿项
        x_transformed = torch.sigmoid(self.fc_combine(x_transformed))
        x_transformed = torch.sigmoid(self.fc_combine2(x_transformed))  # 输出形状为 [batch, seq_len, 6]
        compensation_term = x_transformed[:, :, 2:]
        bias_term1 = x_transformed[:, :, 0]
        bias_term2 = x_transformed[:, :, 1]
        # 最终的物理方程
        Q_bearing_fn = torch.stack((derivative_term, derivative_term2, current_term, tempture_term, quadratic_term1,
                                    quadratic_term2, bias_term1, bias_term2), dim=-1)
        Q_bearing = torch.stack((Q_bearing_fn, compensation_term), dim=-1)

        Q_bearing = Q_bearing.permute(0, 3, 1, 2)
        Q_bearing = torch.sigmoid(self.com_conv1(Q_bearing))
        Q_bearing = self.nor1(Q_bearing)
        Q_bearing = torch.sigmoid(self.com_conv2(Q_bearing))
        Q_bearing = self.nor2(Q_bearing)
        Q_bearing = torch.sigmoid(self.com_conv3(Q_bearing))
        Q_bearing = self.nor3(Q_bearing)
        Q_bearing = Q_bearing.reshape(Q_bearing.size(0), -1)
        Q_bearing = torch.sigmoid(self.com_fc1(Q_bearing))
        hi = torch.sigmoid(self.com_fc2(Q_bearing))

        return hi, Q_bearing_fn
class Encoder_Duibi(nn.Module):
    def __init__(self, input_dim, hidden_dim, seq_len):
        super(Encoder_Duibi, self).__init__()

        self.seq_len = seq_len
        self.hidden_dim = hidden_dim

         # 一维卷积，用于提取序列的局部特征，保持维度不变
        self.conv1 = nn.Conv1d(input_dim, hidden_dim, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=7, padding=3)

        # Transformer 层，用于时序特征学习
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=4,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=6)

        # 将全连接层改为输出与序列相同形状的补偿项
        self.fc_combine = nn.Linear(hidden_dim, 32)  # 生成 [batch, length, 8] 的补偿项
        self.fc_combine2 = nn.Linear(32, 8)  # 生成 [batch, length, 8] 的补偿项


        self.com_fc1 = nn.Linear(2000 * 8, 256)  # 考虑卷积后的维度减少
        self.com_fc2 = nn.Linear(256, 1)


    def forward(self, x):

        batch_size, seq_len, _ = x.shape
         # Step 1: 物理信息网络部分 - 卷积操作提取局部特征
        x_conv = x.permute(0, 2, 1)  # (batch_size, input_dim, seq_len) for Conv1d
        x_conv = torch.sigmoid(self.conv1(x_conv))
        x_conv = torch.sigmoid(self.conv2(x_conv))
        x_conv = x_conv.permute(0, 2, 1)  # (batch_size, seq_len, hidden_dim)

        # Step 1: 时序学习网络部分 - Transformer 提取全局时序特征
        x_transformed = self.transformer_encoder(x_conv)


        # 公式计算：补偿项
        compensation_term = torch.sigmoid(self.fc_combine(x_transformed))
        Q_bearing = torch.sigmoid(self.fc_combine2(compensation_term))# 输出形状为 [batch, seq_len, 6]
        ##compensation_term = compensation_term.squeeze(-1)  # 移除最后的1维，保持与物理量相同的维度

        Q_bearing = Q_bearing.reshape(Q_bearing.size(0), -1)
        Q_bearing = torch.sigmoid(self.com_fc1(Q_bearing))
        hi = torch.sigmoid(self.com_fc2(Q_bearing))

        # 修改：返回两个值以与 Encoder 类保持一致
        # 原始代码: return hi
        # 新代码: 返回 hi 和一个占位符 Q_bearing
        return hi, Q_bearing

def split_into_segments_with_overlap(data, segment_length=1000, step_size=100, padding=False):
    """
    使用滑动窗口将退化数据分割为定长子序列，并保留相邻子序列之间的关系。

    参数:
    data: 形状为 (num_samples, total_length) 的退化数据
    segment_length: 每个子序列的长度
    step_size: 滑动窗口的步长，决定相邻子序列的重叠部分
    padding: 是否填充不足长度的子序列

    返回:
    segments: 分割后的子序列，形状为 (num_segments, segment_length)
    """
    segments = []
    for sequence in data:
        for i in range(0, len(sequence) - segment_length + 1, step_size):
            segment = sequence[i:i + segment_length]
            segments.append(segment)

        # 处理最后一段不足长度的序列
        if len(sequence) % step_size != 0:
            last_segment = sequence[-segment_length:]
            if padding and len(last_segment) < segment_length:
                # 使用零填充不足的部分
                last_segment = np.pad(last_segment, (0, segment_length - len(last_segment)), 'constant')
            segments.append(last_segment)

    return np.array(segments)



def downsample_and_split(data, downsample_rate=10, train_ratio=0.7):
    """
    对退化数据降采样，生成多条完整退化数据，
    每条数据从不同起点开始并分为训练和验证集。

    如果数据长度不能被降采样倍率整除，将舍弃最后一段数据。

    Parameters:
        data (np.ndarray): 原始退化数据，形状为 [n, 1]。
        downsample_rate (int): 降采样倍率，默认为10。
        train_ratio (float): 训练数据占比，默认为0.7。

    Returns:
        train_data (np.ndarray): 训练数据，形状为 [train_samples, sample_length]。
        val_data (np.ndarray): 验证数据，形状为 [val_samples, sample_length]。
    """
    if len(data.shape) != 2 or data.shape[1] != 1:
        raise ValueError("输入数据必须是形状为 [n, 1] 的数组。")

    n = data.shape[0]
    # 计算可以整除的最大长度
    usable_length = (n // downsample_rate) * downsample_rate
    if usable_length < n:
        data = data[:usable_length]

    sample_length = usable_length // downsample_rate

    # 生成降采样数据
    downsampled_data = np.array([
        data[i::downsample_rate].flatten()
        for i in range(downsample_rate)
    ])

    # 分割为训练和验证数据
    num_samples = downsampled_data.shape[0]
    train_size = int(num_samples * train_ratio)

    train_data = downsampled_data[:train_size]
    val_data = downsampled_data[train_size:]

    return train_data, val_data


def generate_rul(length, hold_ratio=0):
    """
    生成 RUL 标签，其中前段恒值，后段线性下降到 0。

    参数:
        length (int): 标签的总长度。
        hold_ratio (float): 前段恒值部分所占比例，默认 0.375 (75% / 2)。

    返回:
        np.ndarray: 生成的 RUL 标签，形状为 (length,)。
    """
    hold_length = int(length * hold_ratio)  # 计算恒值段长度
    decay_length = length - hold_length  # 计算线性下降段长度

    # 构造标签
    hold_part = np.ones(hold_length)  # 恒值部分
    decay_part = np.linspace(1, 0, decay_length)  # 线性下降部分

    # 拼接结果
    return np.concatenate([hold_part, decay_part])
def rul_labels(labels, num_samples):
    """
    将标签复制多份并转换形状。

    Parameters:
        labels (np.ndarray): 原始标签数据，形状为 [1, m]。
        num_samples (int): 需要复制的份数（即训练数据的数量）。

    Returns:
        reshaped_labels (np.ndarray): 转换后的标签数据，形状为 [num_samples * m, 1]。
    """
    if len(labels.shape) != 2 or labels.shape[0] != 1:
        raise ValueError("标签数据必须是形状为 [1, m] 的数组。")

    # 复制标签 num_samples 份
    replicated_labels = np.tile(labels, (num_samples, 1))

    # 将标签转换为 [num_samples * m, 1] 的形状
    reshaped_labels = replicated_labels.flatten().reshape(-1, 1)

    return reshaped_labels
def get_pretrain_dataAndlabel(path, test=False):
    # 移除downsample参数
    data = pd.read_csv(path)
    column_data1 = data.iloc[:, 1]
    column_data2 = data.iloc[:, 2]
    numeric_data1 = pd.to_numeric(column_data1, errors='coerce')
    numeric_data2 = pd.to_numeric(column_data2, errors='coerce')
    # 检查 numeric_data 是否包含 NaN 值
    if numeric_data1.isna().any():
        print("There are NaN values in numeric_data.")
    if numeric_data2.isna().any():
        print("There are NaN values in numeric_data.")

    data1 = np.array(numeric_data1)
    data2 = np.array(numeric_data2)
    start = 721000
    end = 723000
    data1 = np.concatenate((data1[:start], data1[end:]))
    data2 = np.concatenate((data2[:start], data2[end:]))

    data1 = savgol_filter(data1, window_length=10, polyorder=5)
    data2 = savgol_filter(data2, window_length=10, polyorder=5)

    # 使用固定值替代传入的参数
    downsample_rate = 10
    train_ratio = 0.7
    data1_train, data1_test = downsample_and_split(data1.reshape(-1, 1), downsample_rate=downsample_rate, train_ratio=train_ratio)
    data2_train, data2_test = downsample_and_split(data2.reshape(-1, 1), downsample_rate=downsample_rate, train_ratio=train_ratio)

    if test == False:
        segments1 = split_into_segments_with_overlap(data1_train, segment_length=2000, step_size=500, padding=False)
        segments2 = split_into_segments_with_overlap(data2_train, segment_length=2000, step_size=500, padding=False)
        segments = np.dstack((segments1, segments2))
        num = int(downsample_rate * train_ratio)
        # 检查num是否为0
        if num <= 0:
            print(f"警告：计算得到的num值为0，将使用默认值1")
            num = 1
        length = int(segments1.shape[0] / num)
        rul_label = generate_rul(length, hold_ratio=0)
        segments_label = rul_labels(rul_label.reshape(1, -1), num)
        print('训练数据形状大小', segments.shape)
        print('训练标签形状大小', segments_label.shape)
    else:
        segments1 = split_into_segments_with_overlap(data1_test, segment_length=2000, step_size=500, padding=False)
        segments2 = split_into_segments_with_overlap(data2_test, segment_length=2000, step_size=500, padding=False)
        segments = np.dstack((segments1, segments2))
        num = int(downsample_rate * (1 - train_ratio))
        # 检查num是否为0
        if num <= 0:
            print(f"警告：计算得到的num值为0，将使用默认值1")
            num = 1
        length = int(segments1.shape[0] / num)
        rul_label = generate_rul(length, hold_ratio=0)
        segments_label = rul_labels(rul_label.reshape(1, -1), num)
        print('测试数据形状大小', segments.shape)
        print('测试标签形状大小', segments_label.shape)

    return segments, segments_label, length

def calculate_rmse(sequence1, sequence2):
    """
    计算两个序列的RMSE (Root Mean Squared Error)

    参数:
        sequence1: np.ndarray, 形状为 [n, 1]
        sequence2: np.ndarray, 形状为 [n, 1]

    返回:
        rmse: float, 均方根误差
    """
    # 确保输入是NumPy数组，并检查形状
    sequence1 = np.array(sequence1)
    sequence2 = np.array(sequence2)

    if sequence1.shape != sequence2.shape:
        raise ValueError("两个序列的形状必须相同！")

    # 计算RMSE
    mse = np.mean((sequence1 - sequence2) ** 2)  # 均方误差
    rmse = np.sqrt(mse)  # 均方根误差
    return rmse
#定义预训练函数
def train(encoder, train_loader, optimizer, epoch, epochs, device, loss_fun):
    encoder.train()
    total_loss = 0
    loop = tqdm(train_loader, total=len(train_loader))
    loop.set_description(f'Epoch [{epoch + 1}/{epochs}]')
    for batch_data, batch_label in loop:
        batch_data = batch_data.to(device)
        batch_label = batch_label.to(device)
        optimizer.zero_grad()
        # 编码阶段，得到HI和Q_bearing
        hi_seq, _ = encoder(batch_data)
        # 计算损失
        loss = loss_fun(hi_seq, batch_label)
        # 反向传播与优化
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        # 实时更新进度条上的 Loss
        loop.set_postfix(loss=total_loss / (loop.n + 1))
        # 每个 epoch 结束后打印平均损失
    avg_loss = total_loss / len(train_loader)
    loop.set_postfix(loss=avg_loss)
    return avg_loss
def test(encoder, test_loader, device):
    encoder.eval()
    all_hi = []  # 用于保存所有批次的健康指征（HI）

    with torch.no_grad():
        for batch_data in tqdm(test_loader):
            batch_data = batch_data.to(device)
            # 编码阶段
            if isinstance(encoder, Encoder_Duibi):
                hi, _ = encoder(batch_data)  # 确保能正确解包两个值
            else:
                hi, _ = encoder(batch_data)
            # 保存每个批次的 HI
            all_hi.append(hi.cpu().numpy())  # 保存为 numpy 数组以便后续处理

    # 将所有保存的 hi 合并成一个大数组
    all_hi = np.concatenate(all_hi, axis=0)  # (total_samples, sequence_length)
    return all_hi

def pack(train_or_test, train_data_path=None, train_algorithm=None, model_save_path=None,
         test_data_path=None, test_algorithm=None, model_test_path=None, epochs=1):
    # 移除downsample_rate参数
    if train_or_test == 'train':
        input_dim = 2
        seq_len = 2000
        batch_size = 8
        hidden_dim = 64
        # 使用传入的epochs参数而不是硬编码
        epochs = epochs if epochs > 0 else 20
        if torch.cuda.is_available():
            device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            device = torch.device('mps')
        else:
            device = torch.device('cpu')
        # 初始化模型
        if train_algorithm == 'Transformer Physics':
            model = Encoder(input_dim=input_dim, hidden_dim=hidden_dim, seq_len=seq_len)
            model.to(device)
        elif train_algorithm == 'Transformer':
            model = Encoder_Duibi(input_dim=input_dim, hidden_dim=hidden_dim, seq_len=seq_len)
            model.to(device)
        
        # 固定downsample_rate为10
        data, label, _ = get_pretrain_dataAndlabel(train_data_path, test=False)
        train_tensor = torch.tensor(data, dtype=torch.float32)
        label_tensor = torch.tensor(label, dtype=torch.float32)
        dataset = TensorDataset(train_tensor, label_tensor)
        train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        optimizer = optim.Adam(model.parameters(), lr=1e-4)
        loss_fun = nn.MSELoss()
        for epoch in range(0, epochs):
            _ = train(model, train_loader, optimizer, epoch, epochs, device, loss_fun)
        
        # 保存模型参数时，也一并保存模型类型信息
        state_dict = model.state_dict()
        model_info = {
            'state_dict': state_dict,
            'model_type': train_algorithm  # 保存模型类型信息
        }
        torch.save(model_info, model_save_path)

        return f'算法{train_algorithm}训练已完成，训练模型已经保存在{model_save_path}'

    if train_or_test == 'test':
        input_dim = 2
        seq_len = 2000
        batch_size = 32
        hidden_dim = 64
        if torch.cuda.is_available():
            device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            device = torch.device('mps')
        else:
            device = torch.device('cpu')
        
        # 加载模型信息，包括模型类型
        try:
            checkpoint = torch.load(model_test_path, map_location=device)
            
            # 检查是否为新格式（包含模型类型信息）
            if isinstance(checkpoint, dict) and 'model_type' in checkpoint:
                model_type = checkpoint['model_type']
                state_dict = checkpoint['state_dict']
            else:
                # 如果是旧格式或者没有保存模型类型，则使用前端传入的算法类型
                model_type = test_algorithm
                state_dict = checkpoint
                
            # 根据模型类型创建相应的模型实例
            if model_type == 'Transformer Physics':
                model_test = Encoder(input_dim=input_dim, hidden_dim=hidden_dim, seq_len=seq_len)
            else:  # 默认使用 'Transformer'
                model_test = Encoder_Duibi(input_dim=input_dim, hidden_dim=hidden_dim, seq_len=seq_len)
                
            # 加载模型参数
            model_test.load_state_dict(state_dict)
            model_test.to(device)
            
        except Exception as e:
            # 如果加载失败，输出错误信息并尝试使用传入的算法类型
            print(f"加载模型失败: {e}")
            print("尝试使用传入的算法类型创建模型...")
            
            if test_algorithm == 'Transformer Physics':
                model_test = Encoder(input_dim=input_dim, hidden_dim=hidden_dim, seq_len=seq_len)
            else:  # 默认使用 'Transformer'
                model_test = Encoder_Duibi(input_dim=input_dim, hidden_dim=hidden_dim, seq_len=seq_len)
                
            # 直接加载参数，可能会失败
            model_test.load_state_dict(torch.load(model_test_path, map_location=device))
            model_test.to(device)
        
        # 固定downsample_rate为10
        data_test, label_test, length = get_pretrain_dataAndlabel(test_data_path, test=True)
        number = 1
        data_test = data_test[length * (number - 1):length * (number), :]
        label_test = label_test[length * (number - 1):length * (number), :]
        test_tensor = torch.tensor(data_test, dtype=torch.float32)
        test_loader = torch.utils.data.DataLoader(test_tensor, batch_size=batch_size, shuffle=False)
        output = test(model_test, test_loader, device)
        output = output.flatten().reshape(-1, 1)
        label_test = label_test.flatten().reshape(-1, 1)
        rmse = calculate_rmse(label_test, output)
        mae = np.mean(np.abs(output - label_test))
        if len(label_test) < 200:
            label_test = map_and_interpolate(label_test, 607)
            output = map_and_interpolate(output, 607)
        elif len(label_test) > 200:
            label_test = map_and_interpolate(label_test, 198)
            output = map_and_interpolate(output, 198)
        return label_test.reshape(-1).tolist(), output.reshape(-1).tolist(), rmse, mae

class SimpleRegressionNet(nn.Module):
    def __init__(self):
        super(SimpleRegressionNet, self).__init__()
        self.fc1 = nn.Linear(1, 32)  # 输入为 1 个电流值，输出 32 个特征
        self.fc2 = nn.Linear(32, 16) # 隐藏层
        self.fc3 = nn.Linear(16, 1)  # 输出层，预测转矩

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class CNN1D(nn.Module):
    def __init__(self, input_channels=3, input_length=69):
        super(CNN1D, self).__init__()

        # 一维卷积层 1
        self.conv1 = nn.Conv1d(in_channels=input_channels, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm1d(64)  # 批归一化

        # 一维卷积层 2
        self.conv2 = nn.Conv1d(in_channels=64, out_channels=32, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(32)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)

        # 计算全连接层输入维度
        self.fc_input_dim = 32 * (input_length // 2)  # 经过 3 层池化后长度为 L // 2^3

        # 全连接层
        self.fc1 = nn.Linear(self.fc_input_dim, 8)
        self.fc2 = nn.Linear(8, 1)  # 输出维度为 (B, 1)

    def forward(self, x):
        # 第一层卷积 -> 批归一化 -> 激活 -> 池化
        x = F.relu(self.bn1(self.conv1(x)))
        # 第二层卷积 -> 批归一化 -> 激活 -> 池化
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))

        # 展平
        x = x.view(x.size(0), -1)
        # 全连接层 1 -> 激活
        x = F.relu(self.fc1(x))
        # 全连接层 2（输出层）
        x = nn.Sigmoid()(self.fc2(x))
        return x


class CurrentTorqueDataset(Dataset):
    def __init__(self, currents, torques):
        """
        currents: shape (N, 1) -> 每个样本的电流
        torques: shape (N, 1) -> 每个样本的转矩
        """
        self.currents = torch.tensor(currents, dtype=torch.float32)
        self.torques = torch.tensor(torques, dtype=torch.float32)

    def __len__(self):
        return len(self.currents)

    def __getitem__(self, idx):
        return self.currents[idx], self.torques[idx]


class IMappingFSolver():

    def __init__(self, base_path, trained_list=None, base_path2=None, trained_list2=None, test_list=None):
        self.base_path = base_path
        if not trained_list:
            self.trained_list = ['0' + str(i) for i in range(6,26)]
        else:
            self.trained_list = trained_list

        self.base_path2 = base_path2
        self.trained_list2 = trained_list2

        if not test_list:
            self.test_list = ['0' + str(i) for i in range(26,35)]
        else:
            self.test_list = test_list

        self.build_model()

        self.model_save_path = self.base_path + 'i_f_mapping_model.pth'

    def get_trained_data(self):
        if os.path.exists(self.base_path + 'i_f_mapping_trained_i.npy'):
            all_i = np.load(self.base_path + 'i_f_mapping_trained_i.npy')
            all_FrictionTorque = np.load(self.base_path + 'i_f_mapping_trained_f.npy')
            return all_i, all_FrictionTorque

        all_i = []
        all_FrictionTorque = []

        for t in self.trained_list:
            file_dir = self.base_path + t + '/'
            files = os.listdir(file_dir)
            for file in files:
                data = scipy.io.loadmat(file_dir + file)
                i = data['i']
                i = i[::1250]
                FrictionTorque = data['FrictionTorque']
                FrictionTorque = FrictionTorque[::1250]
                all_i.append(i)
                all_FrictionTorque.append(FrictionTorque)

        if self.base_path2 and self.trained_list2:
            for t in self.trained_list2:
                file_dir = self.base_path2 + t + '/'
                files = os.listdir(file_dir)
                for file in files:
                    data = scipy.io.loadmat(file_dir + file)
                    i = data['i']
                    i = i[::1250]
                    FrictionTorque = data['FrictionTorque']
                    FrictionTorque = FrictionTorque[::1250]
                    all_i.append(i)
                    all_FrictionTorque.append(FrictionTorque)

        all_i = np.concatenate(all_i, axis=0)
        all_FrictionTorque = np.concatenate(all_FrictionTorque, axis=0)

        print(all_i.shape)

        np.save(self.base_path + 'i_f_mapping_trained_i', all_i)
        np.save(self.base_path + 'i_f_mapping_trained_f', all_FrictionTorque)

        return all_i, all_FrictionTorque

    def get_test_data(self):

        if os.path.exists(self.base_path + 'i_f_mapping_test_i.npy'):
            all_i = np.load(self.base_path + 'i_f_mapping_test_i.npy')
            all_FrictionTorque = np.load(self.base_path + 'i_f_mapping_test_f.npy')
            return all_i, all_FrictionTorque

        all_i = []
        all_FrictionTorque = []

        for t in self.test_list:
            file_dir = self.base_path + t + '/'
            files = os.listdir(file_dir)
            for file in files:
                data = scipy.io.loadmat(file_dir + file)
                i = data['i']
                i = i[::1250]
                FrictionTorque = data['FrictionTorque']
                FrictionTorque = FrictionTorque[::1250]
                all_i.append(i)
                all_FrictionTorque.append(FrictionTorque)
        all_i = np.concatenate(all_i, axis=0)
        all_FrictionTorque = np.concatenate(all_FrictionTorque, axis=0)

        print(all_i.shape)

        np.save(self.base_path + 'i_f_mapping_test_i', all_i)
        np.save(self.base_path + 'i_f_mapping_test_f', all_FrictionTorque)

        return all_i, all_FrictionTorque

    def get_loader(self):
        train_i, train_f = self.get_trained_data()
        test_i, test_f = self.get_test_data()

        train_dataset = CurrentTorqueDataset(train_i, train_f)
        test_dataset = CurrentTorqueDataset(test_i, test_f)
        self.train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        self.test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    def build_model(self):
        self.model = SimpleRegressionNet()

    def train_and_test(self):
        criterion = nn.MSELoss()  # 损失函数：均方误差
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)  # 优化器：Adam

        # 训练模型
        epochs = 10
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            for currents_batch, torques_batch in self.train_loader:
                optimizer.zero_grad()
                outputs = self.model(currents_batch)
                loss = criterion(outputs, torques_batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            print(f"Epoch {epoch + 1}/{epochs}, Loss: {total_loss / len(self.train_loader):.8f}")

        # 测试模型
        self.model.eval()
        test_loss = 0
        with torch.no_grad():
            for currents_batch, torques_batch in self.test_loader:
                outputs = self.model(currents_batch)
                loss = criterion(outputs, torques_batch)
                test_loss += loss.item()

        print(f"Test Loss: {test_loss / len(self.test_loader):.8f}")

        torch.save(self.model.state_dict(), self.model_save_path)
        print("Model parameters saved successfully.")

def least_square_model(n, F_r, F_a, mu_EHL, viscosity):
    d = 25
    D = 47
    R_1 = 5.03e-7
    R_2 = 1.97
    R_3 = 1.9e-12
    S_1 = 1.3e-2
    S_2 = 0.68
    S_3 = 1.91e-12
    K_z = 4.4
    K_rs = 3e-8

    F_r = abs(F_r)
    F_a = abs(F_a)

    e = 2.718281828459045
    d_m = 0.5 * (d + D)

    # phi_ish = inlet shear heating reduction factor
    phi_ish = 1 / (1 + 1.84e-9 * np.power(n * d_m, 1.28) * np.power(viscosity, 0.64))

    # phi_rs = kinematic replenishment/starvation reduction factor
    phi_rs = 1 / np.power(e, K_rs * viscosity * n * (d + D) * np.power(K_z / (2 * (D - d)), 0.5))

    F_g = R_3 * np.power(d_m, 4) * np.power(n, 2)

    G_rr = R_1 * np.power(d_m, 1.97) * np.power((F_r + F_g + R_2 * F_a), 0.54)

    M_rr = phi_ish * phi_rs * G_rr * np.power(viscosity * n, 0.6)

    phi_bl = 1 / np.power(e, 2.6e-8 * np.power(n * viscosity, 1.4) * d_m)

    mu_bl = 0.15*(n==0).astype(int) + 0.12*(n!=0).astype(int)

    mu_sl = phi_bl * mu_bl + (1 - phi_bl) * mu_EHL

    F_g = S_3 * np.power(d_m, 4) * np.power(n, 2)

    G_sl = S_1 * np.power(d_m, 0.26) * (np.power(F_r + F_g, 4 / 3) + S_2 * np.power(F_a, 4 / 3))

    M_sl = G_sl * mu_sl

    All = M_rr + M_sl

    return All * 0.001


def least_square_model_wrap(x, mu_EHL, viscosity):
    n, F_r, F_a, = x  # 解包输入
    return least_square_model(n, F_r, F_a, mu_EHL, viscosity)

# 数据集定义
class CustomDataset(Dataset):
    def __init__(self, inputs, targets):
        """
        inputs: shape (N, C, L) -> 样本输入
        targets: shape (N, 1) -> 样本目标值
        """
        self.inputs = torch.tensor(inputs, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.float32)

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        return self.inputs[idx], self.targets[idx]


class SimplePredictSolver():

    def __init__(self, train_data_path=None, train_model_save_path=None, test_data_path=None, test_model_load_path=None, epochs=1):
        self.build_model()
        self.model_save_path = train_model_save_path
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path
        self.test_model_load_path = test_model_load_path
        self.epochs = epochs
        self.window = 1250
        # 初始化数据加载器和归一化器
        self.train_loader = None
        self.test_loader = None
        self.scalers = []

    # 新增方法，初始化训练和测试数据
    def initialize_data(self):
        """初始化训练和测试数据，确保归一化器被正确训练"""
        # 如果有训练数据路径，加载训练数据
        if self.train_data_path:
            train_data, train_label = self.get_trained_data()
            # 数据归一化
            B0, C, L = train_data.shape
            self.scalers = []  # 重置scalers
            train_normalized = np.zeros_like(train_data, dtype=np.float32)
            
            # 对每个通道的数据进行归一化处理
            for c in range(C):
                channel_train_data = train_data[:, c, :].reshape(-1, 1)
                scaler = MinMaxScaler()
                train_normalized_channel = scaler.fit_transform(channel_train_data).reshape(B0, L)
                train_normalized[:, c, :] = train_normalized_channel
                self.scalers.append(scaler)
                
            # 创建训练数据加载器
            train_dataset = CustomDataset(train_normalized, train_label)
            self.train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
        
        # 如果有测试数据路径，加载测试数据
        if self.test_path_exists():
            test_data, test_label = self.get_test_data()
            # 数据归一化，使用已训练好的归一化器（如果有）
            B1, C, L = test_data.shape
            test_normalized = np.zeros_like(test_data, dtype=np.float32)
            
            # 如果没有scalers（训练中没有提供训练数据），则创建新的scalers
            if not self.scalers:
                self.scalers = []
                for c in range(C):
                    channel_test_data = test_data[:, c, :].reshape(-1, 1)
                    scaler = MinMaxScaler()
                    test_normalized_channel = scaler.fit_transform(channel_test_data).reshape(B1, L)
                    test_normalized[:, c, :] = test_normalized_channel
                    self.scalers.append(scaler)
            else:
                # 使用训练数据创建的scalers
                for c in range(C):
                    channel_test_data = test_data[:, c, :].reshape(-1, 1)
                    test_normalized_channel = self.scalers[c].transform(channel_test_data).reshape(B1, L)
                    test_normalized[:, c, :] = test_normalized_channel
            
            # 创建测试数据加载器
            test_dataset = CustomDataset(test_normalized, test_label)
            self.test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    def test_path_exists(self):
        """检查测试数据路径是否存在"""
        return self.test_data_path is not None and os.path.isfile(self.test_data_path)

    def get_trained_data(self):
        train_data_label_df = pd.read_csv(self.train_data_path, index_col=0)
        train_data_label = train_data_label_df.values
        B_L, C= train_data_label.shape
        train_data_label = train_data_label.reshape(B_L//69, 69, C).transpose((0, 2, 1))
        all_trained_data = train_data_label[:, 0:3, :]
        all_trained_label = train_data_label[:, -1, 0].reshape(B_L//69, 1)

        return all_trained_data, all_trained_label

    def get_test_data(self):
        test_data_label_df = pd.read_csv(self.test_data_path, index_col=0)
        test_data_label = test_data_label_df.values
        B_L, C= test_data_label.shape
        test_data_label = test_data_label.reshape(B_L//69, 69, C).transpose((0, 2, 1))
        all_tested_data = test_data_label[:, 0:3, :]
        all_tested_label = test_data_label[:, -1, 0].reshape(B_L//69, 1)

        return all_tested_data, all_tested_label

    # 已废弃，使用initialize_data替代
    def get_train_loader(self):
        # 这个方法保留以兼容原始代码，但内部逻辑移到initialize_data
        if not self.train_loader:
            self.initialize_data()
        return self.train_loader

    # 已废弃，使用initialize_data替代
    def get_test_loader(self):
        # 这个方法保留以兼容原始代码，但内部逻辑移到initialize_data
        if not self.test_loader:
            self.initialize_data()
        return self.test_loader

    def build_model(self):
        self.model = CNN1D(input_channels=3)

    def train(self):
        # 确保数据已经准备好
        if not self.train_loader:
            self.initialize_data()
            
        # 如果没有测试加载器（测试数据路径不存在），使用训练数据创建一个
        if not self.test_loader:
            # 创建相同的数据集，但不打乱顺序
            test_dataset = self.train_loader.dataset
            self.test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
        
        criterion = nn.MSELoss()  # 回归任务使用均方误差损失
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        num_epochs = self.epochs

        for epoch in range(num_epochs):
            self.model.train()
            print(f"\nEpoch {epoch + 1}/{num_epochs}")
            total_loss = 0
            for inputs, targets in self.train_loader:
                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {total_loss / len(self.train_loader):.4f}")

            self.model.eval()  # 切换到评估模式
            total_loss = 0
            with torch.no_grad():
                for inputs, targets in self.test_loader:
                    outputs = self.model(inputs)
                    loss = criterion(outputs, targets)
                    total_loss += loss.item()
            avg_loss = total_loss / len(self.test_loader)
            print(f"Validation Loss: {avg_loss:.4f}")

        torch.save(self.model.state_dict(), self.model_save_path)
        # 简化返回的训练结果字符串
        return f"训练完成，模型已保存：{os.path.basename(self.model_save_path)}"

    def test(self):
        try:
            self.model.load_state_dict(torch.load(self.test_model_load_path))
        except Exception as e:
            print(f"加载模型失败: {e}")
            raise RuntimeError(f"加载模型失败: {e}")

        # 测试模式下，直接处理测试数据，不再依赖训练数据
        test_data_label_df = pd.read_csv(self.test_data_path, index_col=0)
        test_data_label = test_data_label_df.values
        B_L, C= test_data_label.shape
        test_data_label = test_data_label.reshape(B_L//69, 69, C).transpose((0, 2, 1))
        all_tested_data = test_data_label[:, 0:3, :]
        all_tested_label = test_data_label[:, -1, 0].reshape(B_L//69, 1)

        test_data = torch.Tensor(all_tested_data)
        test_label = torch.Tensor(all_tested_label)

        # 数据归一化
        B, C, L = test_data.shape
        
        # 初始化归一化后的数据和scalers
        test_normalized = np.zeros_like(test_data, dtype=np.float32)
        self.scalers = []  # 确保scalers被初始化

        for c in range(C):
            channel_test_data = test_data[:, c, :].reshape(-1, 1)
            scaler = MinMaxScaler()
            test_normalized_channel = scaler.fit_transform(channel_test_data).reshape(B, L)
            test_normalized[:, c, :] = test_normalized_channel
            self.scalers.append(scaler)

        test_data = torch.Tensor(test_normalized)
        self.model.eval()
        outputs = self.model(test_data)
        loss = nn.MSELoss()(outputs, test_label)

        # 计算 RMSE
        rmse = torch.sqrt(torch.mean((outputs - test_label) ** 2)).item()
        # 计算 MAE
        mae = torch.mean(torch.abs(outputs - test_label)).item()

        outputs = outputs.detach().cpu().numpy()*B
        test_label = test_label.detach().cpu().numpy()*B

        print('RMSE = {}'.format(rmse))
        print('MAE = {}'.format(mae))

        return test_label.reshape(-1).tolist(), outputs.reshape(-1).tolist(), rmse, mae


class FusionPredictSolver():

    def __init__(self, train_data_path=None, train_model_save_path=None, test_data_path=None, test_model_load_path=None, epochs=1):
        self.build_model()
        self.model_save_path = train_model_save_path
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path
        self.test_model_load_path = test_model_load_path
        self.epochs = epochs
        self.window = 1250
        # 初始化数据加载器和归一化器
        self.train_loader = None
        self.test_loader = None
        self.scalers = []

        current_file_path = os.path.dirname(os.path.abspath(__file__))

        try:
            self.i_m_mapping_solver = IMappingFSolver(current_file_path+'/')
            # 使用weights_only=True解决WARNING
            self.i_m_mapping_solver.model.load_state_dict(torch.load(self.i_m_mapping_solver.model_save_path, weights_only=True))
            self.i_m_mapping_solver.model.eval()
        except Exception as e:
            print(f"警告：加载i_m_mapping模型失败，部分功能可能不可用: {e}")
            
    # 新增方法，初始化训练和测试数据
    def initialize_data(self):
        """初始化训练和测试数据加载器"""
        if self.train_data_path and self.test_data_path:
            train_data, train_label = self.get_trained_data()
            test_data, test_label = self.get_test_data()
            
            # 数据归一化处理
            B0, C, L = train_data.shape
            B1, C, L = test_data.shape
            self.scalers = []
            
            train_normalized = np.zeros_like(train_data, dtype=np.float32)
            test_normalized = np.zeros_like(test_data, dtype=np.float32)
            
            for c in range(C):
                channel_train_data = train_data[:, c, :].reshape(-1, 1)
                channel_test_data = test_data[:, c, :].reshape(-1, 1)
                
                scaler = MinMaxScaler()
                train_normalized_channel = scaler.fit_transform(channel_train_data).reshape(B0, L)
                test_normalized_channel = scaler.transform(channel_test_data).reshape(B1, L)
                
                train_normalized[:, c, :] = train_normalized_channel
                test_normalized[:, c, :] = test_normalized_channel
                
                self.scalers.append(scaler)
                
            # 创建数据加载器
            train_dataset = CustomDataset(train_normalized, train_label)
            test_dataset = CustomDataset(test_normalized, test_label)
            
            self.train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
            self.test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
        elif self.train_data_path:
            # 如果只有训练数据，用训练数据代替测试数据
            train_data, train_label = self.get_trained_data()
            B0, C, L = train_data.shape
            self.scalers = []
            
            train_normalized = np.zeros_like(train_data, dtype=np.float32)
            
            for c in range(C):
                channel_train_data = train_data[:, c, :].reshape(-1, 1)
                scaler = MinMaxScaler()
                train_normalized_channel = scaler.fit_transform(channel_train_data).reshape(B0, L)
                train_normalized[:, c, :] = train_normalized_channel
                self.scalers.append(scaler)
                
            train_dataset = CustomDataset(train_normalized, train_label)
            self.train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
            # 用20%的训练数据作为验证集
            val_size = int(0.2 * len(train_dataset))
            train_size = len(train_dataset) - val_size
            train_subset, val_subset = torch.utils.data.random_split(
                train_dataset, [train_size, val_size]
            )
            self.test_loader = DataLoader(val_subset, batch_size=64, shuffle=False)
        elif self.test_data_path:
            # 如果只有测试数据，只创建测试加载器
            test_data, test_label = self.get_test_data()
            B1, C, L = test_data.shape
            self.scalers = []
            
            test_normalized = np.zeros_like(test_data, dtype=np.float32)
            
            for c in range(C):
                channel_test_data = test_data[:, c, :].reshape(-1, 1)
                scaler = MinMaxScaler()
                test_normalized_channel = scaler.fit_transform(channel_test_data).reshape(B1, L)
                test_normalized[:, c, :] = test_normalized_channel
                self.scalers.append(scaler)
                
            test_dataset = CustomDataset(test_normalized, test_label)
            self.test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # 其他代码保持不变
    def physics_calibration(self, i, Gimbal_speed, w):
        RotorInertia = 0.23875
        BearingSpan = 0.134
        initial_guess = [0.4, 25]
        fittedFricitionTorque = self.i_m_mapping_solver.model(torch.Tensor(i)).detach().numpy().reshape(-1)
        w_rad_s = (w * math.pi / 30).reshape(-1)
        sampled_F_r = w_rad_s * RotorInertia * Gimbal_speed / BearingSpan
        sampled_n = w.reshape(-1)
        sampled_F_a = np.ones_like(sampled_F_r) * 120

        params_opt, params_covariance = curve_fit(least_square_model_wrap,
                                                  (sampled_n, sampled_F_r, sampled_F_a), fittedFricitionTorque,
                                                  p0=initial_guess, bounds=([0., 0], [1, 100.]))
        mu_EHL_estimated, viscosity_estimated = params_opt

        # print(f"Estimated mu_EHL: {mu_EHL_estimated:.5f}")
        # print(f"Estimated viscosity: {viscosity_estimated:.5f}")
        return mu_EHL_estimated, viscosity_estimated

    def get_trained_data(self):
        train_data_label_df = pd.read_csv(self.train_data_path, index_col=0)
        train_data_label = train_data_label_df.values
        B_L, C= train_data_label.shape
        train_data_label = train_data_label.reshape(B_L//69, 69, C).transpose((0, 2, 1))
        all_trained_data = train_data_label[:, :-1, :]
        all_trained_label = train_data_label[:, -1, 0].reshape(B_L//69, 1)

        return all_trained_data, all_trained_label

    def get_test_data(self):
        test_data_label_df = pd.read_csv(self.test_data_path, index_col=0)
        test_data_label = test_data_label_df.values
        B_L, C= test_data_label.shape
        test_data_label = test_data_label.reshape(B_L//69, 69, C).transpose((0, 2, 1))
        all_tested_data = test_data_label[:, :-1, :]
        all_tested_label = test_data_label[:, -1, 0].reshape(B_L//69, 1)

        return all_tested_data, all_tested_label

    def get_loader(self):
        # 为了兼容性保留此方法但内部逻辑迁移到initialize_data
        if not self.train_loader or not self.test_loader:
            self.initialize_data()

    def build_model(self):
        self.model = CNN1D(input_channels=5)

    def train(self):
        # 确保数据已准备好
        if not self.train_loader or not self.test_loader:
            self.initialize_data()
        
        criterion = nn.MSELoss()  # 回归任务使用均方误差损失
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        num_epochs = self.epochs

        for epoch in range(num_epochs):
            self.model.train()
            print(f"\nEpoch {epoch + 1}/{num_epochs}")
            total_loss = 0
            for inputs, targets in self.train_loader:
                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {total_loss / len(self.train_loader):.4f}")

            self.model.eval()  # 切换到评估模式
            total_loss = 0
            with torch.no_grad():
                for inputs, targets in self.test_loader:
                    outputs = self.model(inputs)
                    loss = criterion(outputs, targets)
                    total_loss += loss.item()
            avg_loss = total_loss / len(self.test_loader)
            print(f"Validation Loss: {avg_loss:.4f}")

        torch.save(self.model.state_dict(), self.model_save_path)
        # 简化返回的训练结果字符串
        return f"训练完成，模型已保存：{os.path.basename(self.model_save_path)}"

    def test(self):
        try:
            # 使用weights_only=True解决WARNING
            self.model.load_state_dict(torch.load(self.test_model_load_path, weights_only=True))
        except Exception as e:
            print(f"加载模型失败: {e}")
            raise RuntimeError(f"加载模型失败: {e}")

        try:
            # 测试模式下，直接处理测试数据，不再依赖训练数据
            test_data_label_df = pd.read_csv(self.test_data_path, index_col=0)
            test_data_label = test_data_label_df.values
            B_L, C = test_data_label.shape
            test_data_label = test_data_label.reshape(B_L // 69, 69, C).transpose((0, 2, 1))
            all_tested_data = test_data_label[:, :-1, :]
            all_tested_label = test_data_label[:, -1, 0].reshape(B_L // 69, 1)

            test_data = torch.Tensor(all_tested_data)
            test_label = torch.Tensor(all_tested_label)

            # 数据归一化
            B, C, L = test_data.shape
            
            # 确保scalers被正确初始化并且有足够的元素
            # 如果scalers列表为空或长度不足，重新初始化
            if len(self.scalers) < C:
                print(f"重新初始化scalers - 需要{C}个元素，当前有{len(self.scalers)}个")
                self.scalers = []
                # 对每个通道数据单独创建一个scaler
                for c in range(C):
                    channel_test_data = test_data[:, c, :].reshape(-1, 1)
                    scaler = MinMaxScaler()
                    # 使用fit_transform来确保scaler被正确训练
                    scaler.fit(channel_test_data)
                    self.scalers.append(scaler)
            
            # 初始化归一化后的数据
            test_normalized = np.zeros_like(test_data, dtype=np.float32)
            
            # 使用scalers归一化每个通道的数据
            for c in range(C):
                channel_test_data = test_data[:, c, :].reshape(-1, 1)
                test_normalized_channel = self.scalers[c].transform(channel_test_data).reshape(B, L)
                test_normalized[:, c, :] = test_normalized_channel
            
            test_data = torch.Tensor(test_normalized)
            self.model.eval()
            outputs = self.model(test_data)
            
            # 计算评估指标
            rmse = torch.sqrt(torch.mean((outputs - test_label) ** 2)).item()
            mae = torch.mean(torch.abs(outputs - test_label)).item()
            
            outputs = outputs.detach().cpu().numpy() * B
            test_label = test_label.detach().cpu().numpy() * B
            
            print('RMSE = {}'.format(rmse))
            print('MAE = {}'.format(mae))
            
            return test_label.reshape(-1).tolist(), outputs.reshape(-1).tolist(), rmse, mae
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"测试过程中出现错误: {e}\n{error_detail}")
            raise RuntimeError(f"测试过程中出现错误: {e}")
