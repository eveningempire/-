#!/usr/bin/env python
"""
PHM鍋ュ悍绠＄悊骞冲彴 - 杩佺Щ璁剧疆鑴氭湰
鐢ㄤ簬鑷姩鍖栭厤缃慨鏀瑰拰绯荤粺鍒濆鍖?
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path

def print_header(title):
    """鎵撳嵃鏍囬"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """鎵撳嵃姝ラ"""
    print(f"\n馃敡 姝ラ {step}: {description}")
    print("-" * 40)

def get_user_input(prompt, default=""):
    """鑾峰彇鐢ㄦ埛杈撳叆"""
    if default:
        user_input = input(f"{prompt} (榛樿: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def check_file_exists(file_path):
    """妫€鏌ユ枃浠舵槸鍚﹀瓨鍦?""
    if os.path.exists(file_path):
        print(f"鉁?鎵惧埌鏂囦欢: {file_path}")
        return True
    else:
        print(f"鉂?鏂囦欢涓嶅瓨鍦? {file_path}")
        return False

def backup_file(file_path):
    """澶囦唤鏂囦欢"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"馃搵 宸插浠? {file_path} -> {backup_path}")
            return True
        except Exception as e:
            print(f"鉂?澶囦唤澶辫触: {e}")
            return False
    return False

def update_settings_file():
    """鏇存柊Django璁剧疆鏂囦欢"""
    print_step(1, "閰嶇疆Django璁剧疆")
    
    settings_file = "phm_backend/settings.py"
    if not check_file_exists(settings_file):
        return False
    
    # 澶囦唤鍘熸枃浠?
    backup_file(settings_file)
    
    # 鑾峰彇鏁版嵁搴撻厤缃?
    print("\n馃搳 鏁版嵁搴撻厤缃?")
    db_name = get_user_input("鏁版嵁搴撳悕绉?, "cmg_health_management")
    db_user = get_user_input("鏁版嵁搴撶敤鎴峰悕", "root")
    db_password = get_user_input("鏁版嵁搴撳瘑鐮?, "")
    db_host = get_user_input("鏁版嵁搴撲富鏈?, "localhost")
    db_port = get_user_input("鏁版嵁搴撶鍙?, "3306")
    
    # 鑾峰彇Redis閰嶇疆
    print("\n馃敶 Redis閰嶇疆:")
    redis_host = get_user_input("Redis涓绘満", "localhost")
    redis_port = get_user_input("Redis绔彛", "6379")
    
    # 鑾峰彇鏈嶅姟鍣ㄩ厤缃?
    print("\n馃寪 鏈嶅姟鍣ㄩ厤缃?")
    allowed_hosts = get_user_input("鍏佽鐨勪富鏈?(鐢ㄩ€楀彿鍒嗛殧)", "localhost,127.0.0.1")
    secret_key = get_user_input("Django瀵嗛挜 (鐣欑┖鑷姩鐢熸垚)", "")
    
    # 璇诲彇璁剧疆鏂囦欢
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"鉂?璇诲彇璁剧疆鏂囦欢澶辫触: {e}")
        return False
    
    # 鏇存柊鏁版嵁搴撻厤缃?
    db_config = f"""DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{db_name}',
        'USER': '{db_user}',
        'PASSWORD': '{db_password}',
        'HOST': '{db_host}',
        'PORT': '{db_port}',
        'OPTIONS': {{
            'charset': 'utf8mb4',
        }},
    }}
}}"""
    
    # 鏇挎崲鏁版嵁搴撻厤缃?
    db_pattern = r'DATABASES\s*=\s*\{[^}]*\}'
    if re.search(db_pattern, content, re.DOTALL):
        content = re.sub(db_pattern, db_config, content, flags=re.DOTALL)
    else:
        # 濡傛灉鎵句笉鍒版暟鎹簱閰嶇疆锛屽湪鏂囦欢鏈熬娣诲姞
        content += f"\n\n{db_config}\n"
    
    # 鏇存柊Redis閰嶇疆
    redis_config = f"""
