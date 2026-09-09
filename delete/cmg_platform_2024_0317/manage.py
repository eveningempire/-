"""
PHM骞冲彴鐨凢lask搴旂敤鍏ュ彛
"""
import argparse
import signal
import sys
import atexit
import logging
from app import create_app

# 璁剧疆鏃ュ織璁板綍
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = create_app()

def cleanup_resources():
    """鍦ㄥ簲鐢ㄩ€€鍑哄墠娓呯悊璧勬簮锛岄伩鍏峵kinter鐩稿叧寮傚父"""
    logger.info("姝ｅ湪娓呯悊搴旂敤璧勬簮...")
    # 灏濊瘯娓呯悊鍙兘瀛樺湪鐨則kinter璧勬簮
    try:
        import tkinter
        if 'Tk' in dir(tkinter) and tkinter._default_root:
            logger.info("娓呯悊tkinter璧勬簮")
            tkinter._default_root.destroy()
            tkinter._default_root = None
    except Exception as e:
        logger.error(f"娓呯悊tkinter璧勬簮鏃跺嚭閿? {e}")
    logger.info("璧勬簮娓呯悊瀹屾垚")

def signal_handler(sig, frame):
    """澶勭悊缁堟淇″彿"""
    logger.info(f"鎺ユ敹鍒颁俊鍙?{sig}锛屾鍦ㄥ叧闂簲鐢?..")
    cleanup_resources()
    sys.exit(0)

if __name__ == "__main__":
    # 娉ㄥ唽淇″彿澶勭悊鍣?
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 娉ㄥ唽閫€鍑烘椂鐨勬竻鐞嗗嚱鏁?
    atexit.register(cleanup_resources)
    
    parser = argparse.ArgumentParser(description="IP:Port Configuration")
    parser.add_argument("--addr", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8005)
    args = parser.parse_args()
    
    logger.info(f"鍚姩PHM骞冲彴锛岀洃鍚湴鍧€: {args.addr}:{args.port}")
    app.run(host=args.addr, port=args.port, debug=False)

