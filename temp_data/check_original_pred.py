"""
检查原始模型的预测结果
"""
import pandas as pd
import numpy as np

# 加载原始预测结果
pred_res = pd.read_csv('intelligent_sensing/ganzhi/data/pred_res_original_model.csv')

print("CSV文件列:", pred_res.columns.tolist())
print("\nCSV形状:", pred_res.shape)
print("\n前10行:")
print(pred_res.head(10))

# 加载真实标签对比
test_labels = np.load('intelligent_sensing/ganzhi/data/015_test_label.npy')
print(f"\n真实标签前10个: {test_labels[:10].flatten()}")