# Redis閰嶇疆
REDIS_HOST = '{redis_host}'
REDIS_PORT = {redis_port}
REDIS_DB = 0
"""
    
    # 鏇挎崲Redis閰嶇疆
    redis_pattern = r'REDIS_HOST\s*=\s*.*'
    if re.search(redis_pattern, content):
        content = re.sub(redis_pattern, f"REDIS_HOST = '{redis_host}'", content)
        content = re.sub(r'REDIS_PORT\s*=\s*\d+', f"REDIS_PORT = {redis_port}", content)
    else:
        content += redis_config
    
    # 鏇存柊鍏佽鐨勪富鏈?
    hosts_pattern = r'ALLOWED_HOSTS\s*=\s*\[[^\]]*\]'
    hosts_list = [host.strip() for host in allowed_hosts.split(',')]
    hosts_config = f"ALLOWED_HOSTS = {json.dumps(hosts_list)}"
    
    if re.search(hosts_pattern, content):
        content = re.sub(hosts_pattern, hosts_config, content)
    else:
        content += f"\n{hosts_config}\n"
    
    # 鏇存柊瀵嗛挜
    if secret_key:
        secret_pattern = r'SECRET_KEY\s*=\s*[\'"][^\'"]*[\'"]'
        if re.search(secret_pattern, content):
            content = re.sub(secret_pattern, f"SECRET_KEY = '{secret_key}'", content)
        else:
            content += f"\nSECRET_KEY = '{secret_key}'\n"
    
    # 鍐欏叆鏇存柊鍚庣殑鏂囦欢
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("鉁?Django璁剧疆鏂囦欢鏇存柊鎴愬姛")
        return True
    except Exception as e:
        print(f"鉂?鏇存柊璁剧疆鏂囦欢澶辫触: {e}")
        return False

def update_frontend_config():
    """鏇存柊鍓嶇閰嶇疆"""
    print_step(2, "閰嶇疆鍓嶇璁剧疆")
    
    # 妫€鏌ュ墠绔洰褰?
    frontend_dir = "frontend"
    if not os.path.exists(frontend_dir):
        print(f"鉂?鍓嶇鐩綍涓嶅瓨鍦? {frontend_dir}")
        return False
    
    # 鏇存柊API閰嶇疆
    api_file = "frontend/src/api/index.js"
    if check_file_exists(api_file):
        backup_file(api_file)
        
        print("\n馃寪 API閰嶇疆:")
        api_host = get_user_input("鍚庣API涓绘満", "localhost")
        api_port = get_user_input("鍚庣API绔彛", "8000")
        
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 鏇存柊baseURL
            base_url = f"http://{api_host}:{api_port}/api/v1"
            url_pattern = r'const\s+baseURL\s*=\s*[\'"][^\'"]*[\'"]'
            if re.search(url_pattern, content):
                content = re.sub(url_pattern, f"const baseURL = '{base_url}'", content)
            else:
                content += f"\nconst baseURL = '{base_url}'\n"
            
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("鉁?鍓嶇API閰嶇疆鏇存柊鎴愬姛")
        except Exception as e:
            print(f"鉂?鏇存柊鍓嶇閰嶇疆澶辫触: {e}")
            return False
    
    # 鏇存柊Vite閰嶇疆
    vite_file = "frontend/vite.config.js"
    if check_file_exists(vite_file):
        backup_file(vite_file)
        
        print("\n鈿?Vite閰嶇疆:")
        frontend_port = get_user_input("鍓嶇绔彛", "3000")
        
        try:
            with open(vite_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 鏇存柊绔彛閰嶇疆
            port_pattern = r'port:\s*\d+'
            if re.search(port_pattern, content):
                content = re.sub(port_pattern, f"port: {frontend_port}", content)
            
            # 纭繚host閰嶇疆姝ｇ‘
            host_pattern = r'host:\s*[\'"][^\'"]*[\'"]'
            if re.search(host_pattern, content):
                content = re.sub(host_pattern, "host: '0.0.0.0'", content)
            else:
                # 鍦╯erver閰嶇疆涓坊鍔爃ost
                server_pattern = r'server:\s*\{'
                if re.search(server_pattern, content):
                    content = re.sub(server_pattern, "server: {\n    host: '0.0.0.0',", content)
            
            with open(vite_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("鉁?Vite閰嶇疆鏇存柊鎴愬姛")
        except Exception as e:
            print(f"鉂?鏇存柊Vite閰嶇疆澶辫触: {e}")
            return False
    
    return True

def create_env_file():
    """鍒涘缓鐜鍙橀噺鏂囦欢"""
    print_step(3, "鍒涘缓鐜鍙橀噺鏂囦欢")
    
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"鈿狅笍  鐜鍙橀噺鏂囦欢宸插瓨鍦? {env_file}")
        overwrite = get_user_input("鏄惁瑕嗙洊? (y/N)", "N").lower()
        if overwrite != 'y':
            print("璺宠繃鐜鍙橀噺鏂囦欢鍒涘缓")
            return True
    
    print("\n馃敡 鐜鍙橀噺閰嶇疆:")
    db_name = get_user_input("鏁版嵁搴撳悕绉?, "cmg_health_management")
    db_user = get_user_input("鏁版嵁搴撶敤鎴峰悕", "root")
    db_password = get_user_input("鏁版嵁搴撳瘑鐮?, "")
    db_host = get_user_input("鏁版嵁搴撲富鏈?, "localhost")
    db_port = get_user_input("鏁版嵁搴撶鍙?, "3306")
    redis_host = get_user_input("Redis涓绘満", "localhost")
    redis_port = get_user_input("Redis绔彛", "6379")
    
    env_content = f"""# 鏁版嵁搴撻厤缃?
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}

