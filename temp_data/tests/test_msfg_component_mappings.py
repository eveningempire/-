#!/usr/bin/env python
"""
娴嬭瘯MSFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰鍔熻兘
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition
from data_management.models import PHMModel

def test_msfg_component_mappings_page():
    """娴嬭瘯MSFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰"""
    client = Client()
    
    print("=== 娴嬭瘯MSFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰 ===")
    
    # 1. 娴嬭瘯椤甸潰璁块棶
    print("\n1. 娴嬭瘯椤甸潰璁块棶...")
    try:
        response = client.get('/api/v1/msfg/component-mappings-ui/', HTTP_HOST='localhost:8000')
        print(f"椤甸潰璁块棶鐘舵€佺爜: {response.status_code}")
        if response.status_code == 200:
            print("鉁?椤甸潰璁块棶鎴愬姛")
        else:
            print("鉂?椤甸潰璁块棶澶辫触")
            return False
    except Exception as e:
        print(f"鉂?椤甸潰璁块棶寮傚父: {e}")
        return False
    
    # 2. 娴嬭瘯API绔偣
    print("\n2. 娴嬭瘯API绔偣...")
    try:
        response = client.get('/api/v1/msfg/msfg-definitions/', HTTP_HOST='localhost:8000')
        print(f"API璁块棶鐘舵€佺爜: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"鉁?API璁块棶鎴愬姛锛屾壘鍒?{len(data)} 涓狹SFG瀹氫箟")
            
            # 鏌ユ壘娲昏穬鐨凪SFG
            active_msfg = None
            for msfg in data:
                if msfg.get('is_active'):
                    active_msfg = msfg
                    break
            
            if active_msfg:
                print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.get('name')} (ID: {active_msfg.get('id')})")
                print(f"   PHM妯″瀷: {active_msfg.get('cmg_model_name')}")
                print(f"   娴嬭瘯鐐规暟閲? {len(active_msfg.get('test_names', []))}")
                print(f"   閮ㄤ欢鏁伴噺: {len(active_msfg.get('component_names', []))}")
                
                if active_msfg.get('component_names'):
                    print(f"   閮ㄤ欢鍒楄〃: {', '.join(active_msfg.get('component_names'))}")
                else:
                    print("   鈿狅笍 娌℃湁鎵惧埌閮ㄤ欢淇℃伅")
            else:
                print("鈿狅笍 娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        else:
            print("鉂?API璁块棶澶辫触")
            return False
    except Exception as e:
        print(f"鉂?API璁块棶寮傚父: {e}")
        return False
    
    # 3. 妫€鏌ユ暟鎹簱涓殑MSFG瀹氫箟
    print("\n3. 妫€鏌ユ暟鎹簱涓殑MSFG瀹氫箟...")
    try:
        msfg_count = MSFGDefinition.objects.count()
        active_count = MSFGDefinition.objects.filter(is_active=True).count()
        print(f"鎬籑SFG瀹氫箟鏁伴噺: {msfg_count}")
        print(f"娲昏穬MSFG瀹氫箟鏁伴噺: {active_count}")
        
        if active_count > 0:
            active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
            print(f"娲昏穬MSFG: {active_msfg.name} (ID: {active_msfg.id})")
            print(f"PHM妯″瀷: {active_msfg.cmg_model.model_name}")
            print(f"娴嬭瘯鐐? {active_msfg.test_names}")
            print(f"閮ㄤ欢: {active_msfg.component_names}")
        else:
            print("鈿狅笍 鏁版嵁搴撲腑娌℃湁娲昏穬鐨凪SFG瀹氫箟")
    except Exception as e:
        print(f"鉂?鏁版嵁搴撴煡璇㈠紓甯? {e}")
        return False
    
    print("\n鉁?娴嬭瘯瀹屾垚")
    return True

if __name__ == '__main__':
    test_msfg_component_mappings_page()

