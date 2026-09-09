#!/usr/bin/env python
"""
娴嬭瘯MSFG鐩稿叧鐨凙PI绔偣
"""
import os
import sys
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.test import Client
from msfg_analysis.models import MSFGDefinition, PHMModel

def test_api_endpoints():
    print("馃攳 娴嬭瘯MSFG鐩稿叧鐨凙PI绔偣")
    print("=" * 60)
    
    try:
        # 鑾峰彇鏈€鏂扮殑MSFG瀹氫箟
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌婵€娲荤殑PHM妯″瀷")
            return
            
        msfg_definition = MSFGDefinition.objects.filter(cmg_model=cmg_model).order_by('-created_at').first()
        if not msfg_definition:
            print("鉂?娌℃湁鎵惧埌MSFG瀹氫箟")
            return
            
        print(f"馃搵 妫€鏌MG妯″瀷: {cmg_model}")
        print(f"  鉁?MSFG: {msfg_definition}")
        print(f"  馃搳 MSFG ID: {msfg_definition.id}")
        
        # 鍒涘缓Django娴嬭瘯瀹㈡埛绔?
        client = Client()
        
        # 1. 娴嬭瘯MSFG瀹氫箟璇︽儏API
        print(f"\n馃攳 1. 娴嬭瘯MSFG瀹氫箟璇︽儏API")
        print("=" * 40)
        
        url = f"/api/v1/msfg/msfg-definitions/{msfg_definition.id}/"
        print(f"URL: {url}")
        
        try:
            response = client.get(url)
            print(f"鐘舵€佺爜: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"鉁?鎴愬姛鑾峰彇MSFG瀹氫箟")
                print(f"  - name: {data.get('name')}")
                print(f"  - test_names: {len(data.get('test_names', []))} 涓?)
                print(f"  - component_names: {len(data.get('component_names', []))} 涓?)
                print(f"  - fault_names: {len(data.get('fault_names', []))} 涓?)
                
                if data.get('component_names'):
                    print(f"  - 閮ㄤ欢鍒楄〃: {data['component_names']}")
            else:
                print(f"鉂?璇锋眰澶辫触: {response.content.decode()}")
        except Exception as e:
            print(f"鉂?璇锋眰寮傚父: {e}")
        
        # 2. 娴嬭瘯閮ㄤ欢鎻愬彇API
        print(f"\n馃攳 2. 娴嬭瘯閮ㄤ欢鎻愬彇API")
        print("=" * 40)
        
        url = f"/api/v1/msfg/msfg-definitions/{msfg_definition.id}/components/"
        print(f"URL: {url}")
        
        try:
            response = client.get(url)
            print(f"鐘舵€佺爜: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"鉁?鎴愬姛鑾峰彇閮ㄤ欢鍒楄〃")
                print(f"  - components: {len(data.get('components', []))} 涓?)
                if data.get('components'):
                    print(f"  - 閮ㄤ欢鍒楄〃: {data['components']}")
            else:
                print(f"鉂?璇锋眰澶辫触: {response.content.decode()}")
        except Exception as e:
            print(f"鉂?璇锋眰寮傚父: {e}")
        
        # 3. 娴嬭瘯鏄犲皠API
        print(f"\n馃攳 3. 娴嬭瘯鏄犲皠API")
        print("=" * 40)
        
        url = f"/api/v1/msfg/component-mappings/?msfg_definition_id={msfg_definition.id}"
        print(f"URL: {url}")
        
        try:
            response = client.get(url)
            print(f"鐘舵€佺爜: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"鉁?鎴愬姛鑾峰彇鏄犲皠鍒楄〃")
                print(f"  - mappings: {len(data) if isinstance(data, list) else 0} 涓?)
                if isinstance(data, list) and data:
                    print(f"  - 鏄犲皠绀轰緥: {data[0]}")
            else:
                print(f"鉂?璇锋眰澶辫触: {response.content.decode()}")
        except Exception as e:
            print(f"鉂?璇锋眰寮傚父: {e}")
        
        # 4. 娴嬭瘯graph-inspect API
        print(f"\n馃攳 4. 娴嬭瘯graph-inspect API")
        print("=" * 40)
        
        url = f"/api/v1/msfg/msfg-definitions/{msfg_definition.id}/graph-inspect/"
        print(f"URL: {url}")
        
        try:
            response = client.get(url)
            print(f"鐘舵€佺爜: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"鉁?鎴愬姛鑾峰彇graph-inspect")
                print(f"  - tests: {len(data.get('tests', []))} 涓?)
                print(f"  - faults: {len(data.get('faults', []))} 涓?)
                print(f"  - components: {len(data.get('components', []))} 涓?)
            else:
                print(f"鉂?璇锋眰澶辫触: {response.content.decode()}")
        except Exception as e:
            print(f"鉂?璇锋眰寮傚父: {e}")
        
        print("\n" + "=" * 60)
        print("鉁?API娴嬭瘯瀹屾垚")
        
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇旳PI绔偣...")
    test_api_endpoints()