# Redis閰嶇疆
REDIS_HOST={redis_host}
REDIS_PORT={redis_port}

# Django閰嶇疆
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 鍏朵粬閰嶇疆
CELERY_BROKER_URL=redis://{redis_host}:{redis_port}/0
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"鉁?鐜鍙橀噺鏂囦欢鍒涘缓鎴愬姛: {env_file}")
        return True
    except Exception as e:
        print(f"鉂?鍒涘缓鐜鍙橀噺鏂囦欢澶辫触: {e}")
        return False

def check_dependencies():
    """妫€鏌ヤ緷璧?""
    print_step(4, "妫€鏌ョ郴缁熶緷璧?)
    
    # 妫€鏌ython
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"鉁?Python: {result.stdout.strip()}")
        else:
            print("鉂?Python鏈畨瑁呮垨涓嶅湪PATH涓?)
            return False
    except Exception as e:
        print(f"鉂?妫€鏌ython澶辫触: {e}")
        return False
    
    # 妫€鏌ip
    try:
        result = subprocess.run(['pip', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"鉁?pip: {result.stdout.strip()}")
        else:
            print("鉂?pip鏈畨瑁?)
            return False
    except Exception as e:
        print(f"鉂?妫€鏌ip澶辫触: {e}")
        return False
    
    # 妫€鏌ode.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"鉁?Node.js: {result.stdout.strip()}")
        else:
            print("鉂?Node.js鏈畨瑁?)
            return False
    except Exception as e:
        print(f"鉂?妫€鏌ode.js澶辫触: {e}")
        return False
    
    # 妫€鏌pm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"鉁?npm: {result.stdout.strip()}")
        else:
            print("鉂?npm鏈畨瑁?)
            return False
    except Exception as e:
        print(f"鉂?妫€鏌pm澶辫触: {e}")
        return False
    
    return True

def install_dependencies():
    """瀹夎渚濊禆"""
    print_step(5, "瀹夎椤圭洰渚濊禆")
    
    # 妫€鏌ヨ櫄鎷熺幆澧?
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print("鉂?铏氭嫙鐜涓嶅瓨鍦紝璇峰厛澶嶅埗.venv鐩綍")
        return False
    
    print("鉁?铏氭嫙鐜宸插瓨鍦?)
    
    # 瀹夎鍚庣渚濊禆
    print("\n馃摝 瀹夎鍚庣渚濊禆...")
    try:
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("鉁?鍚庣渚濊禆瀹夎鎴愬姛")
        else:
            print(f"鉂?鍚庣渚濊禆瀹夎澶辫触: {result.stderr}")
            return False
    except Exception as e:
        print(f"鉂?瀹夎鍚庣渚濊禆澶辫触: {e}")
        return False
    
    # 瀹夎鍓嶇渚濊禆
    print("\n馃摝 瀹夎鍓嶇渚濊禆...")
    try:
        os.chdir("frontend")
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        os.chdir("..")
        if result.returncode == 0:
            print("鉁?鍓嶇渚濊禆瀹夎鎴愬姛")
        else:
            print(f"鉂?鍓嶇渚濊禆瀹夎澶辫触: {result.stderr}")
            return False
    except Exception as e:
        print(f"鉂?瀹夎鍓嶇渚濊禆澶辫触: {e}")
        return False
    
    return True

def run_migrations():
    """杩愯鏁版嵁搴撹縼绉?""
    print_step(6, "鏁版嵁搴撹縼绉?)
    
    print("馃攧 杩愯鏁版嵁搴撹縼绉?..")
    try:
        result = subprocess.run(['python', 'manage.py', 'makemigrations'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("鉁?鍒涘缓杩佺Щ鏂囦欢鎴愬姛")
        else:
            print(f"鈿狅笍  鍒涘缓杩佺Щ鏂囦欢璀﹀憡: {result.stderr}")
        
        result = subprocess.run(['python', 'manage.py', 'migrate'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("鉁?鏁版嵁搴撹縼绉绘垚鍔?)
        else:
            print(f"鉂?鏁版嵁搴撹縼绉诲け璐? {result.stderr}")
            return False
    except Exception as e:
        print(f"鉂?杩愯杩佺Щ澶辫触: {e}")
        return False
    
    return True

def create_superuser():
    """鍒涘缓瓒呯骇鐢ㄦ埛"""
    print_step(7, "鍒涘缓瓒呯骇鐢ㄦ埛")
    
    create_user = get_user_input("鏄惁鍒涘缓瓒呯骇鐢ㄦ埛? (Y/n)", "Y").lower()
    if create_user != 'y':
        print("璺宠繃瓒呯骇鐢ㄦ埛鍒涘缓")
        return True
    
    print("馃懁 鍒涘缓瓒呯骇鐢ㄦ埛...")
    try:
        # 鎻愪緵鐢ㄦ埛鍚嶃€侀偖绠便€佸瘑鐮佸拰瑙掕壊鐨勮緭鍏?
        user_input = "admin\nadmin@example.com\nadmin123\nadmin123\nadmin\n"
        result = subprocess.run(['python', 'manage.py', 'createsuperuser'], 
                              input=user_input, text=True)
        if result.returncode == 0:
            print("鉁?瓒呯骇鐢ㄦ埛鍒涘缓鎴愬姛")
            print("   鐢ㄦ埛鍚? admin")
            print("   瀵嗙爜: admin123")
            print("   瑙掕壊: 绠＄悊鍛?)
        else:
            print("鈿狅笍  瓒呯骇鐢ㄦ埛鍒涘缓鍙兘闇€瑕佹墜鍔ㄥ畬鎴?)
            print("璇锋墜鍔ㄨ繍琛? python manage.py createsuperuser")
    except Exception as e:
        print(f"鉂?鍒涘缓瓒呯骇鐢ㄦ埛澶辫触: {e}")
        print("璇锋墜鍔ㄨ繍琛? python manage.py createsuperuser")
    
    return True

def print_summary():
    """鎵撳嵃鎬荤粨"""
    print_header("杩佺Щ璁剧疆瀹屾垚")
    
    print("馃帀 绯荤粺杩佺Щ璁剧疆宸插畬鎴愶紒")
    print("\n馃搵 涓嬩竴姝ユ搷浣?")
    print("1. 纭繚MySQL鏈嶅姟姝ｅ湪杩愯")
    print("2. 纭繚Redis鏈嶅姟姝ｅ湪杩愯")
    print("3. 鍚姩鍚庣鏈嶅姟: python manage.py runserver 0.0.0.0:8000")
    print("4. 鍚姩鍓嶇鏈嶅姟: cd frontend && npm run dev")
    print("5. 璁块棶绯荤粺: http://localhost:3000")
    
    print("\n馃摎 鐩稿叧鏂囨。:")
    print("- 绯荤粺瀹夎鎸囧崡: docs/绯荤粺瀹夎鎸囧崡.md")
    print("- 鐢ㄦ埛鎵嬪唽: docs/鐢ㄦ埛鎵嬪唽.md")
    print("- API鏂囨。: http://localhost:8000/api/v1/")
    
    print("\n鈿狅笍  娉ㄦ剰浜嬮」:")
    print("- 璇风‘淇濇暟鎹簱杩炴帴姝ｅ父")
    print("- 妫€鏌ラ槻鐏璁剧疆")
    print("- 鍦ㄧ敓浜х幆澧冧腑淇敼DEBUG=False")
    print("- 瀹氭湡澶囦唤鏁版嵁搴?)

def main():
    """涓诲嚱鏁?""
    print_header("PHM鍋ュ悍绠＄悊骞冲彴 - 杩佺Щ璁剧疆")
    print("鏈剼鏈皢甯姪鎮ㄩ厤缃郴缁熻縼绉诲埌鏂扮幆澧?)
    
    # 妫€鏌ュ綋鍓嶇洰褰?
    if not os.path.exists("manage.py"):
        print("鉂?璇峰湪椤圭洰鏍圭洰褰曡繍琛屾鑴氭湰")
        return
    
    # 鎵ц閰嶇疆姝ラ
    steps = [
        ("妫€鏌ョ郴缁熶緷璧?, check_dependencies),
        ("閰嶇疆Django璁剧疆", update_settings_file),
        ("閰嶇疆鍓嶇璁剧疆", update_frontend_config),
        ("鍒涘缓鐜鍙橀噺鏂囦欢", create_env_file),
        ("瀹夎椤圭洰渚濊禆", install_dependencies),
        ("杩愯鏁版嵁搴撹縼绉?, run_migrations),
        ("鍒涘缓瓒呯骇鐢ㄦ埛", create_superuser),
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"鉂?{step_name}澶辫触锛岃妫€鏌ラ敊璇俊鎭?)
                return
        except KeyboardInterrupt:
            print("\n鈿狅笍  鐢ㄦ埛涓柇鎿嶄綔")
            return
        except Exception as e:
            print(f"鉂?{step_name}鍑虹幇寮傚父: {e}")
            return
    
    print_summary()

if __name__ == "__main__":
    main()

