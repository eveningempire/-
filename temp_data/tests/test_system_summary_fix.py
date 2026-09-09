#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
娴嬭瘯绯荤粺姒傝璁＄畻淇
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.algorithms.msfg.fusion import summarize_system

def test_system_summary():
    """娴嬭瘯绯荤粺姒傝璁＄畻"""
    print("馃И 娴嬭瘯绯荤粺姒傝璁＄畻淇")
    print("=" * 50)
    
    # 娴嬭瘯鏁版嵁1锛氱畝鍗曟暟鍊兼牸寮忥紙fuse_test_to_fault杩斿洖鐨勬牸寮忥級
    fault_scores_1 = {
        '妗嗘灦鏁呴殰': 0.8,
        '杞瓙鏁呴殰': 0.4,
        '娓╁害鏁呴殰': 0.2,
        '鐢垫簮鏁呴殰': 0.9,
        '閫氫俊鏁呴殰': 0.1
    }
    
    result_1 = summarize_system(fault_scores_1)
    print(f"鉁?绠€鍗曟暟鍊兼牸寮忔祴璇?")
    print(f"   鏁呴殰鏁伴噺: {result_1['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_1['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_1['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_1['critical_faults']}")
    
    # 娴嬭瘯鏁版嵁2锛氬祵濂楀璞℃牸寮?
    fault_scores_2 = {
        '妗嗘灦鏁呴殰': {'fault_probability': 0.8, 'fuzzy_probability': 0.1},
        '杞瓙鏁呴殰': {'fault_probability': 0.4, 'fuzzy_probability': 0.3},
        '娓╁害鏁呴殰': {'fault_probability': 0.2, 'fuzzy_probability': 0.1},
        '鐢垫簮鏁呴殰': {'fault_probability': 0.9, 'fuzzy_probability': 0.2},
        '閫氫俊鏁呴殰': {'fault_probability': 0.1, 'fuzzy_probability': 0.05}
    }
    
    result_2 = summarize_system(fault_scores_2)
    print(f"\n鉁?宓屽瀵硅薄鏍煎紡娴嬭瘯:")
    print(f"   鏁呴殰鏁伴噺: {result_2['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_2['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_2['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_2['critical_faults']}")
    
    # 娴嬭瘯鏁版嵁3锛氭贩鍚堟牸寮?
    fault_scores_3 = {
        '妗嗘灦鏁呴殰': 0.8,
        '杞瓙鏁呴殰': {'fault_probability': 0.4, 'fuzzy_probability': 0.3},
        '娓╁害鏁呴殰': 0.2,
        '鐢垫簮鏁呴殰': {'fault_probability': 0.9, 'fuzzy_probability': 0.2}
    }
    
    result_3 = summarize_system(fault_scores_3)
    print(f"\n鉁?娣峰悎鏍煎紡娴嬭瘯:")
    print(f"   鏁呴殰鏁伴噺: {result_3['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_3['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_3['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_3['critical_faults']}")
    
    # 娴嬭瘯鏁版嵁4锛氱┖鏁版嵁
    result_4 = summarize_system({})
    print(f"\n鉁?绌烘暟鎹祴璇?")
    print(f"   鏁呴殰鏁伴噺: {result_4['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_4['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_4['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_4['critical_faults']}")
    
    # 娴嬭瘯鏁版嵁5锛氭甯告儏鍐碉紙鏃犳椿璺冩晠闅滐級
    fault_scores_5 = {
        '妗嗘灦鏁呴殰': 0.1,
        '杞瓙鏁呴殰': 0.2,
        '娓╁害鏁呴殰': 0.05
    }
    
    result_5 = summarize_system(fault_scores_5)
    print(f"\n鉁?姝ｅ父鎯呭喌娴嬭瘯锛堟棤娲昏穬鏁呴殰锛?")
    print(f"   鏁呴殰鏁伴噺: {result_5['fault_count']}")
    print(f"   鏈€涓ラ噸鏁呴殰: {result_5['worst_fault_score']}")
    print(f"   骞冲潎鏁呴殰鍒嗘暟: {result_5['average_fault_score']}")
    print(f"   鍏抽敭鏁呴殰: {result_5['critical_faults']}")

def main():
    """涓绘祴璇曞嚱鏁?""
    print("馃殌 寮€濮嬫祴璇曠郴缁熸瑙堣绠椾慨澶?)
    print("=" * 60)
    
    try:
        test_system_summary()
        
        print("\n" + "=" * 60)
        print("鉁?娴嬭瘯瀹屾垚锛?)
        print("\n馃搵 淇璇存槑:")
        print("1. 鉁?淇浜嗙郴缁熸瑙堣绠楅€昏緫")
        print("2. 鉁?鍏煎绠€鍗曟暟鍊煎拰宓屽瀵硅薄涓ょ鏁版嵁鏍煎紡")
        print("3. 鉁?姝ｇ‘璁＄畻娲昏穬鏁呴殰鏁伴噺銆佹渶涓ラ噸鏁呴殰銆佸钩鍧囨晠闅滃垎鏁?)
        print("4. 鉁?姝ｇ‘璇嗗埆鍏抽敭鏁呴殰鍒楄〃")
        
    except Exception as e:
        print(f"\n鉂?娴嬭瘯杩囩▼涓嚭鐜伴敊璇? {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

