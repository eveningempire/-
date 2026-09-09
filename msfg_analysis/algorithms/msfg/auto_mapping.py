#!/usr/bin/env python
"""
自动从MSFG提取测点-部件映射关系
改进版本：支持多层路径搜索、正确的权重处理、更好的节点分类
"""

import logging
from typing import Dict, List, Tuple, Any, Set, Optional
import numpy as np
from collections import defaultdict, deque
from django.db import transaction

logger = logging.getLogger(__name__)

class MSFGAutoMapping:
    """MSFG自动映射提取器 - 改进版"""
    
    def __init__(self, msfg_data: Dict[str, Any]):
        """
        初始化MSFG自动映射提取器
        
        Args:
            msfg_data: MSFG的原始图数据
        """
        self.msfg_data = msfg_data
        self.nodes = msfg_data.get('nodes', [])
        self.edges = msfg_data.get('edges', [])
        
        # 构建节点信息映射
        self.node_info = {}  # node_id -> node_info
        self.node_types = {}  # node_id -> classified_type
        
        # 构建完整的邻接表（支持多层遍历）
        self.adjacency_graph = defaultdict(list)  # source_id -> [(target_id, weight), ...]
        self.reverse_graph = defaultdict(list)    # target_id -> [(source_id, weight), ...]
        
        self._build_node_info()
        self._classify_nodes()
        self._build_adjacency_graph()
    
    def _build_node_info(self):
        """构建节点信息映射"""
        for node in self.nodes:
            node_id = node.get('id', '')
            if node_id:
                self.node_info[node_id] = {
                    'id': node_id,
                    'name': self._get_node_name(node),
                    'type': node.get('type', ''),
                    'raw_data': node
                }
    
    def _classify_nodes(self):
        """改进的节点分类 - 更灵活的节点类型识别"""
        for node_id, node_info in self.node_info.items():
            node_type = str(node_info['type']).lower()
            node_name = node_info['name'].lower()
            
            # 多重判断逻辑，减少对单一标注的依赖
            classified_type = 'unknown'
            
            # 测试点/传感器识别
            test_indicators = ['test', 'sensor', 'measure', 'monitor', 'detect', '测试', '传感', '监测']
            if any(indicator in node_type or indicator in node_name for indicator in test_indicators):
                classified_type = 'testpoint'
            # 故障识别
            else:
                fault_indicators = ['fault', 'failure', 'error', 'fail', 'malfunction', '故障', '失效', '错误']
                if any(indicator in node_type or indicator in node_name for indicator in fault_indicators):
                    classified_type = 'fault'
                # 部件/系统识别
                else:
                    component_indicators = ['system', 'component', 'module', 'unit', 'assembly', '系统', '部件', '模块', '组件']
                    if any(indicator in node_type or indicator in node_name for indicator in component_indicators):
                        # 排除根节点
                        if 'root' not in node_type and 'root' not in node_name:
                            classified_type = 'component'
            
            self.node_types[node_id] = classified_type
        
        # 统计分类结果
        type_counts = defaultdict(int)
        for node_type in self.node_types.values():
            type_counts[node_type] += 1
        
        logger.info(f"节点分类完成: {dict(type_counts)}")
    
    def _build_adjacency_graph(self):
        """构建完整的邻接图"""
        for edge in self.edges:
            # 兼容不同的边字段格式：支持 sourceNodeId/targetNodeId 和 source/target
            source_id = edge.get('sourceNodeId') or edge.get('source', '')
            target_id = edge.get('targetNodeId') or edge.get('target', '')
            weight = float(edge.get('weight', 1.0))
            
            if source_id and target_id and source_id in self.node_info and target_id in self.node_info:
                self.adjacency_graph[source_id].append((target_id, weight))
                self.reverse_graph[target_id].append((source_id, weight))
        
        logger.info(f"构建邻接图完成: {len(self.adjacency_graph)} 个源节点, {len(self.edges)} 条边")
        
        # 检查图的完整性
        self._check_graph_integrity()
    
    def _get_node_name(self, node: Dict[str, Any]) -> str:
        """获取节点名称"""
        # 尝试多种方式获取节点名称，增加 properties.tableName 的兜底支持
        name = (
            (node.get('text', {}) or {}).get('value') or
            node.get('name') or
            (node.get('properties', {}) or {}).get('tableName') or
            node.get('id')
        )
        return str(name).strip() if name else ''
    
    def _find_node_name(self, node_id: str, node_list: List[Tuple[str, str]]) -> str:
        """根据节点ID查找节点名称"""
        for nid, name in node_list:
            if nid == node_id:
                return name
        return ''
    
    def _find_all_paths(self, start_node_id: str, target_type: str, max_depth: int = 10) -> List[Tuple[List[str], float]]:
        """
        使用BFS查找从起始节点到目标类型节点的所有路径
        
        Args:
            start_node_id: 起始节点ID
            target_type: 目标节点类型 ('testpoint', 'fault', 'component')
            max_depth: 最大搜索深度，防止无限循环
            
        Returns:
            List[Tuple[List[str], float]]: [(路径节点ID列表, 路径权重), ...]
        """
        if start_node_id not in self.node_info:
            return []
        
        paths = []
        queue = deque([(start_node_id, [start_node_id], 1.0, set([start_node_id]))])  # (当前节点, 路径, 累积权重, 访问过的节点)
        
        while queue:
            current_node, path, path_weight, visited = queue.popleft()
            
            # 检查深度限制
            if len(path) > max_depth:
                continue
            
            # 检查是否到达目标类型
            if self.node_types.get(current_node) == target_type and len(path) > 1:  # 排除起始节点自己
                paths.append((path.copy(), path_weight))
                continue  # 找到目标，但继续搜索更长的路径
            
            # 扩展到邻居节点
            for neighbor_id, edge_weight in self.adjacency_graph.get(current_node, []):
                if neighbor_id not in visited:  # 防止循环
                    new_visited = visited.copy()
                    new_visited.add(neighbor_id)
                    new_path = path + [neighbor_id]
                    new_weight = path_weight * edge_weight  # 串行路径权重相乘
                    
                    queue.append((neighbor_id, new_path, new_weight, new_visited))
        
        return paths
    
    def _combine_parallel_weights(self, weights: List[float], method: str = 'probabilistic') -> float:
        """
        组合并行路径的权重
        
        Args:
            weights: 权重列表
            method: 组合方法 ('sum', 'max', 'probabilistic')
        
        Returns:
            组合后的权重
        """
        if not weights:
            return 0.0
        
        if method == 'sum':
            return sum(weights)
        elif method == 'max':
            return max(weights)
        elif method == 'probabilistic':
            # 概率组合：P(A or B) = P(A) + P(B) - P(A) * P(B)
            result = 0.0
            for weight in weights:
                result = result + weight - result * weight
            return result
        else:
            return sum(weights)  # 默认求和
    
    def _validate_path(self, path: List[str]) -> bool:
        """
        验证路径的有效性
        
        Args:
            path: 节点ID路径
        
        Returns:
            bool: 路径是否有效
        """
        if len(path) < 2:
            return False
        
        # 检查路径中的所有节点是否存在
        for node_id in path:
            if node_id not in self.node_info:
                logger.warning(f"路径中包含不存在的节点: {node_id}")
                return False
        
        # 检查路径中的边是否存在
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]
            
            # 检查是否存在从source_id到target_id的边
            found_edge = False
            for neighbor_id, _ in self.adjacency_graph.get(source_id, []):
                if neighbor_id == target_id:
                    found_edge = True
                    break
            
            if not found_edge:
                logger.warning(f"路径中不存在边: {source_id} -> {target_id}")
                return False
        
        return True
    
    def _detect_cycles(self) -> List[List[str]]:
        """
        检测图中的循环
        
        Returns:
            List[List[str]]: 发现的循环路径列表
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]):
            if node_id in rec_stack:
                # 找到循环
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                cycles.append(cycle)
                return
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for neighbor_id, _ in self.adjacency_graph.get(node_id, []):
                dfs(neighbor_id, path.copy())
            
            rec_stack.remove(node_id)
        
        for node_id in self.node_info:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def _check_graph_integrity(self):
        """检查图的完整性"""
        # 检测循环
        cycles = self._detect_cycles()
        if cycles:
            logger.warning(f"检测到 {len(cycles)} 个循环引用:")
            for i, cycle in enumerate(cycles[:5]):  # 只显示前5个循环
                cycle_names = [self.node_info.get(node_id, {}).get('name', node_id) for node_id in cycle]
                logger.warning(f"  循环 {i+1}: {' -> '.join(cycle_names)}")
        
        # 检查孤立节点
        isolated_nodes = []
        for node_id in self.node_info:
            has_incoming = node_id in self.reverse_graph and self.reverse_graph[node_id]
            has_outgoing = node_id in self.adjacency_graph and self.adjacency_graph[node_id]
            if not has_incoming and not has_outgoing:
                isolated_nodes.append(node_id)
        
        if isolated_nodes:
            logger.warning(f"发现 {len(isolated_nodes)} 个孤立节点:")
            for node_id in isolated_nodes[:10]:  # 只显示前10个
                node_name = self.node_info[node_id]['name']
                logger.warning(f"  孤立节点: {node_name} ({node_id})")
        
        # 检查连通性
        testpoint_nodes = [node_id for node_id, node_type in self.node_types.items() if node_type == 'testpoint']
        component_nodes = [node_id for node_id, node_type in self.node_types.items() if node_type == 'component']
        
        disconnected_tests = []
        for test_id in testpoint_nodes:
            component_paths = self._find_all_paths(test_id, 'component', max_depth=15)
            if not component_paths:
                disconnected_tests.append(test_id)
        
        if disconnected_tests:
            logger.warning(f"发现 {len(disconnected_tests)} 个测试点无法到达任何部件:")
            for test_id in disconnected_tests[:10]:  # 只显示前10个
                test_name = self.node_info[test_id]['name']
                logger.warning(f"  断连测试点: {test_name} ({test_id})")
    
    def extract_test_component_mappings(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        改进的测试点→部件映射关系提取
        支持多层路径搜索和正确的权重处理
            
        Returns:
            Dict[str, List[Tuple[str, float]]]: 测试点名称 -> [(部件名称, 影响强度), ...]
        """
        mappings = {}
        
        # 获取所有测试点节点
        testpoint_nodes = [node_id for node_id, node_type in self.node_types.items() if node_type == 'testpoint']
        
        logger.info(f"开始提取 {len(testpoint_nodes)} 个测试点的映射关系")
        
        for testpoint_id in testpoint_nodes:
            testpoint_name = self.node_info[testpoint_id]['name']
            
            # 查找从该测试点到所有部件的路径
            component_paths = self._find_all_paths(testpoint_id, 'component', max_depth=15)
            
            if not component_paths:
                logger.debug(f"测试点 {testpoint_name} 没有找到到部件的路径")
                mappings[testpoint_name] = []
                continue
            
            # 按目标部件分组路径
            component_influences = defaultdict(list)  # component_name -> [weights]
            
            for path, path_weight in component_paths:
                if len(path) < 2:  # 路径太短，跳过
                    continue
                
                # 验证路径有效性
                if not self._validate_path(path):
                    logger.debug(f"跳过无效路径: {path}")
                    continue
                
                target_component_id = path[-1]  # 路径的最后一个节点是目标部件
                target_component_name = self.node_info[target_component_id]['name']
                
                component_influences[target_component_name].append(path_weight)
            
            # 对每个部件的多条路径进行权重组合
            final_influences = {}
            for component_name, path_weights in component_influences.items():
                # 使用概率组合方法处理并行路径
                combined_weight = self._combine_parallel_weights(path_weights, method='probabilistic')
                final_influences[component_name] = combined_weight
            
            # 转换为列表格式并排序
            if final_influences:
                mappings[testpoint_name] = [
                    (comp_name, strength) 
                    for comp_name, strength in final_influences.items()
                    if strength > 1e-6  # 过滤掉极小的权重
                ]
                # 按影响强度排序
                mappings[testpoint_name].sort(key=lambda x: x[1], reverse=True)
            else:
                mappings[testpoint_name] = []
            
            logger.debug(f"测试点 {testpoint_name}: 找到 {len(component_paths)} 条路径, "
                        f"映射到 {len(mappings[testpoint_name])} 个部件")
        
        logger.info(f"提取映射关系完成: {len(mappings)} 个测试点")
        return mappings
    
    def get_mapping_matrix(self) -> Tuple[List[str], List[str], np.ndarray]:
        """
        获取映射矩阵
            
        Returns:
            Tuple[List[str], List[str], np.ndarray]: (测试点列表, 部件列表, 映射矩阵)
        """
        mappings = self.extract_test_component_mappings()
        
        # 收集所有测试点和部件
        test_points = list(mappings.keys())
        components = set()
        for mapping_list in mappings.values():
            for comp_name, _ in mapping_list:
                components.add(comp_name)
        components = list(components)
        
        # 构建矩阵
        matrix = np.zeros((len(components), len(test_points)))
        
        for i, test_point in enumerate(test_points):
            for comp_name, strength in mappings[test_point]:
                if comp_name in components:
                    j = components.index(comp_name)
                    matrix[j, i] = strength
        
        return test_points, components, matrix
    
    def normalize_mappings(self, mappings: Dict[str, List[Tuple[str, float]]], 
                          method: str = 'max') -> Dict[str, List[Tuple[str, float]]]:
        """
        归一化映射关系
        
        Args:
            mappings: 原始映射关系
            method: 归一化方法 ('max' 或 'sum')
        
        Returns:
            归一化后的映射关系
        """
        normalized = {}
        
        for test_name, mapping_list in mappings.items():
            if not mapping_list:
                normalized[test_name] = []
                continue
            
            strengths = [strength for _, strength in mapping_list]
            
            if method == 'max':
                max_strength = max(strengths)
                if max_strength > 0:
                    normalized[test_name] = [
                        (comp_name, strength / max_strength)
                        for comp_name, strength in mapping_list
                    ]
                else:
                    normalized[test_name] = mapping_list
            elif method == 'sum':
                total_strength = sum(strengths)
                if total_strength > 0:
                    normalized[test_name] = [
                        (comp_name, strength / total_strength)
                        for comp_name, strength in mapping_list
                    ]
                else:
                    normalized[test_name] = mapping_list
            else:
                normalized[test_name] = mapping_list
        
        return normalized
    

