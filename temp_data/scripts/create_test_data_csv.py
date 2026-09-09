#!/usr/bin/env python
"""
鍒涘缓閫傚悎500NM鍨嬪彿PHM鐨勬祴璇曟暟鎹枃浠?
"""

import csv
import os
from datetime import datetime, timedelta


def create_test_data_for_500nm():
    """涓?00NM鍨嬪彿鍒涘缓娴嬭瘯鏁版嵁"""
    print("鍒涘缓500NM鍨嬪彿娴嬭瘯鏁版嵁...")
    
    # 鍩轰簬鐜版湁瑙勫垯鐨勫弬鏁板悕锛堟牴鎹鏌ョ粨鏋滐級
    headers = ["timestamp", "鑷瀛?, "甯ц鏁?, "浣庨€熶綅缃?, "楂橀€熶綅缃?, "浣庨€熺數娴?, "楂橀€熺數娴?]
    
    # 鍒涘缓娴嬭瘯鏁版嵁
    data = []
    base_time = datetime(2024, 8, 14, 10, 0, 0)
    
    for i in range(50):  # 鍒涘缓50鏉¤褰?
        timestamp = base_time + timedelta(seconds=i * 10)  # 姣?0绉掍竴鏉¤褰?
        
        # 鍒涘缓涓€浜涙甯稿拰寮傚父鐨勬暟鎹?
        if i < 30:
            # 姝ｅ父鏁版嵁
            record = [
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                0,  # 鑷瀛?(姝ｅ父搴旇<=1)
                200 + i * 2,  # 甯ц鏁?(姝ｅ父搴旇<=388.7)
                80 + i,  # 浣庨€熶綅缃?(姝ｅ父搴旇<=116.6)
                150 + i,  # 楂橀€熶綅缃?
                1.5 + i * 0.01,  # 浣庨€熺數娴?
                2.0 + i * 0.02,  # 楂橀€熺數娴?
            ]
        else:
            # 寮傚父鏁版嵁 - 瑙﹀彂瑙勫垯
            record = [
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                2,  # 鑷瀛?> 1 (瑙﹀彂瑙勫垯)
                400 + i,  # 甯ц鏁?> 388.7 (瑙﹀彂瑙勫垯)
                120 + i,  # 浣庨€熶綅缃?> 116.6 (瑙﹀彂瑙勫垯)
                180 + i,  # 楂橀€熶綅缃?
                2.5 + i * 0.02,  # 浣庨€熺數娴?
                3.0 + i * 0.03,  # 楂橀€熺數娴?
            ]
        
        data.append(record)
    
    # 鍐欏叆CSV鏂囦欢
    filename = "test_data_500nm.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)
    
    print(f"鉁?鍒涘缓娴嬭瘯鏂囦欢: {filename}")
    print(f"鉁?鍖呭惈 {len(data)} 鏉¤褰?)
    print(f"鉁?鍓?0鏉′负姝ｅ父鏁版嵁锛屽悗20鏉′负寮傚父鏁版嵁锛堝皢瑙﹀彂瑙勫垯锛?)
    print(f"鉁?鍙傛暟鍖呮嫭: {', '.join(headers[1:])}")
    
    return filename


def main():
    """涓诲嚱鏁?""
    print("=== 鍒涘缓娴嬭瘯鏁版嵁 ===")
    
    try:
        filename = create_test_data_for_500nm()
        
        print(f"\n=== 浣跨敤璇存槑 ===")
        print(f"1. 鍦ㄥ墠绔枃浠朵笂浼犻〉闈㈤€夋嫨PHM: PHM-01")
        print(f"2. 涓婁紶鏂囦欢: {filename}")
        print(f"3. 瑙傚療澶勭悊杩涘害鍜屾娴嬬粨鏋?)
        print(f"4. 妫€鏌ユ槸鍚︽纭娴嬪埌寮傚父骞惰Е鍙戣鍒?)
        
        return True
        
    except Exception as e:
        print(f"鍒涘缓娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

