from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import csv
import os
import pandas as pd
import json
import numpy as np
from scipy.stats import skew, kurtosis
import joblib
from scipy.stats import kurtosis, skew, entropy, linregress
from scipy.signal import stft
import pywt
from PyEMD import EMD
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
import warnings
import pickle
import traceback
import time
import random
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)






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
    
class GCNLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super(GCNLayer, self).__init__()
        self.linear = nn.Linear(in_features, out_features)
    def forward(self, X, A):
        # A: 邻接矩阵, X: 节点特征
        I = torch.eye(A.size(0))
        A_hat = A + I
        D_hat = torch.diag(A_hat.sum(1)**-0.5)
        X = D_hat @ A_hat @ D_hat @ X
        return self.linear(X)

class GCN(nn.Module):
    def __init__(self, in_features, hidden_features, out_features):
        super(GCN, self).__init__()
        self.gcn1 = GCNLayer(in_features, hidden_features)
        self.gcn2 = GCNLayer(hidden_features, out_features)
    def forward(self, X, A):
        X = F.relu(self.gcn1(X, A))
        X = torch.sigmoid(self.gcn2(X, A))  # 输出0~1
        return X


class Encoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 32)
        self.fc_mu = nn.Linear(32, latent_dim)
        self.fc_logvar = nn.Linear(32, latent_dim)
    def forward(self, x):
        h = F.relu(self.fc1(x))
        return self.fc_mu(h), self.fc_logvar(h)

class Decoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.fc1 = nn.Linear(latent_dim, 32)
        self.fc2 = nn.Linear(32, input_dim)
    def forward(self, z):
        h = F.relu(self.fc1(z))
        return self.fc2(h)

