import pandas as pd

# 1. 读取 CSV 文件
file_path = r"D:\pythonpro\datacsv\12\4.csv"   # ← 修改为你的 CSV 文件路径
df = pd.read_csv(file_path)

# 2. 检查列名,确保有 'S' 列
if 'Time' not in df.columns or 'flag' not in df.columns:
    raise ValueError("CSV 中未找到 'Time' 或 'S' 列,请确认列名是否正确")

# 3. 设置行范围(S2 到 S19018 → 索引 1 到 19017)
row_start = 0
row_end = 19017
# 3. 将 S 列第 2 行到第 19018 行(即索引 1 到 19017)填充为 0
mask = (df.index >= row_start) & (df['Time'] >= 0)&(df['P12'] >= 0.195)
df.loc[mask, 'flag'] = 12
mask2 = (df.index >= row_start) & (df['Time'] >= 0)&(df['P12'] < 0.195)
df.loc[mask2, 'flag'] = 0
# 4. 保存文件(可以覆盖或另存为)
# 覆盖保存:
df.to_csv(file_path, index=False)

# 或另存为新文件:
# new_file_path = r"D:\your\path\file_filled.csv"
# df.to_csv(new_file_path, index=False)

print("已成功将 S2:S19018 区域填充为 0 ✅")