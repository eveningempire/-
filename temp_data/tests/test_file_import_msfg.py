#!/usr/bin/env python
"""
娴嬭瘯鏂囦欢瀵煎叆鏃剁殑MSFG妫€娴?
楠岃瘉鏄惁浣跨敤鏂扮殑鍏堣繘MSFG铻嶅悎绠楁硶
"""

import os
import sys
import django
import numpy as np
from django.test import Client

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMData, PHMModel
from data_management.batch_processing import BatchFileProcessor
from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge

def test_file_import_msfg():
    """娴嬭瘯鏂囦欢瀵煎叆鏃剁殑MSFG妫€娴?""
    print("=== 娴嬭瘯鏂囦欢瀵煎叆鏃剁殑MSFG妫€娴?===")
    
    # 1. 鑾峰彇娴嬭瘯鐢ㄧ殑PHM鍜孧SFG
    print("\n1. 鑾峰彇娴嬭瘯鏁版嵁...")
    
    # 鑾峰彇绗竴涓狢MG妯″瀷
    cmg_model = PHMModel.objects.first()
    if not cmg_model:
        print("鉂?娌℃湁鎵惧埌PHM妯″瀷")
        return False
    
    print(f"鉁?浣跨敤PHM妯″瀷: {cmg_model.model_name}")
    
    # 鑾峰彇璇ユā鍨嬬殑绗竴涓狢MG
    cmg = PHM.objects.filter(cmg_model=cmg_model).first()
    if not cmg:
        print("鉂?娌℃湁鎵惧埌PHM")
        return False
    
    print(f"鉁?浣跨敤PHM: {cmg.cmg_id}")
    
    # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?浣跨敤MSFG: {msfg.name}")
    
    # 2. 鍒涘缓娴嬭瘯鏁版嵁鐐?
    print("\n2. 鍒涘缓娴嬭瘯鏁版嵁鐐?..")
    
    # 鍒涘缓妯℃嫙鐨勯仴娴嬫暟鎹?
    test_data = {
        '浣庨€熷３娓?: 45.2,
        '浣庨€熶綅缃?: 123.4,
        '楂橀€熻浆閫熸帶鍒剁ǔ瀹氬害': 0.85,
        '浣庨€烠鐩哥數娴?: 2.1,
        '楂橀€熸粦鍔ㄧ杞存俯': 52.3,
        '楂橀€熷浐绱х杞存俯娓╁害': 48.7,
        '100V閬ユ祴': 12.1,
        '+45V閬ユ祴': 45.2,
        '妗嗘灦鐢垫祦': 1.8,
        '+5V閬ユ祴': 5.1,
        '楂橀€熻浆閫熸帶鍒剁簿搴?: 0.92,
        '楂橀€熻浆閫?: 3000.0,
        '浣庨€熻浆閫?: 1500.0,
        '婊戝姩绔酱娓╅仴娴?: 51.2,
        '瀹氳閿佸畾绮惧害': 0.88,
        '浣庨€烝鐩哥數娴?: 1.9,
        '+12V閬ユ祴': 12.2,
        '楂橀€熸粦鍔ㄧ杞存俯娓╁害': 53.1,
        '楂橀€熷浐绱х杞存俯': 49.2,
        '100V寮€鍏充俊鍙?: 1.0,
        '楂橀€熺數鏈虹數鍘?: 24.5,
        '鍥虹揣绔酱娓╅仴娴?: 47.8,
        '楂橀€熺數鏈虹數娴?: 3.2
    }
    
    # 鍒涘缓PHM鏁版嵁璁板綍
    data_point = PHMData.objects.create(
        cmg=cmg,
        timestamp=timezone.now(),
        data=test_data
    )
    
    print(f"鉁?鍒涘缓鏁版嵁鐐? ID {data_point.id}")
    print(f"   鏁版嵁瀛楁鏁? {len(test_data)}")
    
    # 3. 娴嬭瘯MSFG妫€娴?
    print("\n3. 娴嬭瘯MSFG妫€娴?..")
    
    processor = BatchFileProcessor()
    
    try:
        # 杩愯MSFG妫€娴?
        msfg_result = processor._run_msfg_detection(data_point, cmg)
        
        if msfg_result is None:
            print("鉂?MSFG妫€娴嬭繑鍥濶one")
            return False
        
        print("鉁?MSFG妫€娴嬫垚鍔?)
        
        # 4. 楠岃瘉妫€娴嬬粨鏋?
        print("\n4. 楠岃瘉妫€娴嬬粨鏋?..")
        
        # 楠岃瘉娴嬭瘯缁撴灉
        test_results = msfg_result['test_results']
        print(f"   娴嬭瘯缁撴灉鏁伴噺: {len(test_results)}")
        for test_name, result in test_results.items():
            print(f"     {test_name}: 铻嶅悎鍒嗘暟={result['score']:.3f}")
        
        # 楠岃瘉鏁呴殰缁撴灉
        fault_results = msfg_result['fault_results']
        print(f"   鏁呴殰缁撴灉鏁伴噺: {len(fault_results)}")
        for fault_name, result in fault_results.items():
            print(f"     {fault_name}: 鏁呴殰姒傜巼={result['fault_probability']:.3f}, 妯＄硦姒傜巼={result['fuzzy_probability']:.3f}")
        
        # 楠岃瘉閮ㄤ欢缁撴灉
        component_results = msfg_result['component_results']
        print(f"   閮ㄤ欢缁撴灉鏁伴噺: {len(component_results)}")
        for component_name, result in component_results.items():
            print(f"     {component_name}:")
            print(f"       鍋ュ悍鍒嗘暟: {result['health_score']:.3f}")
            print(f"       鏁呴殰姒傜巼: {result['fault_probability']:.3f}")
            print(f"       妯＄硦姒傜巼: {result['fuzzy_probability']:.3f}")
            print(f"       鏁呴殰鏁伴噺: {result['fault_count']}")
            print(f"       鏈€澶ф晠闅滄鐜? {result['max_fault_prob']:.3f}")
            print(f"       骞冲潎鏁呴殰姒傜巼: {result['avg_fault_prob']:.3f}")
        
        # 楠岃瘉绯荤粺缁撴灉
        system_results = msfg_result['system_results']
        print(f"   绯荤粺鏁翠綋鍋ュ悍搴? {system_results['overall_health']:.3f}")
        print(f"   閮ㄤ欢鏁伴噺: {system_results['component_count']}")
        print(f"   鍏抽敭閮ㄤ欢: {system_results['critical_components']}")
        print(f"   鏈€宸儴浠? {system_results['worst_component']}")
        print(f"   鍋ュ悍搴﹀垎甯? {system_results['health_distribution']}")
        print(f"   鏈€灏忓仴搴峰害: {system_results['min_health']:.3f}")
        print(f"   鏈€澶у仴搴峰害: {system_results['max_health']:.3f}")
        print(f"   骞冲潎鍋ュ悍搴? {system_results['avg_health']:.3f}")
        
        # 楠岃瘉鍒嗘瀽璇︽儏
        analysis_details = msfg_result['analysis_details']
        print(f"   鏁版嵁婧? {analysis_details['source']}")
        print(f"   娴嬭瘯鑺傜偣鏁? {analysis_details['total_test_nodes']}")
        print(f"   鏁呴殰鑺傜偣鏁? {analysis_details['total_fault_nodes']}")
        print(f"   杈规暟: {analysis_details['total_edges']}")
        
        # 楠岃瘉绠楁硶鐗堟湰
        metadata = analysis_details['analysis_metadata']
        print(f"   绠楁硶鐗堟湰: {metadata['algorithm_version']}")
        print(f"   D鐭╅樀褰㈢姸: {metadata['d_matrix_shape']}")
        
        # 5. 楠岃瘉鏄惁浣跨敤浜嗘柊鐨勫厛杩涚畻娉?
        print("\n5. 楠岃瘉绠楁硶浣跨敤鎯呭喌...")
        
        if analysis_details['source'] == 'batch_processing_advanced_fusion':
            print("   鉁?浣跨敤浜嗘柊鐨勫厛杩汳SFG铻嶅悎绠楁硶")
        else:
            print("   鉂?娌℃湁浣跨敤鏂扮殑鍏堣繘绠楁硶")
            return False
        
        if metadata['algorithm_version'] == 'advanced_fusion_v1.0':
            print("   鉁?绠楁硶鐗堟湰姝ｇ‘")
        else:
            print("   鉂?绠楁硶鐗堟湰涓嶆纭?)
            return False
        
        # 6. 楠岃瘉璁＄畻閫昏緫鐨勫悎鐞嗘€?
        print("\n6. 楠岃瘉璁＄畻閫昏緫鐨勫悎鐞嗘€?..")
        
        # 楠岃瘉鍋ュ悍鍒嗘暟鑼冨洿
        all_health_scores = [result['health_score'] for result in component_results.values()]
        if all(0 <= score <= 1 for score in all_health_scores):
            print("   鉁?鍋ュ悍鍒嗘暟閮藉湪鍚堢悊鑼冨洿鍐?[0, 1]")
        else:
            print("   鉂?鍋ュ悍鍒嗘暟瓒呭嚭鍚堢悊鑼冨洿")
            return False
        
        # 楠岃瘉鏁呴殰姒傜巼涓庡仴搴峰垎鏁扮殑鍏崇郴
        for component_name, result in component_results.items():
            expected_health = 1.0 - result['fault_probability']
            if abs(result['health_score'] - expected_health) < 0.001:
                print(f"   鉁?{component_name} 鍋ュ悍鍒嗘暟璁＄畻姝ｇ‘")
            else:
                print(f"   鉂?{component_name} 鍋ュ悍鍒嗘暟璁＄畻閿欒")
                return False
        
        # 楠岃瘉绯荤粺鍋ュ悍搴︾殑鍚堢悊鎬?
        if system_results['component_count'] > 0:
            avg_health = system_results['avg_health']
            if abs(system_results['overall_health'] - avg_health) < 0.1:  # 鍏佽涓€瀹氳宸?
                print("   鉁?绯荤粺鍋ュ悍搴﹁绠楀悎鐞?)
            else:
                print("   鈿狅笍 绯荤粺鍋ュ悍搴﹀彲鑳介渶瑕佽皟鏁存潈閲?)
        
        print("\n鉁?鏂囦欢瀵煎叆MSFG妫€娴嬫祴璇曞畬鎴?)
        return True
        
    except Exception as e:
        print(f"鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 娓呯悊娴嬭瘯鏁版嵁
        try:
            data_point.delete()
            print("鉁?娓呯悊娴嬭瘯鏁版嵁瀹屾垚")
        except Exception as e:
            print(f"鈿狅笍 娓呯悊娴嬭瘯鏁版嵁澶辫触: {e}")

if __name__ == '__main__':
    from django.utils import timezone
    test_file_import_msfg()

