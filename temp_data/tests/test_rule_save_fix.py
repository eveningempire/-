#!/usr/bin/env python
"""
娴嬭瘯瑙勫垯淇濆瓨淇
"""

import os
import sys
import django
import json
import requests

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from rule_detection.models import RuleDefinition, FaultDefinition

def test_rule_save():
    """娴嬭瘯瑙勫垯淇濆瓨鍔熻兘"""
    print("=" * 60)
    print("娴嬭瘯瑙勫垯淇濆瓨淇")
    print("=" * 60)
    
    # 鑾峰彇涓€涓狢MG妯″瀷
    try:
        cmg_model = PHMModel.objects.first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌PHM妯″瀷锛岃鍏堝垱寤烘ā鍨?)
            return
        print(f"鉁?浣跨敤PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})")
    except Exception as e:
        print(f"鉂?鑾峰彇PHM妯″瀷澶辫触: {e}")
        return
    
    # 娴嬭瘯鏁版嵁
    test_rule_data = [
        {
            "showId": "TEST_RULE_001",
            "ruleExpress": "temperature > 80",
            "faultName": "娓╁害杩囬珮鏁呴殰",
            "faultLevel": 2,
            "component": "鏁ｇ儹绯荤粺",
            "source": "expert",
            "planDescript": "妫€鏌ユ暎鐑郴缁燂紝娓呯悊椋庢墖",
            "ruleOnline": True,
            "isNew": True,
            "editable": True
        },
        {
            "showId": "TEST_RULE_002", 
            "ruleExpress": "pressure < 50",
            "faultName": "鍘嬪姏杩囦綆鏁呴殰",
            "faultLevel": 3,
            "component": "娑插帇绯荤粺",
            "source": "data_driven",
            "planDescript": "妫€鏌ユ恫鍘嬬郴缁熷帇鍔?,
            "ruleOnline": True,
            "isNew": True,
            "editable": True
        }
    ]
    
    # 1. 娴嬭瘯淇濆瓨瑙勫垯
    print(f"\n1. 娴嬭瘯淇濆瓨瑙勫垯...")
    try:
        # 妯℃嫙鍓嶇淇濆瓨璇锋眰
        url = f"http://localhost:8000/api/v1/rules/editor/config-rule/"
        data = {
            'cmg_model_id': cmg_model.id,
            'tableData': json.dumps(test_rule_data)
        }
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        
        response = requests.post(url, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("鉁?瑙勫垯淇濆瓨鎴愬姛")
            else:
                print(f"鉂?瑙勫垯淇濆瓨澶辫触: {result}")
                return
        else:
            print(f"鉂?瑙勫垯淇濆瓨璇锋眰澶辫触: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"鉂?娴嬭瘯瑙勫垯淇濆瓨澶辫触: {e}")
        return
    
    # 2. 楠岃瘉瑙勫垯鏄惁宸蹭繚瀛樺埌鏁版嵁搴?
    print(f"\n2. 楠岃瘉鏁版嵁搴撲腑鐨勮鍒?..")
    try:
        saved_rules = RuleDefinition.objects.filter(cmg_model=cmg_model)
        print(f"   鏁版嵁搴撲腑鐨勮鍒欐暟閲? {saved_rules.count()}")
        
        for rule in saved_rules:
            print(f"   - 瑙勫垯ID: {rule.rule_id}")
            print(f"     鏁呴殰鍚嶇О: {rule.fault_definition.fault_name}")
            print(f"     瑙勫垯琛ㄨ揪寮? {rule.rule_expression}")
            print(f"     缁勪欢: {rule.fault_definition.component}")
            print(f"     鍦ㄧ嚎鐘舵€? {rule.is_online}")
            print()
            
    except Exception as e:
        print(f"鉂?楠岃瘉鏁版嵁搴撳け璐? {e}")
        return
    
    # 3. 娴嬭瘯鍔犺浇瑙勫垯
    print(f"\n3. 娴嬭瘯鍔犺浇瑙勫垯...")
    try:
        url = f"http://localhost:8000/api/v1/rules/editor/init-all-rule/"
        data = {'cmg_model_id': cmg_model.id}
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        
        response = requests.post(url, data=data, headers=headers)
        
        if response.status_code == 200:
            loaded_rules = response.json()
            print(f"   鍔犺浇鐨勮鍒欐暟閲? {len(loaded_rules)}")
            
            for rule in loaded_rules:
                print(f"   - 瑙勫垯ID: {rule.get('showId')}")
                print(f"     鏁呴殰鍚嶇О: {rule.get('faultName')}")
                print(f"     瑙勫垯琛ㄨ揪寮? {rule.get('ruleExpress')}")
                print()
                
            print("鉁?瑙勫垯鍔犺浇鎴愬姛")
        else:
            print(f"鉂?瑙勫垯鍔犺浇澶辫触: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"鉂?娴嬭瘯瑙勫垯鍔犺浇澶辫触: {e}")
        return
    
    # 4. 娓呯悊娴嬭瘯鏁版嵁
    print(f"\n4. 娓呯悊娴嬭瘯鏁版嵁...")
    try:
        # 鍒犻櫎娴嬭瘯瑙勫垯
        test_rule_ids = ["TEST_RULE_001", "TEST_RULE_002"]
        deleted_count = RuleDefinition.objects.filter(
            cmg_model=cmg_model,
            rule_id__in=test_rule_ids
        ).delete()[0]
        
        # 鍒犻櫎鐩稿叧鐨勬晠闅滃畾涔夛紙濡傛灉娌℃湁鍏朵粬瑙勫垯寮曠敤锛?
        for fault_name in ["娓╁害杩囬珮鏁呴殰", "鍘嬪姏杩囦綆鏁呴殰"]:
            fault = FaultDefinition.objects.filter(
                cmg_model=cmg_model,
                fault_name=fault_name
            ).first()
            if fault and not fault.rules.exists():
                fault.delete()
        
        print(f"鉁?娓呯悊瀹屾垚锛屽垹闄や簡 {deleted_count} 涓祴璇曡鍒?)
        
    except Exception as e:
        print(f"鉂?娓呯悊娴嬭瘯鏁版嵁澶辫触: {e}")
    
    print(f"\n" + "=" * 60)
    print("娴嬭瘯瀹屾垚锛?)
    print("=" * 60)
    print("\n淇璇存槑:")
    print("1. 淇敼浜嗗墠绔殑 saveRule() 鏂规硶锛屼娇鍏跺湪淇濆瓨瑙勫垯鍚庤嚜鍔ㄨ皟鐢?configRule()")
    print("2. 浼樺寲浜嗛敊璇鐞嗗拰鐢ㄦ埛鍙嶉")
    print("3. 鐜板湪鏂板缓鎴栫紪杈戣鍒欏悗浼氳嚜鍔ㄤ繚瀛樺埌鍚庣鏁版嵁搴?)
    print("4. 鐢ㄦ埛涓嶅啀闇€瑕佹墜鍔ㄧ偣鍑?閰嶇疆瑙勫垯'鎸夐挳")

if __name__ == "__main__":
    test_rule_save()

