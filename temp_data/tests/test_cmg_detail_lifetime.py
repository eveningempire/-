#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHM璇︽儏椤甸潰瀵垮懡棰勬祴鍔熻兘娴嬭瘯鑴氭湰

璇ヨ剼鏈敤浜庢祴璇旵MG璇︽儏椤甸潰涓鍛介娴嬪姛鑳界殑闆嗘垚銆?
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


def create_test_data_for_cmg_detail():
    """涓篊MG璇︽儏椤甸潰鍒涘缓娴嬭瘯鏁版嵁"""
    print("涓篊MG璇︽儏椤甸潰鍒涘缓娴嬭瘯鏁版嵁...")
    
    # 鍒涘缓PHM绫诲瀷
    cmg_type, created = PHMType.objects.get_or_create(
        name="PHM璇︽儏娴嬭瘯绫诲瀷",
        defaults={'description': '鐢ㄤ簬PHM璇︽儏椤甸潰娴嬭瘯鐨凜MG绫诲瀷'}
    )
    
    # 鍒涘缓PHM妯″瀷
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="PHM璇︽儏娴嬭瘯妯″瀷",
        defaults={
            'description': '鐢ㄤ簬PHM璇︽儏椤甸潰娴嬭瘯鐨凜MG妯″瀷',
            'cmg_type': cmg_type,
            'is_active': True
        }
    )
    
    # 鍒涘缓PHM涓綋
    cmg, created = PHM.objects.get_or_create(
        cmg_id="PHM_DETAIL_TEST_001",
        defaults={
            'name': 'PHM璇︽儏娴嬭瘯-001',
            'cmg_model': cmg_model,
            'enabled': True
        }
    )
    
    # 鍒涘缓娴嬭瘯閬ユ祴鏁版嵁锛堟ā鎷熶竴娈垫椂闂寸殑鏁版嵁锛?
    base_time = datetime.now() - timedelta(hours=2)
    
    for i in range(200):  # 鍒涘缓200鏉℃祴璇曟暟鎹?
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


def test_cmg_detail_lifetime_prediction():
    """娴嬭瘯PHM璇︽儏椤甸潰鐨勫鍛介娴嬪姛鑳?""
    print("\n娴嬭瘯PHM璇︽儏椤甸潰鐨勫鍛介娴嬪姛鑳?..")
    
    service = LifetimePredictionService()
    
    # 鑾峰彇娴嬭瘯PHM
    try:
        cmg = PHM.objects.get(cmg_id="PHM_DETAIL_TEST_001")
    except PHM.DoesNotExist:
        print("鏈壘鍒版祴璇旵MG锛岃鍏堣繍琛宑reate_test_data_for_cmg_detail()")
        return
    
    # 璁剧疆鏃堕棿娈碉紙鏈€鍚?灏忔椂鐨勬暟鎹級
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    print(f"娴嬭瘯鏃堕棿娈? {start_time} 鍒?{end_time}")
    
    # 娴嬭瘯甯︽椂闂存鐨勫鍛介娴?
    result = service.predict_lifetime(
        cmg.id, 
        start_time=start_time.isoformat(),
        data_start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        use_time_range=True
    )
    
    print(f"瀵垮懡棰勬祴缁撴灉: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('status') == 'success':
        print("鉁?PHM璇︽儏椤甸潰瀵垮懡棰勬祴鍔熻兘娴嬭瘯閫氳繃")
        print(f"   RUL鍊? {result.get('rul_value', 0):.2f} 灏忔椂")
        print(f"   缃俊搴? {result.get('confidence', 0):.3f}")
    else:
        print("鉂?PHM璇︽儏椤甸潰瀵垮懡棰勬祴鍔熻兘娴嬭瘯澶辫触")
        print(f"   閿欒淇℃伅: {result.get('message', '鏈煡閿欒')}")


def test_api_endpoints():
    """娴嬭瘯API绔偣"""
    print("\n娴嬭瘯API绔偣...")
    
    print("API绔偣娴嬭瘯闇€瑕佽繍琛孌jango鏈嶅姟鍣?)
    print("鍙互閫氳繃浠ヤ笅鍛戒护鍚姩鏈嶅姟鍣ㄨ繘琛屾祴璇?")
    print("python manage.py runserver")
    print()
    print("鍓嶇娴嬭瘯:")
    print("1. 鍚姩鍓嶇寮€鍙戞湇鍔″櫒: cd frontend && npm run dev")
    print("2. 璁块棶PHM璇︽儏椤甸潰: http://localhost:3000/cmg-detail")
    print("3. 閫夋嫨PHM鍜屾椂闂存")
    print("4. 鐐瑰嚮'棰勬祴瀵垮懡'鎸夐挳")
    print()
    print("API娴嬭瘯:")
    print("- 瀵垮懡棰勬祴: POST http://localhost:8000/api/v1/lifetime/predict/")
    print("- 璇锋眰浣? {\"cmg_id\": 1, \"start_time\": \"2025-08-20T14:00:00\", \"end_time\": \"2025-08-20T15:00:00\"}")


def main():
    """涓绘祴璇曞嚱鏁?""
    print("=" * 60)
    print("PHM璇︽儏椤甸潰瀵垮懡棰勬祴鍔熻兘娴嬭瘯")
    print("=" * 60)
    
    try:
        # 鍒涘缓娴嬭瘯鏁版嵁
        test_cmg = create_test_data_for_cmg_detail()
        
        # 娴嬭瘯瀵垮懡棰勬祴鍔熻兘
        test_cmg_detail_lifetime_prediction()
        
        # 娴嬭瘯API绔偣
        test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("娴嬭瘯瀹屾垚!")
        print("=" * 60)
        
        print("\n涓嬩竴姝?")
        print("1. 鍚姩Django鏈嶅姟鍣? python manage.py runserver")
        print("2. 鍚姩鍓嶇寮€鍙戞湇鍔″櫒: cd frontend && npm run dev")
        print("3. 璁块棶PHM璇︽儏椤甸潰杩涜鍔熻兘楠岃瘉")
        print("4. 閫夋嫨PHM鍜屾椂闂存锛岀偣鍑?棰勬祴瀵垮懡'鎸夐挳")
        
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓彂鐢熼敊璇? {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