def auto_extract_msfg_mappings(msfg_definition) -> Dict[str, List[Tuple[str, float]]]:
    """
    自动从MSFG定义中提取测试点-部件映射关系
    
    Args:
        msfg_definition: MSFG定义对象
        
    Returns:
        测试点→部件的映射关系
    """
    try:
        from msfg_analysis.models import MSFGNode, MSFGEdge
        
        # 从数据库读取节点和边
        nodes_in_db = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        edges_in_db = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
        
        if not nodes_in_db.exists():
            logger.warning(f"MSFG {msfg_definition.name} 没有节点数据")
            return {}
        
        # 构建图数据结构
        msfg_data = {
            'nodes': [],
            'edges': []
        }
        
        # 构建节点数据
        for node in nodes_in_db:
            node_data = {
                'id': str(node.id),
                'name': node.name,
                'type': node.node_type,
                'text': {'value': node.name}
            }
            msfg_data['nodes'].append(node_data)
        
        # 构建边数据
        for edge in edges_in_db:
            edge_data = {
                'source': str(edge.source_node.id) if edge.source_node else '',
                'target': str(edge.target_node.id) if edge.target_node else '',
                'weight': getattr(edge, 'weight', 1.0)  # 兼容没有weight字段的情况
            }
            msfg_data['edges'].append(edge_data)
        
        logger.info(f"从数据库构建MSFG数据: {len(msfg_data['nodes'])} 个节点, {len(msfg_data['edges'])} 条边")
        
        # 创建自动映射提取器
        extractor = MSFGAutoMapping(msfg_data)
        
        # 提取映射关系
        mappings = extractor.extract_test_component_mappings()
        
        # 归一化
        normalized_mappings = extractor.normalize_mappings(mappings, method='max')
        
        logger.info(f"自动提取MSFG {msfg_definition.name} 的映射关系: {len(mappings)} 个测试点")
        
        return normalized_mappings
        
    except Exception as e:
        logger.error(f"自动提取MSFG映射关系失败: {e}")
        return {}


