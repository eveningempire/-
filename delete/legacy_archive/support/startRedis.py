import os
try:
    os.system('.\\support\\Redis5\\redis-server.exe .\\support\\Redis5\\redis.windows.conf')
    print("[INFO] Seemingly succeed to connecting Redis which is now to be confirmed.")
except Exception as e:
    print(f"[WARN] Failed to connect Redis. Please open it by double-click \'.\\support\\Redis5\\redis-server.exe\'\n\t[Traceback] {repr(e)}")