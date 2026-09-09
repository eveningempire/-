#!/usr/bin/env python
"""
娴嬭瘯淇鍚庣殑鏂囦欢瀵煎叆MSFG妫€娴?
楠岃瘉numpy绫诲瀷杞崲淇鏄惁鏈夋晥
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.batch_processing import BatchFileProcessor
from data_management.models import PHM, PHMData, ImportSession
from msfg_analysis.models import MSFGDefinition

def test_file_import_msfg_fixed():
    """娴嬭瘯淇鍚庣殑鏂囦欢瀵煎叆MSFG妫€娴?""
    print("寮€濮嬫祴璇曚慨澶嶅悗鐨勬枃浠跺鍏SFG妫€娴?..")
    
    try:
        # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
        active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
        if not active_msfg:
            print("鉂?鏈壘鍒版椿璺冪殑MSFG瀹氫箟")
            return False
        
        print(f"鉁?浣跨敤娲昏穬鐨凪SFG: {active_msfg.name}")
        
        # 鑾峰彇涓€涓狢MG瀹炰緥
        cmg = PHM.objects.first()
        if not cmg:
            print("鉂?鏈壘鍒癈MG瀹炰緥")
            return False
        
        print(f"鉁?浣跨敤PHM: {cmg.name}")
        
        # 鍒涘缓涓€涓ā鎷熺殑PHMData璁板綍
        timestamp = datetime.now()
        cmg_data = PHMData.objects.create(
            cmg=cmg,
            timestamp=timestamp,
            data={
                '楂橀€熸粦鍔ㄧ杞存俯': 45.2,
                '楂橀€熸粦鍔ㄧ杞存俯娓╁害': 45.5,
                '浣庨€熷３娓?: 38.1,
                '浣庨€烝鐩哥數娴?: 2.3,
                '浣庨€烠鐩哥數娴?: 2.1,
                '瀹氳閿佸畾绮惧害': 0.02,
                '楂橀€熻浆閫熸帶鍒剁簿搴?: 0.015,
                '楂橀€熻浆閫熸帶鍒剁ǔ瀹氬害': 0.008
            }
        )
        
        print(f"鉁?鍒涘缓娴嬭瘯鏁版嵁璁板綍: {cmg_data.id}")
        
        # 鍒涘缓BatchFileProcessor瀹炰緥
        processor = BatchFileProcessor()
        
        # 娴嬭瘯MSFG妫€娴?
        print("寮€濮婱SFG妫€娴?..")
        msfg_result = processor._run_msfg_detection(cmg_data, cmg)
        
        if msfg_result:
            print("鉁?MSFG妫€娴嬫垚鍔燂紒")
            print(f"妫€娴嬬粨鏋滃寘鍚?{len(msfg_result.get('test_results', {}))} 涓祴璇曠偣")
            print(f"妫€娴嬬粨鏋滃寘鍚?{len(msfg_result.get('fault_results', {}))} 涓晠闅滅偣")
            print(f"妫€娴嬬粨鏋滃寘鍚?{len(msfg_result.get('component_results', {}))} 涓儴浠?)
            
            # 娴嬭瘯JSON搴忓垪鍖?
            try:
                json_str = json.dumps(msfg_result, ensure_ascii=False, indent=2)
                print("鉁?MSFG妫€娴嬬粨鏋淛SON搴忓垪鍖栨垚鍔燂紒")
                print(f"搴忓垪鍖栫粨鏋滈暱搴? {len(json_str)} 瀛楃")
                
                # 楠岃瘉鍏抽敭瀛楁鐨勭被鍨?
                test_results = msfg_result.get('test_results', {})
                for test_name, test_data in test_results.items():
                    score = test_data.get('score')
                    if score is not None:
                        assert isinstance(score, (int, float)), f"娴嬭瘯鐐瑰垎鏁扮被鍨嬮敊璇? {type(score)}"
                        print(f"鉁?娴嬭瘯鐐?{test_name} 鍒嗘暟绫诲瀷姝ｇ‘: {type(score)}")
                
                fault_results = msfg_result.get('fault_results', {})
                for fault_name, fault_data in fault_results.items():
                    fault_prob = fault_data.get('fault_probability')
                    fuzzy_prob = fault_data.get('fuzzy_probability')
                    if fault_prob is not None:
                        assert isinstance(fault_prob, (int, float)), f"鏁呴殰姒傜巼绫诲瀷閿欒: {type(fault_prob)}"
                    if fuzzy_prob is not None:
                        assert isinstance(fuzzy_prob, (int, float)), f"妯＄硦姒傜巼绫诲瀷閿欒: {type(fuzzy_prob)}"
                    print(f"鉁?鏁呴殰鐐?{fault_name} 姒傜巼绫诲瀷姝ｇ‘")
                
                component_results = msfg_result.get('component_results', {})
                for component_name, component_data in component_results.items():
                    health_score = component_data.get('health_score')
                    if health_score is not None:
                        assert isinstance(health_score, (int, float)), f"閮ㄤ欢鍋ュ悍搴︾被鍨嬮敊璇? {type(health_score)}"
                        print(f"鉁?閮ㄤ欢 {component_name} 鍋ュ悍搴︾被鍨嬫纭? {type(health_score)}")
                
                system_results = msfg_result.get('system_results', {})
                overall_health = system_results.get('overall_health')
                if overall_health is not None:
                    assert isinstance(overall_health, (int, float)), f"绯荤粺鍋ュ悍搴︾被鍨嬮敊璇? {type(overall_health)}"
                    print(f"鉁?绯荤粺鍋ュ悍搴︾被鍨嬫纭? {type(overall_health)}")
                
                print("\n馃帀 鎵€鏈夌被鍨嬫鏌ラ€氳繃锛丮SFG妫€娴嬬粨鏋滃彲浠ユ甯镐繚瀛樺埌鏁版嵁搴?)
                return True
                
            except Exception as e:
                print(f"鉂?JSON搴忓垪鍖栧け璐? {e}")
                return False
        else:
            print("鉂?MSFG妫€娴嬪け璐ワ紝杩斿洖绌虹粨鏋?)
            return False
            
    except Exception as e:
        print(f"鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 娓呯悊娴嬭瘯鏁版嵁
        try:
            if 'cmg_data' in locals():
                cmg_data.delete()
                print("鉁?娓呯悊娴嬭瘯鏁版嵁瀹屾垚")
        except Exception as e:
            print(f"鈿狅笍 娓呯悊娴嬭瘯鏁版嵁澶辫触: {e}")

if __name__ == '__main__':
    success = test_file_import_msfg_fixed()
    if success:
        print("\n馃帀 淇楠岃瘉鎴愬姛锛乶umpy绫诲瀷杞崲闂宸茶В鍐?)
    else:
        print("\n鉂?淇楠岃瘉澶辫触锛岄渶瑕佽繘涓€姝ユ鏌?)

