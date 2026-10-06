import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib  # 用于保存/加载模型

# 1. 读取 CSV 文件
csv_path = r"D:\pythonpro\datacsv\sys\system.csv"   # ← 这里换成你的实际 CSV 路径
df = pd.read_csv(csv_path)

# 2. 选择特征和标签
X = df[['power', 'control']]   # 特征
y = df['flag']                # 标签(0/1)

# 3. 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. 初始化随机森林分类器
rf = RandomForestClassifier(
    n_estimators=100,        # 树的数量
    max_depth=None,          # 自动决定树深
    random_state=42
)

# 5. 训练模型
rf.fit(X_train, y_train)

# 6. 测试模型
y_pred = rf.predict(X_test)
print("✅ 测试集准确率:", accuracy_score(y_test, y_pred))
print("分类报告:\n", classification_report(y_test, y_pred))

# 7. 保存模型
model_path = r"D:\pythonpro\health\backend\algotest\rf_health_model.pkl"  # ← 模型保存路径
joblib.dump(rf, model_path)
print(f"📁 模型已保存到:{model_path}")
