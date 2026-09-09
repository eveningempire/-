#!/usr/bin/env python
"""
蹇€熸祴璇曡剼鏈?- 鍙緭鍑哄叧閿俊鎭?
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.test import Client

User = get_user_model()

def main():
    print("=== 蹇€熸祴璇?===")
    
    # 妫€鏌ョ敤鎴?
    users = User.objects.all()
    print(f"鐢ㄦ埛鏁伴噺: {users.count()}")
    
    # 娴嬭瘯璁よ瘉
    user = authenticate(username='admin', password='admin123456')
    print(f"璁よ瘉缁撴灉: {'鎴愬姛' if user else '澶辫触'}")
    
    # 娴嬭瘯鐧诲綍API
    client = Client()
    response = client.post('/api/v1/users/login/', {
        'username': 'admin',
        'password': 'admin123456'
    })
    
    print(f"鐧诲綍API鐘舵€佺爜: {response.status_code}")
    if response.status_code != 200:
        print(f"閿欒淇℃伅: {response.content.decode()[:100]}...")

if __name__ == "__main__":
    main()

