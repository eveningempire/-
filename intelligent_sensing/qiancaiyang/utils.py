import json
import numpy as np


def json_serialize_with_ndarray(obj, indent: int = 4) -> str:
    """
    序列化包含 numpy 数组的任意 Python 对象为 JSON 字符串
    核心：自动将 ndarray 转为列表（tolist()），兼容字典、列表、元组等嵌套结构

    Args:
        obj: 待序列化的对象（可包含 ndarray、字典、列表、基本类型等）
        indent: JSON 缩进，美化输出（默认4）

    Returns:
        str: 序列化后的 JSON 字符串

    Raises:
        TypeError: 遇到无法序列化的类型（非 ndarray/基础类型/容器类型）
    """

    def _serialize_handler(item):
        # 处理 numpy 数组：转为列表
        if isinstance(item, np.ndarray):
            return item.tolist()
        # 处理 numpy 数值类型（如 np.int64、np.float32）：转为 Python 原生类型
        elif isinstance(item, (np.integer, np.floating)):
            return item.item()
        # 处理元组：转为列表（JSON 不支持元组，统一转列表）
        elif isinstance(item, tuple):
            return list(item)
        # 处理字典：递归遍历键值对
        elif isinstance(item, dict):
            return {k: _serialize_handler(v) for k, v in item.items()}
        # 处理列表/集合：递归遍历元素
        elif isinstance(item, (list, set)):
            return [_serialize_handler(elem) for elem in item]
        # 处理 None/布尔/字符串/原生数值：直接返回
        elif item is None or isinstance(item, (bool, str, int, float)):
            return item
        # 其他不支持的类型：抛出异常
        else:
            raise TypeError(f"无法序列化的类型: {type(item)} (值: {item})")

    # 调用 json.dumps，使用自定义处理器
    return json.dumps(obj, default=_serialize_handler, indent=indent, ensure_ascii=False)
