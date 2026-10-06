import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


def plot_time_height(csv_path):
    """
    从指定路径读取CSV文件,并以Time列为横坐标(时间/s),
    以H列为纵坐标(高度/km)绘制曲线图。

    参数:
        csv_path (str): CSV文件路径
    """
    try:
        # 读取CSV
        df = pd.read_csv(csv_path)
        
        # 检查是否存在所需列
        # if 'Time' not in df.columns or 'H' not in df.columns:
        #     raise ValueError("CSV文件中必须包含 'Time' 和 'H' 两列!")
        
        # 字体设置
        plt.rcParams['font.sans-serif'] = ['SimSun']             # 中文宋体
        plt.rcParams['font.serif'] = ['Times New Roman']         # 英文新罗马
        plt.rcParams['axes.unicode_minus'] = False               # 解决负号显示问题
        plt.rcParams['font.size'] = 10.5                         # 5号字

        # 绘图
        plt.figure(figsize=(8, 5))
        plt.plot(df['Time'], df['S9'], color='royalblue', linewidth=2)
        plt.plot(df['Time'], df['Pitch'], color='seagreen', linewidth=1.8, label='真实俯仰角')

        # 设置标题和坐标轴
        plt.title('栅格舵在故障和正常情况下俯仰角对比', fontsize=10.5  )
        plt.xlabel('时间 / s', fontsize=10.5  )
        plt.ylabel('俯仰角 / rad', fontsize=10.5  )

        # 网格与样式
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"❌ 出错:{e}")


csv_path = r"D:\pythonpro\datacsv\scope_data.csv"
plot_time_height(csv_path)