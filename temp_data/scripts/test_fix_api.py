#!/usr/bin/env python
"""
娴嬭瘯淇API鏄惁姝ｅ父宸ヤ綔
"""

import os
import sys
import django
import requests
import json

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel

def test_fix_api():
    """娴嬭瘯淇API"""
    print("馃И 娴嬭瘯淇API")
    print("=" * 80)
    
    try:
        # 1. 鏌ユ壘鍙敤鐨凜MG妯″瀷
        cmg_models = PHMModel.objects.all()
        print(f"鎵惧埌 {cmg_models.count()} 涓狢MG妯″瀷:")
        for model in cmg_models:
            print(f"  - {model.model_name} (ID: {model.id})")
        
        if not cmg_models.exists():
            print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
            return False
        
        # 2. 閫夋嫨绗竴涓ā鍨嬭繘琛屾祴璇?
        test_model = cmg_models.first()
        print(f"\n馃敡 娴嬭瘯妯″瀷: {test_model.model_name} (ID: {test_model.id})")
        
        # 3. 璋冪敤淇API
        api_url = "http://localhost:8000/api/v1/msfg/fix-components/"
        payload = {
            "cmg_model_id": test_model.id
        }
        
        print(f"馃摗 璋冪敤API: {api_url}")
        print(f"馃摝 璇锋眰鏁版嵁: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        print(f"馃搳 鍝嶅簲鐘舵€佺爜: {response.status_code}")
        print(f"馃搫 鍝嶅簲鍐呭:")
        
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if result.get('success'):
                details = result.get('details', {})
                print(f"\n鉁?API娴嬭瘯鎴愬姛锛?)
                print(f"   妯″瀷: {details.get('model_name')}")
                print(f"   MSFG: {details.get('msfg_name')}")
                print(f"   閮ㄤ欢鏁伴噺: {details.get('components_count')}")
                print(f"   绯荤粺鑺傜偣: {details.get('system_nodes_created')}")
                print(f"   鏄犲皠鏁伴噺: {details.get('mappings_count')}")
                return True
            else:
                print(f"鉂?API杩斿洖澶辫触: {result.get('error')}")
                return False
        else:
            print(f"鉂?API璋冪敤澶辫触: {response.status_code}")
            print(f"閿欒淇℃伅: {response.text}")
            return False
            
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓诲嚱鏁?""
    success = test_fix_api()
    
    if success:
        print(f"\n馃帀 API娴嬭瘯閫氳繃锛?)
        print("淇鍔熻兘鍙互姝ｅ父浣跨敤銆?)
    else:
        print(f"\n鉂?API娴嬭瘯澶辫触锛?)
        print("璇锋鏌?")
        print("1. Django鏈嶅姟鍣ㄦ槸鍚﹁繍琛屽湪8000绔彛")
        print("2. 澶氫俊鍙锋祦鍥鹃厤缃?json鏂囦欢鏄惁瀛樺湪")
        print("3. 鏁版嵁搴撹繛鎺ユ槸鍚︽甯?)

if __name__ == "__main__":
    main()

