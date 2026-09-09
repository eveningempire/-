#!/usr/bin/env python3
"""
娴嬭瘯鏃堕棿鎴宠В鏋愪慨澶?
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_timestamp_parsing():
    """娴嬭瘯鏃堕棿鎴宠В鏋愬姛鑳?""
    print("娴嬭瘯鏃堕棿鎴宠В鏋愪慨澶?..")
    
    # 娴嬭瘯鏁版嵁
    test_timestamps = [
        "2024-04-24T15:46:29.001000+00:00",  # 鍘熷閿欒鏍煎紡
        "2024-04-24T15:46:29.001Z",          # Z鏍煎紡
        "2024-04-24T15:46:29.001",           # 鏃犳椂鍖烘牸寮?
        "2024-04-24 15:46:29",               # 绌烘牸鍒嗛殧鏍煎紡
        "2024/04/24 15:46:29",               # 鏂滄潬鍒嗛殧鏍煎紡
    ]
    
    def parse_timestamp(ts):
        """妯℃嫙淇鍚庣殑鏃堕棿鎴宠В鏋愬嚱鏁?""
        if isinstance(ts, str):
            # 澶勭悊ISO8601鏍煎紡鐨勬椂闂存埑
            if ts.endswith('+00:00'):
                # 宸茬粡鏄纭殑鏍煎紡
                return pd.to_datetime(ts)
            elif ts.endswith('Z'):
                # 灏哯鏇挎崲涓?00:00
                return pd.to_datetime(ts.replace('Z', '+00:00'))
            else:
                # 灏濊瘯鐩存帴瑙ｆ瀽
                return pd.to_datetime(ts)
        return pd.to_datetime(ts)
    
    print("\n娴嬭瘯鍚勭鏃堕棿鎴虫牸寮?")
    for i, ts in enumerate(test_timestamps, 1):
        try:
            parsed = parse_timestamp(ts)
            print(f"鉁?{i}. {ts} -> {parsed}")
        except Exception as e:
            print(f"鉂?{i}. {ts} -> 閿欒: {e}")
    
    # 娴嬭瘯pandas Series
    print("\n娴嬭瘯pandas Series:")
    try:
        time_stamps_series = pd.Series(test_timestamps)
        parsed_series = time_stamps_series.apply(parse_timestamp)
        print("鉁?pandas Series瑙ｆ瀽鎴愬姛")
        for i, (original, parsed) in enumerate(zip(test_timestamps, parsed_series)):
            print(f"   {i+1}. {original} -> {parsed}")
    except Exception as e:
        print(f"鉂?pandas Series瑙ｆ瀽澶辫触: {e}")

def test_lifetime_prediction_service():
    """娴嬭瘯瀵垮懡棰勬祴鏈嶅姟鐨勬椂闂村鐞?""
    print("\n娴嬭瘯瀵垮懡棰勬祴鏈嶅姟...")
    
    try:
        from lifetime_prediction.services import LifetimePredictionService
        
        service = LifetimePredictionService()
        print("鉁?瀵垮懡棰勬祴鏈嶅姟鍒濆鍖栨垚鍔?)
        
        # 娴嬭瘯涓嶅甫鏃堕棿娈电殑璋冪敤锛堝鍛介娴嬬晫闈級
        print("\n娴嬭瘯涓嶅甫鏃堕棿娈电殑璋冪敤锛堝鍛介娴嬬晫闈級:")
        # 杩欓噷闇€瑕佸疄闄呯殑PHM ID锛屾殏鏃惰烦杩?
        print("   闇€瑕佸疄闄呯殑PHM ID杩涜娴嬭瘯")
        
    except Exception as e:
        print(f"鉂?瀵垮懡棰勬祴鏈嶅姟娴嬭瘯澶辫触: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("鏃堕棿鎴宠В鏋愪慨澶嶆祴璇?)
    print("=" * 60)
    
    test_timestamp_parsing()
    test_lifetime_prediction_service()
    
    print("\n" + "=" * 60)
    print("娴嬭瘯瀹屾垚!")
    print("=" * 60)

