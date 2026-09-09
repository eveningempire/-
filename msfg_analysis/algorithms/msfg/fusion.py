"""
MSFG融合计算（增强版本）

根据测试点分数与MSFG图的测试-故障连接关系，计算故障与系统层面的结果。
支持部件级别的健康分析和故障定位。
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional
import numpy as np


def fuse_test_to_fault(
    test_scores: Dict[str, float],
    edges: List[Tuple[str, str]],
    test_name_by_id: Dict[str, str],
    fault_name_by_id: Dict[str, str],
    msfg_definition=None,
) -> Dict[str, float]:
    """将测试点分数融合到故障分数。

    - test_scores: 测试点名称到分数（0..1）
    - edges: (source_id, target_id)
    - name_by_id: 映射id->名称
    - msfg_definition: MSFG定义对象，用于获取映射关系
    
    优先级：
    1. 用户定义的测试点-故障映射（TestPointFaultMapping）
    2. MSFG图的直接连接
    3. 智能匹配（应急方案）
    """
    fault_scores: Dict[str, float] = {}
    
    # 1. 优先使用用户定义的测试点-故障映射
    if msfg_definition:
        try:
            from msfg_analysis.models import TestPointFaultMapping
            mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg_definition)
            
            for mapping in mappings:
                test_name = mapping.test_point_name
                fault_name = mapping.fault_name
                weight = mapping.weight
                confidence = mapping.confidence
                
                if test_name in test_scores:
                    test_score = test_scores[test_name]
                    # 应用权重和置信度
                    weighted_score = test_score * weight * confidence
                    
                    if fault_name in fault_scores:
                        # 如果故障已有分数，取最大值
                        fault_scores[fault_name] = max(fault_scores[fault_name], weighted_score)
                    else:
                        fault_scores[fault_name] = weighted_score
                        
            print(f"使用用户映射: 找到 {len(mappings)} 个测试点-故障映射")
            
        except Exception as e:
            print(f"获取用户映射失败: {e}")
    
    # 2. 使用MSFG图的直接连接
    if not fault_scores:  # 如果没有用户映射，使用图连接
        # 创建名称到ID的反向映射
        test_id_by_name = {name: node_id for node_id, name in test_name_by_id.items()}
        
        # 反向建立 fault_name -> list of test_names
        fault_to_tests: Dict[str, List[str]] = {}
        
        for sid, tid in edges:
            # 获取源节点（测试点）名称
            test_name = test_name_by_id.get(sid)
            if test_name is None:
                continue
                
            # 获取目标节点（故障）名称
            fault_name = fault_name_by_id.get(tid)
            if fault_name is None:
                continue
                
            fault_to_tests.setdefault(fault_name, []).append(test_name)

        # 计算故障分数
        for fault_name, test_names in fault_to_tests.items():
            if not test_names:
                continue
                
            # 从test_scores中查找对应测试点的分数
            test_values = []
            for test_name in test_names:
                # 直接匹配测试点名称
                if test_name in test_scores:
                    test_values.append(test_scores[test_name])
                else:
                    # 模糊匹配：查找包含测试点名称的键
                    for score_key, score_value in test_scores.items():
                        if test_name.lower() in score_key.lower() or score_key.lower() in test_name.lower():
                            test_values.append(score_value)
                            break
                    else:
                        # 没有找到匹配的测试点分数，使用0
                        test_values.append(0.0)
            
            # 使用最大值作为故障分数
            fault_scores[fault_name] = max(test_values) if test_values else 0.0
            
        print(f"使用图连接: 找到 {len(fault_to_tests)} 个故障-测试点连接")

    # 3. 应急方案：如果没有找到任何连接，使用智能匹配
    if not fault_scores and test_scores:
        print("警告：没有找到测试->故障的连接，使用智能匹配")
        
        for fault_name in fault_name_by_id.values():
            if not fault_name or fault_name.strip() == '':
                continue
                
            matched_score = 0.0
            
            # 尝试基于关键词匹配
            fault_keywords = fault_name.lower().split()
            
            for test_name, test_score in test_scores.items():
                test_keywords = test_name.lower().split()
                
                # 查找共同关键词
                common_words = set(fault_keywords) & set(test_keywords)
                if common_words:
                    matched_score = max(matched_score, test_score)
                
                # 查找包含关系
                if any(keyword in test_name.lower() for keyword in fault_keywords):
                    matched_score = max(matched_score, test_score)
                elif any(keyword in fault_name.lower() for keyword in test_keywords):
                    matched_score = max(matched_score, test_score)
            
            # 设置故障分数
            if matched_score > 0:
                fault_scores[fault_name] = matched_score
                
        print(f"使用智能匹配: 匹配到 {len(fault_scores)} 个故障")

    return fault_scores


def summarize_system(fault_scores: Dict[str, float]) -> Dict[str, float]:
    """生成系统层面的健康概览。
    
    改进策略：
      - fault_count = 活跃故障数量（故障概率 > 0.3）
      - worst_fault_score = 最严重的故障分数
      - average_fault_score = 平均故障分数（代表系统整体健康状态）
      - critical_faults = 高风险故障列表（故障概率 > 0.7）
    """
    if not fault_scores:
        return {
            "fault_count": 0,
            "worst_fault_score": 0.0,
            "average_fault_score": 0.0,
            "critical_faults": []
        }
    
    # 提取故障概率值 - 兼容两种数据结构
    fault_values = []
    fault_names = []
    
    for fault_name, fault_data in fault_scores.items():
        if isinstance(fault_data, dict):
            # 如果是嵌套对象，提取故障概率
            fault_prob = fault_data.get('fault_probability', 0)
            fault_values.append(fault_prob)
            fault_names.append(fault_name)
        else:
            # 如果是简单数值
            fault_values.append(fault_data)
            fault_names.append(fault_name)
    
    if not fault_values:
        return {
            "fault_count": 0,
            "worst_fault_score": 0.0,
            "average_fault_score": 0.0,
            "critical_faults": []
        }
    
    # 计算关键指标
    worst_fault = max(fault_values)
    average_fault = sum(fault_values) / len(fault_values)
    
    # 活跃故障数量：故障概率 > 0.3 的故障
    active_faults = []
    critical_faults = []
    
    for i, (fault_name, fault_value) in enumerate(zip(fault_names, fault_values)):
        if fault_value > 0.3:
            active_faults.append(fault_value)
        if fault_value > 0.7:
            critical_faults.append(fault_name)
    
    fault_count = len(active_faults)
    
    return {
        "fault_count": fault_count,
        "worst_fault_score": round(worst_fault, 3),
        "average_fault_score": round(average_fault, 3),
        "critical_faults": critical_faults
    }


def calculate_component_scores(
    fault_scores: Dict[str, float],
    test_scores: Dict[str, float],
    nodes: List,
    edges: List,
    msfg_definition=None
) -> Dict[str, Dict[str, float]]:
    """计算部件级别的健康分数
    
    使用测试点-部件映射和故障传播关系计算部件健康分数
    
    Args:
        fault_scores: 故障分数字典
        test_scores: 测试点分数字典
        nodes: MSFG节点列表
        edges: MSFG边列表
        msfg_definition: MSFG定义对象
        
    Returns:
        部件分数字典，格式: {component_name: {health_score: float, fault_details: dict}}
    """
    component_scores = {}
    
    # 1. 首先尝试使用测试点-部件映射
    if msfg_definition:
        try:
            from msfg_analysis.models import TestPointComponentMapping
            component_mappings = TestPointComponentMapping.objects.filter(
                msfg_definition=msfg_definition
            )
            
            # 基于测试点映射计算部件分数
            test_based_components = {}
            for mapping in component_mappings:
                component_name = mapping.component_name
                test_point_name = mapping.test_point_name
                weight = mapping.importance_weight
                is_critical = mapping.is_critical
                
                if test_point_name in test_scores:
                    test_score = test_scores[test_point_name]
                    
                    if component_name not in test_based_components:
                        test_based_components[component_name] = {
                            'scores': [],
                            'weights': [],
                            'critical': False,
                            'test_points': []
                        }
                    
                    test_based_components[component_name]['scores'].append(test_score)
                    test_based_components[component_name]['weights'].append(weight)
                    test_based_components[component_name]['critical'] = test_based_components[component_name]['critical'] or is_critical
                    test_based_components[component_name]['test_points'].append(test_point_name)
            
            # 计算基于测试点的部件健康分数
            for component_name, data in test_based_components.items():
                scores = np.array(data['scores'])
                weights = np.array(data['weights'])
                
                # 加权平均分数
                if len(scores) > 0:
                    weighted_score = np.average(scores, weights=weights)
                    max_score = np.max(scores)
                    
                    # 关键部件的权重更高
                    if data['critical']:
                        health_score = 1.0 - max_score * 1.2  # 关键部件更敏感
                    else:
                        health_score = 1.0 - weighted_score
                    
                    health_score = max(0.0, min(1.0, health_score))
                    
                    component_scores[component_name] = {
                        "health_score": round(health_score, 3),
                        "max_test_score": round(max_score, 3),
                        "avg_test_score": round(weighted_score, 3),
                        "test_point_count": len(scores),
                        "is_critical": data['critical'],
                        "test_points": data['test_points'],
                        "test_details": {tp: round(test_scores.get(tp, 0), 3) for tp in data['test_points']},
                        "source": "testpoint_mapping"
                    }
        except Exception as e:
            # 如果测试点映射失败，使用故障节点映射作为备选
            pass
    
    # 2. 备选方案：基于故障节点的部件映射
    if not component_scores:
        fault_nodes = {node.name: node for node in nodes if node.node_type == 'fault'}
        component_faults = {}
        
        for fault_name, fault_score in fault_scores.items():
            if fault_name in fault_nodes:
                fault_node = fault_nodes[fault_name]
                # 尝试从节点属性中获取组件信息
                component = fault_node.properties.get('component', 'Unknown')
                if not component or component == 'Unknown':
                    # 如果没有明确的组件信息，尝试从故障名称推断
                    component = extract_component_from_fault_name(fault_name)
                
                if component not in component_faults:
                    component_faults[component] = []
                component_faults[component].append((fault_name, fault_score))
        
        # 计算每个部件的健康分数
        for component, faults in component_faults.items():
            if not faults:
                continue
                
            fault_scores_list = [score for _, score in faults]
            fault_names_list = [name for name, _ in faults]
            
            # 部件健康分数计算策略
            max_fault_score = max(fault_scores_list)
            avg_fault_score = np.mean(fault_scores_list)
            # 更合理的活跃故障判断：故障概率 > 0.3 或模糊概率 > 0.2
            active_faults = []
            for name, score in faults:
                if isinstance(score, dict):
                    # 如果是嵌套对象，提取故障概率
                    fault_prob = score.get('fault_probability', 0)
                    fuzzy_prob = score.get('fuzzy_probability', 0)
                    if fault_prob > 0.3 or fuzzy_prob > 0.2:
                        active_faults.append(name)
                else:
                    # 如果是简单数值
                    if score > 0.3:
                        active_faults.append(name)
            
            # 参考老平台的_or_failure_fuzzy逻辑
            component_health = calculate_component_health(fault_scores_list)
            
            component_scores[component] = {
                "health_score": round(component_health, 3),
                "max_fault_score": round(max_fault_score, 3),  # 保持字段名一致
                "avg_fault_score": round(avg_fault_score, 3),
                "active_fault_count": len(active_faults),  # 保持字段名一致
                "total_fault_count": len(faults),
                "active_faults": active_faults,
                "fault_details": {name: round(score, 3) for name, score in faults},
                "source": "fault_node_mapping"
            }
    
    return component_scores


def extract_component_from_fault_name(fault_name: str) -> str:
    """从故障名称中提取部件名称的启发式方法"""
    # 这里可以根据实际的命名规则来调整
    if '电机' in fault_name or 'Motor' in fault_name:
        return '电机系统'
    elif '轴承' in fault_name or 'Bearing' in fault_name:
        return '轴承系统'
    elif '齿轮' in fault_name or 'Gear' in fault_name:
        return '传动系统'
    elif '传感器' in fault_name or 'Sensor' in fault_name:
        return '传感器系统'
    elif '控制' in fault_name or 'Control' in fault_name:
        return '控制系统'
    else:
        return '其他部件'


def calculate_component_health(fault_scores: List[float]) -> float:
    """计算部件健康分数
    
    参考老平台的_or_failure_fuzzy和_anomCount方法
    渐进式调整：提高异常敏感度，但保持稳定性
    """
    if not fault_scores:
        return 1.0
    
    fault_scores = np.array(fault_scores)
    
    # 使用类似老平台的逻辑：考虑最大值和平均值的组合
    max_score = np.max(fault_scores)
    avg_score = np.mean(fault_scores)
    
    # 模拟老平台的模糊推理逻辑
    # proba = max(fault_scores)
    # fuzzy_proba = min(fault_scores * fuzzy_factor + 1 - fault_scores) * max(fault_scores)
    
    # 渐进式调整：降低活跃故障阈值，提高敏感度
    active_count = np.sum(fault_scores > 0.35)  # 从0.5降低到0.35
    total_count = len(fault_scores)
    
    if active_count == 0:
        # 没有活跃故障，但仍需考虑异常程度
        # 渐进式调整：提高系数从0.2到0.5，降低下限从0.8到0.6
        health_score = max(0.6, 1.0 - max_score * 0.5)
    else:
        # 有活跃故障，健康分数综合考虑严重程度和范围
        severity_factor = max_score
        coverage_factor = active_count / total_count
        
        # 渐进式调整：增加平均分数的影响权重
        avg_factor = avg_score * 0.3  # 新增平均分数影响
        
        # 综合计算，确保下限不会过低
        health_score = max(0.1, 1.0 - severity_factor - coverage_factor * 0.4 - avg_factor)
    
    return health_score


def _estimate_probability_from_fault_details(max_fault_score: float, avg_fault_score: float, active_fault_count: int, total_fault_count: int) -> float:
    """根据故障明细估计部件故障概率。
    兼顾最大值与平均值，适度考虑活跃故障占比。
    """
    # 基础概率：偏向保守，更多参考最大故障
    base_prob = 0.7 * max_fault_score + 0.3 * avg_fault_score
    coverage = 0.0
    if total_fault_count > 0:
        coverage = min(1.0, active_fault_count / max(1, total_fault_count)) * 0.15  # 覆盖度最多加权0.15
    return float(max(0.0, min(1.0, base_prob + coverage)))


def _estimate_probability_from_test_details(test_max: float, test_avg: float, active_tp_count: int, total_tp_count: int) -> float:
    """根据测试点异常估计部件故障概率。
    将测试点异常视为“先验迹象”，强度略低于直接故障。
    """
    base_prob = 0.6 * test_max + 0.4 * test_avg
    coverage = 0.0
    if total_tp_count > 0:
        coverage = min(1.0, active_tp_count / max(1, total_tp_count)) * 0.1
    return float(max(0.0, min(1.0, base_prob + coverage)))


def _compute_confidence_weight(has_fault_evidence: bool, has_test_evidence: bool,
                               fault_prob: float, test_prob: float,
                               fault_count: int, test_count: int) -> tuple:
    """计算两路证据的置信度权重。
    - 故障证据优先级更高；
    - 当仅有一路证据时，权重倾向该路；
    - 多数量或更高概率提升相应权重。
    返回 (w_fault, w_test)，两者和为1。
    """
    if not has_fault_evidence and not has_test_evidence:
        return 0.5, 0.5

    fault_conf = 0.0
    test_conf = 0.0

    if has_fault_evidence:
        fault_conf = 0.5 + 0.3 * fault_prob + 0.2 * min(1.0, fault_count / 3.0)
    if has_test_evidence:
        test_conf = 0.3 + 0.3 * test_prob + 0.2 * min(1.0, test_count / 5.0)

    total = fault_conf + test_conf
    if total <= 0:
        return 0.5, 0.5
    return fault_conf / total, test_conf / total


def fuse_component_results(
    test_based: dict,
    fault_based: dict
) -> dict:
    """融合测试点与故障两路的部件结果。
    参数格式：
      - test_based[component] = {health_score, max_fault_score?, active_fault_count? ...}
      - fault_based[component] = {health_score, max_fault_score, avg_fault_score, active_fault_count, total_fault_count ...}
    返回：与 fault_based 相同风格，并提供 fused 字段说明来源。
    """
    components = set()
    if isinstance(test_based, dict):
        components.update(test_based.keys())
    if isinstance(fault_based, dict):
        components.update(fault_based.keys())

    fused = {}
    for comp in components:
        tb = (test_based or {}).get(comp) or {}
        fb = (fault_based or {}).get(comp) or {}

        # 故障路径估计
        fb_max = float(fb.get('max_fault_score', 0.0) or 0.0)
        fb_avg = float(fb.get('avg_fault_score', fb_max) or fb_max)
        fb_active = int(fb.get('active_fault_count', 0) or 0)
        fb_total = int(fb.get('total_fault_count', max(1, fb_active)) or max(1, fb_active))
        fault_prob_est = _estimate_probability_from_fault_details(fb_max, fb_avg, fb_active, fb_total)

        # 测试点路径估计
        tb_health = tb.get('health_score')
        # 从测试侧估计“异常概率”，若无 health_score 则尝试使用 test 的 max/avg（若存在）
        if tb_health is not None:
            test_prob_est = float(max(0.0, min(1.0, 1.0 - float(tb_health))))
        else:
            tb_max = float(tb.get('max_fault_score', 0.0) or 0.0)
            tb_avg = float(tb.get('avg_fault_score', tb_max) or tb_max)
            tb_active = int(tb.get('active_fault_count', 0) or 0)
            tb_total = int(tb.get('total_test_count', max(1, tb_active)) or max(1, tb_active))
            test_prob_est = _estimate_probability_from_test_details(tb_max, tb_avg, tb_active, tb_total)

        has_fault_ev = fb != {}
        has_test_ev = tb != {}
        w_fault, w_test = _compute_confidence_weight(has_fault_ev, has_test_ev, fault_prob_est, test_prob_est, fb_total, tb.get('total_test_count', tb_active if tb else 0) or 0)

        fused_prob = w_fault * fault_prob_est + w_test * test_prob_est
        fused_health = float(max(0.0, min(1.0, 1.0 - fused_prob)))

        fused[comp] = {
            'health_score': round(fused_health, 3),
            'fused_fault_probability': round(fused_prob, 3),
            'fusion_weights': {'fault': round(w_fault, 3), 'test': round(w_test, 3)},
            'max_fault_score': round(max(fb_max, tb.get('max_fault_score', 0.0) or 0.0), 3),
            'avg_fault_score': round((fb_avg + float(tb.get('avg_fault_score', 0.0) or 0.0)) / 2.0, 3) if has_test_ev else round(fb_avg, 3),
            'active_fault_count': int(max(fb_active, int(tb.get('active_fault_count', 0) or 0))),
            'total_fault_count': int(fb_total),
            'source': 'fused(test+fault)'
        }

        # 合并原有的细节，优先保留故障侧细节
        if 'fault_details' in fb:
            fused[comp]['fault_details'] = fb['fault_details']
        if 'test_details' in tb:
            fused[comp]['test_details'] = tb['test_details']

    return fused


def enhanced_msfg_analysis(
    test_scores: Dict[str, float],
    edges: List[Tuple[str, str]],
    test_name_by_id: Dict[str, str],
    fault_name_by_id: Dict[str, str],
    nodes: List,
    msfg_definition=None,
    include_component_analysis: bool = True
) -> Dict:
    """增强的MSFG分析，包含部件级别分析
    
    使用统一的部件健康计算逻辑，确保部件来源于MSFG配置
    
    Returns:
        完整的分析结果，包括故障分数、系统概览和部件分析
    """
    # 基础故障分数计算
    fault_scores = fuse_test_to_fault(test_scores, edges, test_name_by_id, fault_name_by_id, msfg_definition)
    
    # 部件级别分析（融合测试点与故障两路）
    fault_based = {}
    test_based = {}
    if include_component_analysis:
        # 0) 优先使用用户提供的映射（不臆测）
        if msfg_definition:
            try:
                from msfg_analysis.models import TestPointComponentMapping, FaultComponentMapping
                # 测试点侧证据
                tp_map = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
                comp_to_tp_scores: Dict[str, List[float]] = {}
                comp_to_tp_all: Dict[str, List[Tuple[str, float]]] = {}
                comp_to_tp_active: Dict[str, int] = {}
                comp_to_tp_total: Dict[str, int] = {}
                for m in tp_map:
                    tp = m.test_point_name
                    if tp in test_scores:
                        comp = m.component_name
                        w = float(getattr(m, 'weight', 1.0) or 1.0)
                        val = float(test_scores.get(tp) or 0.0) * w
                        comp_to_tp_scores.setdefault(comp, []).append(val)
                        comp_to_tp_all.setdefault(comp, []).append((tp, val))
                        comp_to_tp_total[comp] = comp_to_tp_total.get(comp, 0) + 1
                        if val > 0.3:
                            comp_to_tp_active[comp] = comp_to_tp_active.get(comp, 0) + 1
                # 汇总测试点侧
                for comp, vals in comp_to_tp_scores.items():
                    if not vals:
                        continue
                    tmax = max(vals)
                    tavg = float(np.mean(vals))
                    test_based[comp] = {
                        'max_fault_score': round(tmax, 3),
                        'avg_fault_score': round(tavg, 3),
                        'active_fault_count': int(comp_to_tp_active.get(comp, 0)),
                        'total_test_count': int(comp_to_tp_total.get(comp, len(vals))),
                        'test_details': {k: round(v, 3) for k, v in comp_to_tp_all.get(comp, [])},
                        'source': 'user_mapping:testpoint'
                    }

                # 故障侧证据
                fc_map = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
                comp_to_fault_scores: Dict[str, List[float]] = {}
                comp_to_fault_all: Dict[str, List[Tuple[str, float]]] = {}
                comp_to_fault_active: Dict[str, int] = {}
                comp_to_fault_total: Dict[str, int] = {}
                for m in fc_map:
                    fn = m.fault_name
                    if fn in fault_scores:
                        comp = m.component_name
                        w = float(getattr(m, 'weight', 1.0) or 1.0)
                        raw = fault_scores.get(fn)
                        # 接受嵌套或纯数值
                        if isinstance(raw, dict):
                            val = float(raw.get('fault_probability', 0.0))
                        else:
                            val = float(raw or 0.0)
                        val *= w
                        comp_to_fault_scores.setdefault(comp, []).append(val)
                        comp_to_fault_all.setdefault(comp, []).append((fn, val))
                        comp_to_fault_total[comp] = comp_to_fault_total.get(comp, 0) + 1
                        if val > 0.3:
                            comp_to_fault_active[comp] = comp_to_fault_active.get(comp, 0) + 1
                # 汇总故障侧
                for comp, vals in comp_to_fault_scores.items():
                    if not vals:
                        continue
                    fmax = max(vals)
                    favg = float(np.mean(vals))
                    fault_based[comp] = {
                        'health_score': None,  # 由融合器估计概率后再反推
                        'max_fault_score': round(fmax, 3),
                        'avg_fault_score': round(favg, 3),
                        'active_fault_count': int(comp_to_fault_active.get(comp, 0)),
                        'total_fault_count': int(comp_to_fault_total.get(comp, len(vals))),
                        'fault_details': {k: round(v, 3) for k, v in comp_to_fault_all.get(comp, [])},
                        'source': 'user_mapping:fault'
                    }
            except Exception:
                # 用户映射不可用时忽略
                pass

        # 若用户映射未覆盖，使用原有策略补齐
        if nodes and not fault_based:
            fault_based = calculate_component_scores(
                fault_scores, test_scores, nodes, edges, msfg_definition
            )
        if msfg_definition and not test_based:
            try:
                from .component_integration import calculate_msfg_component_health
                test_based = calculate_msfg_component_health(
                    test_scores=test_scores,
                    msfg_definition=msfg_definition,
                    include_unmapped_components=True
                )
            except ImportError:
                test_based = {}

    # 融合
    component_analysis = fuse_component_results(test_based, fault_based) if include_component_analysis else {}

    # 系统级别概览（融合后微调平均故障分数以更贴近整体健康）
    system_summary = summarize_system(fault_scores)
    if component_analysis:
        comp_fault_probs = [max(0.0, min(1.0, 1.0 - c.get('health_score', 1.0))) for c in component_analysis.values()]
        if comp_fault_probs:
            blended_avg = 0.7 * system_summary.get('average_fault_score', 0.0) + 0.3 * (sum(comp_fault_probs) / len(comp_fault_probs))
            system_summary['average_fault_score'] = round(blended_avg, 3)
    
    # 将test_scores的键转换为测试点名称以便前端显示
    named_test_results = {}
    id_to_name = {v: k for k, v in test_name_by_id.items()}  # 反转映射：name -> id
    
    for test_key, score in test_scores.items():
        # 尝试找到匹配的测试点名称
        matching_name = None
        
        # 首先尝试直接匹配测试点名称
        if test_key in test_name_by_id.values():
            matching_name = test_key
        else:
            # 如果没有直接匹配，尝试在测试点名称中查找包含该键的项
            for name in test_name_by_id.values():
                if str(test_key).lower() in name.lower() or name.lower() in str(test_key).lower():
                    matching_name = name
                    break
        
        # 使用找到的名称或原键
        final_key = matching_name if matching_name else f"未知测点_{test_key}"
        named_test_results[final_key] = score
    
    return {
        "test_results": named_test_results,
        "fault_results": fault_scores,
        "system_results": system_summary,
        "component_results": component_analysis,  # 改为 component_results 以匹配前端和模型
        "analysis_metadata": {
            "test_count": len(test_scores),
            "fault_count": len(fault_scores),
            "component_count": len(component_analysis),
            "edge_count": len(edges),
            "msfg_source": msfg_definition.name if msfg_definition else "unknown"
        }
    }


