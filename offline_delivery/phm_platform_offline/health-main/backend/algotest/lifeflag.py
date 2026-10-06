import pandas as pd

# 1. 读取 CSV 文件
file_path = r"D:\pythonpro\datacsv\life\3\9.csv"   # ← 修改为你的 CSV 文件路径      #*888#
df = pd.read_csv(file_path)

# 2. 检查列名,确保有 'S' 列
if 'Time' not in df.columns or 'RUL' not in df.columns:
    raise ValueError("CSV 中未找到 'Time' 或 'RUL' 列,请确认列名是否正确")


# 3. 查找 P1 列第一个小于 0.8 的值对应的 Time
first_less_than_08 = df[df['P3'] < 0.8]                               #*888#

firsttime = 0

if not first_less_than_08.empty:
    first_time = first_less_than_08.iloc[0]['Time']
    firsttime = first_time
    print(f"P1 列第一个小于 0.8 的值对应的 Time 是: {first_time}")
    
    # 如果需要查看具体是哪一行
    first_index = first_less_than_08.index[0]
    first_p1_value = first_less_than_08.iloc[0]['P3']                  #*888#
    print(f"位于第 {first_index} 行,P1 值为: {first_p1_value}")

      # 4. 设置 RUL 值
    # 找到第一个小于0.8的行索引
    first_failure_index = first_less_than_08.index[0]            
    
    # 之后的 RUL 都设为 0
    df.loc[first_failure_index:, 'RUL'] = 0
    
    # 之前的行根据时间戳计算剩余寿命
    failure_time = first_time
    for idx in range(first_failure_index):
        current_time = df.loc[idx, 'Time']
        remaining_life = max(0, failure_time - current_time)  # 确保不为负数
        df.loc[idx, 'RUL'] = remaining_life
    
    print(f"\n已成功设置 RUL 值:")
    print(f"- 第 {first_failure_index} 行及之后的行 RUL = 0")
    print(f"- 之前的行根据时间戳计算剩余寿命")
    
    # 显示一些示例
    print(f"\n前5行的 RUL 值:")
    print(df.head()[['Time', 'P2', 'RUL']])
    print(f"\n故障点附近几行的 RUL 值:")
    start_idx = max(0, first_failure_index - 2)
    end_idx = min(len(df), first_failure_index + 3)
    print(df.iloc[start_idx:end_idx][['Time', 'P2', 'RUL']])
    df.to_csv(file_path, index=False)
else:
    print("P17 列中没有小于 0.8 的值")

     # 读取 5.csv 的 RUL 第一个数据作为增加值
    try:
        # 再次读取同一个文件来获取 RUL 的第一个值
        df_temp = pd.read_csv(r"D:\pythonpro\datacsv\life\3\19.csv")                       #*888#
        if 'RUL' in df_temp.columns and not df_temp.empty:
            increase_value = df_temp['RUL'].iloc[0]+480*9  # 获取 RUL 列的第一个值         #*888#
            print(f"从 5.csv 读取的 RUL 增加值: {increase_value}")
            
            # 根据公式计算 RUL
            max_time = df['Time'].max()
            df['RUL'] = max_time - df['Time'] + increase_value
            df.to_csv(file_path, index=False)
            
            print(f"使用公式计算 RUL: RUL = {max_time} - Time + {increase_value}")
        else:
            print("5.csv 中没有 RUL 列或数据为空,使用默认计算")
            max_time = df['Time'].max()
            df['RUL'] = max_time - df['Time']
    except Exception as e:
        print(f"读取 RUL 增加值时出错: {e}")
        # 备用方案
        max_time = df['Time'].max()
        df['RUL'] = max_time - df['Time']





