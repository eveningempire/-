#!/usr/bin/env python
"""
璇婃柇閮ㄤ欢鍋ュ悍鍒嗘瀽涓殑娲昏穬鏁呴殰鍜屾渶澶ф晠闅滃垎鏁拌绠楅棶棰?
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGAnalysisResult
from msfg_analysis.algorithms.msfg.component_integration import calculate_msfg_component_health
from msfg_analysis.algorithms.msfg.fusion import calculate_component_scores
import json

def diagnose_component_metrics():
    """璇婃柇閮ㄤ欢鍋ュ悍鍒嗘瀽涓殑娲昏穬鏁呴殰鍜屾渶澶ф晠闅滃垎鏁拌绠楅棶棰?""
    print("馃攳 璇婃柇閮ㄤ欢鍋ュ悍鍒嗘瀽涓殑娲昏穬鏁呴殰鍜屾渶澶ф晠闅滃垎鏁拌绠楅棶棰?)
    print("="*60)
    
    # 鑾峰彇鏈€杩戠殑MSFG鍒嗘瀽缁撴灉
    results = MSFGAnalysisResult.objects.order_by('-created_at')[:3]
    
    if not results.exists():
        print("鉂?娌℃湁鎵惧埌MSFG鍒嗘瀽缁撴灉")
        return
    
    print(f"鎵惧埌 {results.count()} 鏉℃渶杩戠殑鍒嗘瀽缁撴灉")
    
    for i, result in enumerate(results, 1):
        print(f"\n馃搳 鍒嗘瀽缁撴灉 {i}:")
        print(f"  鏃堕棿: {result.created_at}")
        print(f"  PHM: {result.data_point.cmg.cmg_id}")
        print(f"  MSFG: {result.msfg_definition.name}")
        
        # 妫€鏌omponent_results
        component_results = result.component_results
        print(f"\n  馃攳 閮ㄤ欢鍒嗘瀽缁撴灉 (component_results):")
        print(f"    绫诲瀷: {type(component_results)}")
        print(f"    閮ㄤ欢鏁伴噺: {len(component_results) if component_results else 0}")
        
        if component_results:
            for component_name, data in list(component_results.items())[:3]:  # 鍙樉绀哄墠3涓?
                print(f"\n    閮ㄤ欢: {component_name}")
                print(f"      鏁版嵁绫诲瀷: {type(data)}")
                print(f"      鏁版嵁鍐呭: {data}")
                
                # 妫€鏌ュ叧閿瓧娈?
                health_score = data.get('health_score', 'N/A')
                active_fault_count = data.get('active_fault_count', 'N/A')
                max_fault_score = data.get('max_fault_score', 'N/A')
                max_test_score = data.get('max_test_score', 'N/A')
                
                print(f"      鍋ュ悍鍒嗘暟: {health_score}")
                print(f"      娲昏穬鏁呴殰鏁? {active_fault_count}")
                print(f"      鏈€澶ф晠闅滃垎鏁? {max_fault_score}")
                print(f"      鏈€澶ф祴璇曞垎鏁? {max_test_score}")
                
                # 妫€鏌ユ槸鍚︽湁NaN鎴栧紓甯稿€?
                if isinstance(active_fault_count, (int, float)):
                    if active_fault_count == 0:
                        print(f"        鈿狅笍 娲昏穬鏁呴殰鏁颁负0")
                if isinstance(max_fault_score, (int, float)):
                    if max_fault_score == 0:
                        print(f"        鈿狅笍 鏈€澶ф晠闅滃垎鏁颁负0")
        
        print("-" * 50)
        
        # 鍙缁嗗垎鏋愮涓€鏉＄粨鏋?
        if i == 1:
            print(f"\n馃敡 璇︾粏鍒嗘瀽绗竴鏉＄粨鏋滅殑璁＄畻閫昏緫:")
            
            # 鑾峰彇娴嬭瘯鐐瑰垎鏁板拰鏁呴殰鍒嗘暟
            test_results = result.test_results
            fault_results = result.fault_results
            
            print(f"\n  娴嬭瘯鐐瑰垎鏁?(test_results):")
            print(f"    鏁伴噺: {len(test_results) if test_results else 0}")
            if test_results:
                for key, value in list(test_results.items())[:3]:
                    print(f"      {key}: {value}")
            
            print(f"\n  鏁呴殰鍒嗘暟 (fault_results):")
            print(f"    鏁伴噺: {len(fault_results) if fault_results else 0}")
            if fault_results:
                for key, value in list(fault_results.items())[:3]:
                    print(f"      {key}: {value}")
            
            # 鍒嗘瀽璁＄畻閫昏緫
            print(f"\n  馃搵 璁＄畻閫昏緫鍒嗘瀽:")
            
            # 1. 妫€鏌omponent_integration.py鐨勮绠楅€昏緫
            try:
                print(f"    1. 浣跨敤component_integration.py璁＄畻:")
                test_scores = {}
                if test_results:
                    for key, value in test_results.items():
                        if isinstance(value, dict) and 'score' in value:
                            test_scores[key] = value['score']
                        else:
                            test_scores[key] = value
                
                component_health = calculate_msfg_component_health(
                    test_scores=test_scores,
                    msfg_definition=result.msfg_definition,
                    include_unmapped_components=True
                )
                
                print(f"      璁＄畻缁撴灉閮ㄤ欢鏁伴噺: {len(component_health)}")
                for comp_name, comp_data in list(component_health.items())[:2]:
                    print(f"        {comp_name}:")
                    print(f"          health_score: {comp_data.get('health_score')}")
                    print(f"          active_fault_count: {comp_data.get('active_fault_count')}")
                    print(f"          max_test_score: {comp_data.get('max_test_score')}")
                    
            except Exception as e:
                print(f"      鉂?component_integration璁＄畻澶辫触: {e}")
            
            # 2. 妫€鏌usion.py鐨勮绠楅€昏緫
            try:
                print(f"\n    2. 浣跨敤fusion.py璁＄畻:")
                from msfg_analysis.models import MSFGNode, MSFGEdge
                
                nodes = list(result.msfg_definition.nodes.all())
                edges_qs = list(result.msfg_definition.edges.all())
                edges = [(e.source_node.node_id, e.target_node.node_id) for e in edges_qs]
                
                component_scores = calculate_component_scores(
                    fault_scores=fault_results,
                    test_scores=test_scores,
                    nodes=nodes,
                    edges=edges,
                    msfg_definition=result.msfg_definition
                )
                
                print(f"      璁＄畻缁撴灉閮ㄤ欢鏁伴噺: {len(component_scores)}")
                for comp_name, comp_data in list(component_scores.items())[:2]:
                    print(f"        {comp_name}:")
                    print(f"          health_score: {comp_data.get('health_score')}")
                    print(f"          active_fault_count: {comp_data.get('active_fault_count')}")
                    print(f"          max_fault_score: {comp_data.get('max_fault_score')}")
                    
            except Exception as e:
                print(f"      鉂?fusion璁＄畻澶辫触: {e}")

def check_testpoint_component_mappings():
    """妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠"""
    print(f"\n馃敡 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠")
    print("="*40)
    
    from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
    
    # 鑾峰彇婵€娲荤殑MSFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌婵€娲荤殑MSFG瀹氫箟")
        return
    
    print(f"鉁?婵€娲荤殑MSFG: {active_msfg.name}")
    
    # 妫€鏌ユ槧灏?
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    print(f"鉁?娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏁伴噺: {mappings.count()}")
    
    if mappings.exists():
        print(f"\n  鏄犲皠璇︽儏:")
        for mapping in mappings[:5]:  # 鍙樉绀哄墠5涓?
            print(f"    {mapping.test_point_name} -> {mapping.component_name} (鏉冮噸: {mapping.importance_weight})")
    else:
        print(f"  鈿狅笍 娌℃湁鎵惧埌娴嬭瘯鐐?閮ㄤ欢鏄犲皠")

if __name__ == "__main__":
    diagnose_component_metrics()
    check_testpoint_component_mappings()

