#!/usr/bin/env python
"""
璋冭瘯鐧诲綍闂鑴氭湰
"""

import os
import sys
import django

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.test import Client
from django.urls import reverse

User = get_user_model()

def test_authentication():
    """娴嬭瘯鐢ㄦ埛璁よ瘉"""
    print("=== 娴嬭瘯鐢ㄦ埛璁よ瘉 ===")
    
    # 妫€鏌ョ敤鎴锋槸鍚﹀瓨鍦?
    users = User.objects.all()
    print(f"鏁版嵁搴撲腑鍏辨湁 {users.count()} 涓敤鎴?")
    for user in users:
        print(f"  - {user.username} (瑙掕壊: {user.role}, 婵€娲? {user.is_active})")
    
    # 娴嬭瘯璁よ瘉
    test_credentials = [
        ('admin', 'admin123456'),
        ('doctor1', 'doctor123'),
        ('user1', 'user123'),
        ('wrong_user', 'wrong_password')
    ]
    
    for username, password in test_credentials:
        print(f"\n娴嬭瘯璁よ瘉: {username}")
        user = authenticate(username=username, password=password)
        if user:
            print(f"鉁?璁よ瘉鎴愬姛: {user.username} (瑙掕壊: {user.role})")
        else:
            print(f"鉂?璁よ瘉澶辫触: {username}")

def test_login_view():
    """娴嬭瘯鐧诲綍瑙嗗浘"""
    print("\n=== 娴嬭瘯鐧诲綍瑙嗗浘 ===")
    
    client = Client()
    
    # 娴嬭瘯鐧诲綍璇锋眰
    login_data = {
        'username': 'admin',
        'password': 'admin123456'
    }
    
    try:
        response = client.post('/api/v1/users/login/', login_data)
        print(f"鐧诲綍鍝嶅簲鐘舵€佺爜: {response.status_code}")
        print(f"鐧诲綍鍝嶅簲鍐呭: {response.content.decode()}")
        
        if response.status_code == 200:
            print("鉁?鐧诲綍瑙嗗浘宸ヤ綔姝ｅ父")
        else:
            print("鉂?鐧诲綍瑙嗗浘鏈夐棶棰?)
            
    except Exception as e:
        print(f"鉂?娴嬭瘯鐧诲綍瑙嗗浘鏃跺嚭閿? {e}")

def test_urls():
    """娴嬭瘯URL閰嶇疆"""
    print("\n=== 娴嬭瘯URL閰嶇疆 ===")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # 妫€鏌ョ敤鎴风浉鍏崇殑URL
        user_urls = [
            '/api/v1/users/login/',
            '/api/v1/users/logout/',
            '/api/v1/users/',
            '/api/v1/users/register/'
        ]
        
        for url in user_urls:
            try:
                resolver.resolve(url)
                print(f"鉁?URL {url} 閰嶇疆姝ｇ‘")
            except Exception as e:
                print(f"鉂?URL {url} 閰嶇疆閿欒: {e}")
                
    except Exception as e:
        print(f"鉂?娴嬭瘯URL閰嶇疆鏃跺嚭閿? {e}")

def main():
    """涓诲嚱鏁?""
    print("鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁?- 鐧诲綍璋冭瘯宸ュ叿")
    print("=" * 50)
    
    # 娴嬭瘯鐢ㄦ埛璁よ瘉
    test_authentication()
    
    # 娴嬭瘯鐧诲綍瑙嗗浘
    test_login_view()
    
    # 娴嬭瘯URL閰嶇疆
    test_urls()
    
    print("\n=== 璋冭瘯瀹屾垚 ===")

if __name__ == "__main__":
    main()