def _create_mapping_safely(msfg_definition, test_point_name: str, component_name: str, 
                          mapping_type: str, weight: float, component_type: str,
                          importance_weight: float, is_critical: bool, description: str) -> int:
    """
    安全地创建映射关系，避免重复代码
    
    Returns:
        int: 成功创建的映射数量 (0 or 1)
    """
    try:
        from msfg_analysis.models import TestPointComponentMapping
        
        TestPointComponentMapping.objects.create(
            msfg_definition=msfg_definition,
            test_point_name=test_point_name,
            component_name=component_name,
            mapping_type=mapping_type,
            weight=weight,
            component_type=component_type,
            importance_weight=importance_weight,
            is_critical=is_critical,
            description=description
        )
        return 1
    except Exception as e:
        logger.warning(f"创建映射失败 {test_point_name} -> {component_name}: {e}")
        # 尝试使用get_or_create避免重复
        try:
            TestPointComponentMapping.objects.get_or_create(
                msfg_definition=msfg_definition,
                test_point_name=test_point_name,
                component_name=component_name,
                defaults={
                    'mapping_type': mapping_type,
                    'weight': weight,
                    'component_type': component_type,
                    'importance_weight': importance_weight,
                    'is_critical': is_critical,
                    'description': description
                }
            )
            return 1
        except Exception as e2:
            logger.error(f"get_or_create也失败: {e2}")
            return 0


