import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

# 假设的健康分数数据（时间，健康分数）
time = np.array([0, 1, 2, 3, 4, 5, 6, 7])
health_scores = np.array([75, 78, 76, 77, 79, 80, 82, 81])

# 将数据转化为时间序列格式
data = pd.Series(health_scores)

# 1. 检测数据平稳性（ADF检验）
result = adfuller(data)
print("ADF检验的p值:", result[1])  # p值小于0.05表示时间序列是平稳的

# 如果数据不平稳，则需要差分处理（此处假设数据是平稳的，跳过差分步骤）

# 2. 拟合 ARIMA 模型
# 假设选择了 p=1, d=0, q=1（可根据 ACF 和 PACF 图来选择 p 和 q）
model = ARIMA(data, order=(1, 0, 1))
model_fit = model.fit()

# 3. 进行预测
forecast_steps = 5  # 预测未来5个时间点
forecast = model_fit.forecast(steps=forecast_steps)

# 4. 绘制结果
plt.plot(time, health_scores, label='实际健康分数')
plt.plot(np.arange(8, 8 + forecast_steps), forecast, label='预测健康分数', linestyle='--')
plt.xlabel('时间')
plt.ylabel('健康分数')
plt.legend()
plt.show()

# 输出预测结果
print("未来5个时间点的预测健康分数:", forecast)