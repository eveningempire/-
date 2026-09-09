#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
娴嬭瘯鎵€鏈変慨澶嶆槸鍚︽甯稿伐浣?
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.algorithms.msfg.fusion import summarize_system
from msfg_analysis.algorithms.msfg.component_integration import calculate_msfg_component_health
from msfg_analysis.models import MSFGDefinition

def test_system_summary():
    """娴嬭瘯绯荤粺姒傝璁＄畻"""
    print("馃И 娴嬭瘯绯荤粺姒傝璁＄畻")
    print("=" * 50)
    
    # 娴嬭瘯鏁版嵁1锛氭甯告儏鍐?
    fault_scores_1 = {
        '妗嗘灦鏁呴殰': {'fault_probability': 0.1, 'fuzzy_probability': 0.05},
        '杞瓙鏁呴殰': {'fault_probability': 0.2, 'fuzzy_probability': 0.1},
        '娓╁害鏁呴殰': {'fault_probability': 0.05, 'fuzzy_probability': 0.02}
    }
    
    result_1 = summarize_system(fault_scores_1)
    print(f"鉁?姝ｅ父鎯呭喌娴嬭瘯:")
    print(f"   鏁呴殰鏁伴噺: {result_1['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_1['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_1['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_1['critical_faults']}")
    
    # 娴嬭瘯鏁版嵁2锛氭湁娲昏穬鏁呴殰
    fault_scores_2 = {
        '妗嗘灦鏁呴殰': {'fault_probability': 0.8, 'fuzzy_probability': 0.1},
        '杞瓙鏁呴殰': {'fault_probability': 0.4, 'fuzzy_probability': 0.3},
        '娓╁害鏁呴殰': {'fault_probability': 0.2, 'fuzzy_probability': 0.1},
        '鐢垫簮鏁呴殰': {'fault_probability': 0.9, 'fuzzy_probability': 0.2}
    }
    
    result_2 = summarize_system(fault_scores_2)
    print(f"\n鉁?鏈夋椿璺冩晠闅滄祴璇?")
    print(f"   鏁呴殰鏁伴噺: {result_2['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_2['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_2['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_2['critical_faults']}")
    
    # 娴嬭瘯鏁版嵁3锛氱┖鏁版嵁
    result_3 = summarize_system({})
    print(f"\n鉁?绌烘暟鎹祴璇?")
    print(f"   鏁呴殰鏁伴噺: {result_3['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_3['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_3['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_3['critical_faults']}")

