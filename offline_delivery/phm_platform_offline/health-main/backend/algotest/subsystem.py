import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import glob
import numpy as np
import os
import json
import pickle
# ----------------------
# 1. 定义 GCN
# ----------------------
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


# -----------------------
# 节点顺序映射(必须与 CSV 中的 power(11)+control(5) 对齐)
# -----------------------
node_names = [
    "液氧泵","氧涡轮","煤油管路","煤油主阀","燃气发生器","燃烧室","喷管",
    "液氧管路","液氧主阀","煤油泵","煤油涡轮",
    "TVC","RCS","栅格舵","传感器","PID控制器"
]
n_nodes = len(node_names)  # 16

# -----------------------
# 构造邻接矩阵(根据你描述的拓扑)
# 先用有向边定义,再对称化成无向图(GCN常用对称邻接)
# -----------------------
def build_adjacency():
    A = torch.zeros(n_nodes, n_nodes, dtype=torch.float32)

    # 液氧串: 0 -> 1 -> 7 -> 8
    A[0,1] = 1
    A[1,7] = 1
    A[7,8] = 1

    # 煤油串: 9 -> 10 -> 2 -> 3
    A[9,10] = 1
    A[10,2] = 1
    A[2,3] = 1

    

    # 并联到燃气发生器: 8 -> 4, 3 -> 4
    A[8,4] = 1
    A[3,4] = 1
    #A[3,0] = 1

    # 燃气发生器后串: 4 -> 5 -> 6
    A[4,5] = 1
    A[5,6] = 1

    # 动力输出到飞控传感器: 6 -> 14
    #A[6,14] = 1

    # 飞控串: 14 -> 15
    A[14,15] = 1

    # PID -> 执行器并联: 15 -> 11/12/13
    A[15,11] = 1
    A[15,12] = 1
    A[15,13] = 1

    # A[15,11] = 1
    # A[11,12] = 1
    # A[12,13] = 1


    # 对称化(无向)
    A_sym = ((A + A.t()) > 0).float()
    return A_sym