def update_msfg_mappings_from_structure(msfg_definition) -> bool:
    """
    根据MSFG结构更新测试点-部件映射关系
    
    Args:
        msfg_definition: MSFG定义对象
        
    Returns:
        是否更新成功
    """
    try:
        from msfg_analysis.models import TestPointComponentMapping
        
        with transaction.atomic():
            # 自动提取映射关系
            auto_mappings = auto_extract_msfg_mappings(msfg_definition)
            
            if not auto_mappings:
                logger.warning(f"无法从MSFG {msfg_definition.name} 提取映射关系")
                return False
            
            # 删除现有映射（使用更安全的方式）
            existing_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
            existing_count = existing_mappings.count()
            existing_mappings.delete()
            logger.info(f"删除了 {existing_count} 个现有映射")
            
            # 创建新的映射
            created_count = 0
            
            # 获取所有可用的部件名称
            available_components = msfg_definition.component_names or []
            
            for test_name, component_mappings in auto_mappings.items():
                # 如果有自动映射的部件，使用自动映射
                if component_mappings:
                    for component_name, influence_strength in component_mappings:
                        # 降低阈值，保留更多映射
                        if influence_strength > 0.05:  # 降低阈值
                            created_count += _create_mapping_safely(
                                msfg_definition, test_name, component_name,
                                    mapping_type='one_to_many' if len(component_mappings) > 1 else 'one_to_one',
                                    weight=influence_strength,
                                    component_type='other',
                                    importance_weight=influence_strength,
                                    is_critical=influence_strength > 0.8,
                                    description=f'自动提取: 影响强度 {influence_strength:.3f}'
                                )
                else:
                    # 如果没有自动映射，为测试点创建默认映射到所有可用部件
                    logger.info(f"测试点 {test_name} 没有自动映射，创建默认映射")
                    for component_name in available_components:
                        created_count += _create_mapping_safely(
                            msfg_definition, test_name, component_name,
                                mapping_type='one_to_many',
                            weight=0.1,
                                component_type='other',
                                importance_weight=0.1,
                                is_critical=False,
                            description='默认映射: 无直接路径'
                        )
            
            logger.info(f"更新MSFG {msfg_definition.name} 映射关系: 创建了 {created_count} 个映射")
            return True
            
    except Exception as e:
        logger.error(f"更新MSFG映射关系失败: {e}")
        return False


