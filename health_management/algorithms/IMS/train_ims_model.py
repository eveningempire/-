#!/usr/bin/env python3
"""
IMS妯″瀷璁粌鑴氭湰
鐙珛杩愯锛岀敓鎴愯缁冨ソ鐨処MS妯″瀷JSON鏂囦欢
"""

import os
import sys
import pandas as pd
import numpy as np
import json
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

from health_management.algorithms.IMS.ims_algorithm import create_ims_model


def load_training_data(data_dir, selected_params=None):
    """鍔犺浇璁粌鏁版嵁"""
    data_dir = Path(data_dir)
    all_data = []
    
    # 璇诲彇鎵€鏈塁SV鏂囦欢
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"鍦?{data_dir} 涓湭鎵惧埌CSV鏂囦欢")
    
    print(f"鎵惧埌 {len(csv_files)} 涓缁冩暟鎹枃浠?")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
    
    for csv_file in csv_files:
        try:
            # 灏濊瘯涓嶅悓鐨勭紪鐮?
            for encoding in ['gbk', 'utf-8', 'utf-8-sig']:
                try:
                    df = pd.read_csv(csv_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"璀﹀憡: 鏃犳硶璇诲彇鏂囦欢 {csv_file}锛岃烦杩?)
                continue
            
            print(f"鎴愬姛璇诲彇 {csv_file.name}锛屽舰鐘? {df.shape}")
            
            # 濡傛灉鏈夋椂闂村垪锛屽幓鎺夊畠
            time_columns = ['鏃堕棿', 'time', 'timestamp', '鏃堕棿鎴?]
            for col in time_columns:
                if col in df.columns:
                    df = df.drop(columns=[col])
            
            # 鍘绘帀闈炴暟鍊煎垪
            numeric_columns = []
            for col in df.columns:
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    numeric_columns.append(col)
                except:
                    continue
            
            df_numeric = df[numeric_columns]
            
            # 杩囨护閫夊畾鐨勫弬鏁?
            if selected_params:
                available_params = [p for p in selected_params if p in df_numeric.columns]
                if available_params:
                    df_numeric = df_numeric[available_params]
                else:
                    print(f"璀﹀憡: 鏂囦欢 {csv_file.name} 涓病鏈夋壘鍒版寚瀹氱殑鍙傛暟")
                    continue
            
            # 杞崲涓烘暟鍊肩被鍨?
            for col in df_numeric.columns:
                df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce')
            
            # 绉婚櫎鍏ㄤ负NaN鐨勮鍜屽垪
            df_numeric = df_numeric.dropna(axis=1, how='all')  # 鍒犻櫎鍏ㄤ负NaN鐨勫垪
            df_numeric = df_numeric.dropna(axis=0, how='all')  # 鍒犻櫎鍏ㄤ负NaN鐨勮
            
            if len(df_numeric) > 0:
                all_data.append(df_numeric)
                print(f"  鏈夋晥鏁版嵁褰㈢姸: {df_numeric.shape}")
                print(f"  鍙傛暟鍒? {list(df_numeric.columns)}")
        
        except Exception as e:
            print(f"璇诲彇鏂囦欢 {csv_file} 鏃跺嚭閿? {e}")
            continue
    
    if not all_data:
        raise ValueError("娌℃湁鏈夋晥鐨勮缁冩暟鎹?)
    
    # 鍚堝苟鎵€鏈夋暟鎹?
    print("\n鍚堝苟璁粌鏁版嵁...")
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # 纭繚鎵€鏈夊弬鏁板悕涓€鑷?
    all_columns = set()
    for df in all_data:
        all_columns.update(df.columns)
    
    # 閲嶆柊绱㈠紩锛岀己澶辩殑鍒楃敤NaN濉厖
    combined_data = combined_data.reindex(columns=list(all_columns))
    
    print(f"鍚堝苟鍚庢暟鎹舰鐘? {combined_data.shape}")
    print(f"鏈€缁堝弬鏁板垪: {list(combined_data.columns)}")
    
    return combined_data


def filter_parameters(df, exclude_patterns=None, min_variance=1e-6):
    """杩囨护鍙傛暟锛屽幓闄や笉閫傚悎鐩戞祴鐨勫弬鏁?""
    if exclude_patterns is None:
        exclude_patterns = [
            'frame', 'Frame', '甯?,
            'time', 'Time', '鏃堕棿',
            'id', 'ID', '缂栧彿',
            'count', 'Count', '璁℃暟',
            'flag', 'Flag', '鏍囧織',
            'status', 'Status', '鐘舵€?,
            'code', 'Code', '浠ｇ爜',
            'src', 'source', '婧愮爜'
        ]
    
    filtered_columns = []
    
    for col in df.columns:
        # 妫€鏌ユ槸鍚﹀尮閰嶆帓闄ゆā寮?
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern.lower() in col.lower():
                should_exclude = True
                break
        
        if should_exclude:
            print(f"鎺掗櫎鍙傛暟: {col} (鍖归厤鎺掗櫎妯″紡)")
            continue
        
        # 妫€鏌ユ柟宸?
        col_data = pd.to_numeric(df[col], errors='coerce')
        if col_data.var() < min_variance:
            print(f"鎺掗櫎鍙傛暟: {col} (鏂瑰樊杩囧皬: {col_data.var():.2e})")
            continue
        
        # 妫€鏌ラ潪NaN鍊肩殑姣斾緥
        valid_ratio = col_data.notna().sum() / len(col_data)
        if valid_ratio < 0.5:
            print(f"鎺掗櫎鍙傛暟: {col} (鏈夋晥鍊兼瘮渚嬭繃浣? {valid_ratio:.2%})")
            continue
        
        filtered_columns.append(col)
    
    print(f"\n杩囨护鍚庝繚鐣?{len(filtered_columns)} 涓弬鏁?")
    for col in filtered_columns:
        print(f"  - {col}")
    
    return filtered_columns


def train_ims_model(data_dir, output_path, selected_params=None, model_config=None):
    """璁粌IMS妯″瀷"""
    print("=" * 60)
    print("寮€濮婭MS妯″瀷璁粌")
    print("=" * 60)
    
    # 鍔犺浇鏁版嵁
    print("\n1. 鍔犺浇璁粌鏁版嵁...")
    df = load_training_data(data_dir, selected_params)
    
    # 杩囨护鍙傛暟
    print("\n2. 杩囨护鍙傛暟...")
    if selected_params is None:
        valid_params = filter_parameters(df)
        df_filtered = df[valid_params]
    else:
        valid_params = [p for p in selected_params if p in df.columns]
        df_filtered = df[valid_params]
        print(f"浣跨敤鐢ㄦ埛鎸囧畾鐨?{len(valid_params)} 涓弬鏁?)
    
    if len(valid_params) == 0:
        raise ValueError("娌℃湁鏈夋晥鐨勫弬鏁扮敤浜庤缁?)
    
    # 鏁版嵁棰勫鐞?
    print("\n3. 鏁版嵁棰勫鐞?..")
    print(f"鍘熷鏁版嵁褰㈢姸: {df_filtered.shape}")
    
    # 绉婚櫎鍖呭惈杩囧NaN鐨勮
    threshold = len(valid_params) * 0.7  # 鑷冲皯70%鐨勫弬鏁版湁鍊?
    df_clean = df_filtered.dropna(thresh=threshold)
    print(f"娓呯悊鍚庢暟鎹舰鐘? {df_clean.shape}")
    
    if len(df_clean) < 100:
        print("璀﹀憡: 璁粌鏁版嵁杈冨皯锛屾ā鍨嬫晥鏋滃彲鑳戒笉浣?)
    
    # 鏁版嵁閲囨牱锛堝鏋滄暟鎹お澶э級
    if len(df_clean) > 50000:
        print(f"鏁版嵁閲忚緝澶?{len(df_clean)}琛?锛岄噰鏍疯嚦50000琛?)
        df_clean = df_clean.sample(n=50000, random_state=42)
    
    # 杞崲涓簄umpy鏁扮粍
    training_data = df_clean.values.astype(np.float32)
    
    # 鍒涘缓鍜岃缁冩ā鍨?
    print("\n4. 鍒涘缓鍜岃缁僆MS妯″瀷...")
    if model_config is None:
        model_config = {
            "contamination": 0.05,      # PHM绯荤粺寮傚父鐜囬€氬父杈冧綆
            "n_estimators": 150,        # 澧炲姞鏍戠殑鏁伴噺鎻愰珮绮惧害
            "max_samples": "auto",
            "max_features": 0.8,        # 浣跨敤80%鐨勭壒寰?
            "bootstrap": False,
            "random_state": 42,
            "scaler_type": "standard"   # 浣跨敤鏍囧噯鍖?
        }
    
    model = create_ims_model(valid_params, model_config)
    
    print(f"璁粌鍙傛暟: {valid_params}")
    print(f"妯″瀷閰嶇疆: {model_config}")
    
    # 璁粌妯″瀷
    model.fit(training_data, save=False)
    
    # 淇濆瓨妯″瀷
    print("\n5. 淇濆瓨妯″瀷...")
    model_json = model.to_json()
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(model_json)
    
    print(f"妯″瀷宸蹭繚瀛樺埌: {output_path}")
    
    # 淇濆瓨鍏冩暟鎹?
    metadata = {
        "model_type": "IMS",
        "parameters": valid_params,
        "config": model_config,
        "training_data_shape": df_clean.shape,
        "training_samples": len(df_clean),
        "threshold": float(model.threshold_value),
        "feature_importance": {
            param: float(importance) 
            for param, importance in zip(valid_params, model.feature_importance)
        } if model.feature_importance is not None else {}
    }
    
    metadata_path = output_path.with_suffix('.metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"鍏冩暟鎹凡淇濆瓨鍒? {metadata_path}")
    
    # 璇勪及妯″瀷
    print("\n6. 妯″瀷璇勪及...")
    try:
        # 鍦ㄨ缁冩暟鎹笂娴嬭瘯
        anomaly_list, scores, _ = model.validate(training_data[:1000])  # 娴嬭瘯鍓?000涓牱鏈?
        anomaly_rate = len(anomaly_list) / 1000
        avg_score = np.mean(scores)
        
        print(f"娴嬭瘯鏍锋湰寮傚父鐜? {anomaly_rate:.2%}")
        print(f"骞冲潎寮傚父鍒嗘暟: {avg_score:.4f}")
        print(f"闃堝€? {model.threshold_value:.4f}")
        
        # 鐗瑰緛閲嶈鎬?
        if model.feature_importance is not None:
            print("\n鐗瑰緛閲嶈鎬ф帓鍚?")
            importance_pairs = list(zip(valid_params, model.feature_importance))
            importance_pairs.sort(key=lambda x: x[1], reverse=True)
            for i, (param, importance) in enumerate(importance_pairs[:10]):
                print(f"  {i+1:2d}. {param}: {importance:.4f}")
    
    except Exception as e:
        print(f"妯″瀷璇勪及鏃跺嚭閿? {e}")
    
    print("\n" + "=" * 60)
    print("IMS妯″瀷璁粌瀹屾垚!")
    print("=" * 60)
    
    return model, metadata


def main():
    """涓诲嚱鏁?""
    import argparse
    
    parser = argparse.ArgumentParser(description='璁粌IMS寮傚父妫€娴嬫ā鍨?)
    parser.add_argument('--data_dir', 
                       default='health_management/algorithms/IMS/Health',
                       help='璁粌鏁版嵁鐩綍')
    parser.add_argument('--output', 
                       default='health_management/algorithms/IMS/models/ims_model.json',
                       help='杈撳嚭妯″瀷鏂囦欢璺緞')
    parser.add_argument('--params', nargs='+', 
                       help='鎸囧畾瑕佺洃娴嬬殑鍙傛暟鍚嶇О')
    parser.add_argument('--contamination', type=float, default=0.05,
                       help='寮傚父姣斾緥 (榛樿: 0.05)')
    parser.add_argument('--n_estimators', type=int, default=150,
                       help='闅旂鏍戞暟閲?(榛樿: 150)')
    
    args = parser.parse_args()
    
    # 妯″瀷閰嶇疆
    model_config = {
        "contamination": args.contamination,
        "n_estimators": args.n_estimators,
        "max_samples": "auto",
        "max_features": 0.8,
        "bootstrap": False,
        "random_state": 42,
        "scaler_type": "standard"
    }
    
    try:
        model, metadata = train_ims_model(
            data_dir=args.data_dir,
            output_path=args.output,
            selected_params=args.params,
            model_config=model_config
        )
        print(f"\n鉁?璁粌鎴愬姛锛佹ā鍨嬫枃浠? {args.output}")
        
    except Exception as e:
        print(f"\n鉂?璁粌澶辫触: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

