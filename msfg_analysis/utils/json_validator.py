"""
MSFG 图JSON结构校验与规范化工具

用于在后端保存前快速校验用户上传/编辑后的多信号流图结构：
- 检查 SystemData 列表结构
- 检查 nodes/edges 基本字段与引用一致性
- 识别 test/fault/system 节点并统计
- 返回规范化后的结构与错误列表
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _ensure_list_system_data(struct_raw: Any) -> List[Dict[str, Any]]:
    if isinstance(struct_raw, list):
        return struct_raw
    if isinstance(struct_raw, dict) and 'SystemData' in struct_raw:
        sd = struct_raw.get('SystemData')
        return sd if isinstance(sd, list) else []
    # 兜底：包装为单个系统
    if isinstance(struct_raw, dict):
        return [{
            'system_id': struct_raw.get('system_id', 1),
            'parent_id': struct_raw.get('parent_id'),
            'name': struct_raw.get('name', 'root'),
            'data': {
                'nodes': struct_raw.get('nodes', []),
                'edges': struct_raw.get('edges', []),
            }
        }]
    return []


def validate_msfg_graph(struct_raw: Any) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    """
    校验MSFG图结构。

    Returns:
        (is_valid, errors, normalized_system_data)
    """
    errors: List[str] = []
    system_list = _ensure_list_system_data(struct_raw)

    if not system_list:
        errors.append('SystemData 为空或格式不正确')
        return False, errors, []

    # 基本字段检查与引用一致性
    global_has_test = False
    global_has_fault = False
    for i, sys_item in enumerate(system_list):
        data = (sys_item or {}).get('data') or {}
        nodes = data.get('nodes') or []
        edges = data.get('edges') or []

        # 节点唯一性与必要字段
        node_ids: set[str] = set()
        local_has_test = False
        local_has_fault = False
        for n in nodes:
            nid = str(n.get('id') or '').strip()
            if not nid:
                errors.append(f'系统#{i}: 存在缺少id的节点')
                continue
            if nid in node_ids:
                errors.append(f'系统#{i}: 节点ID重复: {nid}')
            node_ids.add(nid)

            # 名称字段准备
            txt = (n.get('text') or {}).get('value')
            name = txt or n.get('name') or (n.get('properties') or {}).get('tableName')
            if not name:
                errors.append(f'系统#{i}: 节点 {nid} 缺少名称')

            ntype = str((n.get('type') or '')).lower()
            if 'test' in ntype:
                local_has_test = True
                global_has_test = True
            if 'fault' in ntype:
                local_has_fault = True
                global_has_fault = True

        # 边引用检查
        for e in edges:
            sid = str((e.get('sourceNodeId') or e.get('source') or '')).strip()
            tid = str((e.get('targetNodeId') or e.get('target') or '')).strip()
            if not sid or not tid:
                errors.append(f'系统#{i}: 边缺少source/target')
                continue
            if sid not in node_ids or tid not in node_ids:
                errors.append(f'系统#{i}: 边引用不存在的节点: {sid}->{tid}')

        # 对单个系统不强制必须同时存在 test 和 fault，避免跨层级设计被误判。
        # 只在全局范围内做至少存在一个 test 和一个 fault 的校验（见下方）。

    # 全局范围：至少存在一个测试点和一个故障点
    if not global_has_test:
        errors.append('未发现任何测试点(test-node)节点')
    if not global_has_fault:
        errors.append('未发现任何故障(fault-node)节点')

    is_valid = len(errors) == 0
    return is_valid, errors, system_list


