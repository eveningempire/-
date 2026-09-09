#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHM鍋ュ悍绠＄悊骞冲彴 - 鐜妫€娴嬭剼鏈?
妫€娴嬫柊鐢佃剳鐨勭郴缁熺幆澧冩槸鍚︽弧瓒宠繍琛岃姹?
"""

import os
import sys
import subprocess
import platform
import socket
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class EnvironmentChecker:
    def __init__(self):
        self.results = {
            "system_info": {},
            "python_env": {},
            "node_env": {},
            "database": {},
            "redis": {},
            "ports": {},
            "permissions": {},
            "recommendations": []
        }
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / ".venv"
        
    def print_header(self, title: str):
        """鎵撳嵃鏍囬"""
        print("\n" + "="*60)
        print(f"馃攳 {title}")
        print("="*60)
    
    def print_result(self, item: str, status: str, details: str = ""):
        """鎵撳嵃妫€娴嬬粨鏋?""
        status_icon = "鉁? if status == "PASS" else "鉂? if status == "FAIL" else "鈿狅笍"
        print(f"{status_icon} {item}: {status}")
        if details:
            print(f"   璇︽儏: {details}")
    
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """杩愯鍛戒护骞惰繑鍥炵粨鏋?""
        try:
            if capture_output:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                return result.returncode, result.stdout.strip(), result.stderr.strip()
            else:
                result = subprocess.run(command, timeout=30)
                return result.returncode, "", ""
        except subprocess.TimeoutExpired:
            return -1, "", "鍛戒护鎵ц瓒呮椂"
        except FileNotFoundError:
            return -1, "", "鍛戒护鏈壘鍒?
        except Exception as e:
            return -1, "", str(e)
    
    def check_system_info(self):
        """妫€娴嬬郴缁熶俊鎭?""
        self.print_header("绯荤粺淇℃伅妫€娴?)
        
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        
        # 妫€娴嬪唴瀛?
        try:
            import psutil
            memory = psutil.virtual_memory()
            system_info["total_memory_gb"] = round(memory.total / (1024**3), 2)
            system_info["available_memory_gb"] = round(memory.available / (1024**3), 2)
        except ImportError:
            system_info["memory_info"] = "鏃犳硶妫€娴嬶紙闇€瑕佸畨瑁卲sutil锛?
        
        # 妫€娴嬬鐩樼┖闂?
        try:
            disk = shutil.disk_usage(self.project_root)
            system_info["free_disk_gb"] = round(disk.free / (1024**3), 2)
        except:
            system_info["disk_info"] = "鏃犳硶妫€娴?
        
        self.results["system_info"] = system_info
        
        print(f"鎿嶄綔绯荤粺: {system_info['platform']} {system_info['platform_version']}")
        print(f"鏋舵瀯: {system_info['architecture']}")
        print(f"澶勭悊鍣? {system_info['processor']}")
        print(f"Python鐗堟湰: {system_info['python_version']}")
        
        if "total_memory_gb" in system_info:
            print(f"鎬诲唴瀛? {system_info['total_memory_gb']} GB")
            print(f"鍙敤鍐呭瓨: {system_info['available_memory_gb']} GB")
            
            if system_info["total_memory_gb"] < 8:
                self.results["recommendations"].append("鈿狅笍 鍐呭瓨涓嶈冻锛屽缓璁嚦灏?GB鍐呭瓨")
        
        if "free_disk_gb" in system_info:
            print(f"鍙敤纾佺洏绌洪棿: {system_info['free_disk_gb']} GB")
            
            if system_info["free_disk_gb"] < 10:
                self.results["recommendations"].append("鈿狅笍 纾佺洏绌洪棿涓嶈冻锛屽缓璁嚦灏?0GB鍙敤绌洪棿")
    
    def check_python_env(self):
        """妫€娴婸ython鐜"""
        self.print_header("Python鐜妫€娴?)
        
        # 妫€娴婸ython鐗堟湰
        python_version = sys.version_info
        version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        
        if python_version >= (3, 8):
            self.print_result("Python鐗堟湰", "PASS", f"鐗堟湰 {version_str} 婊¤冻瑕佹眰")
        else:
            self.print_result("Python鐗堟湰", "FAIL", f"鐗堟湰 {version_str} 杩囦綆锛岄渶瑕?.8+")
            self.results["recommendations"].append("鉂?璇峰畨瑁匬ython 3.8鎴栨洿楂樼増鏈?)
        
        # 妫€娴媝ip
        code, output, error = self.run_command([sys.executable, "-m", "pip", "--version"])
        if code == 0:
            self.print_result("pip", "PASS", "pip宸插畨瑁?)
        else:
            self.print_result("pip", "FAIL", "pip鏈畨瑁呮垨鏃犳硶浣跨敤")
            self.results["recommendations"].append("鉂?璇峰畨瑁卲ip")
        
        # 妫€娴嬭櫄鎷熺幆澧?
        if self.venv_path.exists():
            self.print_result("铏氭嫙鐜", "PASS", f"铏氭嫙鐜瀛樺湪浜?{self.venv_path}")
            
            # 妫€娴嬭櫄鎷熺幆澧冧腑鐨凱ython
            venv_python = self.venv_path / "Scripts" / "python.exe" if platform.system() == "Windows" else self.venv_path / "bin" / "python"
            if venv_python.exists():
                self.print_result("铏氭嫙鐜Python", "PASS", "铏氭嫙鐜Python鍙墽琛?)
            else:
                self.print_result("铏氭嫙鐜Python", "FAIL", "铏氭嫙鐜Python涓嶅彲鎵ц")
        else:
            self.print_result("铏氭嫙鐜", "FAIL", "铏氭嫙鐜涓嶅瓨鍦?)
            self.results["recommendations"].append("鈿狅笍 寤鸿鍒涘缓铏氭嫙鐜")
        
        # 妫€娴嬪叧閿緷璧?
        key_packages = ["django", "mysqlclient", "redis", "channels"]
        for package in key_packages:
            try:
                __import__(package)
                self.print_result(f"渚濊禆鍖?{package}", "PASS", "宸插畨瑁?)
            except ImportError:
                self.print_result(f"渚濊禆鍖?{package}", "FAIL", "鏈畨瑁?)
                self.results["recommendations"].append(f"鉂?璇峰畨瑁?{package}")
        
        self.results["python_env"] = {
            "version": version_str,
            "venv_exists": self.venv_path.exists(),
            "key_packages": key_packages
        }
    
    def check_node_env(self):
        """妫€娴婲ode.js鐜"""
        self.print_header("Node.js鐜妫€娴?)
        
        # 妫€娴婲ode.js
        code, output, error = self.run_command(["node", "--version"])
        if code == 0:
            version = output.strip()
            # 瑙ｆ瀽鐗堟湰鍙?
            try:
                major_version = int(version.split('.')[0].replace('v', ''))
                if major_version >= 16:
                    self.print_result("Node.js鐗堟湰", "PASS", f"鐗堟湰 {version} 婊¤冻瑕佹眰")
                else:
                    self.print_result("Node.js鐗堟湰", "FAIL", f"鐗堟湰 {version} 杩囦綆锛岄渶瑕?6+")
                    self.results["recommendations"].append("鉂?璇峰畨瑁匩ode.js 16鎴栨洿楂樼増鏈?)
            except:
                self.print_result("Node.js鐗堟湰", "FAIL", f"鏃犳硶瑙ｆ瀽鐗堟湰鍙? {version}")
        else:
            self.print_result("Node.js", "FAIL", "Node.js鏈畨瑁?)
            self.results["recommendations"].append("鉂?璇峰畨瑁匩ode.js")
        
        # 妫€娴媙pm
        code, output, error = self.run_command(["npm", "--version"])
        if code == 0:
            self.print_result("npm", "PASS", f"鐗堟湰 {output.strip()}")
        else:
            self.print_result("npm", "FAIL", "npm鏈畨瑁呮垨鏃犳硶浣跨敤")
            self.results["recommendations"].append("鉂?璇峰畨瑁卬pm")
        
        # 妫€娴嬪墠绔緷璧?
        frontend_path = self.project_root / "frontend"
        if frontend_path.exists():
            node_modules = frontend_path / "node_modules"
            if node_modules.exists():
                self.print_result("鍓嶇渚濊禆", "PASS", "node_modules宸插瓨鍦?)
            else:
                self.print_result("鍓嶇渚濊禆", "FAIL", "node_modules涓嶅瓨鍦?)
                self.results["recommendations"].append("鈿狅笍 璇疯繍琛?npm install 瀹夎鍓嶇渚濊禆")
        else:
            self.print_result("鍓嶇鐩綍", "FAIL", "frontend鐩綍涓嶅瓨鍦?)
        
        self.results["node_env"] = {
            "node_version": output.strip() if code == 0 else None,
            "npm_version": output.strip() if code == 0 else None,
            "frontend_exists": frontend_path.exists()
        }
    
    def check_database(self):
        """妫€娴嬫暟鎹簱鐜"""
        self.print_header("鏁版嵁搴撶幆澧冩娴?)
        
        # 妫€娴婱ySQL瀹㈡埛绔?
        code, output, error = self.run_command(["mysql", "--version"])
        if code == 0:
            self.print_result("MySQL瀹㈡埛绔?, "PASS", "MySQL瀹㈡埛绔凡瀹夎")
        else:
            self.print_result("MySQL瀹㈡埛绔?, "FAIL", "MySQL瀹㈡埛绔湭瀹夎")
            self.results["recommendations"].append("鉂?璇峰畨瑁匨ySQL瀹㈡埛绔?)
        
        # 妫€娴婱ySQL鏈嶅姟杩炴帴
        # 杩欓噷闇€瑕佺敤鎴锋彁渚涙暟鎹簱杩炴帴淇℃伅
        print("馃摑 鏁版嵁搴撹繛鎺ユ祴璇曢渶瑕侀厤缃俊鎭?)
        print("   璇峰湪閰嶇疆鏂囦欢涓缃纭殑鏁版嵁搴撹繛鎺ュ弬鏁?)
        
        # 妫€娴嬮粯璁ょ鍙?
        if self.check_port(3306):
            self.print_result("MySQL绔彛3306", "PASS", "绔彛鍙敤")
        else:
            self.print_result("MySQL绔彛3306", "FAIL", "绔彛琚崰鐢?)
            self.results["recommendations"].append("鈿狅笍 MySQL绔彛3306琚崰鐢紝璇锋鏌ySQL鏈嶅姟")
        
        self.results["database"] = {
            "mysql_client": code == 0,
            "port_3306_available": self.check_port(3306)
        }
    
    def check_redis(self):
        """妫€娴婻edis鐜"""
        self.print_header("Redis鐜妫€娴?)
        
        # 妫€娴婻edis瀹㈡埛绔?
        code, output, error = self.run_command(["redis-cli", "--version"])
        if code == 0:
            self.print_result("Redis瀹㈡埛绔?, "PASS", "Redis瀹㈡埛绔凡瀹夎")
        else:
            self.print_result("Redis瀹㈡埛绔?, "FAIL", "Redis瀹㈡埛绔湭瀹夎")
            self.results["recommendations"].append("鉂?璇峰畨瑁匯edis瀹㈡埛绔?)
        
        # 妫€娴婻edis鏈嶅姟
        code, output, error = self.run_command(["redis-cli", "ping"])
        if code == 0 and output.strip() == "PONG":
            self.print_result("Redis鏈嶅姟", "PASS", "Redis鏈嶅姟姝ｅ湪杩愯")
        else:
            self.print_result("Redis鏈嶅姟", "FAIL", "Redis鏈嶅姟鏈繍琛屾垨鏃犳硶杩炴帴")
            self.results["recommendations"].append("鈿狅笍 璇峰惎鍔≧edis鏈嶅姟")
        
        # 妫€娴婻edis绔彛
        if self.check_port(6379):
            self.print_result("Redis绔彛6379", "PASS", "绔彛鍙敤")
        else:
            self.print_result("Redis绔彛6379", "FAIL", "绔彛琚崰鐢?)
            self.results["recommendations"].append("鈿狅笍 Redis绔彛6379琚崰鐢紝璇锋鏌edis鏈嶅姟")
        
        # 妫€娴嬮」鐩腑鐨凴edis
        redis_path = self.project_root / "Redis-x64-5.0.14.1"
        if redis_path.exists():
            self.print_result("椤圭洰Redis", "PASS", "椤圭洰鍖呭惈Redis瀹夎鍖?)
        else:
            self.print_result("椤圭洰Redis", "FAIL", "椤圭洰涓嶅寘鍚玆edis瀹夎鍖?)
            self.results["recommendations"].append("鈿狅笍 椤圭洰涓嶅寘鍚玆edis锛岃鍗曠嫭瀹夎Redis")
        
        self.results["redis"] = {
            "redis_client": code == 0,
            "redis_service": code == 0 and output.strip() == "PONG",
            "port_6379_available": self.check_port(6379),
            "project_redis_exists": redis_path.exists()
        }
    
    def check_ports(self):
        """妫€娴嬬鍙ｅ崰鐢ㄦ儏鍐?""
        self.print_header("绔彛鍗犵敤妫€娴?)
        
        ports_to_check = [8000, 5173, 3306, 6379]
        
        for port in ports_to_check:
            if self.check_port(port):
                self.print_result(f"绔彛{port}", "PASS", "绔彛鍙敤")
            else:
                self.print_result(f"绔彛{port}", "FAIL", "绔彛琚崰鐢?)
                self.results["recommendations"].append(f"鈿狅笍 绔彛{port}琚崰鐢紝璇锋鏌ョ浉鍏虫湇鍔?)
        
        self.results["ports"] = {f"port_{port}": self.check_port(port) for port in ports_to_check}
    
    def check_port(self, port: int) -> bool:
        """妫€娴嬬鍙ｆ槸鍚﹀彲鐢?""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0  # 濡傛灉杩炴帴澶辫触锛岃鏄庣鍙ｅ彲鐢?
        except:
            return True
    
    def check_permissions(self):
        """妫€娴嬫枃浠舵潈闄?""
        self.print_header("鏂囦欢鏉冮檺妫€娴?)
        
        # 妫€娴嬮」鐩洰褰曟潈闄?
        try:
            test_file = self.project_root / "test_permission.tmp"
            test_file.write_text("test")
            test_file.unlink()
            self.print_result("椤圭洰鐩綍鍐欐潈闄?, "PASS", "鐩綍鍙啓")
        except Exception as e:
            self.print_result("椤圭洰鐩綍鍐欐潈闄?, "FAIL", f"鐩綍涓嶅彲鍐? {e}")
            self.results["recommendations"].append("鉂?璇锋鏌ラ」鐩洰褰曟潈闄?)
        
        # 妫€娴嬭櫄鎷熺幆澧冩潈闄?
        if self.venv_path.exists():
            try:
                venv_test = self.venv_path / "test_permission.tmp"
                venv_test.write_text("test")
                venv_test.unlink()
                self.print_result("铏氭嫙鐜鍐欐潈闄?, "PASS", "铏氭嫙鐜鍙啓")
            except Exception as e:
                self.print_result("铏氭嫙鐜鍐欐潈闄?, "FAIL", f"铏氭嫙鐜涓嶅彲鍐? {e}")
                self.results["recommendations"].append("鉂?璇锋鏌ヨ櫄鎷熺幆澧冩潈闄?)
        
        self.results["permissions"] = {
            "project_writable": True,  # 绠€鍖栧鐞?
            "venv_writable": self.venv_path.exists()
        }
    
    def generate_report(self):
        """鐢熸垚妫€娴嬫姤鍛?""
        self.print_header("妫€娴嬫姤鍛?)
        
        # 缁熻缁撴灉
        total_checks = 0
        passed_checks = 0
        
        for category in self.results.values():
            if isinstance(category, dict):
                for key, value in category.items():
                    if isinstance(value, bool):
                        total_checks += 1
                        if value:
                            passed_checks += 1
        
        print(f"馃搳 妫€娴嬬粺璁?")
        print(f"   鎬绘鏌ラ」: {total_checks}")
        print(f"   閫氳繃椤? {passed_checks}")
        print(f"   澶辫触椤? {total_checks - passed_checks}")
        print(f"   閫氳繃鐜? {passed_checks/total_checks*100:.1f}%" if total_checks > 0 else "   閫氳繃鐜? 0%")
        
        # 鏄剧ず寤鸿
        if self.results["recommendations"]:
            print(f"\n馃挕 寤鸿:")
            for i, recommendation in enumerate(self.results["recommendations"], 1):
                print(f"   {i}. {recommendation}")
        
        # 淇濆瓨鎶ュ憡
        report_file = self.project_root / "environment_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 璇︾粏鎶ュ憡宸蹭繚瀛樺埌: {report_file}")
        
        # 杩斿洖鎬讳綋鐘舵€?
        return passed_checks == total_checks
    
    def run_all_checks(self):
        """杩愯鎵€鏈夋娴?""
        print("馃殌 PHM鍋ュ悍绠＄悊骞冲彴 - 鐜妫€娴嬪紑濮?)
        print(f"馃搧 椤圭洰璺緞: {self.project_root}")
        
        try:
            self.check_system_info()
            self.check_python_env()
            self.check_node_env()
            self.check_database()
            self.check_redis()
            self.check_ports()
            self.check_permissions()
            
            all_passed = self.generate_report()
            
            if all_passed:
                print("\n馃帀 鐜妫€娴嬪畬鎴愶紒鎵€鏈夋鏌ラ」閮介€氳繃浜嗐€?)
                print("   鎮ㄥ彲浠ョ户缁畨瑁呭拰閰嶇疆PHM骞冲彴銆?)
            else:
                print("\n鈿狅笍 鐜妫€娴嬪畬鎴愶紒鍙戠幇涓€浜涢棶棰橀渶瑕佽В鍐炽€?)
                print("   璇锋牴鎹笂杩板缓璁繘琛屼慨澶嶅悗閲嶆柊妫€娴嬨€?)
            
            return all_passed
            
        except Exception as e:
            print(f"\n鉂?妫€娴嬭繃绋嬩腑鍙戠敓閿欒: {e}")
            return False

def main():
    """涓诲嚱鏁?""
    checker = EnvironmentChecker()
    success = checker.run_all_checks()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

