import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
import optuna
from torch.utils.data import DataLoader, TensorDataset
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
from sklearn.model_selection import train_test_split
import os



def load_hi_rul_csv(path, seq_len=50):
    df = pd.read_csv(path)
    hi = df['HI_norm'].values
    rul = df['RUL'].values

    # 归一化
    #scaler = MinMaxScaler()
    #hi = scaler.fit_transform(hi.reshape(-1, 1)).flatten()

    X, y = [], []
    for i in range(len(hi) - seq_len):
        X.append(hi[i:i+seq_len])
        y.append(rul[i+seq_len])
    X = np.array(X)[:, :, np.newaxis]  # (N, seq_len, 1)
    y = np.array(y)
    return X, y


class CNNNet(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.conv1 = nn.Conv1d(1, hidden_dim, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = x.transpose(1, 2)  # (B, 1, seq_len)
        x = torch.relu(self.conv1(x))
        x = self.pool(x).squeeze(-1)
        return self.fc(x)

class BiRNN(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.rnn = nn.RNN(input_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim*2, 1)

    def forward(self, x):
        out, _ = self.rnn(x)
        return self.fc(out[:, -1, :])

class BiLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim*2, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

class BiGRU(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim*2, 1)

    def forward(self, x):
        out, _ = self.gru(x)
        return self.fc(out[:, -1, :])

class SRNN(nn.Module):
    """堆叠双层RNN"""
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.rnn1 = nn.RNN(input_dim, hidden_dim, batch_first=True)
        self.rnn2 = nn.RNN(hidden_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        out, _ = self.rnn1(x)
        out, _ = self.rnn2(out)
        return self.fc(out[:, -1, :])
    
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
def objective(trial, X_train, y_train, X_val, y_val, model_type):

    hidden_dim = trial.suggest_int('hidden_dim', 16, 256)
    lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
    dropout = trial.suggest_float('dropout', 0.0, 0.5)
    batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
    epochs = trial.suggest_int('epochs', 30, 150)

    # 模型选择
    input_dim = X_train.shape[-1]
    if model_type == 'CNN': model = CNNNet(input_dim, hidden_dim)
    elif model_type == 'BiRNN': model = BiRNN(input_dim, hidden_dim)
    elif model_type == 'BiLSTM': model = BiLSTM(input_dim, hidden_dim)
    elif model_type == 'BiGRU': model = BiGRU(input_dim, hidden_dim)
    else: model = SRNN(input_dim, hidden_dim)

    model.to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32),
                             torch.tensor(y_train, dtype=torch.float32))
    val_ds = TensorDataset(torch.tensor(X_val, dtype=torch.float32),
                           torch.tensor(y_val, dtype=torch.float32))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device).unsqueeze(1)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

    # 验证
    model.eval()
    preds, trues = [], []
    with torch.no_grad():
        for xb, yb in val_loader:
            xb = xb.to(device)
            pred = model(xb).cpu().numpy().flatten()
            preds.extend(pred)
            trues.extend(yb.numpy())
    rmse = np.sqrt(np.mean((np.array(preds) - np.array(trues))**2))
    return rmse


def train_best_model(X_train, y_train, X_val, y_val, X_test, model_type, best_params):
    """使用 best_params 重训练一次模型(train+val),并返回模型+预测"""
    hidden_dim = best_params['hidden_dim']
    lr = best_params['lr']
    dropout = best_params['dropout']
    batch_size = best_params['batch_size']
    epochs = best_params['epochs']

    input_dim = X_train.shape[-1]
    if model_type == 'CNN': model = CNNNet(input_dim, hidden_dim)
    elif model_type == 'BiRNN': model = BiRNN(input_dim, hidden_dim)
    elif model_type == 'BiLSTM': model = BiLSTM(input_dim, hidden_dim)
    elif model_type == 'BiGRU': model = BiGRU(input_dim, hidden_dim)
    else: model = SRNN(input_dim, hidden_dim)

    model.to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # 合并 train+val 数据一起训练
    X_all = np.concatenate([X_train, X_val], axis=0)
    y_all = np.concatenate([y_train, y_val], axis=0)

    train_ds = TensorDataset(torch.tensor(X_all, dtype=torch.float32),
                             torch.tensor(y_all, dtype=torch.float32))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    # ---- 再训练 ----
    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device).unsqueeze(1)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

    # ---- 测试集预测 ----
    model.eval()
    with torch.no_grad():
        preds_test = model(torch.tensor(X_test, dtype=torch.float32).to(device))
        preds_test = preds_test.cpu().numpy().flatten()

    return model, preds_test



