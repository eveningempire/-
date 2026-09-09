#!/usr/bin/env python
"""
璁剧疆娴嬭瘯鏁版嵁鑴氭湰
鍒涘缓PHM妯″瀷銆丆MG瀹炰緥鍜岀ず渚嬭鍒?
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from data_management.models import PHMType, Satellite, PHMModel, PHM
from rule_detection.models import FaultDefinition, RuleDefinition, ComponentDefinition

def setup_test_data():
    print("馃殌 寮€濮嬭缃祴璇曟暟鎹?..")
    
    # 1. 鍒涘缓PHM绫诲瀷
    cmg_type, created = PHMType.objects.get_or_create(
        name="SPIN",
        defaults={'description': '鏃嬭浆鎺у埗鍔涚煩闄€铻?}
    )
    if created:
        print("鉁?鍒涘缓PHM绫诲瀷: SPIN")
    
    # 2. 鍒涘缓鍗槦
    satellite, created = Satellite.objects.get_or_create(
        name="娴嬭瘯鍗槦-01"
    )
    if created:
        print("鉁?鍒涘缓鍗槦: 娴嬭瘯鍗槦-01")
    
    # 3. 鍒涘缓PHM妯″瀷
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name="PHM_Default",
        defaults={
            'description': '榛樿PHM妯″瀷锛岀敤浜庢祴璇曡鍒欐娴?,
            'cmg_type': cmg_type,
            'is_active': True,
            'is_default': True
        }
    )
    if created:
        print("鉁?鍒涘缓PHM妯″瀷: PHM_Default")
    
    # 4. 鍒涘缓PHM瀹炰緥
    cmg, created = PHM.objects.get_or_create(
        cmg_id="PHM_001",
        defaults={
            'name': 'PHM娴嬭瘯璁惧-001',
            'satellite': satellite,
            'cmg_model': cmg_model,
            'enabled': True
        }
    )
    if created:
        print("鉁?鍒涘缓PHM瀹炰緥: PHM_001")
    
    # 5. 鍒涘缓缁勪欢瀹氫箟
    components = [
        ('娓╁害浼犳劅鍣?, '鐩戞祴绯荤粺娓╁害'),
        ('鐢垫祦浼犳劅鍣?, '鐩戞祴绯荤粺鐢垫祦'),
        ('杞€熶紶鎰熷櫒', '鐩戞祴闄€铻鸿浆閫?),
        ('鎸姩浼犳劅鍣?, '鐩戞祴绯荤粺鎸姩'),
        ('娑︽粦绯荤粺', '娑︽粦娌圭郴缁?),
        ('缁煎悎绯荤粺', '绯荤粺缁煎悎鐩戞祴')
    ]
    
    for comp_name, desc in components:
        comp, created = ComponentDefinition.objects.get_or_create(
            cmg_model=cmg_model,
            component_name=comp_name,
            defaults={
                'description': desc,
                'parameters': []
            }
        )
        if created:
            print(f"鉁?鍒涘缓缁勪欢: {comp_name}")
    
    # 6. 鍒涘缓鏁呴殰瀹氫箟鍜岃鍒?
    fault_rules = [
        {
            'fault_name': '娓╁害杩囬珮鏁呴殰',
            'fault_level': 3,  # HIGH
            'component': '娓╁害浼犳劅鍣?,
            'description': '绯荤粺娓╁害瓒呰繃瀹夊叏闃堝€?,
            'rules': [
                {
                    'rule_id': 'TEMP_HIGH_001',
                    'expression': 'value_highT > 30.0',
                    'description': '楂樻俯浼犳劅鍣ㄨ鏁拌繃楂樻姤璀?,
                    'parameters': ['value_highT']
                },
                {
                    'rule_id': 'TEMP_HIGH_002', 
                    'expression': 'value_lowI > 3.0 and value_highT > 25.0',
                    'description': '娓╁害涓庣數娴佽仈鍚堝紓甯告娴?,
                    'parameters': ['value_lowI', 'value_highT']
                }
            ]
        },
        {
            'fault_name': '鐢垫祦寮傚父鏁呴殰',
            'fault_level': 2,  # MEDIUM
            'component': '鐢垫祦浼犳劅鍣?,
            'description': '绯荤粺鐢垫祦瓒呭嚭姝ｅ父鑼冨洿',
            'rules': [
                {
                    'rule_id': 'CURRENT_HIGH_001',
                    'expression': 'value_highI > 1.0',
                    'description': '楂樼數娴佷紶鎰熷櫒寮傚父',
                    'parameters': ['value_highI']
                },
                {
                    'rule_id': 'CURRENT_LOW_001',
                    'expression': 'value_lowI > 4.0',
                    'description': '浣庣數娴佷紶鎰熷櫒寮傚父',
                    'parameters': ['value_lowI']
                }
            ]
        },
        {
            'fault_name': '杞€熷紓甯告晠闅?, 
            'fault_level': 3,  # HIGH
            'component': '杞€熶紶鎰熷櫒',
            'description': '闄€铻鸿浆閫熷亸绂绘甯稿伐浣滆寖鍥?,
            'rules': [
                {
                    'rule_id': 'SPEED_LOW_001',
                    'expression': 'w < 5900.0',
                    'description': '杞€熻繃浣庢晠闅?,
                    'parameters': ['w']
                },
                {
                    'rule_id': 'SPEED_HIGH_001',
                    'expression': 'w > 6100.0', 
                    'description': '杞€熻繃楂樻晠闅?,
                    'parameters': ['w']
                }
            ]
        },
        {
            'fault_name': '鎸姩寮傚父鏁呴殰',
            'fault_level': 2,  # MEDIUM
            'component': '鎸姩浼犳劅鍣?,
            'description': '绯荤粺鎸姩瓒呭嚭姝ｅ父鑼冨洿',
            'rules': [
                {
                    'rule_id': 'VIBRATION_001',
                    'expression': 'u > 30.0',
                    'description': '鎸姩骞呭€煎紓甯?,
                    'parameters': ['u']
                }
            ]
        },
        {
            'fault_name': '娑︽粦绯荤粺鏁呴殰',
            'fault_level': 3,  # HIGH
            'component': '娑︽粦绯荤粺',
            'description': '娑︽粦娌圭矘搴﹀紓甯?,
            'rules': [
                {
                    'rule_id': 'VISCOSITY_001',
                    'expression': 'viscosity_estimated > 20.0',
                    'description': '娑︽粦娌圭矘搴﹁繃楂?,
                    'parameters': ['viscosity_estimated']
                },
                {
                    'rule_id': 'VISCOSITY_002',
                    'expression': 'viscosity_estimated < 10.0',
                    'description': '娑︽粦娌圭矘搴﹁繃浣?,
                    'parameters': ['viscosity_estimated']
                }
            ]
        },
        {
            'fault_name': '绯荤粺缁煎悎鏁呴殰',
            'fault_level': 4,  # CRITICAL
            'component': '缁煎悎绯荤粺',
            'description': '澶氫釜鍙傛暟鍚屾椂寮傚父',
            'rules': [
                {
                    'rule_id': 'SYSTEM_CRITICAL_001',
                    'expression': 'value_highT > 28.0 and w < 5950.0',
                    'description': '楂樻俯涓旇浆閫熷紓甯哥殑涓ラ噸鏁呴殰',
                    'parameters': ['value_highT', 'w']
                },
                {
                    'rule_id': 'SYSTEM_CRITICAL_002',
                    'expression': 'value_highI > 0.8 and value_lowI > 3.5 and u > 28.0',
                    'description': '鐢垫祦鍜屾尟鍔ㄥ悓鏃跺紓甯?,
                    'parameters': ['value_highI', 'value_lowI', 'u']
                }
            ]
        }
    ]
    
    # 娓呯悊鐜版湁瑙勫垯
    print("馃棏锔?娓呯悊鐜版湁瑙勫垯...")
    FaultDefinition.objects.filter(cmg_model=cmg_model).delete()
    
    # 鍒涘缓鏁呴殰鍜岃鍒?
    total_rules = 0
    for fault_config in fault_rules:
        # 鍒涘缓鏁呴殰瀹氫箟
        fault_def = FaultDefinition.objects.create(
            cmg_model=cmg_model,
            fault_name=fault_config['fault_name'],
            fault_level=fault_config['fault_level'],
            component=fault_config['component'],
            description=fault_config['description']
        )
        print(f"馃搵 鍒涘缓鏁呴殰瀹氫箟: {fault_config['fault_name']}")
        
        # 鍒涘缓瀵瑰簲鐨勮鍒?
        for rule_config in fault_config['rules']:
            rule_def = RuleDefinition.objects.create(
                cmg_model=cmg_model,
                fault_definition=fault_def,
                rule_id=rule_config['rule_id'],
                rule_expression=rule_config['expression'],
                source='expert',
                plan_description=rule_config['description'],
                is_online=True,
                is_new=True,
                is_editable=True,
                related_parameters=rule_config['parameters']
            )
            total_rules += 1
            print(f"  鉁?鍒涘缓瑙勫垯: {rule_config['rule_id']} - {rule_config['expression']}")
    
    print(f"\n馃帀 娴嬭瘯鏁版嵁璁剧疆瀹屾垚锛?)
    print(f"馃搳 鏁呴殰绫诲瀷鏁伴噺: {len(fault_rules)}")
    print(f"馃搹 瑙勫垯鎬绘暟: {total_rules}")
    print(f"馃幆 PHM妯″瀷: {cmg_model.model_name}")
    print(f"馃敡 PHM瀹炰緥: {cmg.cmg_id}")
    print(f"\n馃挕 鏀寔鐨勯仴娴嬪弬鏁板寘鎷細")
    all_params = set()
    for fault in fault_rules:
        for rule in fault['rules']:
            all_params.update(rule['parameters'])
    for param in sorted(all_params):
        print(f"   - {param}")
    
    print(f"\n馃敡 鎮ㄧ幇鍦ㄥ彲浠ワ細")
    print(f"   1. 浣跨敤TCP鎺ユ敹鍣ㄥ彂閫佸寘鍚繖浜涘弬鏁扮殑閬ユ祴鏁版嵁")
    print(f"   2. 鏌ョ湅瀹炴椂瑙勫垯妫€娴嬬粨鏋?)
    print(f"   3. 鍦ㄥ墠绔鍒欑紪杈戝櫒涓慨鏀硅鍒?)

if __name__ == '__main__':
    setup_test_data()

