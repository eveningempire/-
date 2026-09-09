"""
让我们直接用year1.py测试，看看它是否能正常工作
"""
import sys
sys.path.insert(0, 'intelligent_sensing/ganzhi')

from year1 import get_all_predict_result
import json
import numpy as np

# 测试year1.py的预测功能
result_str = get_all_predict_result(exp="015")
result = json.loads(result_str)

print("Keys:", list(result.keys()))
print("\nBase predictions:")
base_preds = np.array(result['base']['pred_labels'])
base_true = np.array(result['base']['true_labels'])

print(f"Prediction range: [{base_preds.min():.4f}, {base_preds.max():.4f}]")
print(f"True range: [{base_true.min():.4f}, {base_true.max():.4f}]")
print(f"\n前10个预测值:")
print("True:     ", base_true[:10])
print("Predicted:", base_preds[:10])
print("\n期望值 (from CSV): [0.704, 0.707, 0.757, 0.697, 0.707, 0.661, 0.653, 0.676, 0.673, 0.622]")
