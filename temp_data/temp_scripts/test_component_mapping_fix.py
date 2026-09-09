#!/usr/bin/env python3
"""
娴嬭瘯閮ㄤ欢鏄犲皠淇鏁堟灉
楠岃瘉鏄惁鍙樉绀烘槑纭槧灏勭殑娴嬬偣鍜屾晠闅?
"""

import requests
import json
from datetime import datetime, timedelta

# API鍩虹URL
BASE_URL = "http://localhost:8000/api/v1/data/detection-overview/"

def test_component_mapping():
    """娴嬭瘯閮ㄤ欢鏄犲皠鏄惁姝ｇ‘"""
    
    # 娴嬭瘯鍙傛暟
    test_params = {
        "action": "component_details",
        "cmg_id": "1",  # 鍋囪PHM ID涓?
        "component_name": "鏃嬪彉SPI",  # 娴嬭瘯杩欎釜閮ㄤ欢
        "start_time": "2024-03-30T18:27:01.000Z",
        "end_time": "2024-03-30T18:28:43.007Z"
    }
    
    print("=== 娴嬭瘯閮ㄤ欢鏄犲皠淇鏁堟灉 ===")
    print(f"娴嬭瘯閮ㄤ欢: {test_params['component_name']}")
    print(f"鏃堕棿鑼冨洿: {test_params['start_time']} ~ {test_params['end_time']}")
    print()
    
    try:
        # 鍙戦€佽姹?
        response = requests.get(BASE_URL, params=test_params)
        
        if response.status_code == 200:
            data = response.json()
            
            print("鉁?API璋冪敤鎴愬姛")
            print(f"閮ㄤ欢鍚嶇О: {data.get('component_name', 'N/A')}")
            print(f"PHM ID: {data.get('cmg_id', 'N/A')}")
            print(f"鎬昏褰曟暟: {data.get('total_records', 0)}")
            print()
            
            # 妫€鏌ヤ腑蹇冮儴浠?
            center_component = data.get('center_component', {})
            print("=== 涓績閮ㄤ欢淇℃伅 ===")
            print(f"鍚嶇О: {center_component.get('name', 'N/A')}")
            print(f"骞冲潎鍒嗘暟: {center_component.get('average_score', 0.0)}")
            print(f"鏁呴殰鏁? {center_component.get('average_fault_count', 0.0)}")
            print()
            
            # 妫€鏌ユ祴鐐?
            testpoints = data.get('surrounding_testpoints', [])
            print(f"=== 娴嬬偣淇℃伅 (鍏?{len(testpoints)} 涓? ===")
            for i, tp in enumerate(testpoints[:5]):  # 鍙樉绀哄墠5涓?
                print(f"{i+1}. {tp.get('name', 'N/A')}: {tp.get('average_score', 0.0)}")
            if len(testpoints) > 5:
                print(f"... 杩樻湁 {len(testpoints) - 5} 涓祴鐐?)
            print()
            
            # 妫€鏌ユ晠闅?
            faults = data.get('surrounding_faults', [])
            print(f"=== 鏁呴殰淇℃伅 (鍏?{len(faults)} 涓? ===")
            for i, fault in enumerate(faults[:5]):  # 鍙樉绀哄墠5涓?
                print(f"{i+1}. {fault.get('name', 'N/A')}: {fault.get('average_score', 0.0)}")
            if len(faults) > 5:
                print(f"... 杩樻湁 {len(faults) - 5} 涓晠闅?)
            print()
            
            # 妫€鏌ユ槸鍚︽湁鏄犲皠淇℃伅
            raw_data = data.get('raw_data', {})
            testpoint_mappings = raw_data.get('testpoint_mappings', [])
            fault_mappings = raw_data.get('fault_mappings', [])
            
            print("=== 鏄犲皠鍏崇郴淇℃伅 ===")
            print(f"娴嬬偣鏄犲皠鏁伴噺: {len(testpoint_mappings)}")
            print(f"鏁呴殰鏄犲皠鏁伴噺: {len(fault_mappings)}")
            
            if testpoint_mappings:
                print("娴嬬偣鏄犲皠璇︽儏:")
                for mapping in testpoint_mappings[:3]:  # 鍙樉绀哄墠3涓?
                    print(f"  - {mapping.get('test_point_name', 'N/A')} -> {mapping.get('component_name', 'N/A')} (鏉冮噸: {mapping.get('weight', 0.0)})")
                if len(testpoint_mappings) > 3:
                    print(f"  ... 杩樻湁 {len(testpoint_mappings) - 3} 涓祴鐐规槧灏?)
            
            if fault_mappings:
                print("鏁呴殰鏄犲皠璇︽儏:")
                for mapping in fault_mappings[:3]:  # 鍙樉绀哄墠3涓?
                    print(f"  - {mapping.get('fault_name', 'N/A')} -> {mapping.get('component_name', 'N/A')} (鏉冮噸: {mapping.get('weight', 0.0)})")
                if len(fault_mappings) > 3:
                    print(f"  ... 杩樻湁 {len(fault_mappings) - 3} 涓晠闅滄槧灏?)
            
            print()
            print("=== 淇鏁堟灉楠岃瘉 ===")
            
            # 楠岃瘉鏄惁鍙樉绀烘槑纭槧灏勭殑鑺傜偣
            if len(testpoints) == len(testpoint_mappings):
                print("鉁?娴嬬偣鏁伴噺涓庢槧灏勬暟閲忎竴鑷达紝娌℃湁澶氫綑鐨勬祴鐐?)
            else:
                print(f"鈿狅笍  娴嬬偣鏁伴噺 ({len(testpoints)}) 涓庢槧灏勬暟閲?({len(testpoint_mappings)}) 涓嶄竴鑷?)
            
            if len(faults) == len(fault_mappings):
                print("鉁?鏁呴殰鏁伴噺涓庢槧灏勬暟閲忎竴鑷达紝娌℃湁澶氫綑鐨勬晠闅?)
            else:
                print(f"鈿狅笍  鏁呴殰鏁伴噺 ({len(faults)}) 涓庢槧灏勬暟閲?({len(fault_mappings)}) 涓嶄竴鑷?)
            
            # 妫€鏌ユ槸鍚︽湁娑堟伅鎻愮ず
            message = data.get('message', '')
            if message:
                print(f"鈩癸笍  娑堟伅: {message}")
            
        else:
            print(f"鉂?API璋冪敤澶辫触: {response.status_code}")
            print(f"閿欒淇℃伅: {response.text}")
            
    except Exception as e:
        print(f"鉂?娴嬭瘯澶辫触: {e}")

def test_multiple_components():
    """娴嬭瘯澶氫釜閮ㄤ欢鐨勬槧灏勬儏鍐?""
    
    test_components = [
        "鏃嬪彉SPI",
        "鐢垫簮鏉?, 
        "杞瓙椹卞姩鐢垫満",
        "杞瓙杞存壙"
    ]
    
    print("\n=== 娴嬭瘯澶氫釜閮ㄤ欢鐨勬槧灏勬儏鍐?===")
    
    for component in test_components:
        print(f"\n--- 娴嬭瘯閮ㄤ欢: {component} ---")
        
        test_params = {
            "action": "component_details",
            "cmg_id": "1",
            "component_name": component,
            "start_time": "2024-03-30T18:27:01.000Z",
            "end_time": "2024-03-30T18:28:43.007Z"
        }
        
        try:
            response = requests.get(BASE_URL, params=test_params)
            
            if response.status_code == 200:
                data = response.json()
                testpoints = data.get('surrounding_testpoints', [])
                faults = data.get('surrounding_faults', [])
                message = data.get('message', '')
                
                print(f"娴嬬偣鏁? {len(testpoints)}, 鏁呴殰鏁? {len(faults)}")
                if message:
                    print(f"娑堟伅: {message}")
            else:
                print(f"API璋冪敤澶辫触: {response.status_code}")
                
        except Exception as e:
            print(f"娴嬭瘯澶辫触: {e}")

if __name__ == "__main__":
    test_component_mapping()
    test_multiple_components()

