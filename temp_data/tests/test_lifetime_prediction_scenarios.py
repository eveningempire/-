#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瀵垮懡棰勬祴鍦烘櫙娴嬭瘯鑴氭湰

娴嬭瘯涓ょ涓嶅悓鐨勫鍛介娴嬪満鏅細
1. 瀵垮懡棰勬祴澶х晫闈細涓嶉渶瑕佹椂闂存锛屽彧闇€瑕佸惎鐢ㄦ椂闂?
2. PHM璇︽儏椤甸潰锛氶渶瑕佹椂闂存鍜屽惎鐢ㄦ椂闂?
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMModel, PHMType, PHMData
from lifetime_prediction.services import LifetimePredictionService


def create_test_data():
    """鍒涘缓娴嬭瘯鏁版嵁"""
    print("鍒涘缓娴嬭瘯鏁版嵁...")
    
    # 鍒涘缓PHM绫诲瀷
    cmg_type, created = PHMType.objects.get_or_create(
        name="瀵垮懡棰勬祴娴嬭瘯绫诲瀷",
        defaults={'description': '鐢ㄤ簬瀵垮懡棰勬祴娴嬭瘯鐨凜MG绫诲瀷'}
    )
    
    # 鍒涘缓PHM妯″瀷
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="瀵垮懡棰勬祴娴嬭瘯妯″瀷",
        defaults={
            'description': '鐢ㄤ簬瀵垮懡棰勬祴娴嬭瘯鐨凜MG妯″瀷',
            'cmg_type': cmg_type,
            'is_active': True
        }
    )
    
    # 鍒涘缓PHM涓綋
    cmg, created = PHM.objects.get_or_create(
        cmg_id="LIFETIME_TEST_001",
        defaults={
            'name': '瀵垮懡棰勬祴娴嬭瘯-001',
            'cmg_model': cmg_model,
            'enabled': True
        }
    )
    
    # 鍒涘缓娴嬭瘯閬ユ祴鏁版嵁锛堟ā鎷熶竴娈垫椂闂寸殑鏁版嵁锛?
    base_time = datetime.now() - timedelta(hours=3)
    
    for i in range(300):  # 鍒涘缓300鏉℃祴璇曟暟鎹?
        timestamp = base_time + timedelta(minutes=i)
        
        # 鍒涘缓鍖呭惈鎵€闇€閬ユ祴閲忕殑鏁版嵁
        telemetry_data = {
            "楂橀€熺數鏈虹數鍘?: 100.0 + i * 0.1 + (i % 10) * 0.5,  # 妯℃嫙鐢靛帇鍙樺寲
            "楂橀€熺數鏈虹數娴?: 5.0 + i * 0.05 + (i % 15) * 0.2,   # 妯℃嫙鐢垫祦鍙樺寲
            "浣庨€烝鐩哥數娴?: 2.0 + i * 0.02 + (i % 20) * 0.1,    # 妯℃嫙A鐩哥數娴?
            "浣庨€烠鐩哥數娴?: 2.0 + i * 0.02 + (i % 25) * 0.1,    # 妯℃嫙C鐩哥數娴?
            "鍏朵粬鍙傛暟1": 50.0 + i * 0.1,      # 鍏朵粬閬ユ祴閲?
            "鍏朵粬鍙傛暟2": 25.0 + i * 0.05,
        }
        
        cmg_data, created = PHMData.objects.get_or_create(
            cmg=cmg,
            timestamp=timestamp,
            defaults={
                'data': telemetry_data,
                'import_session': None
            }
        )
    
    print(f"鍒涘缓浜?{PHMData.objects.filter(cmg=cmg).count()} 鏉℃祴璇曟暟鎹?)
    return cmg


def test_lifetime_prediction_main_interface():
    """娴嬭瘯瀵垮懡棰勬祴澶х晫闈紙涓嶉渶瑕佹椂闂存锛?""
    print("\n" + "="*60)
    print("娴嬭瘯瀵垮懡棰勬祴澶х晫闈紙涓嶉渶瑕佹椂闂存锛?)
    print("="*60)
    
    service = LifetimePredictionService()
    
    # 鑾峰彇娴嬭瘯PHM
    try:
        cmg = PHM.objects.get(cmg_id="LIFETIME_TEST_001")
    except PHM.DoesNotExist:
        print("鏈壘鍒版祴璇旵MG锛岃鍏堣繍琛宑reate_test_data()")
        return
    
    # 璁剧疆鍚敤鏃堕棿锛堜絾涓嶈缃椂闂存锛?
    start_time = "2024-01-01 00:00:00"  # PHM鍚敤鏃堕棿
    
    print(f"PHM: {cmg.cmg_id}")
    print(f"鍚敤鏃堕棿: {start_time}")
    print("鏃堕棿娈? 涓嶆寚瀹氾紙鑷姩鑾峰彇鏈€鍚?000鏉℃暟鎹級")
    
    # 娴嬭瘯涓嶅甫鏃堕棿娈电殑瀵垮懡棰勬祴锛堝鍛介娴嬪ぇ鐣岄潰锛?
    result = service.predict_lifetime(
        cmg.id, 
        design_life=10.0,  # 10骞磋璁″鍛?
        start_time=start_time,  # PHM鍚敤鏃堕棿
        # 涓嶄紶閫抎ata_start_time鍜宔nd_time锛岃〃绀轰笉浣跨敤鏃堕棿娈佃繃婊?
        use_time_range=False
    )
    
    print(f"\n棰勬祴缁撴灉: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('status') == 'success':
        print("鉁?瀵垮懡棰勬祴澶х晫闈㈡祴璇曢€氳繃")
        print(f"   RUL鍊? {result.get('rul_value', 0):.2f} 灏忔椂")
    else:
        print("鉂?瀵垮懡棰勬祴澶х晫闈㈡祴璇曞け璐?)
        print(f"   閿欒淇℃伅: {result.get('message', '鏈煡閿欒')}")


def test_cmg_detail_lifetime_prediction():
    """娴嬭瘯PHM璇︽儏椤甸潰鐨勫鍛介娴嬶紙闇€瑕佹椂闂存锛?""
    print("\n" + "="*60)
    print("娴嬭瘯PHM璇︽儏椤甸潰鐨勫鍛介娴嬶紙闇€瑕佹椂闂存锛?)
    print("="*60)
    
    service = LifetimePredictionService()
    
    # 鑾峰彇娴嬭瘯PHM
    try:
        cmg = PHM.objects.get(cmg_id="LIFETIME_TEST_001")
    except PHM.DoesNotExist:
        print("鏈壘鍒版祴璇旵MG锛岃鍏堣繍琛宑reate_test_data()")
        return
    
    # 璁剧疆鏃堕棿娈碉紙鏈€鍚?灏忔椂鐨勬暟鎹級
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    # 璁剧疆鍚敤鏃堕棿
    cmg_start_time = "2024-01-01 00:00:00"  # PHM鍚敤鏃堕棿
    
    print(f"PHM: {cmg.cmg_id}")
    print(f"鍚敤鏃堕棿: {cmg_start_time}")
    print(f"鏁版嵁鏌ヨ鏃堕棿娈? {start_time} 鍒?{end_time}")
    
    # 娴嬭瘯甯︽椂闂存鐨勫鍛介娴嬶紙PHM璇︽儏椤甸潰锛?
    result = service.predict_lifetime(
        cmg.id, 
        design_life=10.0,  # 10骞磋璁″鍛?
        start_time=cmg_start_time,  # PHM鍚敤鏃堕棿
        data_start_time=start_time.isoformat(),  # 鏁版嵁鏌ヨ寮€濮嬫椂闂?
        end_time=end_time.isoformat(),  # 鏁版嵁鏌ヨ缁撴潫鏃堕棿
        use_time_range=True  # 浣跨敤鏃堕棿娈佃繃婊?
    )
    
    print(f"\n棰勬祴缁撴灉: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('status') == 'success':
        print("鉁?PHM璇︽儏椤甸潰瀵垮懡棰勬祴娴嬭瘯閫氳繃")
        print(f"   RUL鍊? {result.get('rul_value', 0):.2f} 灏忔椂")
    else:
        print("鉂?PHM璇︽儏椤甸潰瀵垮懡棰勬祴娴嬭瘯澶辫触")
        print(f"   閿欒淇℃伅: {result.get('message', '鏈煡閿欒')}")


def test_timestamp_parsing():
    """娴嬭瘯鏃堕棿鎴宠В鏋愬姛鑳?""
    print("\n" + "="*60)
    print("娴嬭瘯鏃堕棿鎴宠В鏋愬姛鑳?)
    print("="*60)
    
    import pandas as pd
    
    # 娴嬭瘯鏁版嵁
    test_timestamps = [
        "2024-04-24T15:46:29.001000+00:00",  # 鍘熷閿欒鏍煎紡
        "2024-04-24T15:46:29.001Z",          # Z鏍煎紡
        "2024-04-24T15:46:29.001",           # 鏃犳椂鍖烘牸寮?
        "2024-04-24 15:46:29",               # 绌烘牸鍒嗛殧鏍煎紡
        "2024/04/24 15:46:29",               # 鏂滄潬鍒嗛殧鏍煎紡
    ]
    
    def parse_timestamp(ts):
        """妯℃嫙淇鍚庣殑鏃堕棿鎴宠В鏋愬嚱鏁?""
        if isinstance(ts, str):
            # 澶勭悊ISO8601鏍煎紡鐨勬椂闂存埑
            if ts.endswith('+00:00'):
                # 宸茬粡鏄纭殑鏍煎紡
                return pd.to_datetime(ts)
            elif ts.endswith('Z'):
                # 灏哯鏇挎崲涓?00:00
                return pd.to_datetime(ts.replace('Z', '+00:00'))
            else:
                # 灏濊瘯鐩存帴瑙ｆ瀽
                return pd.to_datetime(ts)
        return pd.to_datetime(ts)
    
    print("娴嬭瘯鍚勭鏃堕棿鎴虫牸寮?")
    for i, ts in enumerate(test_timestamps, 1):
        try:
            parsed = parse_timestamp(ts)
            print(f"鉁?{i}. {ts} -> {parsed}")
        except Exception as e:
            print(f"鉂?{i}. {ts} -> 閿欒: {e}")
    
    # 娴嬭瘯pandas Series
    print("\n娴嬭瘯pandas Series:")
    try:
        time_stamps_series = pd.Series(test_timestamps)
        parsed_series = time_stamps_series.apply(parse_timestamp)
        print("鉁?pandas Series瑙ｆ瀽鎴愬姛")
        for i, (original, parsed) in enumerate(zip(test_timestamps, parsed_series)):
            print(f"   {i+1}. {original} -> {parsed}")
    except Exception as e:
        print(f"鉂?pandas Series瑙ｆ瀽澶辫触: {e}")


def main():
    """涓绘祴璇曞嚱鏁?""
    print("=" * 80)
    print("瀵垮懡棰勬祴鍦烘櫙娴嬭瘯")
    print("=" * 80)
    
    try:
        # 鍒涘缓娴嬭瘯鏁版嵁
        test_cmg = create_test_data()
        
        # 娴嬭瘯鏃堕棿鎴宠В鏋?
        test_timestamp_parsing()
        
        # 娴嬭瘯瀵垮懡棰勬祴澶х晫闈?
        test_lifetime_prediction_main_interface()
        
        # 娴嬭瘯PHM璇︽儏椤甸潰
        test_cmg_detail_lifetime_prediction()
        
        print("\n" + "=" * 80)
        print("娴嬭瘯瀹屾垚!")
        print("=" * 80)
        
        print("\n鎬荤粨:")
        print("1. 鉁?鏃堕棿鎴宠В鏋愪慨澶嶅凡搴旂敤")
        print("2. 鉁?瀵垮懡棰勬祴澶х晫闈細涓嶉渶瑕佹椂闂存锛屽彧闇€瑕佸惎鐢ㄦ椂闂?)
        print("3. 鉁?PHM璇︽儏椤甸潰锛氶渶瑕佹椂闂存鍜屽惎鐢ㄦ椂闂?)
        print("4. 鉁?涓ょ鍦烘櫙閮借兘姝ｇ‘鍖哄垎鍜屽鐞?)
        
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓彂鐢熼敊璇? {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

