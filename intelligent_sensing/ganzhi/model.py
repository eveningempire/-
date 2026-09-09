import datetime
import os
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
# from torch.utils.tensorboard.writer import SummaryWriter
from torch_geometric.data import Batch, Data
from torch_geometric.nn import GCNConv
from torch_geometric.utils import dense_to_sparse

"""
class GCNLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super(GCNLayer, self).__init__()
        self.conv = GCNConv(in_features, out_features)

    def forward(self, x, edge_index, edge_weight):
        # x: (batch_size, num_nodes, in_features)
        batch_size, num_nodes, _ = x.shape

        # 创建 Data 对象列表
        data_list = []
        for i in range(batch_size):
            data = Data(x=x[i], edge_index=edge_index, edge_attr=edge_weight)
            data_list.append(data)

        # 批处理
        batch = Batch.from_data_list(data_list)

        # 应用 GCNConv
        out = self.conv(batch.x, batch.edge_index, batch.edge_attr)

        # 重新整形为 (batch_size, num_nodes, out_features)
        out = out.view(batch_size, num_nodes, -1)
        return out

    def get_bimodal_regularization(self, edge_weights):
        # 双峰分布正则项 H(p) = -p log p - (1-p) log(1-p)
        p = torch.sigmoid(edge_weights)  # 确保在 [0,1]
        h = -p * torch.log(p + 1e-8) - (1 - p) * torch.log(1 - p + 1e-8)
        return torch.sum(h)  # 鼓励低熵


class RegressionHead(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(RegressionHead, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

    def forward(self, x):
        raise NotImplementedError


class LinearRegressionHead(RegressionHead):
    def __init__(self, input_dim, output_dim):
        super(LinearRegressionHead, self).__init__(input_dim, output_dim)
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, x):
        return self.linear(x)


class SimpleGCNModel(nn.Module):
    def __init__(self, num_nodes=3, node_features=69, hidden_dim=32, output_dim=1, lambda_reg=0.01):
        super(SimpleGCNModel, self).__init__()
        self.num_nodes = num_nodes
        self.node_features = node_features
        self.lambda_reg = lambda_reg

        # 可学习的边权重，初始化为随机值
        self.edge_weights = nn.Parameter(torch.rand(num_nodes, num_nodes) * 0.2 + 0.4)

        # 创建完整的 edge_index（无向图，所有可能的无向边，包括自环）
        edge_index = []
        for i in range(num_nodes):
            for j in range(i, num_nodes):  # 只添加 i <= j，避免重复
                edge_index.append([i, j])
        self.edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

        # GCN 层
        self.gcn1 = GCNLayer(node_features, hidden_dim)
        self.gcn2 = GCNLayer(hidden_dim, hidden_dim)

        # Regression head - 只使用Linear
        self.reg_head = LinearRegressionHead(hidden_dim, output_dim)

        # 归一化器
        self.channel_scaler = StandardScaler()
        self.label_scaler = MinMaxScaler()

        # 标志是否已拟合归一化器
        self.channel_fitted = False
        self.label_fitted = False

    def fit_scalers(self, data, labels):
        # data: (N, 3, 69)
        # labels: (N, output_dim)
        # 通道归一化：对每个通道的69维数据标准化
        N, C, L = data.shape
        data_flat = data.transpose(0, 2, 1).reshape(-1, C)  # (N*L, C)
        self.channel_scaler.fit(data_flat)
        self.channel_fitted = True

        # 标签归一化
        self.label_scaler.fit(labels)
        self.label_fitted = True

    def normalize_channels(self, data):
        if not self.channel_fitted:
            raise ValueError("Channel scaler not fitted. Call fit_scalers first.")
        N, C, L = data.shape
        data_flat = data.transpose(1, 2).reshape(-1, C)  # (N*L, C)
        data_norm = self.channel_scaler.transform(data_flat)
        data_norm = data_norm.reshape(N, L, C).transpose(0, 2, 1)  # 转回 (N, C, L)
        return torch.tensor(data_norm, dtype=data.dtype, device=data.device)

    def normalize_labels(self, labels):
        if not self.label_fitted:
            raise ValueError("Label scaler not fitted. Call fit_scalers first.")
        return self.label_scaler.transform(labels)

    def denormalize_labels(self, labels_norm):
        if not self.label_fitted:
            raise ValueError("Label scaler not fitted. Call fit_scalers first.")
        return self.label_scaler.inverse_transform(labels_norm)

    def get_bimodal_regularization(self):
        return self.gcn1.get_bimodal_regularization(self.edge_weights) + self.gcn2.get_bimodal_regularization(
            self.edge_weights
        )

    def forward(self, x):
        # x: (batch_size, 3, 69)
        # 归一化通道
        x_norm = self.normalize_channels(x)

        # 获取边权重（对应无向图的上三角，使用 sigmoid 确保 [0,1]）
        edge_weight = []
        for i in range(self.num_nodes):
            for j in range(i, self.num_nodes):
                edge_weight.append(torch.sigmoid(self.edge_weights[i, j]))
        edge_weight = torch.stack(edge_weight)

        # GCN
        x_gcn = self.gcn1(x_norm, self.edge_index, edge_weight)  # (batch, 3, hidden)
        x_gcn = F.relu(x_gcn)
        x_gcn = self.gcn2(x_gcn, self.edge_index, edge_weight)  # (batch, 3, hidden)
        x_gcn = F.relu(x_gcn)

        # 全局平均池化
        x_pool = x_gcn.mean(dim=1)  # (batch, hidden)

        # Regression head
        out = self.reg_head(x_pool)  # (batch, output_dim)
        return out

    def save_scalers(self, path="scalers/scalers_base.pkl"):
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "channel_scaler": self.channel_scaler,
                    "label_scaler": self.label_scaler,
                    "channel_fitted": self.channel_fitted,
                    "label_fitted": self.label_fitted,
                },
                f,
            )

    def load_scalers(self, path="scalers/scalers_base.pkl"):
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
                self.channel_scaler = data["channel_scaler"]
                self.label_scaler = data["label_scaler"]
                self.channel_fitted = data["channel_fitted"]
                self.label_fitted = data["label_fitted"]

    def train_model(
        self,
        train_data,
        train_labels,
        val_data=None,
        val_labels=None,
        epochs=100,
        lr=0.001,
        batch_size=32,
        save_path=None,
        patience=10,
        exp_name="Experiment",
        train_time=None,
    ):
        optimizer = torch.optim.Adam(self.parameters(), lr=lr)
        criterion = nn.MSELoss()

        # 归一化标签
        train_labels_norm = torch.tensor(self.normalize_labels(train_labels.numpy()), dtype=torch.float32)
        if val_data is not None and val_labels is not None:
            val_labels_norm = torch.tensor(self.normalize_labels(val_labels.numpy()), dtype=torch.float32)

        # TensorBoard
        if train_time is None:
            train_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tensorboard_log_dir = f"tensorboard_logs/{exp_name}-{train_time}"
        os.makedirs(tensorboard_log_dir, exist_ok=True)
        writer = SummaryWriter(log_dir=tensorboard_log_dir)

        best_loss = float("inf")
        patience_counter = 0

        for epoch in range(epochs):
            # 训练
            self.train()
            train_loss = 0
            num_train_batches = len(train_data) // batch_size
            for i in range(0, len(train_data), batch_size):
                batch_data = train_data[i : i + batch_size]
                batch_labels = train_labels_norm[i : i + batch_size]

                optimizer.zero_grad()
                outputs = self(batch_data)
                loss = criterion(outputs, batch_labels)
                # 添加双峰正则化
                reg_loss = self.get_bimodal_regularization()
                total_loss = loss + self.lambda_reg * reg_loss
                total_loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= num_train_batches

            # 验证
            val_loss = 0
            if val_data is not None and val_labels is not None:
                self.eval()
                with torch.no_grad():
                    val_outputs = self(val_data)
                    val_loss = criterion(val_outputs, val_labels_norm).item()

            # 记录到 TensorBoard
            writer.add_scalar("Loss/Train", train_loss, epoch)
            if val_data is not None:
                writer.add_scalar("Loss/Validation", val_loss, epoch)

            # 早停和保存最佳模型
            monitor_loss = val_loss if val_data is not None else train_loss
            if monitor_loss < best_loss:
                best_loss = monitor_loss
                patience_counter = 0
                if save_path:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    torch.save(self.state_dict(), save_path)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch+1}")
                    break

            if (epoch + 1) % 10 == 0:
                if val_data is not None:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
                else:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}")

        writer.close()

    def evaluate_model(self, test_data, test_labels, log_dir=None, step=0):
        self.eval()
        with torch.no_grad():
            predictions = self(test_data)
            predictions_denorm = self.denormalize_labels(predictions.numpy())
            true_labels = test_labels.numpy()

            # 计算各种指标
            mse = mean_squared_error(true_labels, predictions_denorm)
            mae = np.mean(np.abs(true_labels - predictions_denorm))
            rmse = np.sqrt(mse)
            r2 = 1 - np.sum((true_labels - predictions_denorm) ** 2) / np.sum(
                (true_labels - np.mean(true_labels)) ** 2
            )
            max_error = np.max(np.abs(true_labels - predictions_denorm))
            mean_error = np.mean(true_labels - predictions_denorm)

            # print(f"Test MSE: {mse:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")

            # 可视化预测 vs 真实
            if log_dir:
                writer = SummaryWriter(log_dir=log_dir)

                # 保存原始数据为文本
                true_flat = true_labels.flatten()
                pred_flat = predictions_denorm.flatten()
                data_text = "Index\tTrue\tPredicted\tError\n"
                for i in range(len(true_flat)):
                    error = pred_flat[i] - true_flat[i]
                    data_text += f"{i}\t{true_flat[i]:.6f}\t{pred_flat[i]:.6f}\t{error:.6f}\n"
                writer.add_text("Test/Predicted_vs_True_Data", data_text, global_step=step)

                results_dict = {
                    "true_labels": true_flat,
                    "predictions": pred_flat,
                    "errors": pred_flat - true_flat,
                    "mse": mse,
                    "mae": mae,
                    "rmse": rmse,
                    "r2": r2,
                }
                # 保存为pickle文件
                results_path = os.path.join(log_dir, f"prediction_results_step_{step}.pkl")
                with open(results_path, "wb") as f:
                    pickle.dump(results_dict, f)

                # 仍然保留图片可视化
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.scatter(true_flat, pred_flat, alpha=0.6)
                ax.plot(
                    [true_flat.min(), true_flat.max()],
                    [true_flat.min(), true_flat.max()],
                    "r--",
                    label="Perfect Prediction",
                )
                ax.set_xlabel("True Labels")
                ax.set_ylabel("Predicted Labels")
                ax.set_title("Predicted vs True Labels")
                ax.legend()
                ax.grid(True)
                writer.add_figure("Test/Predicted_vs_True", fig, global_step=step)
                writer.close()
                plt.close(fig)

            return mse, mae, rmse, r2
"""

class GCNLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super(GCNLayer, self).__init__()
        self.conv = GCNConv(in_features, out_features)

    def forward(self, x, edge_index, edge_weight):
        # x: (batch_size, num_nodes, in_features)
        batch_size, num_nodes, _ = x.shape
        
        # 创建 Data 对象列表
        data_list = []
        for i in range(batch_size):
            data = Data(x=x[i], edge_index=edge_index, edge_attr=edge_weight)
            data_list.append(data)
        
        # 批处理
        batch = Batch.from_data_list(data_list)
        
        # 应用 GCNConv
        out = self.conv(batch.x, batch.edge_index, batch.edge_attr)
        
        # 重新整形为 (batch_size, num_nodes, out_features)
        out = out.view(batch_size, num_nodes, -1)
        return out

    def get_bimodal_regularization(self, edge_weights):
        # 双峰分布正则项 H(p) = -p log p - (1-p) log(1-p)
        p = torch.sigmoid(edge_weights)  # 确保在 [0,1]
        h = -p * torch.log(p + 1e-8) - (1 - p) * torch.log(1 - p + 1e-8)
        return torch.sum(h)  # 鼓励低熵

class RegressionHead(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(RegressionHead, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

    def forward(self, x):
        raise NotImplementedError

class LinearRegressionHead(RegressionHead):
    def __init__(self, input_dim, output_dim):
        super(LinearRegressionHead, self).__init__(input_dim, output_dim)
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, x):
        return self.linear(x)

class OSELMRegressionHead(RegressionHead):
    def __init__(self, input_dim, output_dim, hidden_dim=100, lambda_reg=0.1):
        super(OSELMRegressionHead, self).__init__(input_dim, output_dim)
        self.hidden_dim = hidden_dim
        self.lambda_reg = lambda_reg

        # 初始化输入权重和偏置
        self.W = torch.randn(input_dim, hidden_dim) * 0.1
        self.b = torch.randn(hidden_dim) * 0.1

        # 输出权重
        self.beta = torch.zeros(hidden_dim, output_dim)

        # P 矩阵用于在线更新
        self.P = torch.eye(hidden_dim) / lambda_reg

        # 标志是否已初始化
        self.initialized = False

    def _activation(self, x):
        return torch.sigmoid(x)

    def fit_online(self, x, y):
        # x: (batch, input_dim), y: (batch, output_dim)
        H = self._activation(x @ self.W + self.b)  # (batch, hidden_dim)

        # 在线更新
        for i in range(x.shape[0]):
            h = H[i:i+1]  # (1, hidden_dim)
            t = y[i:i+1]  # (1, output_dim)

            # 更新 P
            temp = torch.inverse(torch.eye(1) + h @ self.P @ h.T)
            self.P = self.P - self.P @ h.T @ temp @ h @ self.P

            # 更新 beta
            self.beta = self.beta + self.P @ h.T @ (t - h @ self.beta)

        self.initialized = True

    def forward(self, x):
        if not self.initialized:
            raise ValueError("OSELM head not fitted. Call fit_online first.")
        H = self._activation(x @ self.W + self.b)
        return H @ self.beta

class SimpleGCNModel(nn.Module):
    def __init__(self, num_nodes=5, node_features=69, hidden_dim=32, output_dim=1, reg_head_type='linear', oselm_hidden_dim=100, lambda_reg=0.01):
        super(SimpleGCNModel, self).__init__()
        self.num_nodes = num_nodes
        self.node_features = node_features
        self.lambda_reg = lambda_reg

        # 可学习的边权重，初始化为随机值
        self.edge_weights = nn.Parameter(torch.rand(num_nodes, num_nodes) * 0.2 + 0.4)
        
        # 创建完整的 edge_index（无向图，所有可能的无向边，包括自环）
        edge_index = []
        for i in range(num_nodes):
            for j in range(i, num_nodes):  # 只添加 i <= j，避免重复
                edge_index.append([i, j])
        self.edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

        # GCN 层
        self.gcn1 = GCNLayer(node_features, hidden_dim)
        self.gcn2 = GCNLayer(hidden_dim, hidden_dim)

        # Regression head
        if reg_head_type == 'linear':
            self.reg_head = LinearRegressionHead(hidden_dim, output_dim)
        elif reg_head_type == 'oselm':
            self.reg_head = OSELMRegressionHead(hidden_dim, output_dim, hidden_dim=oselm_hidden_dim, lambda_reg=lambda_reg)
        else:
            raise ValueError("Invalid reg_head_type. Choose 'linear' or 'oselm'.")

        # 归一化器
        self.channel_scaler = StandardScaler()
        self.label_scaler = MinMaxScaler()

        # 标志是否已拟合归一化器
        self.channel_fitted = False
        self.label_fitted = False

    def fit_scalers(self, data, labels):
        # data: (N, 5, 69)
        # labels: (N, output_dim)
        # 通道归一化：对每个通道的69维数据标准化
        N, C, L = data.shape
        # data_flat = data.reshape(N * C, L)  # (N*C, L)
        data_flat = data.transpose(0, 2, 1).reshape(-1, C)  # (N*L, C)
        self.channel_scaler.fit(data_flat)
        self.channel_fitted = True

        # 标签归一化
        self.label_scaler.fit(labels)
        self.label_fitted = True

    def normalize_channels(self, data):
        if not self.channel_fitted:
            raise ValueError("Channel scaler not fitted. Call fit_scalers first.")
        N, C, L = data.shape
        # data_flat = data.reshape(N * C, L)
        data_flat = data.transpose(1, 2).reshape(-1, C)  # (N*L, C)
        data_norm = self.channel_scaler.transform(data_flat)
        # return torch.tensor(data_norm.reshape(N, C, L), dtype=data.dtype, device=data.device)
        data_norm = data_norm.reshape(N, L, C).transpose(0, 2, 1)  # 转回 (N, C, L)
        return torch.tensor(data_norm, dtype=data.dtype, device=data.device)

    def normalize_labels(self, labels):
        if not self.label_fitted:
            raise ValueError("Label scaler not fitted. Call fit_scalers first.")
        return self.label_scaler.transform(labels)

    def denormalize_labels(self, labels_norm):
        if not self.label_fitted:
            raise ValueError("Label scaler not fitted. Call fit_scalers first.")
        return self.label_scaler.inverse_transform(labels_norm)

    def get_bimodal_regularization(self):
        return self.gcn1.get_bimodal_regularization(self.edge_weights) + self.gcn2.get_bimodal_regularization(self.edge_weights)

    def fit_reg_head_online(self, x, y):
        # x: (batch, hidden_dim), y: (batch, output_dim)
        if isinstance(self.reg_head, OSELMRegressionHead):
            self.reg_head.fit_online(x, y)

    def forward(self, x):
        # x: (batch_size, 5, 69)
        # 归一化通道
        x_norm = self.normalize_channels(x)

        # 获取边权重（对应无向图的上三角，使用 sigmoid 确保 [0,1]）
        edge_weight = []
        for i in range(self.num_nodes):
            for j in range(i, self.num_nodes):
                edge_weight.append(torch.sigmoid(self.edge_weights[i, j]))
        edge_weight = torch.stack(edge_weight)

        # GCN
        x_gcn = self.gcn1(x_norm, self.edge_index, edge_weight)  # (batch, 5, hidden)
        x_gcn = F.relu(x_gcn)
        x_gcn = self.gcn2(x_gcn, self.edge_index, edge_weight)  # (batch, 5, hidden)
        x_gcn = F.relu(x_gcn)

        # 全局平均池化
        x_pool = x_gcn.mean(dim=1)  # (batch, hidden)

        # Regression head
        out = self.reg_head(x_pool)  # (batch, output_dim)
        return out

    def save_scalers(self, path='scalers/scalers.pkl'):
        with open(path, 'wb') as f:
            pickle.dump({
                'channel_scaler': self.channel_scaler,
                'label_scaler': self.label_scaler,
                'channel_fitted': self.channel_fitted,
                'label_fitted': self.label_fitted
            }, f)

    def load_scalers(self, path='scalers.pkl'):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.channel_scaler = data['channel_scaler']
                self.label_scaler = data['label_scaler']
                self.channel_fitted = data['channel_fitted']
                self.label_fitted = data['label_fitted']

    def train_model(self, train_data, train_labels, val_data=None, val_labels=None, epochs=100, lr=0.001, batch_size=32, save_path=None, patience=10, exp_name="Experiment", train_time=None):
        if not isinstance(self.reg_head, LinearRegressionHead):
            raise ValueError("Training is only supported for Linear regression head.")

        optimizer = torch.optim.Adam(self.parameters(), lr=lr)
        criterion = nn.MSELoss()

        # 归一化标签
        train_labels_norm = torch.tensor(self.normalize_labels(train_labels.numpy()), dtype=torch.float32)
        if val_data is not None and val_labels is not None:
            val_labels_norm = torch.tensor(self.normalize_labels(val_labels.numpy()), dtype=torch.float32)

        # TensorBoard
        if train_time is None:
            train_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tensorboard_log_dir = f"tensorboard_logs/{exp_name}-{train_time}"
        os.makedirs(tensorboard_log_dir, exist_ok=True)
        # writer = SummaryWriter(log_dir=tensorboard_log_dir)

        best_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # 训练
            self.train()
            train_loss = 0
            num_train_batches = len(train_data) // batch_size
            for i in range(0, len(train_data), batch_size):
                batch_data = train_data[i:i+batch_size]
                batch_labels = train_labels_norm[i:i+batch_size]

                optimizer.zero_grad()
                outputs = self(batch_data)
                loss = criterion(outputs, batch_labels)
                # 添加双峰正则化
                reg_loss = self.get_bimodal_regularization()
                total_loss = loss + self.lambda_reg * reg_loss
                total_loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= num_train_batches

            # 验证
            val_loss = 0
            if val_data is not None and val_labels is not None:
                self.eval()
                with torch.no_grad():
                    val_outputs = self(val_data)
                    val_loss = criterion(val_outputs, val_labels_norm).item()

            # 记录到 TensorBoard
            # writer.add_scalar('Loss/Train', train_loss, epoch)
            # if val_data is not None:
            #     writer.add_scalar('Loss/Validation', val_loss, epoch)

            # 早停和保存最佳模型
            monitor_loss = val_loss if val_data is not None else train_loss
            if monitor_loss < best_loss:
                best_loss = monitor_loss
                patience_counter = 0
                if save_path:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    torch.save(self.state_dict(), save_path)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch+1}")
                    break

            if (epoch + 1) % 10 == 0:
                if val_data is not None:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
                else:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}")

        # writer.close()

    def evaluate_model(self, test_data, test_labels, log_dir=None, step=0):
        self.eval()
        with torch.no_grad():
            predictions = self(test_data)
            predictions_denorm = self.denormalize_labels(predictions.numpy())
            true_labels = test_labels.numpy()
            
            # 计算各种指标
            mse = mean_squared_error(true_labels, predictions_denorm)
            mae = np.mean(np.abs(true_labels - predictions_denorm))
            rmse = np.sqrt(mse)
            r2 = 1 - np.sum((true_labels - predictions_denorm)**2) / np.sum((true_labels - np.mean(true_labels))**2)
            max_error = np.max(np.abs(true_labels - predictions_denorm))
            mean_error = np.mean(true_labels - predictions_denorm)
            
            print(f"Test MSE: {mse:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")

            # 可视化预测 vs 真实
            if log_dir:
                # writer = SummaryWriter(log_dir=log_dir)
                                
                # 保存原始数据为文本
                true_flat = true_labels.flatten()
                pred_flat = predictions_denorm.flatten()
                data_text = "Index\tTrue\tPredicted\tError\n"
                for i in range(len(true_flat)):
                    error = pred_flat[i] - true_flat[i]
                    data_text += f"{i}\t{true_flat[i]:.6f}\t{pred_flat[i]:.6f}\t{error:.6f}\n"
                # writer.add_text('Test/Predicted_vs_True_Data', data_text, global_step=step)
                
                # 仍然保留图片可视化
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.scatter(true_flat, pred_flat, alpha=0.6)
                ax.plot([true_flat.min(), true_flat.max()], [true_flat.min(), true_flat.max()], 'r--', label='Perfect Prediction')
                ax.set_xlabel('True Labels')
                ax.set_ylabel('Predicted Labels')
                ax.set_title('Predicted vs True Labels')
                ax.legend()
                ax.grid(True)
                # writer.add_figure('Test/Predicted_vs_True', fig, global_step=step)
                # writer.close()
                plt.close(fig)
            
            return mse

    def replace_reg_head(self, new_reg_head_type='oselm', oselm_hidden_dim=100, lambda_reg=0.01):
        """替换回归头"""
        if new_reg_head_type == 'linear':
            self.reg_head = LinearRegressionHead(self.gcn2.conv.out_channels, 1)
        elif new_reg_head_type == 'oselm':
            self.reg_head = OSELMRegressionHead(self.gcn2.conv.out_channels, 1, hidden_dim=oselm_hidden_dim, lambda_reg=lambda_reg)
        else:
            raise ValueError("Invalid reg_head_type. Choose 'linear' or 'oselm'.")

    def freeze_gcn_layers(self):
        """冻结GCN层参数"""
        # 对于叶子变量，直接设置requires_grad
        if self.edge_weights.is_leaf:
            self.edge_weights.requires_grad = False
        for param in self.gcn1.parameters():
            if param.is_leaf:
                param.requires_grad = False
        for param in self.gcn2.parameters():
            if param.is_leaf:
                param.requires_grad = False

    def unfreeze_gcn_layers(self):
        """解冻GCN层参数"""
        for param in self.edge_weights:
            param.requires_grad = True
        for param in self.gcn1.parameters():
            param.requires_grad = True
        for param in self.gcn2.parameters():
            param.requires_grad = True

    def train_oselm_online(self, train_data, train_labels, batch_size=1, exp_name="Experiment", train_time=None):
        """在线训练OSELM回归头（GCN层已冻结）"""
        if not isinstance(self.reg_head, OSELMRegressionHead):
            raise ValueError("This method is only for OSELM regression head.")

        # TensorBoard
        if train_time is None:
            train_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tensorboard_log_dir = f"tensorboard_logs/{exp_name}-{train_time}"
        os.makedirs(tensorboard_log_dir, exist_ok=True)
        # writer = SummaryWriter(log_dir=tensorboard_log_dir)

        self.eval()  # GCN层不需要训练模式
        
        print(f"Starting online training with {len(train_data)} samples...")
        
        for i in range(0, len(train_data), batch_size):
            batch_data = train_data[i:i+batch_size]
            batch_labels = train_labels[i:i+batch_size]
            
            # 获取GCN特征
            with torch.no_grad():
                x_norm = self.normalize_channels(batch_data)
                edge_weight = []
                for ii in range(self.num_nodes):
                    for jj in range(ii, self.num_nodes):
                        edge_weight.append(torch.sigmoid(self.edge_weights[ii, jj]))
                edge_weight = torch.stack(edge_weight)

                x_gcn = self.gcn1(x_norm, self.edge_index, edge_weight)
                x_gcn = F.relu(x_gcn)
                x_gcn = self.gcn2(x_gcn, self.edge_index, edge_weight)
                x_gcn = F.relu(x_gcn)
                x_pool = x_gcn.mean(dim=1)  # GCN特征
            
            # 归一化标签
            batch_labels_norm = torch.tensor(self.normalize_labels(batch_labels.numpy()), dtype=torch.float32)
            
            # 在线训练OSELM（逐样本）
            for j in range(len(x_pool)):
                self.reg_head.fit_online(x_pool[j:j+1], batch_labels_norm[j:j+1])
            
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(train_data)} samples")

        print("Online training completed")
        # writer.close()