def train_all_models(X_train, y_train, X_val, y_val, X_test, y_test,csv_path,save_path):

    model_types = ['CNN', 'BiRNN', 'BiLSTM', 'BiGRU', 'SRNN']
    preds_test_all = []

    for mt in model_types:
        print(f"=== 正在优化 {mt} 模型 ===")
        study = optuna.create_study(direction='minimize')
        study.optimize(lambda t: objective(t, X_train, y_train, X_val, y_val, mt), n_trials=20)

        # 训练最佳模型
        best_params = study.best_params
        #print(mt, best_params)
        best_model_rmse = study.best_value
        print(f"{mt} 最佳参数: {best_params} | 最佳RMSE: {best_model_rmse:.4f}")
        # 可以按 best_params 重建训练最佳模型(同上 objective)
        # 并保存到 pkl 或 torch.save

         # ---- 使用最佳参数重训练并预测 ----
        best_model, preds_test = train_best_model(X_train, y_train, X_val, y_val, X_test, mt, best_params)
        preds_test_all.append(preds_test)

        # ---- 保存模型 ----
        model_file = os.path.join(save_path, f"{mt}_best_model.pt")
        torch.save(best_model.state_dict(), model_file)
        print(f"✅ 已保存 {mt} 模型到 {model_file}")

        # ---- 也可以用 joblib 保存参数 ----
        joblib.dump(best_params, os.path.join(save_path, f"{mt}_best_params.pkl"))

        # 评估单个模型性能
        metrics = evaluate(y_test, preds_test)
        print(f"{mt} 测试集性能: RMSE={metrics['RMSE']:.4f}, MAE={metrics['MAE']:.4f}, R2={metrics['R2']:.4f}")

    # 假设你有5个预测结果矩阵 preds_test_all (N,5)
    preds_test_all = np.stack(preds_test_all, axis=1)

    rf = RandomForestRegressor(n_estimators=200)
    rf.fit(preds_test_all, y_test)
    ada = AdaBoostRegressor(n_estimators=200)
    ada.fit(preds_test_all, y_test)

    # 集成预测
    rf_pred = rf.predict(preds_test_all)
    ada_pred = ada.predict(preds_test_all)

    print("RF RMSE:", np.sqrt(mean_squared_error(y_test, rf_pred)))
    print("Ada RMSE:", np.sqrt(mean_squared_error(y_test, ada_pred)))

    # 保存集成器
    joblib.dump({'rf': rf, 'ada': ada}, f"{save_path}/ensemble.pkl")
    print(f"✅ 集成模型已保存到 {save_path}/ensemble.pkl")

    rf_metrics = evaluate(y_test, rf_pred)
    ada_metrics = evaluate(y_test, ada_pred)
    pd.DataFrame([rf_metrics, ada_metrics], index=['RF', 'Ada']).to_csv(os.path.join(save_path, "ensemble_results.csv"))


def evaluate(y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {'RMSE': rmse, 'MAE': mae, 'R2': r2}



if __name__ == "__main__":
    csv_path = r"D:\pythonpro\datacsv\life\15\hi.csv"     # 你的HI_norm+RUL文件
    save_path = r"D:\pythonpro\health\backend\algotest\life\15"

    X, y = load_hi_rul_csv(csv_path)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    train_all_models(X_train, y_train, X_val, y_val, X_test, y_test, csv_path, save_path)
    