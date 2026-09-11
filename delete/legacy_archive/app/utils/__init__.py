"""
工具函数包
"""
import uuid
import time

def get_uuid(kw=""):
    """生成基于时间的UUID"""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kw}#%.7f" % time.time()))
