import pandas as pd
import matplotlib.pyplot as plt

def plot_three_params(csv_path):
    """
    从指定路径读取CSV文件,并绘制三个横向子图:
    1. Time-H(高度/km)
    2. Time-S1
    3. Time-S2

    中文宋体,英文Times New Roman,字号5号(约10.5pt)
    """
    try:
        # 读取CSV
        df = pd.read_csv(csv_path)

        # 检查所需列是否存在
        required_cols = ['Time', 'H', 'S1', 'S2']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"CSV文件缺少必要列: {col}")

        # 设置字体
        plt.rcParams['font.sans-serif'] = ['SimSun']           # 中文宋体
        plt.rcParams['font.serif'] = ['Times New Roman']       # 英文Times New Roman
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10.5                       # 五号字

        # 创建3个横向子图
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        # 第1张:Time vs H
        axes[0].plot(df['Time'], df['S10_X'], color='royalblue', linewidth=1.5)
        axes[0].set_title('滚转力矩随时间变化', fontsize=10.5, family='SimSun')
        axes[0].set_xlabel('时间 / s', fontsize=10.5, family='SimSun')
        axes[0].set_ylabel('滚转力矩 / N·m', fontsize=10.5, family='SimSun')
        axes[0].grid(True, linestyle='--', alpha=0.6)

        # 第2张:Time vs S1
        axes[1].plot(df['Time'], df['S10_Y'], color='seagreen', linewidth=1.5)
        axes[1].set_title('俯仰力矩随时间变化', fontsize=10.5, family='SimSun')
        axes[1].set_xlabel('时间 / s', fontsize=10.5, family='SimSun')
        axes[1].set_ylabel('俯仰角 / N·m', fontsize=10.5, family='SimSun')
        axes[1].grid(True, linestyle='--', alpha=0.6)

        # 第3张:Time vs S2
        axes[2].plot(df['Time'], df['S10_Z'], color='darkorange', linewidth=1.5)
        axes[2].set_title('偏航力矩随时间变化', fontsize=10.5, family='SimSun')
        axes[2].set_xlabel('时间 / s', fontsize=10.5, family='SimSun')
        axes[2].set_ylabel('偏航角 / N·m', fontsize=10.5, family='SimSun')
        axes[2].grid(True, linestyle='--', alpha=0.6)

        # 布局优化
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"❌ 出错:{e}")


csv_path = r"D:\pythonpro\datacsv\scope_data.csv"
plot_three_params(csv_path)