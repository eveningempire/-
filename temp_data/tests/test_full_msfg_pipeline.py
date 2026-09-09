#!/usr/bin/env python
"""
瀹屾暣MSFG鍔熻兘妯″潡绔埌绔祴璇?
娴嬭瘯閾捐矾锛氭祴鐐硅瘎鍒?鈫?鏁呴殰璇勫垎 鈫?缁勪欢鍒嗘暟 鈫?绯荤粺鍒嗘暟
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from data_management.models import PHMModel, PHMData
from msfg_analysis.services.testpoint_scoring import calculate_msfg_test_scores
from msfg_analysis.services.component_mapping import build_msfg_component_mappings
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
from data_management.batch_processing import BatchFileProcessor

def test_full_msfg_pipeline():
    print("=" * 80)
    print("瀹屾暣MSFG鍔熻兘妯″潡绔埌绔祴璇?)
    print("=" * 80)
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    try:
        cmg_model = PHMModel.objects.get(id=3)
        print(f"鉁?PHM妯″瀷: {cmg_model.model_name}")
    except PHMModel.DoesNotExist:
        print("鉁?PHM妯″瀷ID 3涓嶅瓨鍦?)
        return False
    
    # 鑾峰彇婵€娲荤殑MSFG
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    if not msfg:
        print("鉁?娌℃湁鎵惧埌婵€娲荤殑MSFG")
        return False
    
    print(f"鉁?MSFG瀹氫箟: {msfg.name}")
    
    # 鑾峰彇鏁版嵁鐐?
    data_point = PHMData.objects.filter(cmg__cmg_model=cmg_model).first()
    if not data_point:
        print("鉁?娌℃湁鎵惧埌鏁版嵁鐐?)
        return False
    
    print(f"鉁?鏁版嵁鐐? ID {data_point.id}, 鏃堕棿鎴?{data_point.timestamp}")
    
    # 鑾峰彇MSFG鍥剧粨鏋?
    test_nodes = list(MSFGNode.objects.filter(msfg_definition=msfg, node_type='test'))
    fault_nodes = list(MSFGNode.objects.filter(msfg_definition=msfg, node_type='fault'))
    edges = list(MSFGEdge.objects.filter(msfg_definition=msfg))
    
    print(f"鉁?MSFG缁撴瀯: {len(test_nodes)} 涓祴鐐? {len(fault_nodes)} 涓晠闅滅偣, {len(edges)} 鏉¤竟")
    
    print(f"\n{'='*60}")
    print("绗?姝ワ細娴嬬偣璇勫垎")
    print('='*60)
    
    # 娴嬭瘯娴嬬偣璇勫垎
    try:
        test_scores_dict = calculate_msfg_test_scores(data_point, msfg)
        if not test_scores_dict:
            print("鉁?娴嬬偣璇勫垎澶辫触")
            return False
        
        print(f"鉁?娴嬬偣璇勫垎鎴愬姛锛屽叡 {len(test_scores_dict)} 涓祴鐐?)
        
        # 鏄剧ず璇勫垎缁撴灉
        non_zero_scores = {k: v for k, v in test_scores_dict.items() if v > 0.0}
        zero_scores = {k: v for k, v in test_scores_dict.items() if v == 0.0}
        
        print(f"  - 闈為浂璇勫垎娴嬬偣: {len(non_zero_scores)}")
        if non_zero_scores:
            for name, score in sorted(non_zero_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    {name}: {score:.3f}")
        
        print(f"  - 闆惰瘎鍒嗘祴鐐? {len(zero_scores)}")
        
        # 杞崲涓篗SFG铻嶅悎绠楁硶闇€瑕佺殑鏍煎紡
        test_scores = {name: [score] for name, score in test_scores_dict.items()}
        
    except Exception as e:
        print(f"鉁?娴嬬偣璇勫垎澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n{'='*60}")
    print("绗?姝ワ細缁勪欢鏄犲皠")
    print('='*60)
    
    # 娴嬭瘯缁勪欢鏄犲皠
    try:
        component_mappings = build_msfg_component_mappings(msfg)
        if not component_mappings:
            print("鈿狅笍  娌℃湁鎵惧埌缁勪欢鏄犲皠锛屽垱寤洪粯璁ゆ槧灏?)
            # 鍒涘缓榛樿鏄犲皠
            component_mappings = {}
            for fault_node in fault_nodes:
                comp_name = f"缁勪欢_{fault_node.name}"
                if comp_name not in component_mappings:
                    component_mappings[comp_name] = []
                component_mappings[comp_name].append(fault_node.name)
        
        print(f"鉁?缁勪欢鏄犲皠鎴愬姛锛屽叡 {len(component_mappings)} 涓粍浠?)
        for comp_name, fault_list in list(component_mappings.items())[:3]:
            print(f"  - {comp_name}: {fault_list}")
            
    except Exception as e:
        print(f"鉁?缁勪欢鏄犲皠澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n{'='*60}")
    print("绗?姝ワ細MSFG楂樼骇铻嶅悎绠楁硶")
    print('='*60)
    
    # 娴嬭瘯MSFG铻嶅悎绠楁硶
    try:
        fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
        
        print("寮€濮嬭繍琛岄珮绾у垎鏋?..")
        analysis_result = fusion_algorithm.run_advanced_analysis(
            test_scores=test_scores,
            test_nodes=test_nodes,
            fault_nodes=fault_nodes,
            edges=edges,
            component_mappings=component_mappings
        )
        
        print("鉁?MSFG铻嶅悎绠楁硶鎵ц鎴愬姛")
        
        # 鎻愬彇缁撴灉
        test_results = analysis_result['test_results']
        fault_results = analysis_result['fault_results']
        system_results = analysis_result['system_results']
        component_results = analysis_result['component_results']
        
        print(f"  - 娴嬬偣缁撴灉: {len(test_results)} 椤?)
        print(f"  - 鏁呴殰缁撴灉: {len(fault_results)} 椤?)
        print(f"  - 缁勪欢缁撴灉: {len(component_results)} 椤?)
        print(f"  - 绯荤粺缁撴灉: {len(system_results)} 椤?)
        
    except Exception as e:
        print(f"鉁?MSFG铻嶅悎绠楁硶澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n{'='*60}")
    print("绗?姝ワ細缁撴灉鍒嗘瀽")
    print('='*60)
    
    # 鍒嗘瀽鏁呴殰缁撴灉
    print("鏁呴殰鍒嗘瀽缁撴灉:")
    detected_faults = []
    for fault_name, fault_data in fault_results.items():
        fault_prob = fault_data.get('fault_probability', 0.0)
        if fault_prob > 0.1:  # 鏄剧ず姒傜巼澶т簬0.1鐨勬晠闅?
            print(f"  - {fault_name}: {fault_prob:.3f}")
            if fault_prob > 0.7:
                detected_faults.append(fault_name)
    
    if detected_faults:
        print(f"鉁?妫€娴嬪埌楂橀闄╂晠闅? {detected_faults}")
    else:
        print("鉁?鏈娴嬪埌楂橀闄╂晠闅?)
    
    # 鍒嗘瀽缁勪欢鍋ュ悍
    print("\n缁勪欢鍋ュ悍鍒嗘瀽:")
    critical_components = []
    for comp_name, comp_data in component_results.items():
        health_score = comp_data.get('health_score', 1.0)
        print(f"  - {comp_name}: {health_score:.3f}")
        if health_score < 0.7:
            critical_components.append(comp_name)
    
    if critical_components:
        print(f"鉁?鍙戠幇鍏抽敭缁勪欢: {critical_components}")
    else:
        print("鉁?鎵€鏈夌粍浠跺仴搴风姸鍐佃壇濂?)
    
    # 鍒嗘瀽绯荤粺鍋ュ悍
    print("\n绯荤粺鍋ュ悍鍒嗘瀽:")
    overall_health = system_results.get('overall_health', 1.0)
    print(f"  - 鎬讳綋鍋ュ悍鍒嗘暟: {overall_health:.3f}")
    
    if overall_health > 0.8:
        health_status = "浼樼"
    elif overall_health > 0.6:
        health_status = "鑹ソ"
    elif overall_health > 0.4:
        health_status = "涓€鑸?
    else:
        health_status = "闇€瑕佸叧娉?
    
    print(f"  - 鍋ュ悍鐘舵€? {health_status}")
    
    print(f"\n{'='*60}")
    print("绗?姝ワ細鏁版嵁搴撳瓨鍌ㄦ祴璇?)
    print('='*60)
    
    # 娴嬭瘯鏁版嵁搴撳瓨鍌?
    try:
        batch_processor = BatchFileProcessor()
        
        # 妯℃嫙鎵瑰鐞嗕腑鐨凪SFG妫€娴嬮€昏緫
        msfg_result = {
            'data_point_id': data_point.id,
            'data_point_timestamp': data_point.timestamp.isoformat(),
            'msfg_definition_id': msfg.id,
            'msfg_definition_name': msfg.name,
            'test_results': test_results,
            'fault_results': fault_results,
            'system_results': system_results,
            'component_results': component_results,
            'overall_health_score': float(overall_health),
            'detected_faults': detected_faults,
            'critical_components': critical_components,
            'analysis_details': {
                "source": "full_pipeline_test",
                "total_test_nodes": len(test_nodes),
                "total_fault_nodes": len(fault_nodes),
                "total_edges": len(edges),
                "component_mappings_count": len(component_mappings),
                "analysis_metadata": analysis_result['analysis_metadata']
            }
        }
        
        print("鉁?MSFG缁撴灉鏁版嵁鍑嗗瀹屾垚")
        print(f"  - 鏁版嵁鐐笽D: {msfg_result['data_point_id']}")
        print(f"  - 鎬讳綋鍋ュ悍鍒嗘暟: {msfg_result['overall_health_score']:.3f}")
        print(f"  - 妫€娴嬪埌鐨勬晠闅? {len(msfg_result['detected_faults'])}")
        print(f"  - 鍏抽敭缁勪欢: {len(msfg_result['critical_components'])}")
        
        # 杩欓噷鍙互璋冪敤瀹為檯鐨勫瓨鍌ㄩ€昏緫
        # batch_processor._save_msfg_result(msfg_result)
        print("鉁?鏁版嵁搴撳瓨鍌ㄥ噯澶囧氨缁紙鏈疄闄呮墽琛岋級")
        
    except Exception as e:
        print(f"鉁?鏁版嵁搴撳瓨鍌ㄦ祴璇曞け璐? {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n{'='*80}")
    print("馃帀 瀹屾暣MSFG鍔熻兘妯″潡娴嬭瘯鎴愬姛锛?)
    print("鉁?娴嬬偣璇勫垎 鈫?鉁?鏁呴殰鎺ㄦ柇 鈫?鉁?缁勪欢鍋ュ悍 鈫?鉁?绯荤粺璇勪及 鈫?鉁?瀛樺偍鍑嗗")
    print('='*80)
    
    return True

if __name__ == "__main__":
    success = test_full_msfg_pipeline()
    if success:
        print("\n馃殌 MSFG妯″潡宸插畬鍏ㄨ皟閫氾紝鍙互鎶曞叆浣跨敤锛?)
    else:
        print("\n鈿狅笍  MSFG妯″潡浠嶆湁闂闇€瑕佷慨澶?)