class Discriminator(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.fc(x)


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_TYPES = ['CNN', 'BiRNN', 'BiLSTM', 'BiGRU', 'SRNN']

def load_hi_rul_csv(path, seq_len=50):
    df = pd.read_csv(path)
    hi = df['HI_norm'].values
    rul = df['RUL'].values

    X, y = [], []
    for i in range(len(hi) - seq_len):
        X.append(hi[i:i+seq_len])
        y.append(rul[i+seq_len])
    X = np.array(X)[:, :, np.newaxis]  # (N, seq_len, 1)
    y = np.array(y)
    return X, y


def algorithm_configuration(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            data = body.get('data', [])
            print(data)

            # 文件保存路径
            save_path = r'D:\pythonpro\health\backend\algorithm\algorithm_config.json'
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 保存为 JSON 文件
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            return JsonResponse({
                'status': 'success',
                'message': '算法配置已保存',
                'file': save_path
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': '仅支持 POST 请求'}, status=405)

# Create your views here.
def load_paracsv(request):

    value = request.GET.get('value')
    label = request.GET.get('label')

    print("接收到的 value:", value)
    print("接收到的 label:", label)

    label_to_column = {
            "X方向距离": "X",
            "Y方向距离": "Y",
            "运载器高度": "H",
            "发动机推力": "FT",
            "氧泵出口压强": "S1",
            "氧涡轮转速": "S2",
            "煤油管路出口压强": "S3",
            "煤油管路出口流量": "S4",
            "燃气发生器压强": "S5",
            "燃烧室压强": "S6",
            "液氧管路出口压强":"S14",
            "液氧管路出口流量": "S15",
            "煤油泵出口压强": "S16",
            "煤油涡轮转速": "S17",
            "发动机偏角": "S8",
            "栅格舵偏角": "S9",
            "RCS输出力矩": "S10_Y",
            "舵机电流": "S11",
            "滚转角": "Roll",
            "陀螺仪示数": "S13",
            "俯仰角": "S12",
            "偏航角": "Yaw",
            "X方向速度": "Vx",
            "Y方向速度": "Vy",
            "Z方向速度": "Vz",
            "P1":"P1",
            "P2":"P2",
            "P3":"P3",
            "P4":"P4",
            "P5":"P5",
            "P6":"P6",
            "P7":"P7",
            "P8":"P8",
            "P9":"P9",
            "P10":"P10",
            "P11":"P11",
            "P12":"P12",
            "P13":"P13",
            "P14":"P14",
            "P15":"P15",
            "P16":"P16",
            "P17":"P17",
    }
    column_name = label_to_column.get(label)
    if not column_name:
        return JsonResponse({'error': f'未找到对应列名: {label}'}, status=400)
    
    #csv_path = r'D:\pythonpro\datacsv\scope_data.csv' 
    if label.startswith("P"):
        csv_path = r'D:\pythonpro\datacsv\P_values.csv'
    else:
        csv_path = r'D:\pythonpro\datacsv\scope_data.csv'
    if not csv_path or not os.path.exists(csv_path):
        return JsonResponse({'error': 'CSV文件不存在'}, status=404)
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return JsonResponse({'error': f'读取CSV失败: {str(e)}'}, status=500)

    # 5️⃣ 检查列是否存在
    if "Time" not in df.columns or column_name not in df.columns:
        return JsonResponse({'error': f'CSV中缺少列: Time 或 {column_name}'}, status=400)
    
    data = {
        'time': df["Time"].tolist(),
        'value': df[column_name].tolist(),
        'label': label,  # 原始 label 也可以返回给前端
    }

    return JsonResponse(data, safe=False)


def anomaly_detection(request):
    csv_path = r'D:\pythonpro\datacsv\P_values.csv'

    # 1. 检查文件是否存在
    if not os.path.exists(csv_path):
        return JsonResponse({'error': 'CSV文件不存在'}, status=404)
    
    # 2. 读取 CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return JsonResponse({'error': f'CSV读取失败: {str(e)}'}, status=500)
    
    # 3. 检查 Time 列
    if 'Time' not in df.columns:
        return JsonResponse({'error': '缺少 Time 列'}, status=400)

    time_data = df['Time'].values
    #dt = time_data[1] - time_data[0] if len(time_data) > 1 else 0
    dt = 0.1

    print("dt的值是",dt)

    # 4. 检查 P1~P17 是否都存在
    p_columns = [f'P{i}' for i in range(1, 18)]
    missing_cols = [col for col in p_columns if col not in df.columns]
    if missing_cols:
        return JsonResponse({'error': f'缺少列: {missing_cols}'}, status=400)
    
    # 5. 定义专家规则
    # 可以灵活添加更多参数规则
    rules = {
        "P1": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P2": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P3": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P4": {"threshold": 0.9, "relation": "<=", "duration": 1.0},
        "P5": {"threshold": 0.1, "relation": ">=", "duration": 1.0},
        "P6": {"threshold": 1.2, "relation": ">=", "duration": 1.0},
        "P7": {"threshold": 0.9, "relation": "<=", "duration": 1.0},
        "P8": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P9": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P10": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P11": {"threshold": 0.5, "relation": "<=", "duration": 1.0},
        "P12": {"threshold": 0.2, "relation": ">=", "duration": 1.0},
        "P13": {"threshold": 0.5, "relation": "<=", "duration": 1.0},
        "P14": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P15": {"threshold": 0.9, "relation": "<=", "duration": 1.0},
        "P16": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
        "P17": {"threshold": 0.8, "relation": "<=", "duration": 1.0},
    }

    results = []

    # 6. 遍历每个参数,执行异常检测
    for p_name, rule in rules.items():
        if p_name not in df.columns:
            continue

        values = df[p_name].values
        threshold = rule["threshold"]
        relation = rule["relation"]
        duration_limit = rule["duration"]

        # 根据规则关系构建异常掩码
        if relation == "<=":
            abnormal_mask = values <= threshold
        elif relation == ">=":
            abnormal_mask = values >= threshold
        else:
            continue

        print("abnormal_mask的值是",abnormal_mask)

        # 连续异常时间统计
        consecutive_time = 0.0
        status = 0

        for flag in abnormal_mask:
            if flag:
                consecutive_time += dt
                if consecutive_time >= duration_limit:
                    status = 1
                    break
            else:
                consecutive_time = 0.0
        print("consecutive_time的值是",consecutive_time)

        results.append({
            "parameter": p_name,
            "status": status
        })

    return JsonResponse(results, safe=False)


def fault_diagnosis(request):
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)
    
      # 1️⃣ 读取算法配置文件
    config_path = r'D:\pythonpro\health\backend\algorithm\algorithm_config.json'
    if not os.path.exists(config_path):
        return JsonResponse({'error': '算法配置文件不存在'}, status=404)

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    if not config_data or not isinstance(config_data, list):
        return JsonResponse({'error': '算法配置格式错误'}, status=400)

    algorithm_flag = config_data[0]  # 判断是 fault1 还是 fault2

    # 2️⃣ 获取前端传入的 D 和 T
    D_str = request.GET.get('D')
    T_str = request.GET.get('T')

    if not D_str or not T_str:
        return JsonResponse({'error': '缺少 D 或 T 参数'}, status=400)

    try:
        D = json.loads(D_str)
        T = json.loads(T_str)
    except Exception as e:
        return JsonResponse({'error': f'D/T 解析失败: {e}'}, status=400)

    # 3️⃣ 调用不同算法
    if algorithm_flag == 'fault1':
        result = teams_rt_fault_rows(D, T)
    elif algorithm_flag == 'fault2':
        result = teams_rt_v2(D, T)
    else:
        return JsonResponse({'error': f'未知算法标识: {algorithm_flag}'}, status=400)

    return JsonResponse(result, safe=False)


def gradient_boost(request): 
    """
    POST 接收 fuzzy 数组,读取固定 CSV,返回 fuzzy 中的归一化概率 + 原始概率
    """
    if request.method == 'POST':
        try:
            # 解析前端传来的 fuzzy 数组
            body = json.loads(request.body.decode('utf-8'))
            fuzzy_list = body.get('fuzzy', [])
            if not isinstance(fuzzy_list, list):
                return JsonResponse({'error': 'fuzzy 应为数组'}, status=400)

            # 读取 CSV
            csv_path = r'D:\pythonpro\datacsv\P_values.csv'
            df = pd.read_csv(csv_path)

            print("开始特征提取")
            start = time.time()

            # 特征提取(与训练阶段一致)
            x_feat = extract_features_from_df(df).reshape(1, -1)
            print("特征提取完成,耗时:", time.time() - start)

            # 加载 GBDT 模型
            model_path = r'd:/pythonpro/health/backend/algotest/fault_gbdt_model.pkl'
            model = joblib.load(model_path)

            # 预测类别概率
            proba = model.predict_proba(x_feat)[0]  # shape=(14,)

            # 预测最可能的类别
            pred_label = int(np.argmax(proba))

            # 选出 fuzzy 对应概率
            selected_probs = {str(i): proba[i] for i in fuzzy_list if 0 <= i < len(proba)}
            total_prob = sum(selected_probs.values())

            if total_prob > 0:
                normalized_probs = {k: v / total_prob for k, v in selected_probs.items()}
            else:
                normalized_probs = {k: 0 for k in selected_probs.keys()}

            return JsonResponse({
                'pred_label': pred_label,
                'fuzzy_probs': normalized_probs,
                'original_probs': {f'class_{i}': float(p) for i, p in enumerate(proba)}
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': '仅支持POST方法'}, status=405)


def hier14_diagnosis(request):
    """Hier14 端到端 14 类诊断(读取 scope_data.csv)。"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)

    try:
        from algorithm.data_paths import get_scope_csv_path
        from algotest.hier14.predictor import predict_scope_csv

        csv_path = request.GET.get('csv', get_scope_csv_path())
        if not os.path.isfile(csv_path):
            return JsonResponse({'error': f'CSV 文件不存在: {csv_path}'}, status=404)

        result = predict_scope_csv(csv_path)
        return JsonResponse(result, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def component_eval(request):
    csv_path = r'D:\pythonpro\datacsv\P_values.csv'

    # 1. 检查文件是否存在
    if not os.path.exists(csv_path):
        return JsonResponse({'error': 'CSV文件不存在'}, status=404)
    
    # 2. 读取 CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return JsonResponse({'error': f'CSV读取失败: {str(e)}'}, status=500)
    
    FEATURE_NAMES = [ 
        # --- 时域特征 ---
        'mean','std','max','min',
        #'rms','kurt','skew','crest',
        #'mad','iqr','zcr','range','shape_factor','impulse_factor','clearance_factor',
    ]
    
    # 设置路径列表
    file_paths_list = [
        r"D:\pythonpro\health\backend\algotest\life\1",
        r"D:\pythonpro\health\backend\algotest\life\2",
        r"D:\pythonpro\health\backend\algotest\life\3",
        r"D:\pythonpro\health\backend\algotest\life\4",
        r"D:\pythonpro\health\backend\algotest\life\5",
        r"D:\pythonpro\health\backend\algotest\life\6",
        r"D:\pythonpro\health\backend\algotest\life\7",
        r"D:\pythonpro\health\backend\algotest\life\8",
        r"D:\pythonpro\health\backend\algotest\life\9",
        r"D:\pythonpro\health\backend\algotest\life\10",
        r"D:\pythonpro\health\backend\algotest\life\11",
        r"D:\pythonpro\health\backend\algotest\life\12",
        r"D:\pythonpro\health\backend\algotest\life\13",
        r"D:\pythonpro\health\backend\algotest\life\14",
        r"D:\pythonpro\health\backend\algotest\life\15",
    ]

    

    


    params_list = [
        "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", 
        "P10", "P9", "P12", "P14", "P15", "P16", "P17",
    ]

    origin_features = ['mean','rms','max','min']

    features_name=[
        ['min','mean','rms','max'],
        ['min','mean','rms','max'],
        ['min','mean','rms','max'],
        ['min','mean','rms','max'],
        ['rms','mean','max','min'],
        ['mean','rms','max','min'],
        ['min','mean','rms','max'],
        ['mean','rms','max','min'],
        ['mean','rms','max','min'],
        ['mean','rms','max','min'],
        ['max','rms','mean','min'],
        ['min','mean','rms','max'],
        ['min','mean','rms','max'],
        ['min','mean','rms','max'],
        ['min','mean','rms','max'],
    ]

    HI_list = []
    HI_min = []
    results = []

    # 定义7个列表,用来收集每个部件的"最后一帧"预测结果
    cnn_last_list = []
    birnn_last_list = []
    bilstm_last_list = []
    bigru_last_list = []
    srnn_last_list = []
    rf_last_list = []
    ada_last_list = []

    for i, file_path in enumerate(file_paths_list):
        param_name = params_list[i]
        print(f"正在处理第 {i+1} 个文件: {file_path}, 参数: {param_name}")
        
        try:
            # 提取特征
            wf = sliding_window_features(df, signal_col=param_name, time_col='Time', window_sec=2.0, step_sec=1.0)
            X_raw = np.vstack([w['features'] for w in wf])

            current_feature_order = features_name[i]       # 比如 ['min','mean','rms','max']
            print(f"当前特征顺序:{current_feature_order}")

            reorder_indices = [current_feature_order.index(f) for f in origin_features]

             # 3️⃣ 重排 X 的列顺序
            X = X_raw[:, reorder_indices]
            print(f"  → 重排后的特征对应顺序:{origin_features}")
            
            # 加载模型(确保文件路径正确)
            model_folder = file_path  # 如果模型文件直接在该文件夹下
            # 或者如果模型在子文件夹中:model_folder = os.path.join(file_path, 'model')
            
            scaler = joblib.load(os.path.join(model_folder, 'scaler.pkl'))
            pca = joblib.load(os.path.join(model_folder, 'pca.pkl'))
            
            # 加载元数据
            with open(os.path.join(model_folder, 'hi_meta.json'), 'r') as f:
                meta = json.load(f)
            
            # 关键修正:使用 transform 而不是 fit_transform
            X_scaled = scaler.transform(X)  # 使用训练好的scaler进行转换,不要重新拟合
            
            # 关键修正:使用 transform 而不是 fit_transform
            HI_curve = pca.transform(X_scaled).ravel()  # 使用训练好的pca进行转换,不要重新拟合
            
            global_min = meta['global_min']
            global_max = meta['global_max']
            
            # 归一化
            hi_norm = (HI_curve - global_min) / (global_max - global_min + 1e-8)
            
            # 判断是否是 P5, P6, P12 并进行特殊处理
            target_params = ['P5', 'P6', 'P12']
            if param_name in target_params:
                hi_norm = 1 - hi_norm
                print(f"  → 对目标参数 {param_name} 进行 1-HI 反转")

            
            clamped_hi = np.clip(hi_norm, 0, 1)
            HI_list.append(clamped_hi)
            HI_min.append(clamped_hi.min())

            hi = hi_norm

            seq_len=50

            X_seq=[]
            X

            for j in range(len(hi) - seq_len):
                X_seq.append(hi[j:j+seq_len])
            X_seq = np.array(X_seq)[:, :, np.newaxis]  # (N, seq_len, 1)
            #X_tensor = torch.tensor(X, dtype=torch.float32).to(DEVICE)

            model_folder = file_path

            with torch.no_grad():
                preds_all = []

                for mt in MODEL_TYPES:
                    # 加载最佳参数
                    best_params = joblib.load(os.path.join(model_folder, f"{mt}_best_params.pkl"))
                    hidden_dim = best_params['hidden_dim']

                    # 初始化模型
                    input_dim = X_seq.shape[-1]
                    if mt == 'CNN': model = CNNNet(input_dim, hidden_dim)
                    elif mt == 'BiRNN': model = BiRNN(input_dim, hidden_dim)
                    elif mt == 'BiLSTM': model = BiLSTM(input_dim, hidden_dim)
                    elif mt == 'BiGRU': model = BiGRU(input_dim, hidden_dim)
                    else: model = SRNN(input_dim, hidden_dim)

                    # 加载权重
                    model_path = os.path.join(model_folder, f"{mt}_best_model.pt")
                    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
                    model.to(DEVICE)
                    model.eval()

                    # 预测
                    X_tensor = torch.tensor(X_seq, dtype=torch.float32).to(DEVICE)
                    y_pred = model(X_tensor).cpu().numpy().flatten()
                    preds_all.append(y_pred)

                # (N,5)
                preds_all = np.stack(preds_all, axis=1)

                # 集成预测
                ensemble = joblib.load(os.path.join(file_path, 'ensemble.pkl'))
                rf_pred = ensemble['rf'].predict(preds_all)
                ada_pred = ensemble['ada'].predict(preds_all)

                                # --- 提取每个模型的最后一帧预测 ---
                last_preds = preds_all[-1]   # shape: (5,)  按 [CNN, BiRNN, BiLSTM, BiGRU, SRNN]
                last_rf = rf_pred[-1]
                last_ada = ada_pred[-1]

                cnn_last_list.append(float(last_preds[0]))
                birnn_last_list.append(float(last_preds[1]))
                bilstm_last_list.append(float(last_preds[2]))
                bigru_last_list.append(float(last_preds[3]))
                srnn_last_list.append(float(last_preds[4]))
                rf_last_list.append(float(last_rf))
                ada_last_list.append(float(last_ada))

                

                                        
            # 收集结果信息
            results.append({
                'param_name': param_name,
                'is_target_param': param_name in target_params,
                'hi_norm_min': float(hi_norm.min()),
                'hi_norm_max': float(hi_norm.max()),
                'hi_norm_mean': float(hi_norm.mean()),
                'sample_count': len(hi_norm),
                'preds': {mt: preds_all[:, i].tolist() for i, mt in enumerate(MODEL_TYPES)},
                'rf_pred': rf_pred.tolist(),
                'ada_pred': ada_pred.tolist()
            })
            
            print(f"  ✅ 处理完成: HI范围 [{hi_norm.min():.4f}, {hi_norm.max():.4f}]")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}")
            # 添加错误信息到结果
            results.append({
                'param_name': param_name,
                'error': str(e),
                'is_target_param': param_name in ['P5', 'P6', 'P12']
            })
            continue

    # 一共7个列表,对应7种方法的最后一帧预测值
    final_last_frame_results = {
        'CNN': cnn_last_list,
        'BiRNN': birnn_last_list,
        'BiLSTM': bilstm_last_list,
        'BiGRU': bigru_last_list,
        'SRNN': srnn_last_list,
        'RF': rf_last_list,
        'Ada': ada_last_list
        }
    # 3. 返回处理结果
    return JsonResponse({
        'status': 'success',
        'total_processed': len([r for r in results if 'error' not in r]),
        'total_errors': len([r for r in results if 'error' in r]),
        'target_params_processed': len([r for r in results if r.get('is_target_param', False) and 'error' not in r]),
        'hi_norm_values':[arr.tolist() for arr in HI_list],
        'hi_min_values': [float(x) for x in HI_min],
        'results': results,
        'final_last_frame_results': final_last_frame_results,
    })


    


def subsystem_eval(request):
    if request.method == 'POST':
        try:
            # 1️⃣ 解析前端传来的 JSON 数据
            data = json.loads(request.body.decode('utf-8'))
            print('subsubsubsub',data.get('power', []))
            power_list = data.get('power', [])
            control_list = data.get('control', [])

            # 拼接两个列表,生成新的列表
            combined_list = power_list + control_list
            if combined_list is None or len(combined_list) != 16:
                return JsonResponse({"error": "组件健康度数组必须为16维"}, status=400)

            # 简单校验
            if not isinstance(power_list, list) or not isinstance(control_list, list):
                return JsonResponse({'error': '参数必须为列表'}, status=400)
            

             # 两个列表的最大长度
            max_len = max(len(power_list), len(control_list))

            # 不足的部分补 None 或 0
            if len(power_list) < max_len:
                power_list += [None] * (max_len - len(power_list))
            if len(control_list) < max_len:
                control_list += [None] * (max_len - len(control_list))
            

            # 2️⃣ 指定 CSV 保存路径
            save_dir = r'D:\pythonpro\datacsv'   # ⚠️ 这里改成你自己的保存目录
            os.makedirs(save_dir, exist_ok=True)
            csv_path = os.path.join(save_dir, 'subsystem_health.csv')



            # 3️⃣ 写入 CSV 文件
            with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写表头
                writer.writerow(['power', 'control'])
                # 写数据
                for p, c in zip(power_list, control_list):
                    writer.writerow([p, c])
            
            # 加载模型
            model_path = r"D:\pythonpro\health\backend\algotest\gcn_pinn_model.pkl"
            with open(model_path, "rb") as f:
                ckpt = pickle.load(f)
            with open(r"D:\pythonpro\health\backend\algotest\hi_norm_range.json", "r", encoding="utf-8") as f:
                norm_dict = json.load(f)

            model = GCN(in_features=1, hidden_features=64, out_features=1)
            model.load_state_dict(ckpt["model_state"])
            model.eval()

            A = ckpt["adjacency"]

            
            x = torch.tensor(combined_list, dtype=torch.float32).unsqueeze(1)  # (16,1)
            with torch.no_grad():
                pred = model(x, A)
                power_p, control_p, _ = compute_physics_from_out(pred)

            # 归一化
            # p_norm = (power_p.item() - norm_dict["power_min"]) / (norm_dict["power_max"] - norm_dict["power_min"] + 1e-8)
            c_norm = (control_p.item() - norm_dict["control_min"]) / (norm_dict["control_max"] - norm_dict["control_min"] + 1e-8)

            # 对数归一化
            eps = 1e-8  # 防止 log(0)
            p_val = max(power_p.item(), eps)
            # c_val = max(control_p.item(), eps)

            p_norm = (np.log(p_val + eps) - np.log(norm_dict["power_min"] + eps)) / \
                    (np.log(norm_dict["power_max"] + eps) - np.log(norm_dict["power_min"] + eps) + eps)

            # c_norm = (np.log(c_val + eps) - np.log(norm_dict["control_min"] + eps)) / \
            #         (np.log(norm_dict["control_max"] + eps) - np.log(norm_dict["control_min"] + eps) + eps)



            return JsonResponse({
                'message': 'CSV 保存成功',
                'csv_path': csv_path,
                "power_HI": p_norm,
                "control_HI": c_norm
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': '只支持 POST 请求'}, status=405)


def system_eval(request):
    if request.method == 'POST':
        try:
            # 1️⃣ 解析前端传来的 JSON 数据
            data = json.loads(request.body.decode('utf-8'))
            power_value = data.get('power')  # 不再指定默认空列表,而是使用默认None
            # 同理处理control
            control_value = data.get('control')

            encoder = Encoder(1, 2)
            decoder = Decoder(1, 2)
            discriminator = Discriminator(1)

            encoder.load_state_dict(torch.load(r"D:\pythonpro\health\backend\algotest\encoder_best.pt", map_location='cpu'))
            decoder.load_state_dict(torch.load(r"D:\pythonpro\health\backend\algotest\decoder_best.pt", map_location='cpu'))
            discriminator.load_state_dict(torch.load(r"D:\pythonpro\health\backend\algotest\discriminator_best.pt", map_location='cpu'))

            encoder.eval(); decoder.eval(); discriminator.eval()

            BEST_WEIGHT_POWER = 0.633  # ⚠️ 替换为你找到的最优权重
            BEST_WEIGHT_CONTROL = 1 - BEST_WEIGHT_POWER

            model_path = r"D:\pythonpro\health\backend\algotest\rf_health_model.pkl"   # 与训练时保存的路径一致
            rf = joblib.load(model_path)
            print("✅ 模型已加载成功")

            

            new_data = np.array([[float(power_value), float(control_value)]])  # shape: (1, 2)

            # 3. 进行预测
            prediction = rf.predict(new_data)[0]
            prob = rf.predict_proba(new_data)[0][1]   # 预测为1的概率

            # 转换为原生类型
            prediction_py = int(prediction)
            prob_py = float(prob)


            # 2️⃣ 权重加权
            weighted_value = BEST_WEIGHT_POWER * float(power_value) + BEST_WEIGHT_CONTROL * float(control_value)
            x_tensor = torch.tensor([[weighted_value]], dtype=torch.float32)

            # 3️⃣ VAE 重构误差
            with torch.no_grad():
                mu, logvar = encoder(x_tensor)
                z = mu  # 推理时通常使用均值
                recon = decoder(z)
                recon_error = torch.mean((recon - x_tensor) ** 2).item()

                # 4️⃣ 判别器输出(作为置信度)
                disc_prob = discriminator(x_tensor).item()

            # 5️⃣ 设定阈值(可以用训练时保存的)
            # 简单起见,这里给个默认阈值,也可以在训练时保存 recon 阈值到文件
            THRESHOLD = 0.01  # ⚠️ 根据你训练集统计结果调整

            flag = int((recon_error < THRESHOLD) and (disc_prob > 0.5))

            return JsonResponse({
                'message': 'CSV 保存成功',
                'flag': flag,
                'recon_error': recon_error,
                'confidence': disc_prob,
                'power': power_value,
                'control': control_value,
                'weighted_value': weighted_value,
                'prediction':prediction_py,
                'prob':prob_py,
            })

        except Exception as e:
            print("❌ [system_eval] 出现异常:", e)
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': '只支持 POST 请求'}, status=405)


def troubleshoot(request):

    # fault_mat = [
    #     [0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,1,1],  #轴磨损失效故障、轴温升高
    #     [1,0,0,1,0,1,1,1,1,1,0,0,0,0,0,0,1,1],  #冷却通道堵塞故障、异物入侵、冲击负载、轴温升高、振动信号异常、排气温度升高、输出扭矩下降
    #     [0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,1,1],  #涡轮流道堵塞、输出扭矩下降
    #     [0,1,0,0,1,1,1,1,1,1,0,0,0,0,0,0,1,1],  #涡轮转子破坏、涡轮流场紊乱、冲击负载、轴温升高、振动信号异常、排气温度升高、输出扭矩下降
    #     [0,0,1,0,1,1,1,1,1,1,0,0,0,0,0,0,1,1],  #涡轮叶片烧蚀、涡轮流场紊乱、冲击负载、轴温升高、振动信号异常、排气温度升高、输出扭矩下降
    #     [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,1],  #涡轮轴承卡住
    #     [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,1],  #密封圈烧蚀
    #     [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,1],  #涡轮轮缘脱落
    #     [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1],  #叶冠顶帽脱落
    # ]
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            fault_name = data.get('fault_name', '').strip()
            print('故障名称为:',fault_name)
        except Exception as e:
            return JsonResponse({'error': '请求格式错误', 'detail': str(e)}, status=400)



    fault_dict_throuble1 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'排气温度检测'},
        {"number":'C',"operate":'修复轴磨损'},
    ]
    fault_dict_throuble2 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮叶片'},
        {"number":'C',"operate":'修复冷却通道'},
    ]
    fault_dict_throuble3 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'排气温度检测'},
        {"number":'C',"operate":'修复涡轮流道'},
    ]
    fault_dict_throuble4 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮叶片'},
        {"number":'C',"operate":'观测涡轮转子'},
        {"number":'D',"operate":'修复涡轮转子'},
    ]
    fault_dict_throuble5 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮叶片'},
        {"number":'C',"operate":'修复涡轮叶片'},
    ]
    fault_dict_throuble6 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮轮缘'},
        {"number":'C',"operate":'修复涡轮轴承'},
    ]
    fault_dict_throuble7 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮轮缘'},
        {"number":'C',"operate":'观测叶冠顶帽'},
        {"number":'D',"operate":'修复密封圈'},
    ]
    fault_dict_throuble8 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮轮缘'},
        {"number":'C',"operate":'修复涡轮轮缘'},
    ]
    fault_dict_throuble9 = [
        {"number":'A',"operate":'振动信号检测'},
        {"number":'B',"operate":'观测涡轮轮缘'},
        {"number":'C',"operate":'观测叶冠顶帽'},
        {"number":'D',"operate":'修复叶冠顶帽'},
    ]

    # 将所有方案放入字典方便索引
    fault_schemes = {
        1: fault_dict_throuble1,
        2: fault_dict_throuble2,
        3: fault_dict_throuble3,
        4: fault_dict_throuble4,
        5: fault_dict_throuble5,
        6: fault_dict_throuble6,
        7: fault_dict_throuble7,
        8: fault_dict_throuble8,
        9: fault_dict_throuble9,
    }

    # 随机选择一个方案
     # 判断 fault_name
    if fault_name == "涡轮转速下降":
        random_num = random.randint(1, 9)
        selected_scheme = fault_schemes[random_num]
        return JsonResponse({
            'message': '维修排故调用成功',
            'fault_id': random_num,
            'fault_plan': selected_scheme
        })
    else:
        # fault_name 不匹配,返回默认提示
         return JsonResponse({
            'message': '无匹配排故方案',
            'fault_id': 'A',
            'fault_plan': [{"number": "A", "operate": "无此排故方案"}]
        })



def teams_rt_fault_rows(D, T):
    """
    TEAMS-RT算法(行=故障模式,列=测试)

    参数:
    - D: 二维列表或numpy数组,形状为 (num_faults, num_tests)
    - T: 列表或numpy数组,长度 = num_tests,0=pass,1=fail

    返回:
    - 一个字典,包含 Good, Bad, Suspected, Unknown 四个集合(故障索引)
    """
    print("调用TEAMS-RT算法")
    D = np.array(D)
    T = np.array(T)
    num_faults, num_tests = D.shape  # ✅ 注意:这里行=故障,列=测试

    fault_indices = set(range(num_faults))
    Good = set()
    Bad = set()
    Suspected = set()
    Unknown = set(fault_indices)

    # (2) 遍历通过的测试
    for t_idx in range(num_tests):
        if T[t_idx] == 0:  # 通过的测试
            related_faults = np.where(D[:, t_idx] == 1)[0]  # 该测试关联的所有故障
            for f in related_faults:
                if f in Unknown:
                    Unknown.remove(f)
                    Good.add(f)

    # (3) 失败测试中唯一关联故障 → Bad
    bad_candidates = set()
    for t_idx in range(num_tests):
        if T[t_idx] == 1:
            related_faults = [f for f in np.where(D[:, t_idx] == 1)[0] if f in Unknown]
            if len(related_faults) == 1:
                bad_candidates.add(related_faults[0])

    for f in bad_candidates:
        if f in Unknown:
            Unknown.remove(f)
            Bad.add(f)

    # (4) 失败测试中多个关联故障 → Suspected
    for t_idx in range(num_tests):
        if T[t_idx] == 1:
            related_faults = [f for f in np.where(D[:, t_idx] == 1)[0] if f in Unknown]
            for f in related_faults:
                Unknown.remove(f)
                Suspected.add(f)

    return {
        "Good": [int(item)+1 for item in Good],
        "Bad": [int(item)+1 for item in Bad],
        "Suspected": [int(item)+1 for item in Suspected],
        "Unknown": [int(item)+1 for item in Unknown]
    }

def teams_rt_v2(D, T):
    print("调用PTEAMS-RT算法")
    D = np.array(D)
    T = np.array(T)
    num_faults, num_tests = D.shape

    # (1)初始化
    Unknown = set(range(num_faults))
    Good = set()
    Bad = set()
    Suspected = set()

    # 失败测试集合(列的索引)
    failed_tests = set(np.where(T == 1)[0])

    # (2)处理失败测试
    for t in failed_tests:
        # 找到与该失败测试相关的故障(该列中为1的行索引)
        related_faults = set(np.where(D[:, t] == 1)[0])
        related_unknown_faults = related_faults & Unknown

        if len(related_unknown_faults) == 1:
            # 唯一故障,标记为Bad
            f = list(related_unknown_faults)[0]
            Bad.add(f)
            Unknown.remove(f)
        elif len(related_unknown_faults) > 1:
            # 非唯一,将它们移到Suspected
            for f in related_unknown_faults:
                Suspected.add(f)
                Unknown.discard(f)

    # Unknown 剩下的都认为是 Good
    Good.update(Unknown)
    Unknown.clear()

    # (3)扩充失败测试集合
    FT_ext = set()
    for f in list(Suspected):
        # 该故障关联的测试
        related_tests = set(np.where(D[f, :] == 1)[0])
        not_failed_tests = related_tests - failed_tests

        if len(not_failed_tests) == 1:
            # 满足条件,将该故障选中
            # 扩充 FT 集合:Suspected fault 和 Bad faults 的所有关联测试
            faults_to_extend = {f} | Bad
            for ff in faults_to_extend:
                FT_ext.update(set(np.where(D[ff, :] == 1)[0]))

    failed_tests = failed_tests | FT_ext  # FT ∪ FT_ext

    # (4)更新 Suspected 集合
    for f in list(Suspected):
        related_tests = set(np.where(D[f, :] == 1)[0])
        # 如果某故障的关联测试不能被扩充后的失败测试集合覆盖 → 移到 Good
        if not related_tests.issubset(failed_tests):
            Good.add(f)
            Suspected.remove(f)

    return {
        "Good": [int(item)+1 for item in Good],
        "Bad": [int(item)+1 for item in Bad],
        "Suspected": [int(item)+1 for item in Suspected],
        "Unknown": [int(item)+1 for item in Unknown]
    }


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
        mean, rms, max_val, min_val,
         # rms, kurt, skewness, crest,
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
        'mean','rms','max','min',
        #'rms','kurt','skew','crest',
        #'mad','iqr','zcr','range','shape_factor','impulse_factor','clearance_factor',
        # --- 频域特征 ---
        #'energy','max_mag','dominant_freq','centroid','mean_sq_freq','bandwidth','spec_entropy',
        # --- 时频域特征 ---
       # 'wp_energy_ratio','stft_mean_spec','stft_energy','hht_freq_mean','hht_entropy','lcs'
    ]

    # 4. 生成字典形式便于在线检索
    feats_dict = {name: float(val) for name, val in zip(FEATURE_NAMES, feats)}

    return feats,feats_dict  # numpy array


def sliding_window_features(df, signal_col='P1', time_col='Time', window_sec=2.0, step_sec=1.0, min_samples_in_window=8):
    """
    对一个 csv DataFrame 执行滑动窗口特征提取
    返回:
      windows_info: list of dict { 'start':, 'end':, 'center':, 'features': ndarray, 'rul': float }
    """
    times = df[time_col].astype(float).values
    sig = df[signal_col].astype(float).values
    #rul_series = df['RUL'].astype(float).values if 'RUL' in df.columns else np.full_like(times, np.nan, dtype=float)

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
       # window_rul = rul_series[mask]
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
        #rul_value = float(window_rul[-1]) if len(window_rul)>0 and not np.isnan(window_rul[-1]) else (float(np.nan) if len(window_rul)>0 else float(np.nan))
        result.append({
            'start': float(s),
            'end': float(e),
            'center': float((s+e)/2.0),
            'features': feats,
            #'rul': rul_value
        })
    return result




def compute_physics_from_out(out):
    # out: [16,1] or [16]
    o = out.squeeze()
    # serial1: LO 0-1-7-8
    serial1 = o[0] * o[1] * o[7] * o[8]
    # serial2: fuel 9-10-2-3
    serial2 = o[9] * o[10] * o[2] * o[3]
    # parallel OR (prob form)
    parallel = serial1 + serial2 - serial1 * serial2
    #parallel = min(serial1,serial2)
    # power: parallel * GG(4) * CC(5) * N(6)
    power = parallel * o[4] * o[5] * o[6]
    #power = min(o[0],o[1],o[2],o[3],o[4],o[5],o[6],o[7],o[8],o[9],o[10])

    # control: sensor(14) * PID(15) * OR(TVC(11),RCS(12),Grid(13))
    or_act = 1 - (1 - o[11]) * (1 - o[12]) * (1 - o[13])
    #or_act = min(o[11],o[12],o[13])
    control = o[14] * o[15] * or_act
    control = min(o[11],o[12],o[13],o[14],o[15])

    system = power * control
    return power, control, system


def fmeca(request):
    try:
        # 指定JSON文件路径
        json_file_path = r'D:\pythonpro\health\backend\fmeca\fmeca.json'
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            fmeca_data = json.load(file)
        
        return JsonResponse({
            'message': 'FMECA读取成功',
            'data': fmeca_data,
            'status': 'success'
        })
        
    except FileNotFoundError:
        return JsonResponse({
            'message': 'FMECA文件未找到',
            'status': 'error'
        }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'FMECA文件格式错误',
            'status': 'error'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'message': f'读取FMECA文件时发生错误: {str(e)}',
            'status': 'error'
        }, status=500)
    

def editfmeca(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            record_id = data.get('id')
            print(record_id)

            # JSON 文件路径
            json_path = r'D:\pythonpro\health\backend\fmeca\fmeca.json'

            # 读取原数据
            with open(json_path, 'r', encoding='utf-8') as f:
                fmeca_list = json.load(f)

            # 查找对应id的记录并更新
            updated = False
            for item in fmeca_list:
                if item.get('id') == record_id:
                    item['component'] = data.get('component', item['component'])
                    item['fault_name'] = data.get('fault_name', item['fault_name'])
                    item['fault_prob'] = data.get('fault_prob', item['fault_prob'])
                    item['fault_reason'] = data.get('fault_reason', item['fault_reason'])
                    item['degree_harm'] = data.get('degree_harm', item['degree_harm'])
                    updated = True
                    break

            if not updated:
                return JsonResponse({'message': f'未找到 id={record_id} 的记录'}, status=404)

            # 写回文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(fmeca_list, f, ensure_ascii=False, indent=2)

            return JsonResponse({'message': 'FMECA修改成功', 'updated_id': record_id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)


def inituser(request):
    try:
        # 指定JSON文件路径
        json_file_path = r'D:\pythonpro\health\backend\fmeca\userlist.json'
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            user_data = json.load(file)
        
        return JsonResponse({
            'message': '用户列表读取成功',
            'data': user_data,
            'status': 'success'
        })
        
    except FileNotFoundError:
        return JsonResponse({
            'message': 'FMECA文件未找到',
            'status': 'error'
        }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'message': '用户列表格式错误',
            'status': 'error'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'message': f'读取用户列表时发生错误: {str(e)}',
            'status': 'error'
        }, status=500)

def edituser(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("id")
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            role = data.get("role")

            json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"
            if not os.path.exists(json_path):
                return JsonResponse({"status": "error", "msg": "用户文件不存在"})

            # 读取所有用户
            with open(json_path, "r", encoding="utf-8") as f:
                users = json.load(f)

            updated = False
            for u in users:
                if str(u.get("id")) == str(user_id):
                    u["username"] = username
                    u["email"] = email
                    u["password"] = password
                    u["role"] = role
                    updated = True
                    break

            if not updated:
                return JsonResponse({"status": "error", "msg": "未找到该用户"})

            # 写回文件
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=2)

            return JsonResponse({"status": "success", "msg": "用户信息修改成功"})

        except Exception as e:
            return JsonResponse({"status": "error", "msg": str(e)})

def adduser(request):
 if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # id = data.get('id')
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')

            json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"

            # 读取现有用户列表
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            else:
                users = []

            # 判断用户名是否已存在
            if any(u['name'] == username for u in users):
                return JsonResponse({'status': 'error', 'msg': '用户名已存在'})

            # 自动生成新用户id
            new_id = max([u['id'] for u in users], default=0) + 1

            # 添加新用户
            users.append({
                "id": new_id,
                "name": username,
                "email": email,
                "password": password,
                "role": role
            })

            # 保存回文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)

            return JsonResponse({'status': 'success', 'msg': '用户添加成功'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})

def deleteuser(request):
    try:
        # 指定路径
        json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"

        # 从前端获取要删除的用户名
        body = json.loads(request.body.decode("utf-8"))
        username_to_delete = body.get("username")

        if not username_to_delete:
            return JsonResponse({"success": False, "message": "未提供用户名"})

        # 判断文件是否存在
        if not os.path.exists(json_path):
            return JsonResponse({"success": False, "message": "用户列表文件不存在"})

        # 读取 JSON
        with open(json_path, "r", encoding="utf-8") as f:
            users = json.load(f)

        # 如果文件为空或不是列表
        if not isinstance(users, list):
            return JsonResponse({"success": False, "message": "用户数据格式错误"})

        # 查找是否存在该用户
        original_len = len(users)
        users = [u for u in users if u.get("name") != username_to_delete]

        # 如果没删掉,说明没找到该用户
        if len(users) == original_len:
            return JsonResponse({"success": False, "message": "未找到该用户"})

        # 写回 JSON 文件
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

        return JsonResponse({"success": True, "message": f"用户 {username_to_delete} 删除成功"})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"删除失败:{str(e)}"})

def loginuser(request):
    if request.method == "POST":
        try:
            # 解析前端传来的数据
            data = json.loads(request.body.decode('utf-8'))
            username = data.get("username")
            password = data.get("password")

            # JSON 文件路径
            json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"
            if not os.path.exists(json_path):
                return JsonResponse({"success": False, "message": "用户数据文件不存在"})

            # 读取文件
            with open(json_path, "r", encoding="utf-8") as f:
                users = json.load(f)

            # 查找匹配用户
            match = any(
                user["name"] == username and user["password"] == password
                for user in users
            )

            if match:
                login_record_path = r"D:\pythonpro\health\backend\fmeca\username.json"
                with open(login_record_path, "w", encoding="utf-8") as f:
                    json.dump(username, f, ensure_ascii=False, indent=4)
                return JsonResponse({"success": True, "message": "登录成功"})
            else:
                return JsonResponse({"success": False, "message": "用户名或密码错误"})

        except Exception as e:
            return JsonResponse({"success": False, "message": f"错误:{str(e)}"})

    return JsonResponse({"success": False, "message": "仅支持POST请求"})

def currentuser(request):
    login_record_path = r"D:\pythonpro\health\backend\fmeca\username.json"
    # 如果文件不存在或为空
    if not os.path.exists(login_record_path):
        return JsonResponse({"success": False, "message": "暂无登录用户"})

    try:
        with open(login_record_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # current_user = data.get("current_user")
        
        if data:
            return JsonResponse({"success": True, "username": data})
        else:
            return JsonResponse({"success": False, "message": "文件存在但无用户数据"})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON 文件损坏"})


def currentrole(request):
    json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get("username", "").strip()
            print(username)

            if not username:
                return JsonResponse({"success": False, "message": "用户名为空"})

            # 读取 JSON 文件
            if not os.path.exists(json_path):
                return JsonResponse({"success": False, "message": "用户列表文件不存在"})

            with open(json_path, "r", encoding="utf-8") as f:
                users = json.load(f)

            # 遍历查找匹配用户名
            for user in users:
                if user.get("name") == username:
                    role = user.get("role", "未知角色")
                    print(111)
                    print(role)
                    return JsonResponse({"success": True, "username": username, "role": role})

            # 未找到用户
            return JsonResponse({"success": False, "message": "未找到该用户"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "JSON解析错误"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"服务器错误: {str(e)}"})

    else:
        return JsonResponse({"success": False, "message": "仅支持POST请求"})
    

def maxuserid(request):
    try:
        json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"

        # 判断文件是否存在
        if not os.path.exists(json_path):
            return JsonResponse({"success": False, "message": "用户列表文件不存在"})

        # 读取 JSON 文件
        with open(json_path, "r", encoding="utf-8") as f:
            users = json.load(f)

        # 若文件为空或不是列表
        if not isinstance(users, list) or len(users) == 0:
            return JsonResponse({"success": True, "max_id": 0})

        # 提取所有 id 并找最大
        ids = [u.get("id", 0) for u in users if isinstance(u.get("id", 0), int)]
        max_id = max(ids) if ids else 0

        return JsonResponse({
            "success": True,
            "max_id": max_id
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON 文件格式错误"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"服务器错误: {str(e)}"})
    

def searchid(request):
     if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            print(username)

            json_path = r"D:\pythonpro\health\backend\fmeca\userlist.json"

            if not os.path.exists(json_path):
                return JsonResponse({'status': 'error', 'msg': '用户文件不存在'})

            with open(json_path, 'r', encoding='utf-8') as f:
                users = json.load(f)

            # 查找用户
            for u in users:
                if u.get('name') == username:
                    return JsonResponse({'status': 'success', 'userid': u.get('id')})

            return JsonResponse({'status': 'error', 'msg': '未找到该用户'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})
