"""
简化batch处理 - 逐个样本预测
"""
import sys
import numpy as np
import torch
from pathlib import Path

sys.path.insert(0, 'intelligent_sensing/ganzhi')
from model import SimpleGCNModel

# 加载测试数据
test_data = np.load('intelligent_sensing/ganzhi/data/015_fusion_test_data.npy')
test_labels = np.load('intelligent_sensing/ganzhi/data/015_test_label.npy')
test_data_base = test_data[:, :3, :]

# 加载模型
model = SimpleGCNModel(num_nodes=3, lambda_reg=0.0001)
model.load_state_dict(torch.load('intelligent_sensing/ganzhi/models/GCN_LinearRegression_Base/best_model.pth'))
model.load_scalers('intelligent_sensing/ganzhi/scalers/scalers_base.pkl')
model.eval()

print(f"Test data shape: {test_data_base.shape}")

# 尝试单个样本预测 vs 批量预测
single_sample = test_data_base[0:1]  # (1, 3, 69)
batch_samples = test_data_base[0:5]  # (5, 3, 69)

with torch.no_grad():
    # 单个样本
    single_pred = model(torch.tensor(single_sample, dtype=torch.float32))
    print(f"\nSingle sample prediction: {single_pred.shape}, value={single_pred.item():.4f}")
    
    # 批量
    batch_pred = model(torch.tensor(batch_samples, dtype=torch.float32))
    print(f"Batch predictions: {batch_pred.shape}")
    print(f"Batch prediction values: {batch_pred.flatten().numpy()}")
    
    # 逐个预测
    individual_preds = []
    for i in range(5):
        pred = model(torch.tensor(test_data_base[i:i+1], dtype=torch.float32))
        individual_preds.append(pred.item())
    
    print(f"\nIndividual predictions: {individual_preds}")
    print(f"\nAre batch and individual same? {np.allclose(batch_pred.numpy().flatten(), individual_preds)}")
