#!/usr/bin/env python3
"""
PHM鍋ュ悍绠＄悊骞冲彴 - 绯荤粺渚濊禆妫€鏌ヨ剼鏈?

璇ヨ剼鏈敤浜庢鏌ユ柊璁＄畻鏈烘槸鍚︽弧瓒矯MG鍋ュ悍绠＄悊骞冲彴鐨勮繍琛岀幆澧冭姹傘€?
妫€鏌ュ唴瀹瑰寘鎷細Python鐜銆丯ode.js鐜銆佹暟鎹簱鏈嶅姟銆佺郴缁熻祫婧愮瓑銆?

浣跨敤鏂规硶锛?
    python install_check.py

浣滆€咃細PHM寮€鍙戝洟闃?
鐗堟湰锛?.0.0
"""

import sys
import os
import subprocess
import platform
import shutil
import json
import socket
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Colors:
    """缁堢棰滆壊瀹氫箟"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemChecker:
    """绯荤粺鐜妫€鏌ュ櫒"""
    
    def __init__(self):
        self.check_results = {}
        self.errors = []
        self.warnings = []
        
    def print_header(self):
        """鎵撳嵃妫€鏌ヨ剼鏈ご閮ㄤ俊鎭?""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("=" * 60)
        print("    PHM鍋ュ悍绠＄悊骞冲彴 - 绯荤粺渚濊禆妫€鏌?)
        print("    Control Moment Gyroscope Health Management System")
        print("=" * 60)
        print(f"{Colors.END}")
        
    def print_result(self, name: str, status: bool, message: str = "", details: str = ""):
        """鎵撳嵃妫€鏌ョ粨鏋?""
        if status:
            status_text = f"{Colors.GREEN}鉁?閫氳繃{Colors.END}"
        else:
            status_text = f"{Colors.RED}鉁?澶辫触{Colors.END}"
            
        print(f"{Colors.BOLD}{name}:{Colors.END} {status_text}")
        if message:
            print(f"    {message}")
        if details:
            print(f"    {Colors.BLUE}璇︾粏淇℃伅: {details}{Colors.END}")
        print()
        
    def check_python_version(self) -> bool:
        """妫€鏌ython鐗堟湰"""
        try:
            version = sys.version_info
            required_version = (3, 8)
            
            if version >= required_version:
                self.print_result(
                    "Python鐗堟湰妫€鏌?,
                    True,
                    f"褰撳墠鐗堟湰: {version.major}.{version.minor}.{version.micro}",
                    f"瑕佹眰鐗堟湰: {required_version[0]}.{required_version[1]}+"
                )
                return True
            else:
                self.print_result(
                    "Python鐗堟湰妫€鏌?,
                    False,
                    f"褰撳墠鐗堟湰: {version.major}.{version.minor}.{version.micro}",
                    f"瑕佹眰鐗堟湰: {required_version[0]}.{required_version[1]}+"
                )
                return False
        except Exception as e:
            self.print_result("Python鐗堟湰妫€鏌?, False, f"妫€鏌ュけ璐? {str(e)}")
            return False
            
    def check_python_packages(self) -> bool:
        """妫€鏌ython鍖呬緷璧?""
        required_packages = [
            "django>=4.2,<5.0",
            "djangorestframework>=3.14,<4.0",
            "daphne>=4.0,<5.0",
            "channels>=4.0,<5.0",
            "channels-redis>=4.1,<5.0",
            "redis>=5,<6",
            "django-redis>=5.3,<6.0",
            "mysqlclient>=2.2,<3.0",
            "openpyxl>=3.1,<4.0",
            "django-cors-headers>=4.0,<5.0",
            "celery>=5.3,<6.0",
            "chardet>=5.0,<6.0"
        ]
        
        missing_packages = []
        installed_packages = []
        
        for package in required_packages:
            try:
                # 鎻愬彇鍖呭悕锛堝幓鎺夌増鏈彿锛?
                package_name = package.split('>=')[0].split('<')[0].split('==')[0]
                
                # 灏濊瘯瀵煎叆鍖?
                __import__(package_name.replace('-', '_'))
                installed_packages.append(package_name)
            except ImportError:
                missing_packages.append(package)
                
        if not missing_packages:
            self.print_result(
                "Python鍖呬緷璧栨鏌?,
                True,
                f"宸插畨瑁?{len(installed_packages)} 涓繀闇€鍖?,
                f"妫€鏌ョ殑鍖? {', '.join(installed_packages[:5])}{'...' if len(installed_packages) > 5 else ''}"
            )
            return True
        else:
            self.print_result(
                "Python鍖呬緷璧栨鏌?,
                False,
                f"缂哄皯 {len(missing_packages)} 涓寘",
                f"缂哄皯鐨勫寘: {', '.join(missing_packages[:5])}{'...' if len(missing_packages) > 5 else ''}"
            )
            return False
            
    def check_nodejs_version(self) -> bool:
        """妫€鏌ode.js鐗堟湰"""
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_str = result.stdout.strip().lstrip('v')
                version_parts = version_str.split('.')
                major_version = int(version_parts[0])
                
                if major_version >= 16:
                    self.print_result(
                        "Node.js鐗堟湰妫€鏌?,
                        True,
                        f"褰撳墠鐗堟湰: {version_str}",
                        f"瑕佹眰鐗堟湰: 16+"
                    )
                    return True
                else:
                    self.print_result(
                        "Node.js鐗堟湰妫€鏌?,
                        False,
                        f"褰撳墠鐗堟湰: {version_str}",
                        f"瑕佹眰鐗堟湰: 16+"
                    )
                    return False
            else:
                self.print_result("Node.js鐗堟湰妫€鏌?, False, "Node.js鏈畨瑁呮垨鏃犳硶杩愯")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.print_result("Node.js鐗堟湰妫€鏌?, False, "Node.js鏈畨瑁?)
            return False
            
    def check_npm_packages(self) -> bool:
        """妫€鏌pm鍖呬緷璧?""
        try:
            # 妫€鏌ackage.json鏄惁瀛樺湪
            package_json_path = Path("frontend/package.json")
            if not package_json_path.exists():
                self.print_result("npm鍖呬緷璧栨鏌?, False, "package.json鏂囦欢涓嶅瓨鍦?)
                return False
                
            # 妫€鏌ode_modules鏄惁瀛樺湪
            node_modules_path = Path("frontend/node_modules")
            if node_modules_path.exists():
                self.print_result(
                    "npm鍖呬緷璧栨鏌?,
                    True,
                    "node_modules鐩綍瀛樺湪",
                    "鍓嶇渚濊禆宸插畨瑁?
                )
                return True
            else:
                self.print_result(
                    "npm鍖呬緷璧栨鏌?,
                    False,
                    "node_modules鐩綍涓嶅瓨鍦?,
                    "璇疯繍琛? cd frontend && npm install"
                )
                return False
        except Exception as e:
            self.print_result("npm鍖呬緷璧栨鏌?, False, f"妫€鏌ュけ璐? {str(e)}")
            return False
            
    def check_mysql_connection(self) -> bool:
        """妫€鏌ySQL鏁版嵁搴撹繛鎺?""
        try:
            import mysql.connector
            
            # 灏濊瘯杩炴帴MySQL
            connection = mysql.connector.connect(
                host=os.environ.get("MYSQL_HOST", "localhost"),
                port=int(os.environ.get("MYSQL_PORT", "3306")),
                user=os.environ.get("MYSQL_USER", "Kaimol"),
                password=os.environ.get("MYSQL_PASSWORD", "123456"),
                database=os.environ.get("MYSQL_DATABASE", "cmg_db"),
                timeout=5
            )
            connection.close()
            
            self.print_result(
                "MySQL鏁版嵁搴撹繛鎺ユ鏌?,
                True,
                f"鏁版嵁搴? {os.environ.get('MYSQL_DATABASE', 'cmg_db')}",
                f"涓绘満: {os.environ.get('MYSQL_HOST', 'localhost')}:{os.environ.get('MYSQL_PORT', '3306')}"
            )
            return True
        except Exception as e:
            self.print_result(
                "MySQL鏁版嵁搴撹繛鎺ユ鏌?,
                False,
                f"杩炴帴澶辫触: {str(e)}",
                "璇风‘淇滿ySQL鏈嶅姟姝ｅ湪杩愯涓旈厤缃纭?
            )
            return False
            
    def check_redis_connection(self) -> bool:
        """妫€鏌edis杩炴帴"""
        try:
            import redis
            
            # 灏濊瘯杩炴帴Redis
            r = redis.Redis(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", "6379")),
                db=int(os.environ.get("REDIS_DB", "0")),
                password=os.environ.get("REDIS_PASSWORD"),
                socket_timeout=5
            )
            r.ping()
            
            self.print_result(
                "Redis杩炴帴妫€鏌?,
                True,
                f"Redis鏈嶅姟鍣? {os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}",
                f"鏁版嵁搴? {os.environ.get('REDIS_DB', '0')}"
            )
            return True
        except Exception as e:
            self.print_result(
                "Redis杩炴帴妫€鏌?,
                False,
                f"杩炴帴澶辫触: {str(e)}",
                "璇风‘淇漅edis鏈嶅姟姝ｅ湪杩愯"
            )
            return False
            
    def check_system_resources(self) -> bool:
        """妫€鏌ョ郴缁熻祫婧?""
        try:
            import psutil
            
            # 妫€鏌ュ唴瀛?
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            # 妫€鏌ョ鐩樼┖闂?
            disk = psutil.disk_usage('/')
            disk_gb = disk.free / (1024**3)
            
            memory_ok = memory_gb >= 8
            disk_ok = disk_gb >= 50
            
            if memory_ok and disk_ok:
                self.print_result(
                    "绯荤粺璧勬簮妫€鏌?,
                    True,
                    f"鍐呭瓨: {memory_gb:.1f}GB, 鍙敤纾佺洏绌洪棿: {disk_gb:.1f}GB",
                    f"瑕佹眰: 鍐呭瓨8GB+, 纾佺洏绌洪棿50GB+"
                )
                return True
            else:
                issues = []
                if not memory_ok:
                    issues.append(f"鍐呭瓨涓嶈冻 ({memory_gb:.1f}GB < 8GB)")
                if not disk_ok:
                    issues.append(f"纾佺洏绌洪棿涓嶈冻 ({disk_gb:.1f}GB < 50GB)")
                    
                self.print_result(
                    "绯荤粺璧勬簮妫€鏌?,
                    False,
                    f"鍐呭瓨: {memory_gb:.1f}GB, 鍙敤纾佺洏绌洪棿: {disk_gb:.1f}GB",
                    f"闂: {'; '.join(issues)}"
                )
                return False
        except ImportError:
            self.warnings.append("psutil鏈畨瑁咃紝璺宠繃绯荤粺璧勬簮妫€鏌?)
            return True
        except Exception as e:
            self.print_result("绯荤粺璧勬簮妫€鏌?, False, f"妫€鏌ュけ璐? {str(e)}")
            return False
            
    def check_virtual_environment(self) -> bool:
        """妫€鏌ヨ櫄鎷熺幆澧?""
        try:
            # 妫€鏌ユ槸鍚﹀湪铏氭嫙鐜涓?
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                self.print_result(
                    "铏氭嫙鐜妫€鏌?,
                    True,
                    f"褰撳墠铏氭嫙鐜: {sys.prefix}",
                    "寤鸿浣跨敤铏氭嫙鐜杩愯Python搴旂敤"
                )
                return True
            else:
                self.warnings.append("鏈娴嬪埌铏氭嫙鐜锛屽缓璁娇鐢ㄨ櫄鎷熺幆澧?)
                return True
        except Exception as e:
            self.print_result("铏氭嫙鐜妫€鏌?, False, f"妫€鏌ュけ璐? {str(e)}")
            return False
            
    def check_project_structure(self) -> bool:
        """妫€鏌ラ」鐩粨鏋?""
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
            self.print_result(
                "椤圭洰缁撴瀯妫€鏌?,
                True,
                f"椤圭洰鏂囦欢瀹屾暣",
                f"妫€鏌ヤ簡 {len(required_files)} 涓叧閿枃浠?
            )
            return True
        else:
            self.print_result(
                "椤圭洰缁撴瀯妫€鏌?,
                False,
                f"缂哄皯 {len(missing_files)} 涓枃浠?,
                f"缂哄皯鐨勬枃浠? {', '.join(missing_files)}"
            )
            return False
            
    def check_network_ports(self) -> bool:
        """妫€鏌ョ綉缁滅鍙?""
        ports_to_check = [8000, 6379, 3306]  # Django, Redis, MySQL
        available_ports = []
        occupied_ports = []
        
        for port in ports_to_check:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    if result == 0:
                        occupied_ports.append(port)
                    else:
                        available_ports.append(port)
            except Exception:
                occupied_ports.append(port)
                
        if not occupied_ports:
            self.print_result(
                "缃戠粶绔彛妫€鏌?,
                True,
                f"绔彛 {', '.join(map(str, available_ports))} 鍙敤",
                "鎵€鏈夊繀闇€绔彛閮藉彲鐢?
            )
            return True
        else:
            self.print_result(
                "缃戠粶绔彛妫€鏌?,
                False,
                f"绔彛 {', '.join(map(str, occupied_ports))} 琚崰鐢?,
                "璇风‘淇濊繖浜涚鍙ｆ湭琚叾浠栨湇鍔″崰鐢?
            )
            return False
            
    def generate_installation_guide(self):
        """鐢熸垚瀹夎鎸囧崡"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}瀹夎鎸囧崡:{Colors.END}")
        print("1. 瀹夎Python 3.8+")
        print("2. 瀹夎Node.js 16+")
        print("3. 瀹夎MySQL 8.0+")
        print("4. 瀹夎Redis 6.0+")
        print("5. 澶嶅埗.venv鏂囦欢澶瑰埌椤圭洰鏍圭洰褰?)
        print("6. 杩愯: cd frontend && npm install")
        print("7. 閰嶇疆鐜鍙橀噺锛堟暟鎹簱杩炴帴绛夛級")
        print("8. 杩愯: python manage.py migrate")
        print("9. 杩愯: python manage.py runserver")
        
    def run_all_checks(self):
        """杩愯鎵€鏈夋鏌?""
        self.print_header()
        
        checks = [
            ("Python鐗堟湰", self.check_python_version),
            ("Python鍖呬緷璧?, self.check_python_packages),
            ("Node.js鐗堟湰", self.check_nodejs_version),
            ("npm鍖呬緷璧?, self.check_npm_packages),
            ("MySQL杩炴帴", self.check_mysql_connection),
            ("Redis杩炴帴", self.check_redis_connection),
            ("绯荤粺璧勬簮", self.check_system_resources),
            ("铏氭嫙鐜", self.check_virtual_environment),
            ("椤圭洰缁撴瀯", self.check_project_structure),
            ("缃戠粶绔彛", self.check_network_ports),
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for name, check_func in checks:
            try:
                if check_func():
                    passed_checks += 1
            except Exception as e:
                self.print_result(name, False, f"妫€鏌ュ紓甯? {str(e)}")
                
        # 鎵撳嵃鎬荤粨
        print(f"\n{Colors.BOLD}{Colors.BLUE}妫€鏌ユ€荤粨:{Colors.END}")
        print(f"閫氳繃妫€鏌? {Colors.GREEN}{passed_checks}/{total_checks}{Colors.END}")
        
        if passed_checks == total_checks:
            print(f"{Colors.GREEN}鉁?鎵€鏈夋鏌ラ兘閫氳繃浜嗭紒绯荤粺鐜婊¤冻瑕佹眰銆倇Colors.END}")
        else:
            print(f"{Colors.RED}鉁?鏈?{total_checks - passed_checks} 椤规鏌ユ湭閫氳繃锛岃鏍规嵁涓婅堪鎻愮ず杩涜淇銆倇Colors.END}")
            
        if self.warnings:
            print(f"\n{Colors.YELLOW}璀﹀憡:{Colors.END}")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        self.generate_installation_guide()

def main():
    """涓诲嚱鏁?""
    checker = SystemChecker()
    checker.run_all_checks()

if __name__ == "__main__":
    main()


