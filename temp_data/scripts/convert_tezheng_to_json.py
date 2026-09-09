"""
鎻愬彇tezheng鏂囦欢澶圭殑鏁版嵁骞惰浆鎹负JSON
1. 鍘熷淇″彿鏁版嵁锛堥噰鏍凤級
2. HI瓒嬪娍鏁版嵁锛堜粠.mat鏂囦欢鎻愬彇锛?
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
import scipy.io as sio

BASE_DIR = Path(__file__).parent.parent
TEZHENG_DIR = BASE_DIR / "tezheng"
OUTPUT_DIR = BASE_DIR / "frontend" / "public" / "feature-extraction"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_raw_signals():
    """
    鎻愬彇鍘熷淇″彿鏁版嵁锛?涓弬鏁帮紝鎸夊伐鍐靛垎绂伙級
    閲囨牱绛栫暐锛氭瘡灏忔椂閲囨牱锛岄檷閲囨牱鍒扮害2000涓偣姣忎釜宸ュ喌
    浣跨敤鐪熷疄鏃堕棿鎴?
    """
    print("\n[1/2] Extracting raw signals data...")
    
    dataset_dir = TEZHENG_DIR / "Dataset_PHM"
    
    try:
        result = {}
        
        for OC in range(3):
            file_path = dataset_dir / f"PHM_dataset_x24x60_OC{OC}.csv"
            print(f"  Loading {file_path.name}...")
            
            # 璇诲彇CSV锛屽皾璇曞绉嶇紪鐮?
            df = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'gbk', 'gb18030']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"  Successfully read with encoding: {encoding}")
                    break
                except:
                    continue
            
            if df is None:
                print(f"  [ERROR] Could not read file with any encoding")
                continue
            
            # 绗竴鍒楁槸鏃堕棿锛岃浆鎹负datetime
            time_col = df.columns[0]
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.set_index(time_col)
            df = df.dropna()
            
            print(f"  OC{OC}: Loaded {len(df)} rows")
            print(f"  OC{OC}: Time range: {df.index[0]} to {df.index[-1]}")
            
            # OC0鐗规畩澶勭悊锛堟埅鍙栧墠1800灏忔椂锛?
            if OC == 0:
                df = df.iloc[:1800 * 60]
            
            # 鎸夊皬鏃堕噸閲囨牱
            df_resampled = df.resample('1h').mean().dropna()
            
            print(f"  OC{OC}: After hourly resampling: {len(df_resampled)} rows")
            
            # 鎻愬彇闇€瑕佺殑鍒?
            # 鏍规嵁鏌ョ湅鐨勬暟鎹紝鍒楅『搴忎负锛氭椂闂? 鍔熺巼, 鐢垫祦, 娓╁害, ?, 楂橀€熻浆閫? 浣庨€熻浆閫? RUL, ?
            # 绱㈠紩浠?寮€濮嬶紙浣?鏄椂闂达紝宸茶涓篿ndex锛?
            # df.columns搴旇鏄細鍔熺巼(0), 鐢垫祦(1), 娓╁害(2), ?(3), 楂橀€熻浆閫?4), 浣庨€熻浆閫?5), RUL(6), ?(7)
            
            # 鍒犻櫎寮傚父鍊硷紙浣庨€熺粍浠惰浆閫?< 16鐨勭偣锛?
            # 浣嗚纭繚涓嶄細鍒犻櫎鎵€鏈夋暟鎹?
            low_speed_col_idx = 5 if len(df_resampled.columns) > 5 else None
            
            if low_speed_col_idx is not None:
                low_speed_col = df_resampled.columns[low_speed_col_idx]
                # 妫€鏌ユ湁澶氬皯琛屾弧瓒虫潯浠?
                valid_mask = df_resampled[low_speed_col] >= 16
                num_valid = valid_mask.sum()
                
                if num_valid > 0:
                    df_cleaned = df_resampled[valid_mask]
                    if OC == 0 and len(df_cleaned) > 8313:
                        df_cleaned = df_cleaned.iloc[:8313]
                    print(f"  OC{OC}: Removed {len(df_resampled) - len(df_cleaned)} anomalous rows")
                else:
                    # 濡傛灉鎵€鏈夎閮戒笉婊¤冻鏉′欢锛屼笉杩涜杩囨护
                    print(f"  OC{OC}: Warning - all rows have low speed < 16, keeping all data")
                    df_cleaned = df_resampled
            else:
                df_cleaned = df_resampled
            
            # 杩涗竴姝ラ檷閲囨牱鍒?000涓偣
            step = max(1, len(df_cleaned) // 2000)
            df_sampled = df_cleaned.iloc[::step][:2000]
            
            print(f"  OC{OC}: Final sampled: {len(df_sampled)} points")
            
            # 鎻愬彇鏃堕棿鎴冲拰4涓叧閿弬鏁?
            # 鍒楋細鍔熺巼(0), 鐢垫祦(1), 娓╁害(2), ?, 楂橀€熻浆閫?4), 浣庨€熻浆閫?5)
            
            result[f'OC{OC}'] = {
                "timestamps": df_sampled.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                "high_speed": df_sampled.iloc[:, 4].tolist() if len(df_sampled.columns) > 4 else [],
                "high_temp": df_sampled.iloc[:, 2].tolist() if len(df_sampled.columns) > 2 else [],
                "high_current": df_sampled.iloc[:, 1].tolist() if len(df_sampled.columns) > 1 else [],
                "high_voltage": (df_sampled.iloc[:, 0] / df_sampled.iloc[:, 1]).tolist() if len(df_sampled.columns) > 1 else [],
                "metadata": {
                    "points": len(df_sampled),
                    "condition": f"OC{OC}",
                    "time_start": str(df_sampled.index[0]),
                    "time_end": str(df_sampled.index[-1]),
                    "description": "4 key parameters: High Speed, Temp, Current, Voltage"
                }
            }
        
        output_path = OUTPUT_DIR / "raw_signals.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"  [OK] Saved to: {output_path.name}")
        return result
        
    except Exception as e:
        print(f"  [ERROR] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def extract_HI_trends():
    """
    浠嶮ATLAB .mat鏂囦欢鎻愬彇HI瓒嬪娍鏁版嵁
    4绉嶆柟娉?脳 3绉嶅伐鍐?= 12涓暟鎹泦
    """
    print("\n[2/2] Extracting HI trend data from .mat files...")
    
    fig_plot_dir = TEZHENG_DIR / "Fig_plot"
    
    methods = {
        'PCA': 'Fig_7_d',      # PCA鏂规硶
        'CNN': 'Fig_7_b',      # CNN鏂规硶
        'Residual': 'Fig_7_c', # 娈嬪樊鏂规硶
        'Proposed': 'Fig_7_a'  # 鏈枃鎻愬嚭鏂规硶
    }
    
    conditions = ['OC0', 'OC1', 'OC2']
    
    results = {}
    
    for method_name, file_prefix in methods.items():
        results[method_name] = {}
        
        for oc in conditions:
            file_name = f"{file_prefix}_{oc}.mat"
            file_path = fig_plot_dir / file_name
            
            if not file_path.exists():
                print(f"  [WARNING] File not found: {file_name}")
                continue
            
            try:
                # 璇诲彇.mat鏂囦欢
                mat_data = sio.loadmat(file_path)
                
                # 鎻愬彇HI鏁版嵁
                HI = mat_data['HI'].reshape(-1)
                
                # 瀵逛簬Proposed鏂规硶锛岄渶瑕佺疮绉眰鍜屽苟缂╁皬100鍊?
                if method_name == 'Proposed':
                    HI = np.cumsum(HI) / 100.0
                
                HI = HI.tolist()
                
                results[method_name][oc] = {
                    "index": list(range(len(HI))),
                    "HI": HI,
                    "metadata": {
                        "method": method_name,
                        "condition": oc,
                        "points": len(HI)
                    }
                }
                
                print(f"  [OK] Extracted {method_name} {oc}: {len(HI)} points")
                
                # 瀵逛簬Residual鏂规硶锛岃繕鏈塀ias鏁版嵁
                if method_name == 'Residual':
                    bias_file = fig_plot_dir / f"Fig_7_cs_{oc}.mat"
                    if bias_file.exists():
                        bias_data = sio.loadmat(bias_file)
                        HI_bias = bias_data['HI'].reshape(-1).tolist()
                        results[method_name][oc]['HI_bias'] = HI_bias
                        print(f"  [OK] Extracted Residual Bias {oc}: {len(HI_bias)} points")
                
            except Exception as e:
                print(f"  [ERROR] Failed to extract {file_name}: {str(e)}")
    
    # 淇濆瓨鎵€鏈塇I鏁版嵁
    output_path = OUTPUT_DIR / "hi_trends.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Saved to: {output_path.name}")
    return results

def create_feature_definitions():
    """
    鍒涘缓11涓椂鍩熺壒寰佺殑瀹氫箟鏁版嵁
    """
    print("\n[3/3] Creating feature definitions...")
    
    features = [
        {
            "name": "mean",
            "cn_name": "鍧囧€?,
            "formula": "渭 = (1/N) 危x_i",
            "description": "淇″彿鐨勫钩鍧囧€硷紝鍙嶆槧淇″彿鐨勭洿娴佸垎閲?,
            "category": "缁熻鐗瑰緛"
        },
        {
            "name": "var",
            "cn_name": "鏂瑰樊",
            "formula": "蟽虏 = (1/N) 危(x_i - 渭)虏",
            "description": "淇″彿鍋忕鍧囧€肩殑绋嬪害锛屽弽鏄犱俊鍙风殑娉㈠姩鎬?,
            "category": "缁熻鐗瑰緛"
        },
        {
            "name": "std",
            "cn_name": "鏍囧噯宸?,
            "formula": "蟽 = 鈭歷ar",
            "description": "鏂瑰樊鐨勫钩鏂规牴锛屽弽鏄犱俊鍙风殑绂绘暎绋嬪害",
            "category": "缁熻鐗瑰緛"
        },
        {
            "name": "rms",
            "cn_name": "鍧囨柟鏍?,
            "formula": "RMS = 鈭歔(1/N) 危x_i虏]",
            "description": "淇″彿鑳介噺鐨勫害閲忥紝鍙嶆槧淇″彿鐨勬湁鏁堝€?,
            "category": "鑳介噺鐗瑰緛"
        },
        {
            "name": "peak2peak",
            "cn_name": "宄板嘲鍊?,
            "formula": "P2P = max(x) - min(x)",
            "description": "淇″彿鏈€澶у€间笌鏈€灏忓€间箣宸紝鍙嶆槧淇″彿鐨勫姩鎬佽寖鍥?,
            "category": "骞呭€肩壒寰?
        },
        {
            "name": "skew",
            "cn_name": "鍋忓害",
            "formula": "Skew = E[(x-渭)鲁] / 蟽鲁",
            "description": "淇″彿鍒嗗竷鐨勫绉版€у害閲忥紝鍙嶆槧鍒嗗竷鐨勫亸鏂滄柟鍚?,
            "category": "鍒嗗竷鐗瑰緛"
        },
        {
            "name": "kurt",
            "cn_name": "宄害",
            "formula": "Kurt = E[(x-渭)鈦碷 / 蟽鈦?,
            "description": "淇″彿鍒嗗竷鐨勫熬閮ㄥ帤搴︼紝鍙嶆槧寮傚父鍊肩殑瀛樺湪",
            "category": "鍒嗗竷鐗瑰緛"
        },
        {
            "name": "form_factor",
            "cn_name": "娉㈠舰鍥犲瓙",
            "formula": "FF = RMS / mean(|x|)",
            "description": "娉㈠舰褰㈢姸鐨勫害閲忥紝鍙嶆槧淇″彿鐨勬尝褰㈢壒鎬?,
            "category": "褰㈢姸鍥犲瓙"
        },
        {
            "name": "crest_factor",
            "cn_name": "宄板€煎洜瀛?,
            "formula": "CF = max(|x|) / RMS",
            "description": "宄板€间笌鏈夋晥鍊间箣姣旓紝鍙嶆槧鍐插嚮鐗规€?,
            "category": "褰㈢姸鍥犲瓙"
        },
        {
            "name": "clearance_factor",
            "cn_name": "瑁曞害鍥犲瓙",
            "formula": "CLF = max(|x|) / [mean(鈭殀x|)]虏",
            "description": "淇″彿瑁曞害鐨勫害閲忥紝瀵规棭鏈熸晠闅滄晱鎰?,
            "category": "褰㈢姸鍥犲瓙"
        },
        {
            "name": "kurtosis_factor",
            "cn_name": "宄害鍥犲瓙",
            "formula": "KF = Kurt / 蟽鈦?,
            "description": "褰掍竴鍖栫殑宄害锛屽寮哄鍐插嚮鐨勬晱鎰熸€?,
            "category": "褰㈢姸鍥犲瓙"
        }
    ]
    
    output_path = OUTPUT_DIR / "feature_definitions.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(features, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Saved to: {output_path.name}")
    return features

def main():
    print("="*80)
    print(" "*20 + "Feature Extraction Data Conversion")
    print("="*80)
    
    # 1. 鎻愬彇鍘熷淇″彿
    raw_signals = extract_raw_signals()
    
    # 2. 鎻愬彇HI瓒嬪娍
    hi_trends = extract_HI_trends()
    
    # 3. 鍒涘缓鐗瑰緛瀹氫箟
    features = create_feature_definitions()
    
    print("\n" + "="*80)
    print(" "*30 + "Summary")
    print("="*80)
    
    if raw_signals:
        total_points = sum(raw_signals[oc]['metadata']['points'] for oc in raw_signals if 'metadata' in raw_signals[oc])
        print(f"\n[OK] Raw signals: {total_points} points (3 conditions)")
    
    if hi_trends:
        total_datasets = sum(len(methods) for methods in hi_trends.values())
        print(f"[OK] HI trends: {total_datasets} datasets")
    
    if features:
        print(f"[OK] Feature definitions: {len(features)} features")
    
    print(f"\n[OK] Output directory: {OUTPUT_DIR}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

