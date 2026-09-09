import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import matplotlib

# ✅ 设置中文字体为宋体（SimSun），五号对应 fontsize=10 左右
plt.rcParams['font.sans-serif'] = ['SimSun']   # 宋体
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴负号显示问题
# 真实标签和预测标签（这里举个例子，你替换成自己的）
y_true = [0,1,1,2,3,3,4,4,5,6,6,7,7,8,9,10,10,11,12,13,13]
y_pred = [0,1,1,2,3,3,4,4,5,6,7,7,6,8,9,10,10,11,0,13,13]  # 示例预测

# 计算混淆矩阵
cm = confusion_matrix(y_true, y_pred)

# 绘制
plt.figure(figsize=(10,8))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("混淆矩阵")
plt.xlabel("预测标签")
plt.ylabel("真实标签")
plt.tight_layout()
plt.show()