def extract_test_component_fault_mappings(msfg_definition) -> Dict[str, Dict[str, List[Tuple[str, float]]]]:
    """
    从MSFG定义中提取测点→部件→故障的完整映射关系
    
    Args:
        msfg_definition: MSFG定义对象
        
    Returns:
        Dict[str, Dict[str, List[Tuple[str, float]]]]: 
        格式: {
            'test_point_name': {
                'components': [('component_name', strength), ...],
                'faults': [('fault_name', strength), ...]
            }
        }
    """
    try:
        from msfg_analysis.models import MSFGNode, MSFGEdge
        
        # 从数据库读取节点和边
        nodes_in_db = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        edges_in_db = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
        
        if not nodes_in_db.exists():
            logger.warning(f"MSFG {msfg_definition.name} 没有节点数据")
            return {}
        
        # 构建图数据结构
        msfg_data = {
            'nodes': [],
            'edges': []
        }
        
        # 构建节点数据
        for node in nodes_in_db:
            node_data = {
                'id': str(node.id),
                'name': node.name,
                'type': node.node_type,
                'text': {'value': node.name}
            }
            msfg_data['nodes'].append(node_data)
        
        # 构建边数据
        for edge in edges_in_db:
            edge_data = {
                'source': str(edge.source_node.id) if edge.source_node else '',
                'target': str(edge.target_node.id) if edge.target_node else '',
                'weight': getattr(edge, 'weight', 1.0)
            }
            msfg_data['edges'].append(edge_data)
        
        logger.info(f"从数据库构建MSFG数据: {len(msfg_data['nodes'])} 个节点, {len(msfg_data['edges'])} 条边")
        
        # 创建自动映射提取器
        extractor = MSFGAutoMapping(msfg_data)
        
        # 提取完整的映射关系
        complete_mappings = {}
        
        # 获取所有测试点节点
        testpoint_nodes = [node_id for node_id, node_type in extractor.node_types.items() if node_type == 'testpoint']
        
        logger.info(f"开始提取 {len(testpoint_nodes)} 个测试点的完整映射关系")
        
        for testpoint_id in testpoint_nodes:
            testpoint_name = extractor.node_info[testpoint_id]['name']
            
            # 查找从该测试点到所有部件的路径
            component_paths = extractor._find_all_paths(testpoint_id, 'component', max_depth=15)
            
            # 查找从该测试点到所有故障的路径
            fault_paths = extractor._find_all_paths(testpoint_id, 'fault', max_depth=15)
            
            # 处理部件映射
            component_influences = defaultdict(list)
            for path, path_weight in component_paths:
                if len(path) < 2 or not extractor._validate_path(path):
                    continue
                target_component_id = path[-1]
                target_component_name = extractor.node_info[target_component_id]['name']
                component_influences[target_component_name].append(path_weight)
            
            # 处理故障映射
            fault_influences = defaultdict(list)
            for path, path_weight in fault_paths:
                if len(path) < 2 or not extractor._validate_path(path):
                    continue
                target_fault_id = path[-1]
                target_fault_name = extractor.node_info[target_fault_id]['name']
                fault_influences[target_fault_name].append(path_weight)
            
            # 组合权重
            final_components = {}
            for component_name, path_weights in component_influences.items():
                combined_weight = extractor._combine_parallel_weights(path_weights, method='probabilistic')
                if combined_weight > 1e-6:
                    final_components[component_name] = combined_weight
            
            final_faults = {}
            for fault_name, path_weights in fault_influences.items():
                combined_weight = extractor._combine_parallel_weights(path_weights, method='probabilistic')
                if combined_weight > 1e-6:
                    final_faults[fault_name] = combined_weight
            
            # 转换为列表格式并排序
            component_list = [(comp_name, strength) for comp_name, strength in final_components.items()]
            component_list.sort(key=lambda x: x[1], reverse=True)
            
            fault_list = [(fault_name, strength) for fault_name, strength in final_faults.items()]
            fault_list.sort(key=lambda x: x[1], reverse=True)
            
            complete_mappings[testpoint_name] = {
                'components': component_list,
                'faults': fault_list
            }
            
            logger.debug(f"测试点 {testpoint_name}: "
                        f"映射到 {len(component_list)} 个部件, {len(fault_list)} 个故障")
        
        logger.info(f"提取完整映射关系完成: {len(complete_mappings)} 个测试点")
        return complete_mappings
        
    except Exception as e:
        logger.error(f"提取测点→部件→故障映射关系时出错: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_mapping_summary(msfg_definition) -> Dict[str, Any]:
    """
    获取MSFG映射关系的统计摘要
    
    Args:
        msfg_definition: MSFG定义对象
        
    Returns:
        Dict[str, Any]: 映射关系统计信息
    """
    try:
        from msfg_analysis.models import MSFGNode, MSFGEdge
        
        # 获取节点统计
        nodes = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
        
        node_type_counts = {}
        for node in nodes:
            node_type = node.node_type
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
        
        # 获取映射关系
        complete_mappings = extract_test_component_fault_mappings(msfg_definition)
        
        # 统计映射关系
        total_test_points = len(complete_mappings)
        total_component_mappings = sum(len(mapping['components']) for mapping in complete_mappings.values())
        total_fault_mappings = sum(len(mapping['faults']) for mapping in complete_mappings.values())
        
        # 计算平均映射数
        avg_components_per_test = total_component_mappings / total_test_points if total_test_points > 0 else 0
        avg_faults_per_test = total_fault_mappings / total_test_points if total_test_points > 0 else 0
        
        # 找出映射最多的测试点
        test_with_most_components = None
        test_with_most_faults = None
        max_components = 0
        max_faults = 0
        
        for test_name, mapping in complete_mappings.items():
            if len(mapping['components']) > max_components:
                max_components = len(mapping['components'])
                test_with_most_components = test_name
            
            if len(mapping['faults']) > max_faults:
                max_faults = len(mapping['faults'])
                test_with_most_faults = test_name
        
        summary = {
            'msfg_name': msfg_definition.name,
            'node_counts': node_type_counts,
            'edge_count': edges.count(),
            'mapping_stats': {
                'total_test_points': total_test_points,
                'total_component_mappings': total_component_mappings,
                'total_fault_mappings': total_fault_mappings,
                'avg_components_per_test': round(avg_components_per_test, 2),
                'avg_faults_per_test': round(avg_faults_per_test, 2),
                'test_with_most_components': {
                    'name': test_with_most_components,
                    'count': max_components
                } if test_with_most_components else None,
                'test_with_most_faults': {
                    'name': test_with_most_faults,
                    'count': max_faults
                } if test_with_most_faults else None
            },
            'sample_mappings': {}
        }
        
        # 添加一些示例映射
        for i, (test_name, mapping) in enumerate(complete_mappings.items()):
            if i >= 3:  # 只显示前3个示例
                break
            summary['sample_mappings'][test_name] = {
                'components': mapping['components'][:3],  # 只显示前3个
                'faults': mapping['faults'][:3]  # 只显示前3个
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"获取映射摘要时出错: {e}")
        import traceback
        traceback.print_exc()
        return {}
