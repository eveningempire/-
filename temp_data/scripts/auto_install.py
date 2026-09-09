#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHM鍋ュ悍绠＄悊骞冲彴 - 鑷姩瀹夎鑴氭湰
鑷姩閰嶇疆鍜屽畨瑁匔MG骞冲彴鐨勬墍鏈夌粍浠?
"""

import os
import sys
import subprocess
import json
import getpass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class AutoInstaller:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / ".venv"
        self.config = {}
        
    def print_header(self, title: str):
        """鎵撳嵃鏍囬"""
        print("\n" + "="*60)
        print(f"馃殌 {title}")
        print("="*60)
    
    def print_step(self, step: str, message: str):
        """鎵撳嵃姝ラ淇℃伅"""
        print(f"\n馃搵 {step}: {message}")
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """杩愯鍛戒护骞惰繑鍥炵粨鏋?""
        try:
            result = subprocess.run(command, capture_output=True, text=True, cwd=cwd, timeout=300)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "鍛戒护鎵ц瓒呮椂"
        except Exception as e:
            return -1, "", str(e)
    
    def get_user_input(self, prompt: str, default: str = "", password: bool = False) -> str:
        """鑾峰彇鐢ㄦ埛杈撳叆"""
        if password:
            return getpass.getpass(prompt)
        else:
            user_input = input(prompt)
            return user_input if user_input.strip() else default
    
    def check_environment(self):
        """妫€鏌ョ幆澧冩槸鍚︽弧瓒宠姹?""
        self.print_header("鐜妫€鏌?)
        
        # 妫€鏌ョ幆澧冩娴嬭剼鏈?
        env_check_script = self.project_root / "check_environment.py"
        if not env_check_script.exists():
            print("鉂?鏈壘鍒扮幆澧冩娴嬭剼鏈?check_environment.py")
            return False
        
        # 杩愯鐜妫€娴?
        self.print_step("鐜妫€娴?, "杩愯鐜妫€娴嬭剼鏈?..")
        code, output, error = self.run_command([sys.executable, "check_environment.py"])
        
        if code != 0:
            print("鉂?鐜妫€娴嬪け璐ワ紝璇峰厛瑙ｅ喅鐜闂")
            print(f"閿欒淇℃伅: {error}")
            return False
        
        print("鉁?鐜妫€娴嬮€氳繃")
        return True
    
    def configure_database(self):
        """閰嶇疆鏁版嵁搴?""
        self.print_header("鏁版嵁搴撻厤缃?)
        
        print("馃摑 璇疯緭鍏ユ暟鎹簱閰嶇疆淇℃伅:")
        
        # 鑾峰彇鏁版嵁搴撻厤缃?
        self.config["database"] = {
            "host": self.get_user_input("鏁版嵁搴撲富鏈?(榛樿: localhost): ", "localhost"),
            "port": self.get_user_input("鏁版嵁搴撶鍙?(榛樿: 3306): ", "3306"),
            "name": self.get_user_input("鏁版嵁搴撳悕绉?(榛樿: cmg_db): ", "cmg_db"),
            "user": self.get_user_input("鏁版嵁搴撶敤鎴峰悕: "),
            "password": self.get_user_input("鏁版嵁搴撳瘑鐮? ", password=True),
        }
        
        # 娴嬭瘯鏁版嵁搴撹繛鎺?
        self.print_step("鏁版嵁搴撹繛鎺ユ祴璇?, "娴嬭瘯鏁版嵁搴撹繛鎺?..")
        
        # 鍒涘缓娴嬭瘯杩炴帴鑴氭湰
        test_script = f"""
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='{self.config["database"]["host"]}',
        port={self.config["database"]["port"]},
        user='{self.config["database"]["user"]}',
        password='{self.config["database"]["password"]}'
    )
    print("鉁?鏁版嵁搴撹繛鎺ユ垚鍔?)
    conn.close()
except Exception as e:
    print(f"鉂?鏁版嵁搴撹繛鎺ュけ璐? {{e}}")
    exit(1)
"""
        
        test_file = self.project_root / "test_db_connection.py"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        code, output, error = self.run_command([sys.executable, "test_db_connection.py"])
        test_file.unlink()  # 鍒犻櫎娴嬭瘯鏂囦欢
        
        if code != 0:
            print("鉂?鏁版嵁搴撹繛鎺ュけ璐ワ紝璇锋鏌ラ厤缃?)
            return False
        
        print("鉁?鏁版嵁搴撹繛鎺ユ垚鍔?)
        
        # 鍒涘缓鏁版嵁搴?
        self.print_step("鍒涘缓鏁版嵁搴?, f"鍒涘缓鏁版嵁搴?{self.config['database']['name']}...")
        
        create_db_script = f"""
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='{self.config["database"]["host"]}',
        port={self.config["database"]["port"]},
        user='{self.config["database"]["user"]}',
        password='{self.config["database"]["password"]}'
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS {self.config['database']['name']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print("鉁?鏁版嵁搴撳垱寤烘垚鍔?)
    conn.close()
except Exception as e:
    print(f"鉂?鏁版嵁搴撳垱寤哄け璐? {{e}}")
    exit(1)
"""
        
        create_file = self.project_root / "create_database.py"
        with open(create_file, 'w', encoding='utf-8') as f:
            f.write(create_db_script)
        
        code, output, error = self.run_command([sys.executable, "create_database.py"])
        create_file.unlink()
        
        if code != 0:
            print("鉂?鏁版嵁搴撳垱寤哄け璐?)
            return False
        
        print("鉁?鏁版嵁搴撳垱寤烘垚鍔?)
        return True
    
    def configure_redis(self):
        """閰嶇疆Redis"""
        self.print_header("Redis閰嶇疆")
        
        print("馃摑 璇疯緭鍏edis閰嶇疆淇℃伅:")
        
        self.config["redis"] = {
            "host": self.get_user_input("Redis涓绘満 (榛樿: localhost): ", "localhost"),
            "port": self.get_user_input("Redis绔彛 (榛樿: 6379): ", "6379"),
            "db": self.get_user_input("Redis鏁版嵁搴?(榛樿: 0): ", "0"),
            "password": self.get_user_input("Redis瀵嗙爜 (鍙€?: ", password=True),
        }
        
        # 娴嬭瘯Redis杩炴帴
        self.print_step("Redis杩炴帴娴嬭瘯", "娴嬭瘯Redis杩炴帴...")
        
        test_script = f"""
import redis
try:
    r = redis.Redis(
        host='{self.config["redis"]["host"]}',
        port={self.config["redis"]["port"]},
        db={self.config["redis"]["db"]},
        password='{self.config["redis"]["password"]}' if '{self.config["redis"]["password"]}' else None
    )
    r.ping()
    print("鉁?Redis杩炴帴鎴愬姛")
except Exception as e:
    print(f"鉂?Redis杩炴帴澶辫触: {{e}}")
    exit(1)
"""
        
        test_file = self.project_root / "test_redis_connection.py"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        code, output, error = self.run_command([sys.executable, "test_redis_connection.py"])
        test_file.unlink()
        
        if code != 0:
            print("鉂?Redis杩炴帴澶辫触锛岃妫€鏌ラ厤缃?)
            return False
        
        print("鉁?Redis杩炴帴鎴愬姛")
        return True
    
    def create_env_file(self):
        """鍒涘缓鐜鍙橀噺鏂囦欢"""
        self.print_header("鍒涘缓鐜鍙橀噺鏂囦欢")
        
        env_content = f"""# PHM鍋ュ悍绠＄悊骞冲彴鐜鍙橀噺閰嶇疆

# 鏁版嵁搴撻厤缃?
MYSQL_DATABASE={self.config["database"]["name"]}
MYSQL_USER={self.config["database"]["user"]}
MYSQL_PASSWORD={self.config["database"]["password"]}
MYSQL_HOST={self.config["database"]["host"]}
MYSQL_PORT={self.config["database"]["port"]}

# Redis閰嶇疆
REDIS_HOST={self.config["redis"]["host"]}
REDIS_PORT={self.config["redis"]["port"]}
REDIS_DB={self.config["redis"]["db"]}
REDIS_PASSWORD={self.config["redis"]["password"]}

# Django閰嶇疆
DJANGO_SECRET_KEY=django-insecure-change-me-please
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_TIME_ZONE=Asia/Shanghai
"""
        
        env_file = self.project_root / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("鉁?鐜鍙橀噺鏂囦欢鍒涘缓鎴愬姛")
        return True
    
    def install_python_dependencies(self):
        """瀹夎Python渚濊禆"""
        self.print_header("瀹夎Python渚濊禆")
        
        # 妫€鏌ヨ櫄鎷熺幆澧?
        if not self.venv_path.exists():
            self.print_step("鍒涘缓铏氭嫙鐜", "鍒涘缓Python铏氭嫙鐜...")
            code, output, error = self.run_command([sys.executable, "-m", "venv", ".venv"])
            if code != 0:
                print("鉂?铏氭嫙鐜鍒涘缓澶辫触")
                return False
            print("鉁?铏氭嫙鐜鍒涘缓鎴愬姛")
        
        # 婵€娲昏櫄鎷熺幆澧冨苟瀹夎渚濊禆
        self.print_step("瀹夎渚濊禆", "瀹夎Python渚濊禆鍖?..")
        
        # 鑾峰彇铏氭嫙鐜涓殑pip璺緞
        if os.name == 'nt':  # Windows
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:  # Linux/Mac
            pip_path = self.venv_path / "bin" / "pip"
        
        if not pip_path.exists():
            print("鉂?铏氭嫙鐜涓湭鎵惧埌pip")
            return False
        
        # 瀹夎渚濊禆
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            code, output, error = self.run_command([str(pip_path), "install", "-r", "requirements.txt"])
            if code != 0:
                print("鉂?Python渚濊禆瀹夎澶辫触")
                print(f"閿欒淇℃伅: {error}")
                return False
            print("鉁?Python渚濊禆瀹夎鎴愬姛")
        else:
            print("鈿狅笍 鏈壘鍒皉equirements.txt鏂囦欢")
        
        return True
    
    def install_frontend_dependencies(self):
        """瀹夎鍓嶇渚濊禆"""
        self.print_header("瀹夎鍓嶇渚濊禆")
        
        frontend_path = self.project_root / "frontend"
        if not frontend_path.exists():
            print("鉂?鍓嶇鐩綍涓嶅瓨鍦?)
            return False
        
        self.print_step("瀹夎鍓嶇渚濊禆", "瀹夎Node.js渚濊禆鍖?..")
        
        # 妫€鏌ode_modules鏄惁瀛樺湪
        node_modules = frontend_path / "node_modules"
        if node_modules.exists():
            print("鉁?鍓嶇渚濊禆宸插瓨鍦?)
            return True
        
        # 瀹夎渚濊禆
        code, output, error = self.run_command(["npm", "install"], cwd=frontend_path)
        if code != 0:
            print("鉂?鍓嶇渚濊禆瀹夎澶辫触")
            print(f"閿欒淇℃伅: {error}")
            return False
        
        print("鉁?鍓嶇渚濊禆瀹夎鎴愬姛")
        return True
    
    def run_database_migrations(self):
        """杩愯鏁版嵁搴撹縼绉?""
        self.print_header("鏁版嵁搴撹縼绉?)
        
        # 鑾峰彇铏氭嫙鐜涓殑Python璺緞
        if os.name == 'nt':  # Windows
            python_path = self.venv_path / "Scripts" / "python.exe"
        else:  # Linux/Mac
            python_path = self.venv_path / "bin" / "python"
        
        if not python_path.exists():
            print("鉂?铏氭嫙鐜涓湭鎵惧埌Python")
            return False
        
        self.print_step("鍒涘缓杩佺Щ", "鍒涘缓鏁版嵁搴撹縼绉绘枃浠?..")
        code, output, error = self.run_command([str(python_path), "manage.py", "makemigrations"])
        if code != 0:
            print("鉂?鍒涘缓杩佺Щ澶辫触")
            print(f"閿欒淇℃伅: {error}")
            return False
        
        self.print_step("搴旂敤杩佺Щ", "搴旂敤鏁版嵁搴撹縼绉?..")
        code, output, error = self.run_command([str(python_path), "manage.py", "migrate"])
        if code != 0:
            print("鉂?搴旂敤杩佺Щ澶辫触")
            print(f"閿欒淇℃伅: {error}")
            return False
        
        print("鉁?鏁版嵁搴撹縼绉诲畬鎴?)
        return True
    
    def collect_static_files(self):
        """鏀堕泦闈欐€佹枃浠?""
        self.print_header("鏀堕泦闈欐€佹枃浠?)
        
        # 鑾峰彇铏氭嫙鐜涓殑Python璺緞
        if os.name == 'nt':  # Windows
            python_path = self.venv_path / "Scripts" / "python.exe"
        else:  # Linux/Mac
            python_path = self.venv_path / "bin" / "python"
        
        if not python_path.exists():
            print("鉂?铏氭嫙鐜涓湭鎵惧埌Python")
            return False
        
        self.print_step("鏀堕泦闈欐€佹枃浠?, "鏀堕泦Django闈欐€佹枃浠?..")
        code, output, error = self.run_command([str(python_path), "manage.py", "collectstatic", "--noinput"])
        if code != 0:
            print("鉂?闈欐€佹枃浠舵敹闆嗗け璐?)
            print(f"閿欒淇℃伅: {error}")
            return False
        
        print("鉁?闈欐€佹枃浠舵敹闆嗗畬鎴?)
        return True
    
    def create_superuser(self):
        """鍒涘缓瓒呯骇鐢ㄦ埛"""
        self.print_header("鍒涘缓瓒呯骇鐢ㄦ埛")
        
        print("馃摑 鏄惁鍒涘缓瓒呯骇鐢ㄦ埛? (y/n): ", end="")
        choice = input().lower().strip()
        
        if choice not in ['y', 'yes']:
            print("鈴笍 璺宠繃鍒涘缓瓒呯骇鐢ㄦ埛")
            return True
        
        # 鑾峰彇铏氭嫙鐜涓殑Python璺緞
        if os.name == 'nt':  # Windows
            python_path = self.venv_path / "Scripts" / "python.exe"
        else:  # Linux/Mac
            python_path = self.venv_path / "bin" / "python"
        
        if not python_path.exists():
            print("鉂?铏氭嫙鐜涓湭鎵惧埌Python")
            return False
        
        self.print_step("鍒涘缓瓒呯骇鐢ㄦ埛", "鍒涘缓Django瓒呯骇鐢ㄦ埛...")
        code, output, error = self.run_command([str(python_path), "manage.py", "createsuperuser"], input="\n".join([
            "admin",  # 鐢ㄦ埛鍚?
            "admin@example.com",  # 閭
            "admin123",  # 瀵嗙爜
            "admin123",  # 纭瀵嗙爜
            "admin"  # 瑙掕壊
        ]))
        
        if code != 0:
            print("鉂?瓒呯骇鐢ㄦ埛鍒涘缓澶辫触")
            print(f"閿欒淇℃伅: {error}")
            return False
        
        print("鉁?瓒呯骇鐢ㄦ埛鍒涘缓鎴愬姛")
        print("   鐢ㄦ埛鍚? admin")
        print("   瀵嗙爜: admin123")
        return True
    
    def save_config(self):
        """淇濆瓨閰嶇疆"""
        config_file = self.project_root / "install_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        print(f"鉁?閰嶇疆宸蹭繚瀛樺埌: {config_file}")
    
    def run_installation(self):
        """杩愯瀹屾暣瀹夎娴佺▼"""
        print("馃殌 PHM鍋ュ悍绠＄悊骞冲彴 - 鑷姩瀹夎寮€濮?)
        print(f"馃搧 椤圭洰璺緞: {self.project_root}")
        
        try:
            # 1. 鐜妫€鏌?
            if not self.check_environment():
                return False
            
            # 2. 鏁版嵁搴撻厤缃?
            if not self.configure_database():
                return False
            
            # 3. Redis閰嶇疆
            if not self.configure_redis():
                return False
            
            # 4. 鍒涘缓鐜鍙橀噺鏂囦欢
            if not self.create_env_file():
                return False
            
            # 5. 瀹夎Python渚濊禆
            if not self.install_python_dependencies():
                return False
            
            # 6. 瀹夎鍓嶇渚濊禆
            if not self.install_frontend_dependencies():
                return False
            
            # 7. 杩愯鏁版嵁搴撹縼绉?
            if not self.run_database_migrations():
                return False
            
            # 8. 鏀堕泦闈欐€佹枃浠?
            if not self.collect_static_files():
                return False
            
            # 9. 鍒涘缓瓒呯骇鐢ㄦ埛
            if not self.create_superuser():
                return False
            
            # 10. 淇濆瓨閰嶇疆
            self.save_config()
            
            print("\n馃帀 瀹夎瀹屾垚锛?)
            print("\n馃搵 瀹夎鎽樿:")
            print(f"   鈥?鏁版嵁搴? {self.config['database']['name']} @ {self.config['database']['host']}:{self.config['database']['port']}")
            print(f"   鈥?Redis: {self.config['redis']['host']}:{self.config['redis']['port']}")
            print(f"   鈥?铏氭嫙鐜: {self.venv_path}")
            print(f"   鈥?鐜鍙橀噺: {self.project_root / '.env'}")
            
            print("\n馃殌 鍚姩绯荤粺:")
            print("   python start_cmg_platform.bat")
            
            return True
            
        except KeyboardInterrupt:
            print("\n鉂?瀹夎琚敤鎴蜂腑鏂?)
            return False
        except Exception as e:
            print(f"\n鉂?瀹夎杩囩▼涓彂鐢熼敊璇? {e}")
            return False

def main():
    """涓诲嚱鏁?""
    installer = AutoInstaller()
    success = installer.run_installation()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()


