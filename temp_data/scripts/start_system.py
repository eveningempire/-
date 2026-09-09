#!/usr/bin/env python
"""
PHM鍋ュ悍绠＄悊骞冲彴 - 绯荤粺鍚姩鑴氭湰
鐢ㄤ簬蹇€熷惎鍔ㄦ墍鏈夋湇鍔?
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class SystemStarter:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def print_header(self, title):
        """鎵撳嵃鏍囬"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def check_service(self, service_name, check_command):
        """妫€鏌ユ湇鍔＄姸鎬?""
        try:
            result = subprocess.run(check_command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"鉁?{service_name} 姝ｅ湪杩愯")
                return True
            else:
                print(f"鉂?{service_name} 鏈繍琛?)
                return False
        except Exception as e:
            print(f"鉂?妫€鏌?{service_name} 澶辫触: {e}")
            return False
    
    def start_backend(self):
        """鍚姩鍚庣鏈嶅姟"""
        print("馃殌 鍚姩Django鍚庣鏈嶅姟...")
        try:
            # 婵€娲昏櫄鎷熺幆澧冨苟鍚姩Django
            if os.name == 'nt':  # Windows
                cmd = ['.venv\\Scripts\\python.exe', 'manage.py', 'runserver', '0.0.0.0:8000']
            else:  # Linux/macOS
                cmd = ['.venv/bin/python', 'manage.py', 'runserver', '0.0.0.0:8000']
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(('Django鍚庣', process))
            print("鉁?Django鍚庣鏈嶅姟鍚姩涓?..")
            return True
        except Exception as e:
            print(f"鉂?鍚姩Django鍚庣澶辫触: {e}")
            return False
    
    def start_frontend(self):
        """鍚姩鍓嶇鏈嶅姟"""
        print("馃殌 鍚姩Vue.js鍓嶇鏈嶅姟...")
        try:
            # 鍒囨崲鍒板墠绔洰褰曞苟鍚姩寮€鍙戞湇鍔″櫒
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print("鉂?鍓嶇鐩綍涓嶅瓨鍦?)
                return False
            
            os.chdir(frontend_dir)
            process = subprocess.Popen(['npm', 'run', 'dev'], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            os.chdir("..")
            
            self.processes.append(('Vue.js鍓嶇', process))
            print("鉁?Vue.js鍓嶇鏈嶅姟鍚姩涓?..")
            return True
        except Exception as e:
            print(f"鉂?鍚姩Vue.js鍓嶇澶辫触: {e}")
            return False
    
    def start_celery(self):
        """鍚姩Celery宸ヤ綔杩涚▼"""
        print("馃殌 鍚姩Celery宸ヤ綔杩涚▼...")
        try:
            if os.name == 'nt':  # Windows
                cmd = ['.venv\\Scripts\\celery.exe', '-A', 'phm_backend', 'worker', '--loglevel=info']
            else:  # Linux/macOS
                cmd = ['.venv/bin/celery', '-A', 'phm_backend', 'worker', '--loglevel=info']
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(('Celery宸ヤ綔杩涚▼', process))
            print("鉁?Celery宸ヤ綔杩涚▼鍚姩涓?..")
            return True
        except Exception as e:
            print(f"鉂?鍚姩Celery澶辫触: {e}")
            return False
    
    def check_dependencies(self):
        """妫€鏌ヤ緷璧栨湇鍔?""
        print("馃攳 妫€鏌ヤ緷璧栨湇鍔?..")
        
        # 妫€鏌ySQL
        mysql_running = self.check_service("MySQL", "mysql -u root -p -e 'SELECT 1' 2>/dev/null")
        if not mysql_running:
            print("鈿狅笍  MySQL鏈繍琛岋紝璇锋墜鍔ㄥ惎鍔∕ySQL鏈嶅姟")
        
        # 妫€鏌edis
        redis_running = self.check_service("Redis", "redis-cli ping 2>/dev/null")
        if not redis_running:
            print("鈿狅笍  Redis鏈繍琛岋紝璇锋墜鍔ㄥ惎鍔≧edis鏈嶅姟")
        
        return mysql_running and redis_running
    
    def monitor_processes(self):
        """鐩戞帶杩涚▼鐘舵€?""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"鈿狅笍  {name} 宸插仠姝㈣繍琛?)
            time.sleep(5)
    
    def signal_handler(self, signum, frame):
        """淇″彿澶勭悊鍣?""
        print("\n馃洃 鏀跺埌鍋滄淇″彿锛屾鍦ㄥ叧闂湇鍔?..")
        self.running = False
        self.stop_all()
        sys.exit(0)
    
    def stop_all(self):
        """鍋滄鎵€鏈夋湇鍔?""
        print("馃洃 鍋滄鎵€鏈夋湇鍔?..")
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"鉁?{name} 宸插仠姝?)
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"鈿狅笍  {name} 寮哄埗鍋滄")
            except Exception as e:
                print(f"鉂?鍋滄 {name} 澶辫触: {e}")
    
    def print_status(self):
        """鎵撳嵃鏈嶅姟鐘舵€?""
        print("\n馃搳 鏈嶅姟鐘舵€?")
        print("-" * 40)
        for name, process in self.processes:
            if process.poll() is None:
                print(f"鉁?{name}: 杩愯涓?(PID: {process.pid})")
            else:
                print(f"鉂?{name}: 宸插仠姝?)
    
    def print_urls(self):
        """鎵撳嵃璁块棶鍦板潃"""
        print("\n馃寪 璁块棶鍦板潃:")
        print("-" * 40)
        print("鍓嶇鐣岄潰: http://localhost:3000")
        print("鍚庣API:  http://localhost:8000/api/v1/")
        print("绠＄悊鍚庡彴: http://localhost:8000/admin/")
        print("API鏂囨。:  http://localhost:8000/api/v1/")
    
    def run(self):
        """杩愯鍚姩绋嬪簭"""
        self.print_header("PHM鍋ュ悍绠＄悊骞冲彴 - 绯荤粺鍚姩")
        
        # 妫€鏌ュ綋鍓嶇洰褰?
        if not os.path.exists("manage.py"):
            print("鉂?璇峰湪椤圭洰鏍圭洰褰曡繍琛屾鑴氭湰")
            return
        
        # 娉ㄥ唽淇″彿澶勭悊鍣?
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 妫€鏌ヤ緷璧栨湇鍔?
        if not self.check_dependencies():
            print("鈿狅笍  渚濊禆鏈嶅姟妫€鏌ュけ璐ワ紝浣嗙户缁惎鍔?..")
        
        # 鍚姩鏈嶅姟
        services_started = 0
        
        if self.start_backend():
            services_started += 1
        
        if self.start_frontend():
            services_started += 1
        
        if self.start_celery():
            services_started += 1
        
        if services_started == 0:
            print("鉂?娌℃湁鏈嶅姟鎴愬姛鍚姩")
            return
        
        # 鍚姩鐩戞帶绾跨▼
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # 绛夊緟鏈嶅姟鍚姩
        print("\n鈴?绛夊緟鏈嶅姟鍚姩...")
        time.sleep(10)
        
        # 鎵撳嵃鐘舵€佸拰鍦板潃
        self.print_status()
        self.print_urls()
        
        print("\n馃帀 绯荤粺鍚姩瀹屾垚锛?)
        print("鎸?Ctrl+C 鍋滄鎵€鏈夋湇鍔?)
        
        # 淇濇寔杩愯
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()

def main():
    """涓诲嚱鏁?""
    starter = SystemStarter()
    starter.run()

if __name__ == "__main__":
    main()

