"""
直接测试year1.get_all_predict_result函数
"""
import sys
import json
import numpy as np

sys.path.insert(0, 'intelligent_sensing/ganzhi')
from year1 import get_all_predict_result

# 调用函数
res = json.loads(get_all_predict_result())

# 打印base的预测结果范围
print("Base pred_labels max:", np.max(res['base']['pred_labels']))
print("Base pred_labels min:", np.min(res['base']['pred_labels']))

print("\nBase pred_labels前10个值:")
print(res['base']['pred_labels'][:10])

print("\nBase true_labels前10个值:")
print(res['base']['true_labels'][:10])

print("\nBase metrics:")
print(res['base']['metrics'])
