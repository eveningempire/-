"""
PHM5娴嬭瘯鏁版嵁棰勫鐞嗚剼鏈?
- 璇诲彇 pinggu/new_data_PHM5.csv (437涓囪)
- 鐢熸垚鏃堕棿鎴?(2024-02-04 鍒?2024-08-20)
- 杩涜澶у姏搴﹂檷閲囨牱淇濊瘉鍓嶇娓叉煋閫熷害
- 杈撳嚭JSON鏂囦欢渚涘墠绔娇鐢?
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

def process_cmg5_data():
    print("寮€濮嬪鐞咰MG5娴嬭瘯鏁版嵁...")
    
    # 璇诲彇CSV鏂囦欢
    csv_path = "pinggu/new_data_PHM5.csv"
    print(f"璇诲彇鏂囦欢: {csv_path}")
    
    # 璇诲彇鏁版嵁锛堝彧淇濈暀10涓弬鏁板垪锛?
    df = pd.read_csv(csv_path)
    total_rows = len(df)
    print(f"鎬昏鏁? {total_rows}")
    print(f"鍒楀悕: {list(df.columns)}")
    
    # 鏃堕棿鑼冨洿: 2024-02-04 鍒?2024-08-20
    start_date = datetime(2024, 2, 4)  
    end_date = datetime(2024, 8, 20, 23, 59, 59)
    
    # 鐢熸垚鏃堕棿鎴冲簭鍒?
    total_seconds = (end_date - start_date).total_seconds()
    print(f"鏃堕棿璺ㄥ害: {(end_date - start_date).days} 澶?)
    
    # 涓烘瘡涓暟鎹偣鐢熸垚瀵瑰簲鐨勬椂闂存埑
    time_indices = np.linspace(0, total_seconds, total_rows)
    timestamps = [start_date + timedelta(seconds=float(t)) for t in time_indices]
    
    # 娣诲姞鏃堕棿鎴冲垪
    df['timestamp'] = timestamps
    
    # ---闄嶉噰鏍风瓥鐣?--
    # 437涓囪鏁版嵁, 鐩爣闄嶉噰鏍峰埌绾?000-5000涓偣
    # 闄嶉噰鏍锋瘮渚? 闄嶅埌绾?1/1000 鍒?1/1500
    # 浣跨敤鍧囧寑閲囨牱绛栫暐
    target_samples = 3000
    sample_step = total_rows // target_samples
    
    print(f"闄嶉噰鏍?- 鍘熷鏁版嵁鐐? {total_rows}")
    print(f"闄嶉噰鏍?- 鐩爣鏁版嵁鐐? {target_samples}")
    print(f"闄嶉噰鏍?- 閲囨牱姝ラ暱: {sample_step}")
    
    # 鍧囧寑閲囨牱
    sampled_indices = np.arange(0, total_rows, sample_step)
    df_sampled = df.iloc[sampled_indices].copy()
    
    print(f"闄嶉噰鏍峰悗鏁版嵁鐐? {len(df_sampled)}")
    
    # 鏍煎紡鍖栨椂闂存埑
    df_sampled['timestamp_str'] = df_sampled['timestamp'].apply(
        lambda x: x.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # 鍑嗗JSON杈撳嚭缁撴瀯
    result = {
        "metadata": {
            "total_rows": total_rows,
            "sampled_rows": len(df_sampled),
            "sample_rate": f"1:{sample_step}",
            "time_range": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "parameters": list(df.columns[:-2])  # 鎺掗櫎timestamp鍒?
        },
        "data": {}
    }
    
    # 娣诲姞姣忎釜鍙傛暟鐨勬暟鎹?
    param_columns = df.columns[:-2]  # 鎺掗櫎timestamp鍜宼imestamp_str
    for col in param_columns:
        result["data"][col] = {
            "values": df_sampled[col].tolist(),
            "timestamps": df_sampled['timestamp_str'].tolist()
        }
    
    # 淇濆瓨JSON鏂囦欢
    output_dir = Path("frontend/public/assessment-data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "test_data_cmg5_sampled.json"
    print(f"淇濆瓨JSON鏂囦欢: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("澶勭悊瀹屾垚锛?)
    print(f"   - 鍘熷鏁版嵁: {total_rows} 琛?)
    print(f"   - 閲囨牱鏁版嵁: {len(df_sampled)} 琛?)
    print(f"   - 鏃堕棿鑼冨洿: {result['metadata']['time_range']['start']} ~ {result['metadata']['time_range']['end']}")
    print(f"   - 鍙傛暟鏁伴噺: {len(param_columns)}")
    print(f"   - 杈撳嚭鏂囦欢: {output_file}")
    
    # 鎵撳嵃缁熻淇℃伅
    print("\n鏁版嵁缁熻淇℃伅:")
    for col in param_columns:
        col_data = df_sampled[col]
        print(f"  {col}:")
        print(f"    - 鍧囧€? {col_data.mean():.4f}")
        print(f"    - 鏍囧噯宸? {col_data.std():.4f}")
        print(f"    - 鏈€灏忓€? {col_data.min():.4f}")
        print(f"    - 鏈€澶у€? {col_data.max():.4f}")

if __name__ == "__main__":
    process_cmg5_data()

