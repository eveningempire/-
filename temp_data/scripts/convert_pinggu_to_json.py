"""
灏唒inggu鏂囦欢澶圭殑澶SV鏂囦欢閲囨牱骞惰浆鎹负JSON
鐢ㄤ簬鍓嶇蹇€熷姞杞藉拰鍙鍖?
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PINGGU_DIR = BASE_DIR / "pinggu"
OUTPUT_DIR = BASE_DIR / "frontend" / "public" / "assessment-data"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def sample_and_convert_train_data():
    """澶勭悊璁粌鏁版嵁 - 閲囨牱涓?000涓偣"""
    print("\n[1/4] Processing training data...")
    
    df = pd.read_csv(PINGGU_DIR / "I_T_T_data_afterprocess_NoShutDown.csv")
    print(f"  Original rows: {len(df)}")
    
    # 鍧囧寑閲囨牱5000涓偣
    step = len(df) // 5000
    df_sampled = df.iloc[::step][:5000].copy()
    print(f"  Sampled rows: {len(df_sampled)}")
    
    # 杞崲涓洪€傚悎ECharts鐨勬牸寮?
    result = {
        "time": df_sampled['time'].tolist(),
        "value_highI": df_sampled['value_highI'].tolist(),
        "value_highT": df_sampled['value_highT'].tolist(),
        "value_lowI": df_sampled['value_lowI'].tolist(),
        "metadata": {
            "total_rows": len(df),
            "sampled_rows": len(df_sampled),
            "sampling_rate": step,
            "time_range": {
                "start": df['time'].iloc[0],
                "end": df['time'].iloc[-1]
            },
            "stats": {
                "highI": {"min": float(df['value_highI'].min()), "max": float(df['value_highI'].max()), "mean": float(df['value_highI'].mean())},
                "highT": {"min": float(df['value_highT'].min()), "max": float(df['value_highT'].max()), "mean": float(df['value_highT'].mean())},
                "lowI": {"min": float(df['value_lowI'].min()), "max": float(df['value_lowI'].max()), "mean": float(df['value_lowI'].mean())}
            }
        }
    }
    
    output_path = OUTPUT_DIR / "train_data_sampled.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Saved to: {output_path.name}")
    return result

def sample_and_convert_test_data():
    """澶勭悊娴嬭瘯鏁版嵁 - 閲囨牱涓?000涓偣"""
    print("\n[2/4] Processing test data...")
    
    df = pd.read_csv(PINGGU_DIR / "new_data_PHM5_new.csv")
    print(f"  Original rows: {len(df)}")
    
    # 鍧囧寑閲囨牱3000涓偣
    step = len(df) // 3000
    df_sampled = df.iloc[::step][:3000].copy()
    print(f"  Sampled rows: {len(df_sampled)}")
    
    # 杞崲涓洪€傚悎ECharts鐨勬牸寮?
    result = {
        "index": list(range(len(df_sampled))),
        "HighI": df_sampled['HighI'].tolist(),
        "HighT": df_sampled['HighT'].tolist(),
        "metadata": {
            "total_rows": len(df),
            "sampled_rows": len(df_sampled),
            "sampling_rate": step,
            "stats": {
                "HighI": {"min": float(df['HighI'].min()), "max": float(df['HighI'].max()), "mean": float(df['HighI'].mean())},
                "HighT": {"min": float(df['HighT'].min()), "max": float(df['HighT'].max()), "mean": float(df['HighT'].mean())}
            }
        }
    }
    
    output_path = OUTPUT_DIR / "test_data_sampled.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Saved to: {output_path.name}")
    return result

def convert_model_results():
    """杞崲妯″瀷缁撴灉 - 淇濈暀鍏ㄩ儴鏁版嵁"""
    print("\n[3/4] Processing comparison model results...")
    
    df_duibi = pd.read_csv(PINGGU_DIR / "Duibi_Model.csv")
    print(f"  Duibi Model rows: {len(df_duibi)}")
    
    # Duibi_Model鍒楀悕鏄暟瀛楋紝鑾峰彇绗竴鍒?
    col_name = df_duibi.columns[0]
    
    result_duibi = {
        "index": list(range(len(df_duibi))),
        "HI_Value": df_duibi[col_name].tolist(),
        "metadata": {
            "total_rows": len(df_duibi),
            "model_name": "Comparison Model (瀵规瘮妯″瀷)",
            "stats": {
                "min": float(df_duibi[col_name].min()),
                "max": float(df_duibi[col_name].max()),
                "mean": float(df_duibi[col_name].mean()),
                "std": float(df_duibi[col_name].std())
            }
        }
    }
    
    output_path = OUTPUT_DIR / "duibi_model.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_duibi, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Saved to: {output_path.name}")
    
    print("\n[4/4] Processing proposed model results...")
    
    df_proposed = pd.read_csv(PINGGU_DIR / "Proposed_Model.csv")
    print(f"  Proposed Model rows: {len(df_proposed)}")
    
    result_proposed = {
        "index": list(range(len(df_proposed))),
        "HI_Value": df_proposed['HI_Value'].tolist(),
        "metadata": {
            "total_rows": len(df_proposed),
            "model_name": "Proposed Model (鎻愬嚭妯″瀷)",
            "stats": {
                "min": float(df_proposed['HI_Value'].min()),
                "max": float(df_proposed['HI_Value'].max()),
                "mean": float(df_proposed['HI_Value'].mean()),
                "std": float(df_proposed['HI_Value'].std())
            }
        }
    }
    
    output_path = OUTPUT_DIR / "proposed_model.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_proposed, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Saved to: {output_path.name}")
    
    return result_duibi, result_proposed

def main():
    print("="*80)
    print(" "*25 + "PINGGU Data Conversion")
    print("="*80)
    
    train_data = sample_and_convert_train_data()
    test_data = sample_and_convert_test_data()
    duibi_data, proposed_data = convert_model_results()
    
    print("\n" + "="*80)
    print(" "*30 + "Summary")
    print("="*80)
    print(f"\n[OK] Successfully converted 4 files:")
    print(f"  1. train_data_sampled.json    ({train_data['metadata']['sampled_rows']} points)")
    print(f"  2. test_data_sampled.json     ({test_data['metadata']['sampled_rows']} points)")
    print(f"  3. duibi_model.json           ({duibi_data['metadata']['total_rows']} points)")
    print(f"  4. proposed_model.json        ({proposed_data['metadata']['total_rows']} points)")
    print(f"\n[OK] Output directory: {OUTPUT_DIR}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