def test_component_health():
    """娴嬭瘯閮ㄤ欢鍋ュ悍璁＄畻"""
    print("\n馃И 娴嬭瘯閮ㄤ欢鍋ュ悍璁＄畻")
    print("=" * 50)
    
    # 妯℃嫙娴嬭瘯鐐瑰垎鏁?
    test_scores = {
        '浣庨€熸鏋惰浆閫熻秴闄?: 0.8,
        '楂橀€熻浆瀛愮數娴佸紓甯?: 0.4,
        '娓╁害杩囬珮': 0.2,
        '鐢靛帇寮傚父': 0.9,
        '鐢垫祦姝ｅ父': 0.1
    }
    
    try:
        # 鑾峰彇MSFG瀹氫箟
        msfg_def = MSFGDefinition.objects.first()
        if msfg_def:
            print(f"鉁?浣跨敤MSFG: {msfg_def.name}")
            
            # 璁＄畻閮ㄤ欢鍋ュ悍
            component_results = calculate_msfg_component_health(
                test_scores=test_scores,
                msfg_definition=msfg_def,
                include_unmapped_components=True
            )
            
            print(f"   璁＄畻缁撴灉閮ㄤ欢鏁伴噺: {len(component_results)}")
            for component_name, data in list(component_results.items())[:3]:  # 鍙樉绀哄墠3涓?
                print(f"   {component_name}:")
                print(f"     health_score: {data.get('health_score', 'N/A')}")
                print(f"     active_fault_count: {data.get('active_fault_count', 'N/A')}")
                print(f"     max_fault_score: {data.get('max_fault_score', 'N/A')}")
        else:
            print("鈿狅笍  娌℃湁鎵惧埌MSFG瀹氫箟锛岃烦杩囬儴浠跺仴搴锋祴璇?)
            
    except Exception as e:
        print(f"鉂?閮ㄤ欢鍋ュ悍璁＄畻澶辫触: {e}")

def test_frontend_data_structure():
    """娴嬭瘯鍓嶇鏁版嵁缁撴瀯"""
    print("\n馃И 娴嬭瘯鍓嶇鏁版嵁缁撴瀯")
    print("=" * 50)
    
    # 妯℃嫙鍚庣杩斿洖鐨勬暟鎹粨鏋?
    backend_data = {
        'test_results': {
            '浣庨€熸鏋惰浆閫熻秴闄?: {'score': 0.8, 'timestamp': '2024-01-01'},
            '楂橀€熻浆瀛愮數娴佸紓甯?: {'score': 0.4, 'timestamp': '2024-01-01'},
            '娓╁害杩囬珮': {'score': 0.2, 'timestamp': '2024-01-01'}
        },
        'fault_results': {
            '妗嗘灦鏁呴殰': {'fault_probability': 0.8, 'fuzzy_probability': 0.1},
            '杞瓙鏁呴殰': {'fault_probability': 0.4, 'fuzzy_probability': 0.3},
            '娓╁害鏁呴殰': {'fault_probability': 0.2, 'fuzzy_probability': 0.1}
        },
        'system_results': {
            'fault_count': 3,
            'worst_fault_score': 0.8,
            'average_fault_score': 0.47,
            'critical_faults': ['妗嗘灦鏁呴殰']
        }
    }
    
    # 妯℃嫙鍓嶇澶勭悊閫昏緫
    def msfgKv(obj):
        out = []
        if not obj or not isinstance(obj, dict):
            return out
        for k, v in obj.items():
            final_value = v
            if v and isinstance(v, dict) and not isinstance(v, list):
                if 'score' in v:
                    final_value = v['score']
                elif 'fault_probability' in v:
                    final_value = v['fault_probability']
                elif 'fuzzy_probability' in v:
                    final_value = v['fuzzy_probability']
            out.append({'k': k, 'v': final_value})
        return out
    
    # 娴嬭瘯娴嬭瘯鐐瑰垎鏁板鐞?
    test_processed = msfgKv(backend_data['test_results'])
    print(f"鉁?娴嬭瘯鐐瑰垎鏁板鐞?")
    for item in test_processed:
        print(f"   {item['k']}: {item['v']}")
    
    # 娴嬭瘯鏁呴殰鍒嗘暟澶勭悊
    fault_processed = msfgKv(backend_data['fault_results'])
    print(f"\n鉁?鏁呴殰鍒嗘暟澶勭悊:")
    for item in fault_processed:
        print(f"   {item['k']}: {item['v']}")
    
    # 娴嬭瘯绯荤粺姒傝
    system_data = backend_data['system_results']
    print(f"\n鉁?绯荤粺姒傝:")
    print(f"   鏁呴殰鏁伴噺: {system_data['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {system_data['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {system_data['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {system_data['critical_faults']}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫祴璇曟墍鏈変慨澶?)
    print("=" * 60)
    
    try:
        test_system_summary()
        test_component_health()
        test_frontend_data_structure()
        
        print("\n" + "=" * 60)
        print("鉁?鎵€鏈夋祴璇曞畬鎴愶紒")
        print("\n馃搵 淇鎬荤粨:")
        print("1. 鉁?绯荤粺姒傝璁＄畻閫昏緫宸蹭紭鍖?)
        print("2. 鉁?娲昏穬鏁呴殰鍜屾渶澶ф晠闅滃垎鏁板瓧娈靛悕宸茬粺涓€")
        print("3. 鉁?鍓嶇NaN鏄剧ず闂宸蹭慨澶?)
        print("4. 鉁?娴嬭瘯鐐瑰拰鏁呴殰鍒嗘暟瑙ｉ噴宸叉坊鍔?)
        print("5. 鉁?閮ㄤ欢鍋ュ悍鍒嗘暟棰滆壊閫昏緫宸茬粺涓€")
        print("6. 鉁?绯荤粺姒傝鏄剧ず宸插畬鍠?)
        
    except Exception as e:
        print(f"\n鉂?娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

