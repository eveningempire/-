#!/usr/bin/env python
"""
妫€鏌SFG鐨勫疄闄呮暟鎹粨鏋?
"""

import os
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition
from msfg_analysis.algorithms.msfg.component_integration import get_active_msfg_for_cmg_model

def check_msfg_structure():
    """妫€鏌SFG鐨勫疄闄呮暟鎹粨鏋?""
    print("馃攳 妫€鏌SFG鐨勫疄闄呮暟鎹粨鏋?)
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ュ師濮婮SON鏁版嵁
        raw_data = active_msfg.raw_graph_data
        print(f"  馃搳 raw_data绫诲瀷: {type(raw_data)}")
        
        if raw_data and isinstance(raw_data, dict):
            print(f"  馃搳 raw_data閿? {list(raw_data.keys())}")
            
            # 妫€鏌ystemData瀛楁
            if 'SystemData' in raw_data:
                system_data = raw_data['SystemData']
                print(f"  馃搳 SystemData绫诲瀷: {type(system_data)}")
                
                if isinstance(system_data, dict):
                    print(f"  馃搳 SystemData閿? {list(system_data.keys())}")
                    
                    # 妫€鏌ユ槸鍚︽湁nodes鐩稿叧鐨勫瓧娈?
                    for key, value in system_data.items():
                        if 'node' in key.lower() or 'graph' in key.lower():
                            print(f"  馃攳 鍙戠幇鐩稿叧瀛楁: {key} = {type(value)}")
                            if isinstance(value, list):
                                print(f"    馃搳 {key}闀垮害: {len(value)}")
                                if len(value) > 0:
                                    print(f"    馃搳 {key}绗竴涓厓绱? {value[0]}")
                            elif isinstance(value, dict):
                                print(f"    馃搳 {key}閿? {list(value.keys())}")
                elif isinstance(system_data, list):
                    print(f"  馃搳 SystemData闀垮害: {len(system_data)}")
                    if len(system_data) > 0:
                        print(f"  馃搳 SystemData绗竴涓厓绱? {system_data[0]}")
            
            # 妫€鏌estNameSet瀛楁
            if 'testNameSet' in raw_data:
                test_name_set = raw_data['testNameSet']
                print(f"  馃搳 testNameSet绫诲瀷: {type(test_name_set)}")
                if isinstance(test_name_set, list):
                    print(f"  馃搳 testNameSet闀垮害: {len(test_name_set)}")
                    print(f"  馃搳 testNameSet鍐呭: {test_name_set}")
                elif isinstance(test_name_set, dict):
                    print(f"  馃搳 testNameSet閿? {list(test_name_set.keys())}")
            
            # 妫€鏌therNodeNameSet瀛楁
            if 'otherNodeNameSet' in raw_data:
                other_node_set = raw_data['otherNodeNameSet']
                print(f"  馃搳 otherNodeNameSet绫诲瀷: {type(other_node_set)}")
                if isinstance(other_node_set, list):
                    print(f"  馃搳 otherNodeNameSet闀垮害: {len(other_node_set)}")
                    print(f"  馃搳 otherNodeNameSet鍐呭: {other_node_set}")
                elif isinstance(other_node_set, dict):
                    print(f"  馃搳 otherNodeNameSet閿? {list(other_node_set.keys())}")

def check_processed_structure():
    """妫€鏌ュ鐞嗗悗鐨勬暟鎹粨鏋?""
    print("\n馃搫 妫€鏌ュ鐞嗗悗鐨勬暟鎹粨鏋?)
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 妫€鏌MG妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ュ鐞嗗悗鐨凧SON鏁版嵁
        processed_data = active_msfg.processed_graph_data
        print(f"  馃搳 processed_data绫诲瀷: {type(processed_data)}")
        
        if processed_data:
            if isinstance(processed_data, list):
                print(f"  馃搳 processed_data闀垮害: {len(processed_data)}")
                if len(processed_data) > 0:
                    print(f"  馃搳 processed_data绗竴涓厓绱犵被鍨? {type(processed_data[0])}")
                    if isinstance(processed_data[0], dict):
                        print(f"  馃搳 processed_data绗竴涓厓绱犻敭: {list(processed_data[0].keys())}")
                        print(f"  馃搳 processed_data绗竴涓厓绱? {processed_data[0]}")
                    else:
                        print(f"  馃搳 processed_data绗竴涓厓绱? {processed_data[0]}")
            elif isinstance(processed_data, dict):
                print(f"  馃搳 processed_data閿? {list(processed_data.keys())}")
                for key, value in processed_data.items():
                    print(f"  馃搳 {key}: {type(value)}")
                    if isinstance(value, list):
                        print(f"    馃搳 {key}闀垮害: {len(value)}")
                        if len(value) > 0:
                            print(f"    馃搳 {key}绗竴涓厓绱? {value[0]}")

if __name__ == "__main__":
    check_msfg_structure()
    check_processed_structure()

