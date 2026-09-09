#!/usr/bin/env python
"""
娴嬭瘯閮ㄤ欢璇︽儏API鐨勫垎鏁版彁鍙栧姛鑳?
"""
import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmg_v2_5.settings')
django.setup()

def test_component_details_api():
    """娴嬭瘯閮ㄤ欢璇︽儏API"""
    
    # 娴嬭瘯鍙傛暟
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/data/detection-overview/"
    
    # 鑾峰彇褰撳墠鏃堕棿鑼冨洿锛堟渶杩?澶╋級
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    # 鍙互娴嬭瘯涓嶅悓鐨勯儴浠?
    test_components = ['鐢垫簮鏉?, '杞瓙杞存壙', '杞瓙椹卞姩鐢垫満', '妗嗘灦鎺у埗鍣?, '杞瓙鐢垫祦閲囨牱']
    
    for component_name in test_components:
        print(f"\n{'='*60}")
        print(f"娴嬭瘯閮ㄤ欢: {component_name}")
        print(f"{'='*60}")
        
        params = {
            'action': 'component_details',
            'cmg_id': 'PHM001',  # 鏇挎崲涓哄疄闄呯殑PHM ID
            'component_name': component_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        test_single_component(base_url, endpoint, params)

def test_single_component(base_url, endpoint, params):
    """娴嬭瘯鍗曚釜閮ㄤ欢鐨勮鎯匒PI"""
    try:
        print(f"娴嬭瘯API: {base_url}{endpoint}")
        print(f"鍙傛暟: {params}")
        
        response = requests.get(f"{base_url}{endpoint}", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== API鍝嶅簲鎴愬姛 ===")
            print(f"閮ㄤ欢鍚嶇О: {data.get('component_name')}")
            print(f"PHM ID: {data.get('cmg_id')}")
            print(f"鎬昏褰曟暟: {data.get('total_records')}")
            print(f"娴嬬偣鏁伴噺: {data.get('total_testpoints')}")
            print(f"鏁呴殰鏁伴噺: {data.get('total_faults')}")
            
            # 妫€鏌ヤ腑蹇冮儴浠舵暟鎹?
            center_component = data.get('center_component', {})
            print(f"\n=== 涓績閮ㄤ欢鏁版嵁 ===")
            print(f"骞冲潎鍒嗘暟: {center_component.get('average_score')}")
            print(f"鍒嗘暟鑼冨洿: {center_component.get('min_score')} - {center_component.get('max_score')}")
            print(f"璁板綍鏁? {center_component.get('score_count')}")
            
            # 妫€鏌ユ祴鐐规暟鎹?
            testpoints = data.get('surrounding_testpoints', [])
            print(f"\n=== 娴嬬偣鏁版嵁 ({len(testpoints)}涓? ===")
            for i, tp in enumerate(testpoints[:3]):  # 鍙樉绀哄墠3涓?
                print(f"  {i+1}. {tp.get('name')}: 骞冲潎鍒嗘暟 {tp.get('average_score')}")
            
            # 妫€鏌ユ晠闅滄暟鎹?
            faults = data.get('surrounding_faults', [])
            print(f"\n=== 鏁呴殰鏁版嵁 ({len(faults)}涓? ===")
            for i, fault in enumerate(faults[:3]):  # 鍙樉绀哄墠3涓?
                print(f"  {i+1}. {fault.get('name')}: 骞冲潎鍒嗘暟 {fault.get('average_score')}")
            
            # 妫€鏌ュ師濮嬫暟鎹?
            raw_data = data.get('raw_data', {})
            print(f"\n=== 鍘熷鏁版嵁妫€鏌?===")
            print(f"娴嬬偣缁熻: {len(raw_data.get('testpoint_statistics', []))} 涓?)
            print(f"鏁呴殰缁熻: {len(raw_data.get('fault_statistics', []))} 涓?)
            print(f"閮ㄤ欢缁熻: {raw_data.get('component_statistics', {})}")
            
        else:
            print(f"\n=== API鍝嶅簲澶辫触 ===")
            print(f"鐘舵€佺爜: {response.status_code}")
            print(f"鍝嶅簲鍐呭: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("杩炴帴澶辫触锛氳纭繚Django鏈嶅姟鍣ㄦ鍦ㄨ繍琛?(python manage.py runserver)")
    except Exception as e:
        print(f"娴嬭瘯澶辫触: {e}")

if __name__ == "__main__":
    test_component_details_api()

