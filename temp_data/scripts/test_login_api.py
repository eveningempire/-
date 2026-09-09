#!/usr/bin/env python
"""
娴嬭瘯鐧诲綍API鑴氭湰
"""

import os
import sys
import django
import requests

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

def test_login_api():
    """娴嬭瘯鐧诲綍API"""
    print("=== 娴嬭瘯鐧诲綍API ===")
    
    # 娴嬭瘯鏈嶅姟鍣ㄥ湴鍧€
    base_url = "http://localhost:8000"
    
    # 娴嬭瘯鏁版嵁
    test_users = [
        {
            'username': 'admin',
            'password': 'admin123456',
            'expected': True
        },
        {
            'username': 'doctor1',
            'password': 'doctor123',
            'expected': True
        },
        {
            'username': 'user1',
            'password': 'user123',
            'expected': True
        },
        {
            'username': 'wrong_user',
            'password': 'wrong_password',
            'expected': False
        }
    ]
    
    for user_data in test_users:
        print(f"\n娴嬭瘯鐢ㄦ埛: {user_data['username']}")
        
        try:
            # 鍙戦€佺櫥褰曡姹?
            response = requests.post(
                f"{base_url}/api/v1/users/login/",
                data={
                    'username': user_data['username'],
                    'password': user_data['password']
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=10
            )
            
            print(f"鐘舵€佺爜: {response.status_code}")
            print(f"鍝嶅簲鍐呭: {response.text}")
            
            if response.status_code == 200 and user_data['expected']:
                print("鉁?鐧诲綍鎴愬姛")
            elif response.status_code == 401 and not user_data['expected']:
                print("鉁?鐧诲綍澶辫触锛堥鏈熺粨鏋滐級")
            else:
                print("鉂?娴嬭瘯澶辫触")
                
        except requests.exceptions.ConnectionError:
            print("鉂?鏃犳硶杩炴帴鍒版湇鍔″櫒锛岃纭繚Django鏈嶅姟鍣ㄦ鍦ㄨ繍琛?)
            break
        except Exception as e:
            print(f"鉂?璇锋眰澶辫触: {e}")

def test_user_management_api():
    """娴嬭瘯鐢ㄦ埛绠＄悊API"""
    print("\n=== 娴嬭瘯鐢ㄦ埛绠＄悊API ===")
    
    base_url = "http://localhost:8000"
    
    try:
        # 娴嬭瘯鑾峰彇鐢ㄦ埛鍒楄〃
        response = requests.get(f"{base_url}/api/v1/users/")
        print(f"鑾峰彇鐢ㄦ埛鍒楄〃 - 鐘舵€佺爜: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"鉁?鎴愬姛鑾峰彇 {len(users)} 涓敤鎴?)
            for user in users:
                print(f"  - {user.get('username')} ({user.get('role')})")
        else:
            print(f"鉂?鑾峰彇鐢ㄦ埛鍒楄〃澶辫触: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("鉂?鏃犳硶杩炴帴鍒版湇鍔″櫒锛岃纭繚Django鏈嶅姟鍣ㄦ鍦ㄨ繍琛?)
    except Exception as e:
        print(f"鉂?璇锋眰澶辫触: {e}")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- API娴嬭瘯宸ュ叿")
    print("=" * 50)
    
    # 娴嬭瘯鐧诲綍API
    test_login_api()
    
    # 娴嬭瘯鐢ㄦ埛绠＄悊API
    test_user_management_api()
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")
    print("濡傛灉鎵€鏈夋祴璇曢兘閫氳繃锛岃鏄嶢PI閰嶇疆姝ｇ‘")

if __name__ == "__main__":
    main()

