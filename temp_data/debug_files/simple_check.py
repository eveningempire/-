#!/usr/bin/env python3
"""
PHM鍋ュ悍绠＄悊骞冲彴 - 绠€鍖栫幆澧冩鏌ヨ剼鏈?

璇ヨ剼鏈敤浜庡揩閫熸鏌ユ柊璁＄畻鏈烘槸鍚︽弧瓒矯MG鍋ュ悍绠＄悊骞冲彴鐨勫熀鏈繍琛岀幆澧冭姹傘€?
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def print_header():
    """鎵撳嵃鑴氭湰澶撮儴淇℃伅"""
    print("=" * 60)
    print("    PHM鍋ュ悍绠＄悊骞冲彴 - 鐜妫€鏌?)
    print("    Control Moment Gyroscope Health Management System")
    print("=" * 60)
    print()

def print_result(name, status, message=""):
    """鎵撳嵃妫€鏌ョ粨鏋?""
    if status:
        print(f"鉁?{name}: {message}")
    else:
        print(f"鉁?{name}: {message}")
    print()

def check_python_version():
    """妫€鏌ython鐗堟湰"""
    try:
        version = sys.version_info
        required_version = (3, 8)
        
        if version >= required_version:
            print_result(
                "Python鐗堟湰妫€鏌?,
                True,
                f"褰撳墠鐗堟湰: {version.major}.{version.minor}.{version.micro} (瑕佹眰: 3.8+)"
            )
            return True
        else:
            print_result(
                "Python鐗堟湰妫€鏌?,
                False,
                f"褰撳墠鐗堟湰: {version.major}.{version.minor}.{version.micro} (瑕佹眰: 3.8+)"
            )
            return False
    except Exception as e:
        print_result("Python鐗堟湰妫€鏌?, False, f"妫€鏌ュけ璐? {str(e)}")
        return False

def check_nodejs_version():
    """妫€鏌ode.js鐗堟湰"""
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_str = result.stdout.strip().lstrip('v')
            version_parts = version_str.split('.')
            major_version = int(version_parts[0])
            
            if major_version >= 16:
                print_result(
                    "Node.js鐗堟湰妫€鏌?,
                    True,
                    f"褰撳墠鐗堟湰: {version_str} (瑕佹眰: 16+)"
                )
                return True
            else:
                print_result(
                    "Node.js鐗堟湰妫€鏌?,
                    False,
                    f"褰撳墠鐗堟湰: {version_str} (瑕佹眰: 16+)"
                )
                return False
        else:
            print_result("Node.js鐗堟湰妫€鏌?, False, "Node.js鏈畨瑁呮垨鏃犳硶杩愯")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print_result("Node.js鐗堟湰妫€鏌?, False, "Node.js鏈畨瑁?)
        return False

def check_npm():
    """妫€鏌pm"""
    try:
        result = subprocess.run(['npm', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_result("npm妫€鏌?, True, f"褰撳墠鐗堟湰: {version}")
            return True
        else:
            print_result("npm妫€鏌?, False, "npm鏈畨瑁呮垨鏃犳硶杩愯")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print_result("npm妫€鏌?, False, "npm鏈畨瑁?)
        return False

def check_virtual_environment():
    """妫€鏌ヨ櫄鎷熺幆澧?""
    try:
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print_result(
                "铏氭嫙鐜妫€鏌?,
                True,
                f"褰撳墠铏氭嫙鐜: {sys.prefix}"
            )
            return True
        else:
            print_result(
                "铏氭嫙鐜妫€鏌?,
                False,
                "鏈娴嬪埌铏氭嫙鐜锛屽缓璁娇鐢ㄨ櫄鎷熺幆澧?
            )
            return False
    except Exception as e:
        print_result("铏氭嫙鐜妫€鏌?, False, f"妫€鏌ュけ璐? {str(e)}")
        return False

def check_project_files():
    """妫€鏌ラ」鐩枃浠?""
    required_files = [
        "phm_backend/settings.py",
        "frontend/package.json",
        "requirements.txt",
        "manage.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            
    if not missing_files:
        print_result(
            "椤圭洰鏂囦欢妫€鏌?,
            True,
            f"椤圭洰鏂囦欢瀹屾暣锛屾鏌ヤ簡 {len(required_files)} 涓叧閿枃浠?
        )
        return True
    else:
        print_result(
            "椤圭洰鏂囦欢妫€鏌?,
            False,
            f"缂哄皯鏂囦欢: {', '.join(missing_files)}"
        )
        return False

def check_venv_directory():
    """妫€鏌?venv鐩綍"""
    if Path(".venv").exists():
        print_result(
            ".venv鐩綍妫€鏌?,
            True,
            "妫€娴嬪埌.venv铏氭嫙鐜鐩綍"
        )
        return True
    else:
        print_result(
            ".venv鐩綍妫€鏌?,
            False,
            "鏈娴嬪埌.venv鐩綍锛岃澶嶅埗铏氭嫙鐜鏂囦欢澶?
        )
        return False

def check_node_modules():
    """妫€鏌ode_modules鐩綍"""
    if Path("frontend/node_modules").exists():
        print_result(
            "鍓嶇渚濊禆妫€鏌?,
            True,
            "node_modules鐩綍瀛樺湪锛屽墠绔緷璧栧凡瀹夎"
        )
        return True
    else:
        print_result(
            "鍓嶇渚濊禆妫€鏌?,
            False,
            "node_modules鐩綍涓嶅瓨鍦紝璇疯繍琛? cd frontend && npm install"
        )
        return False

def check_system_info():
    """妫€鏌ョ郴缁熶俊鎭?""
    print_result(
        "绯荤粺淇℃伅",
        True,
        f"鎿嶄綔绯荤粺: {platform.system()} {platform.release()}"
    )
    return True

def main():
    """涓诲嚱鏁?""
    print_header()
    
    checks = [
        ("Python鐗堟湰", check_python_version),
        ("Node.js鐗堟湰", check_nodejs_version),
        ("npm", check_npm),
        ("铏氭嫙鐜", check_virtual_environment),
        ("椤圭洰鏂囦欢", check_project_files),
        (".venv鐩綍", check_venv_directory),
        ("鍓嶇渚濊禆", check_node_modules),
        ("绯荤粺淇℃伅", check_system_info),
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed_checks += 1
        except Exception as e:
            print(f"鉁?{name}: 妫€鏌ュ紓甯?- {str(e)}")
            print()
    
    # 鎵撳嵃鎬荤粨
    print("=" * 60)
    print("妫€鏌ユ€荤粨:")
    print(f"閫氳繃妫€鏌? {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("鉁?鎵€鏈夋鏌ラ兘閫氳繃浜嗭紒绯荤粺鐜婊¤冻瑕佹眰銆?)
    else:
        print(f"鉁?鏈?{total_checks - passed_checks} 椤规鏌ユ湭閫氳繃锛岃鏍规嵁涓婅堪鎻愮ず杩涜淇銆?)
    
    print()
    print("瀹夎鎸囧崡:")
    print("1. 瀹夎Python 3.8+: https://www.python.org/downloads/")
    print("2. 瀹夎Node.js 16+: https://nodejs.org/")
    print("3. 瀹夎MySQL 8.0+: https://dev.mysql.com/downloads/")
    print("4. 瀹夎Redis 6.0+: https://redis.io/download")
    print("5. 澶嶅埗.venv鏂囦欢澶瑰埌椤圭洰鏍圭洰褰?)
    print("6. 杩愯: cd frontend && npm install")
    print("7. 閰嶇疆鐜鍙橀噺锛堟暟鎹簱杩炴帴绛夛級")
    print("8. 杩愯: python manage.py migrate")
    print("9. 杩愯: python manage.py runserver")
    print("=" * 60)

if __name__ == "__main__":
    main()