# -----------------------
# 读取 CSV 文件夹 (按文件名 0.csv..18.csv)
# 假设每个 csv 中 power 列有 11 行, control 列有 5 行
# -----------------------
def load_csv_folder(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.csv")),
                   key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    samples = []
    for f in files:
        df = pd.read_csv(f)
        # 确认列存在
        if 'power' not in df.columns or 'control' not in df.columns:
            raise ValueError(f"{f} 缺少 power 或 control 列")
        power = df['power'].dropna().to_numpy(dtype=float).tolist()
        control = df['control'].dropna().to_numpy(dtype=float).tolist()[:5]
        if len(power) != 11 or len(control) != 5:
            raise ValueError(f"{f} 中 power 长度应为11, control 长度应为5, 当前为 {len(power)}, {len(control)}")
        # 按你给定的节点顺序,power 先11个,再 control 5个 -> 直接 concat 即可
        feat = np.array(power + control, dtype=float)  # shape (16,)
        samples.append(feat)
    #✅ 增加一行全 1 的理想健康样本
    ideal_sample = np.ones(16, dtype=float)
    samples.append(ideal_sample)
    files.append("ideal_sample")  # 占位文件名,方便对齐
    return np.vstack(samples), files  # shape (n_samples, 16)

# -----------------------
# 物理约束计算函数(基于模型输出 out: tensor [16,1])
# -----------------------
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
    #parallel = serial1 * serial2
    # power: parallel * GG(4) * CC(5) * N(6)
    power = parallel * o[4] * o[5] * o[6]

    #power = min(o[0],o[1],o[2],o[3],o[4],o[5],o[6],o[7],o[8],o[9],o[10])
    #power = o[0]*o[1]*o[2]*o[3]*o[4]*o[5]*o[6]*o[7]*o[8]*o[9]*o[10]

    # control: sensor(14) * PID(15) * OR(TVC(11),RCS(12),Grid(13))
    or_act = 1 - (1 - o[11]) * (1 - o[12]) * (1 - o[13])
    #or_act = min(o[11],o[12],o[13])
    control = o[14] * o[15] * or_act

    #control = min(o[11],o[12],o[13],o[14],o[15])
    #control = o[11]*o[12]*o[13]*o[14]*o[15]

    system = power * control
    return power, control, system

# -----------------------
# 主训练函数
# -----------------------
def train(folder, epochs=300, lr=1e-3, lambda_phys=1.0, device='cpu'):
    device = torch.device(device)
    A = build_adjacency().to(device)  # [16,16]
    print("邻接矩阵(对称化):\n", A.numpy().astype(int))

    data, file_list = load_csv_folder(folder)  # (n_samples,16)
    X = torch.tensor(data, dtype=torch.float32, device=device)  # (n_samples,16)
    n_samples = X.shape[0]

    model = GCN(in_features=1, hidden_features=64, out_features=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    for epoch in range(1, epochs+1):
        model.train()
        epoch_loss = 0.0
        for i in range(n_samples):
            x_i = X[i].unsqueeze(1)  # (16,1)
            pred = model(x_i, A)     # (16,1)

            # 无监督项:让节点预测尽量接近已知的部件健康度(这是监督在节点层)
            loss_node = F.mse_loss(pred, x_i)

            # 物理约束:pred 经过串并联公式得到 power/control, 希望接近工程计算(用同一时刻原始部件数据计算的物理值)
            # 这里用原始部件健康值计算物理 target(你也可以把 pred->phys_target 作为软约束)
            with torch.no_grad():
                true_feats = x_i.squeeze()  # (16,)
                # compute physics target using the original measured component values
                # serial1_true = true_feats[0]*true_feats[1]*true_feats[7]*true_feats[8] ...
                serial1_t = true_feats[0] * true_feats[1] * true_feats[7] * true_feats[8]
                serial2_t = true_feats[9] * true_feats[10] * true_feats[2] * true_feats[3]
                parallel_t = serial1_t + serial2_t - serial1_t * serial2_t
                #parallel_t = min(serial1_t,serial2_t)
                #parallel_t = serial1_t * serial2_t
                power_t = parallel_t * true_feats[4] * true_feats[5] * true_feats[6]
                #power_t = min(true_feats[0],true_feats[1],true_feats[2],true_feats[3],true_feats[4],true_feats[5],true_feats[6],true_feats[7],true_feats[8],true_feats[9],true_feats[10])
                #power_t = true_feats[0]*true_feats[1]*true_feats[2]*true_feats[3]*true_feats[4]*true_feats[5]*true_feats[6]*true_feats[7]*true_feats[8]*true_feats[9]*true_feats[10]
                or_act_t = 1 - (1 - true_feats[11]) * (1 - true_feats[12]) * (1 - true_feats[13])
                #or_act_t = min(true_feats[11],true_feats[12],true_feats[13])
                control_t = true_feats[14] * true_feats[15] * or_act_t
                #control_t = min(true_feats[11],true_feats[12],true_feats[13],true_feats[14],true_feats[15])
                #control_t = true_feats[11]*true_feats[12]*true_feats[13]*true_feats[14]*true_feats[15]

            # compute physics from pred
            power_p, control_p, _ = compute_physics_from_out(pred)

            # PINN 物理损失:让 pred 推导的 power/control 接近由原始部件值直接计算的物理_targets
            #loss_phys = F.mse_loss(power_p, power_t.unsqueeze(0)) + F.mse_loss(control_p, control_t.unsqueeze(0))
            power_t = torch.tensor(power_t, dtype=torch.float32, device=device)
            control_t = torch.tensor(control_t, dtype=torch.float32, device=device)

            loss_phys = F.mse_loss(power_p, power_t.unsqueeze(0)) + F.mse_loss(control_p, control_t.unsqueeze(0))

            loss = loss_node + lambda_phys * loss_phys

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        if epoch % 20 == 0 or epoch == 1:
            print(f"Epoch {epoch}/{epochs}, avg_loss={epoch_loss/n_samples:.6f}")
            print(f"Epoch {epoch}: avg_total={epoch_loss/n_samples:.6f}")

    # 训练结束,做推理并输出每个样本的 power/control/system
    model.eval()
    results = []
    with torch.no_grad():
        for i in range(n_samples):
            x_i = X[i].unsqueeze(1)
            pred = model(x_i, A)
            p, c, s = compute_physics_from_out(pred)
            # 也计算用原始部件直接算出的物理targets以便对比
            true_feats = X[i]
            serial1_t = true_feats[0] * true_feats[1] * true_feats[7] * true_feats[8]
            serial2_t = true_feats[9] * true_feats[10] * true_feats[2] * true_feats[3]
            parallel_t = serial1_t + serial2_t - serial1_t * serial2_t
            #parallel_t = min(serial1_t,serial2_t)
            #parallel_t = serial1_t * serial2_t
            power_t = parallel_t * true_feats[4] * true_feats[5] * true_feats[6]
            #power_t = min(true_feats[0],true_feats[1],true_feats[2],true_feats[3],true_feats[4],true_feats[5],true_feats[6],true_feats[7],true_feats[8],true_feats[9],true_feats[10])
            #power_t = true_feats[0]*true_feats[1]*true_feats[2]*true_feats[3]*true_feats[4]*true_feats[5]*true_feats[6]*true_feats[7]*true_feats[8]*true_feats[9]*true_feats[10]
            or_act_t = 1 - (1 - true_feats[11]) * (1 - true_feats[12]) * (1 - true_feats[13])
            #or_act_t = min(true_feats[11],true_feats[12],true_feats[13])
            control_t = true_feats[14] * true_feats[15] * or_act_t
            #control_t = min(true_feats[11],true_feats[12],true_feats[13],true_feats[14],true_feats[15])
            #control_t = true_feats[11]*true_feats[12]*true_feats[13]*true_feats[14]*true_feats[15]

            results.append({
                'file': os.path.basename(file_list[i]),
                'power_pred': float(p.cpu().item()),
                'control_pred': float(c.cpu().item()),
                'system_pred': float(s.cpu().item()),
                'power_true': float(power_t.cpu().item()),
                'control_true': float(control_t.cpu().item())
            })

    return model,results


if __name__ == "__main__":
    #folder_path = r"D:\pythonpro\datacsv\sub"

    folder_path = r"D:\pythonpro\datacsv\sub"   # <-- 把这里改成实际文件夹
    model, results = train(folder_path, epochs=200, lr=1e-3, lambda_phys=5.0, device='cpu')
    for r in results:
        print(r)

     # -------- 1️⃣ 提取预测值的最大最小,保存为 JSON --------
    power_preds = [r['power_pred'] for r in results]
    control_preds = [r['control_pred'] for r in results]

    norm_dict = {
        "power_min": float(np.min(power_preds[:6])),
        "power_max": float(np.max(power_preds)),
        "control_min": float(np.min(control_preds)),
        "control_max": float(np.max(control_preds)),
    }

    out_folder = r"D:\pythonpro\health\backend\algotest" 

    json_path = os.path.join(out_folder, "hi_norm_range.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(norm_dict, f, ensure_ascii=False, indent=4)

    print(f"✅ 已保存归一化范围到: {json_path}")
    print(json.dumps(norm_dict, indent=4, ensure_ascii=False))

    # -------- 2️⃣ 保存训练好的 GCN+PINN 模型为 pkl --------
    model_save_path = os.path.join(out_folder, "gcn_pinn_model.pkl")

    # 注意:保存模型参数(state_dict),而不是整个类对象,避免 Django 加载时报错
    with open(model_save_path, "wb") as f:
        pickle.dump({
            "model_state": model.state_dict(),
            "adjacency": build_adjacency()
        }, f)

    print(f"✅ 已保存 GCN+PINN 模型到: {model_save_path}")