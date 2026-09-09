#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复/规范化 MSFG JSON 文件以符合平台要求：
- 确保 SystemData 为列表，包含 root 与 data/nodes/edges 结构
- 规范节点：补齐 text.value；name 不存在时用 text.value 或 properties.tableName 填充
- 规范边：补齐 sourceNodeId/targetNodeId（从 source/target 或 *_AnchorId 推断），清除无效引用
- 全局校验至少存在一个 test-node 和一个 fault-node；若缺失可选地自动补齐占位
- 输出 fixed 文件，避免覆盖原文件

用法：
  python scripts/msfg_fix_json.py input.json -o output.json [--autofill]
"""

from __future__ import annotations

import json
import argparse
from typing import Any, Dict, List, Tuple


def _ensure_system_list(struct_raw: Any) -> List[Dict[str, Any]]:
    if isinstance(struct_raw, dict) and 'SystemData' in struct_raw:
        sd = struct_raw.get('SystemData')
        return sd if isinstance(sd, list) else []
    if isinstance(struct_raw, list):
        return struct_raw
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


def _normalize_system_headers(systems: List[Dict[str, Any]]) -> None:
    # 确保 system_id/parent_id/name 存在；第一个为 root
    if not systems:
        return
    used_ids = set()
    for idx, sys_item in enumerate(systems):
        if 'system_id' not in sys_item or not isinstance(sys_item['system_id'], int):
            # 简单分配一个未用ID
            cand = idx + 1
            while cand in used_ids:
                cand += 1
            sys_item['system_id'] = cand
        used_ids.add(sys_item['system_id'])
        if 'parent_id' not in sys_item:
            sys_item['parent_id'] = None if idx == 0 else systems[0]['system_id']
        if not sys_item.get('name'):
            sys_item['name'] = 'root' if idx == 0 else f"子系统{sys_item['system_id']}"
        if 'data' not in sys_item or not isinstance(sys_item['data'], dict):
            sys_item['data'] = {}
        sys_item['data'].setdefault('nodes', [])
        sys_item['data'].setdefault('edges', [])


def _node_display_name(node: Dict[str, Any]) -> str:
    text = (node.get('text') or {}).get('value')
    if isinstance(text, str) and text.strip():
        return text.strip()
    name = node.get('name')
    if isinstance(name, str) and name.strip():
        return name.strip()
    tbn = (node.get('properties') or {}).get('tableName')
    if isinstance(tbn, str) and tbn.strip():
        return tbn.strip()
    return str(node.get('id') or '')


def _normalize_nodes(nodes: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], int, int]:
    node_by_id: Dict[str, Dict[str, Any]] = {}
    test_count = 0
    fault_count = 0
    for node in nodes:
        nid = str(node.get('id') or '').strip()
        if not nid:
            # 跳过无ID节点
            continue
        # text/value
        node.setdefault('text', {})
        if not isinstance(node['text'], dict):
            node['text'] = {}
        if not node['text'].get('value') or not str(node['text'].get('value')).strip():
            node['text']['value'] = _node_display_name(node) or nid
        # 统计类型
        ntype = str((node.get('type') or '')).lower()
        if 'test' in ntype:
            test_count += 1
        if 'fault' in ntype:
            fault_count += 1
        node_by_id[nid] = node
    return node_by_id, test_count, fault_count


def _extract_node_id_from_anchor(anchor_id: str) -> str | None:
    # 形如: "<node_id>_1_left" => 取 '_' 之前部分
    try:
        if not anchor_id:
            return None
        return str(anchor_id).split('_')[0]
    except Exception:
        return None


def _normalize_edges(edges: List[Dict[str, Any]], node_by_id: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    fixed: List[Dict[str, Any]] = []
    for e in edges:
        sid = e.get('sourceNodeId') or e.get('source')
        tid = e.get('targetNodeId') or e.get('target')
        # 尝试从 anchor 推断
        if not sid:
            sid = _extract_node_id_from_anchor(e.get('sourceAnchorId'))
            if sid:
                e['sourceNodeId'] = sid
        if not tid:
            tid = _extract_node_id_from_anchor(e.get('targetAnchorId'))
            if tid:
                e['targetNodeId'] = tid
        # 仍无效则跳过
        if not sid or not tid:
            continue
        sid = str(sid)
        tid = str(tid)
        if sid not in node_by_id or tid not in node_by_id:
            # 删除指向不存在节点的边
            continue
        # 统一保存为 sourceNodeId/targetNodeId
        e['sourceNodeId'] = sid
        e['targetNodeId'] = tid
        fixed.append(e)
    return fixed


def fix_msfg_json(doc: Dict[str, Any], autofill: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    systems = _ensure_system_list(doc)
    _normalize_system_headers(systems)

    global_test = 0
    global_fault = 0
    total_edges_before = 0
    total_edges_after = 0

    for sys_item in systems:
        data = sys_item['data']
        nodes = data.get('nodes') or []
        edges = data.get('edges') or []
        total_edges_before += len(edges)

        node_by_id, tcnt, fcnt = _normalize_nodes(nodes)
        global_test += tcnt
        global_fault += fcnt

        fixed_edges = _normalize_edges(edges, node_by_id)
        data['edges'] = fixed_edges
        total_edges_after += len(fixed_edges)

    # 全局缺失时可选自动补齐
    if autofill and global_test == 0 and systems:
        root = systems[0]
        nodes = root['data']['nodes']
        # 添加占位测点
        placeholder = {
            'id': 'auto_test_1',
            'type': 'test-node',
            'x': 0,
            'y': 0,
            'properties': {'typeColor': '#eea2a4'},
            'text': {'value': '占位测点_1'},
        }
        nodes.append(placeholder)
        global_test = 1
        # 若存在故障节点，连一条边
        fault_ids = [n.get('id') for n in nodes if 'fault' in str(n.get('type') or '').lower()]
        if fault_ids:
            root['data']['edges'].append({
                'id': 'auto_edge_1',
                'type': 'polyline',
                'sourceNodeId': placeholder['id'],
                'targetNodeId': fault_ids[0],
            })
            total_edges_after += 1

    fixed_doc = {'SystemData': systems, 'currentSystemId': systems[0]['system_id'] if systems else 1}
    summary = {
        'systems': len(systems),
        'test_nodes': global_test,
        'fault_nodes': global_fault,
        'edges_before': total_edges_before,
        'edges_after': total_edges_after,
    }
    return fixed_doc, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='输入 JSON 文件路径')
    ap.add_argument('-o', '--output', help='输出 JSON 文件路径', default=None)
    ap.add_argument('--autofill', action='store_true', help='当缺失 test/fault 时自动补齐占位元素')
    args = ap.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    fixed_doc, summary = fix_msfg_json(doc, autofill=args.autofill)
    out_path = args.output or args.input.replace('.json', '_fixed.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_doc, f, ensure_ascii=False, indent=2)

    print('[MSFG JSON 修复完成]')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f'输出文件: {out_path}')


if __name__ == '__main__':
    main()


