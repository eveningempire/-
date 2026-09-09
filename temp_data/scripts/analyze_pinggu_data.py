"""
鍒嗘瀽pinggu鏂囦欢澶逛腑鐨凜SV鏁版嵁
鐢ㄤ簬浜嗚В鏁版嵁缁撴瀯锛屼负鍓嶇灞曠ず鍋氬噯澶?
"""
import pandas as pd
import numpy as np
from pathlib import Path

# 瀹氫箟鏁版嵁鏂囦欢璺緞
BASE_DIR = Path(__file__).parent.parent
PINGGU_DIR = BASE_DIR / "pinggu"

def analyze_csv(file_path, description):
    """鍒嗘瀽鍗曚釜CSV鏂囦欢"""
    print(f"\n{'='*80}")
    print(f"鏂囦欢: {file_path.name}")
    print(f"璇存槑: {description}")
    print(f"{'='*80}")
    
    try:
        # 璇诲彇CSV
        df = pd.read_csv(file_path)
        
        # 鍩烘湰淇℃伅
        print(f"\n[鍩烘湰淇℃伅]")
        print(f"  琛屾暟: {len(df)}")
        print(f"  鍒楁暟: {len(df.columns)}")
        print(f"  鏂囦欢澶у皬: {file_path.stat().st_size / 1024:.2f} KB")
        
        # 鍒楀悕
        print(f"\n[鍒楀悕] ({len(df.columns)}涓?")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        # 鏁版嵁绫诲瀷
        print(f"\n[鏁版嵁绫诲瀷]")
        for col in df.columns:
            dtype = df[col].dtype
            non_null = df[col].notna().sum()
            null_count = df[col].isna().sum()
            print(f"  {col:30s} | {str(dtype):10s} | 闈炵┖: {non_null:6d} | 绌哄€? {null_count:6d}")
        
        # 鏁板€煎垪缁熻
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            print(f"\n[鏁板€煎垪缁熻] (鍓?鍒?")
            stats = df[numeric_cols[:5]].describe()
            print(stats.to_string())
        
        # 鍓嶅嚑琛屾暟鎹?
        print(f"\n[鍓?琛屾暟鎹瑙圿")
        print(df.head().to_string())
        
        # 鏁版嵁鑼冨洿锛堝鏋滄湁鏃堕棿鐩稿叧鍒楋級
        time_like_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'cycle', 'epoch'])]
        if time_like_cols:
            print(f"\n[鏃堕棿鐩稿叧鍒楄寖鍥碷")
            for col in time_like_cols:
                if pd.api.types.is_numeric_dtype(df[col]):
                    print(f"  {col}: {df[col].min()} ~ {df[col].max()}")
        
        return df
        
    except Exception as e:
        print(f"\n[閿欒] 璇诲彇鏂囦欢澶辫触: {str(e)}")
        return None

def main():
    """涓诲嚱鏁?""
    print("\n" + "="*80)
    print(" "*20 + "PINGGU鏁版嵁鍒嗘瀽鎶ュ憡")
    print("="*80)
    
    # 瀹氫箟瑕佸垎鏋愮殑鏂囦欢
    files_to_analyze = [
        ("I_T_T_data_afterprocess_NoShutDown.csv", "璁粌鏁版嵁 - 鐢ㄤ簬妯″瀷璁粌鐨勫巻鍙叉暟鎹?),
        ("new_data_PHM5_new.csv", "娴嬭瘯鏁版嵁 - 鐢ㄤ簬妯″瀷楠岃瘉鐨勬柊鏁版嵁"),
        ("Duibi_Model.csv", "瀵规瘮妯″瀷缁撴灉 - 浼犵粺鏂规硶鐨勫仴搴锋寚寰佽瘎浼?),
        ("Proposed_Model.csv", "鎻愬嚭妯″瀷缁撴灉 - 鏂版彁鍑烘柟娉曠殑鍋ュ悍鎸囧緛璇勪及")
    ]
    
    results = {}
    
    for filename, description in files_to_analyze:
        file_path = PINGGU_DIR / filename
        
        if not file_path.exists():
            print(f"\n[璀﹀憡] 鏂囦欢涓嶅瓨鍦? {filename}")
            continue
        
        df = analyze_csv(file_path, description)
        if df is not None:
            results[filename] = df
    
    # 鎬荤粨
    print(f"\n\n{'='*80}")
    print(" "*30 + "鍒嗘瀽鎬荤粨")
    print(f"{'='*80}")
    print(f"\n鎴愬姛鍒嗘瀽鏂囦欢鏁? {len(results)}/{len(files_to_analyze)}")
    
    if len(results) > 0:
        print(f"\n[鏁版嵁闆嗗姣擼")
        print(f"{'鏂囦欢鍚?:<40s} | {'琛屾暟':>8s} | {'鍒楁暟':>6s}")
        print("-" * 80)
        for filename, df in results.items():
            print(f"{filename:<40s} | {len(df):>8d} | {len(df.columns):>6d}")
    
    # 妫€鏌ュ垪鍚嶄竴鑷存€?
    if len(results) >= 2:
        print(f"\n[鍒楀悕涓€鑷存€ф鏌")
        all_columns = {}
        for filename, df in results.items():
            all_columns[filename] = set(df.columns)
        
        # 鎵惧嚭鍏卞悓鍒?
        common_cols = set.intersection(*all_columns.values()) if all_columns else set()
        if common_cols:
            print(f"  鍏卞悓鍒楁暟: {len(common_cols)}")
            print(f"  鍏卞悓鍒? {', '.join(sorted(list(common_cols))[:10])}...")
    
    print("\n" + "="*80)
    print(" "*25 + "鍒嗘瀽瀹屾垚")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

