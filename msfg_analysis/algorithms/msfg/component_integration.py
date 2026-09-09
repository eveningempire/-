"""
MSFG閮ㄤ欢闆嗘垚妯″潡
缁熶竴绠＄悊澶氫俊鍙锋祦鍥句腑鐨勯儴浠跺畾涔夊拰鍋ュ悍鐘舵€佹帹鐞?
纭繚閮ㄤ欢鏉ユ簮瀹屽叏鍩轰簬婵€娲荤殑MSFG閰嶇疆
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Tuple
import logging
from django.db import transaction

from data_management.models import PHM, PHMModel, PHMData
from msfg_analysis.models import (
    MSFGDefinition, MSFGNode, TestPointComponentMapping
)

logger = logging.getLogger(__name__)


def get_active_msfg_for_cmg_model(cmg_model: PHMModel) -> Optional[MSFGDefinition]:
    """鑾峰彇PHM妯″瀷鐨勬縺娲籑SFG閰嶇疆"""
    return MSFGDefinition.objects.filter(
        cmg_model=cmg_model,
        is_active=True
    ).order_by('-updated_at').first()


def extract_components_from_msfg(msfg_definition: MSFGDefinition) -> List[str]:
    """浠嶮SFG瀹氫箟涓彁鍙栭儴浠跺垪琛?
    
    浼樺厛绾э細
    1. 娴嬭瘯鐐?閮ㄤ欢鏄犲皠涓殑閮ㄤ欢
    2. MSFG瀹氫箟鐨刢omponent_names瀛楁
    3. 浠庣郴缁熻妭鐐瑰悕绉版帹鏂?
    """
    components = set()
    
    # 1. 浠庢祴璇曠偣-閮ㄤ欢鏄犲皠涓彁鍙?
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
    for mapping in mappings:
        components.add(mapping.component_name)
    
    # 2. 浣跨敤MSFG瀹氫箟鐨刢omponent_names瀛楁
    if msfg_definition.component_names:
        components.update(msfg_definition.component_names)
    
    # 3. 浠庣郴缁熻妭鐐瑰拰缁勪欢鑺傜偣鍚嶇О鎺ㄦ柇锛堥櫎浜唕oot鑺傜偣锛?
    system_nodes = MSFGNode.objects.filter(
        msfg_definition=msfg_definition,
        node_type__in=['system', 'component']
    ).exclude(name__in=['root', 'system', ''])
    
    for node in system_nodes:
        if node.name and node.name.strip():
            components.add(node.name.strip())
    
    return sorted(list(components))


def calculate_msfg_component_health(
    test_scores: Dict[str, float],
    msfg_definition: MSFGDefinition,
    include_unmapped_components: bool = True
) -> Dict[str, Dict[str, Any]]:
    """鍩轰簬MSFG閰嶇疆璁＄畻閮ㄤ欢鍋ュ悍鐘舵€?
    
    Args:
        test_scores: 娴嬭瘯鐐瑰垎鏁板瓧鍏?
        msfg_definition: MSFG瀹氫箟
        include_unmapped_components: 鏄惁鍖呭惈鏈槧灏勭殑閮ㄤ欢
        
    Returns:
        閮ㄤ欢鍋ュ悍鐘舵€佸瓧鍏?
    """
    component_health = {}
    
    # 鑾峰彇娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    mappings = TestPointComponentMapping.objects.filter(
        msfg_definition=msfg_definition
    ).select_related('msfg_definition')
    
    # 鎸夐儴浠跺垎缁勬槧灏?
    component_mappings = {}
    for mapping in mappings:
        component_name = mapping.component_name
        if component_name not in component_mappings:
            component_mappings[component_name] = []
        component_mappings[component_name].append(mapping)
    
    # 璁＄畻姣忎釜閮ㄤ欢鐨勫仴搴风姸鎬?
    for component_name, comp_mappings in component_mappings.items():
        test_point_scores = []
        test_point_weights = []
        test_point_details = {}
        is_critical = False
        
        for mapping in comp_mappings:
            test_point_name = mapping.test_point_name
            weight = mapping.importance_weight
            is_critical = is_critical or mapping.is_critical
            
            # 鏌ユ壘鍖归厤鐨勬祴璇曠偣鍒嗘暟
            test_score = 0.0
            for score_key, score_value in test_scores.items():
                if (test_point_name.lower() in score_key.lower() or 
                    score_key.lower() in test_point_name.lower()):
                    test_score = score_value
                    break
            
            test_point_scores.append(test_score)
            test_point_weights.append(weight)
            test_point_details[test_point_name] = {
                'score': round(test_score, 3),
                'weight': weight
            }
        
        # 璁＄畻閮ㄤ欢鍋ュ悍鍒嗘暟
        if test_point_scores:
            import numpy as np
            scores_array = np.array(test_point_scores)
            weights_array = np.array(test_point_weights)
            
            # 鍔犳潈骞冲潎鍒嗘暟
            weighted_avg = np.average(scores_array, weights=weights_array)
            max_score = np.max(scores_array)
            
            # 鍋ュ悍鍒嗘暟璁＄畻锛? - 寮傚父鍒嗘暟锛堟笎杩涘紡璋冩暣锛?
            if is_critical:
                # 鍏抽敭閮ㄤ欢瀵瑰紓甯告洿鏁忔劅锛屼繚鎸佸師鏈夐€昏緫
                health_score = max(0.0, 1.0 - max_score * 1.2)
            else:
                # 闈炲叧閿儴浠讹細缁撳悎骞冲潎鍊煎拰鏈€澶у€硷紝閬垮厤鍗曚釜楂樺紓甯歌蹇界暐
                # 娓愯繘寮忚皟鏁达細70%鏉冮噸缁欏钩鍧囧€硷紝30%鏉冮噸缁欐渶澶у€?
                combined_score = weighted_avg * 0.7 + max_score * 0.3
                health_score = max(0.0, 1.0 - combined_score)
            
            # 璁＄畻娲昏穬鏁呴殰鏁伴噺锛堟笎杩涘紡璋冩暣锛氶槇鍊间粠0.3闄嶄綆鍒?.25锛?
            active_fault_count = sum(1 for score in test_point_scores if score > 0.25)
            
            component_health[component_name] = {
                'health_score': round(min(health_score, 1.0), 3),
                'max_fault_score': round(max_score, 3),  # 缁熶竴瀛楁鍚?
                'avg_test_score': round(weighted_avg, 3),
                'active_fault_count': active_fault_count,  # 缁熶竴瀛楁鍚?
                'test_point_count': len(test_point_scores),
                'is_critical': is_critical,
                'test_points': list(test_point_details.keys()),
                'test_details': test_point_details,
                'source': 'msfg_mapping'
            }
    
    # 濡傛灉闇€瑕佸寘鍚湭鏄犲皠鐨勯儴浠讹紙浠嶮SFG瀹氫箟涓幏鍙栵級
    if include_unmapped_components:
        all_components = extract_components_from_msfg(msfg_definition)
        for component_name in all_components:
            if component_name not in component_health:
                # 涓烘湭鏄犲皠鐨勯儴浠舵彁渚涢粯璁ゅ仴搴风姸鎬?
                component_health[component_name] = {
                    'health_score': 1.0,
                    'max_test_score': 0.0,
                    'avg_test_score': 0.0,
                    'active_fault_count': 0,
                    'test_point_count': 0,
                    'is_critical': False,
                    'test_points': [],
                    'test_details': {},
                    'source': 'msfg_definition'
                }
    
    return component_health


def ensure_msfg_component_mappings(msfg_definition: MSFGDefinition) -> None:
    """纭繚MSFG閰嶇疆鏈夊畬鏁寸殑娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    
    涓烘病鏈夋槧灏勭殑娴嬭瘯鐐瑰垱寤洪粯璁ょ殑閮ㄤ欢鏄犲皠锛屼紭鍏堟槧灏勫埌浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢
    """
    try:
        with transaction.atomic():
            # 鑾峰彇鎵€鏈夋祴璇曠偣鍚嶇О
            test_names = msfg_definition.test_names or []
            
            # 鑾峰彇浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢鍒楄〃
            available_components = extract_components_from_msfg(msfg_definition)
            
            # 鑾峰彇宸叉湁鐨勬槧灏?
            existing_mappings = set(
                TestPointComponentMapping.objects.filter(
                    msfg_definition=msfg_definition
                ).values_list('test_point_name', flat=True)
            )
            
            logger.info(f"MSFG {msfg_definition.name} 鍙敤閮ㄤ欢: {available_components}")
            logger.info(f"闇€瑕佹槧灏勭殑娴嬭瘯鐐? {[name for name in test_names if name not in existing_mappings]}")
            
            # 涓烘湭鏄犲皠鐨勬祴璇曠偣鍒涘缓榛樿鏄犲皠
            for test_name in test_names:
                if test_name not in existing_mappings:
                    # 浼樺厛鏄犲皠鍒癕SFG缁撴瀯涓殑閮ㄤ欢
                    component_name, component_type = _infer_component_from_test_name(test_name, available_components)
                    
                    TestPointComponentMapping.objects.get_or_create(
                        msfg_definition=msfg_definition,
                        test_point_name=test_name,
                        defaults={
                            'component_name': component_name,
                            'component_type': component_type,
                            'importance_weight': 1.0,
                            'is_critical': False,
                            'description': f'鑷姩鏄犲皠锛歿test_name} 鈫?{component_name}'
                        }
                    )
                    logger.info(f"鍒涘缓鏄犲皠: {test_name} 鈫?{component_name} ({component_type})")
                    
            logger.info(f"宸叉洿鏂癕SFG {msfg_definition.name} 鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠")
                    
    except Exception as e:
        logger.error(f"鏇存柊MSFG閮ㄤ欢鏄犲皠澶辫触: {e}")


def _infer_component_from_test_name(test_name: str, available_components: List[str]) -> Tuple[str, str]:
    """浠庢祴璇曠偣鍚嶇О鎺ㄦ柇閮ㄤ欢鍚嶇О鍜岀被鍨?
    
    浼樺厛鏄犲皠鍒癕SFG缁撴瀯涓凡鏈夌殑閮ㄤ欢
    """
    test_name_lower = test_name.lower()
    
    # 棣栧厛灏濊瘯灏嗘祴璇曠偣鏄犲皠鍒板凡鏈夌殑閮ㄤ欢
    for component in available_components:
        component_lower = component.lower()
        
        # 妫€鏌ユ槸鍚︽湁鐩存帴鐨勫叧閿瘝鍖归厤
        if any(keyword in test_name_lower and keyword in component_lower 
               for keyword in ['鐢垫満', 'motor', '鎺у埗', 'control', '鐢垫簮', 'power', 
                             '杞瓙', 'rotor', '妗嗘灦', 'frame', '杞存壙', 'bearing']):
            return component, _get_component_type_from_name(component)
        
        # 妫€鏌ラ儴浠跺悕绉版槸鍚﹀寘鍚祴璇曠偣鐨勫叧閿瘝
        test_keywords = set(test_name_lower.split())
        component_keywords = set(component_lower.split())
        
        if test_keywords & component_keywords:  # 鏈変氦闆?
            return component, _get_component_type_from_name(component)
    
    # 濡傛灉娌℃湁鎵惧埌鍖归厤鐨勫凡鏈夐儴浠讹紝閫夋嫨鏈€鐩稿叧鐨勯儴浠?
    if available_components:
        # 鍩轰簬鍏抽敭璇嶅尮閰嶅害閫夋嫨鏈€鍚堥€傜殑閮ㄤ欢
        best_match = None
        best_score = 0
        
        for component in available_components:
            score = _calculate_match_score(test_name_lower, component.lower())
            if score > best_score:
                best_score = score
                best_match = component
        
        if best_match and best_score > 0.1:  # 璁剧疆鏈€浣庡尮閰嶉槇鍊?
            return best_match, _get_component_type_from_name(best_match)
    
    # 鏈€鍚庡閫夛細浣跨敤绗竴涓彲鐢ㄧ殑閮ㄤ欢鎴栧垱寤烘柊鐨?
    if available_components:
        return available_components[0], 'other'
    else:
        return f'{test_name}_榛樿閮ㄤ欢', 'other'


def _calculate_match_score(test_name: str, component_name: str) -> float:
    """璁＄畻娴嬭瘯鐐瑰拰閮ㄤ欢鍚嶇О鐨勫尮閰嶅垎鏁?""
    test_keywords = set(test_name.split())
    component_keywords = set(component_name.split())
    
    # 璁＄畻浜ら泦鍗犳瘮
    intersection = test_keywords & component_keywords
    union = test_keywords | component_keywords
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def _get_component_type_from_name(component_name: str) -> str:
    """鏍规嵁閮ㄤ欢鍚嶇О鎺ㄦ柇閮ㄤ欢绫诲瀷"""
    name_lower = component_name.lower()
    
    if any(keyword in name_lower for keyword in ['鐢垫満', 'motor']):
        return 'motor'
    elif any(keyword in name_lower for keyword in ['杞存壙', 'bearing']):
        return 'bearing'
    elif any(keyword in name_lower for keyword in ['鎺у埗', 'control']):
        return 'control'
    elif any(keyword in name_lower for keyword in ['鐢垫簮', 'power']):
        return 'power'
    elif any(keyword in name_lower for keyword in ['浼犳劅鍣?, 'sensor']):
        return 'sensor'
    elif any(keyword in name_lower for keyword in ['榻胯疆', 'gear', '浼犲姩']):
        return 'gear'
    else:
        return 'other'


def sync_msfg_component_definitions(cmg_model: PHMModel) -> Dict[str, Any]:
    """鍚屾MSFG閮ㄤ欢瀹氫箟鍒拌鍒欐娴嬫ā鍧?
    
    纭繚瑙勫垯妫€娴嬫ā鍧楃殑ComponentDefinition涓嶮SFG閰嶇疆鍚屾
    """
    try:
        from rule_detection.models import ComponentDefinition
        
        # 鑾峰彇婵€娲荤殑MSFG閰嶇疆
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            return {
                'success': False,
                'message': f'PHM妯″瀷 {cmg_model.model_name} 娌℃湁婵€娲荤殑MSFG閰嶇疆'
            }
        
        # 鎻愬彇MSFG涓殑閮ㄤ欢
        msfg_components = extract_components_from_msfg(active_msfg)
        
        # 鏇存柊瑙勫垯妫€娴嬫ā鍧楃殑閮ㄤ欢瀹氫箟
        with transaction.atomic():
            # 鍒犻櫎涓嶅湪MSFG涓殑閮ㄤ欢瀹氫箟
            ComponentDefinition.objects.filter(
                cmg_model=cmg_model
            ).exclude(
                component_name__in=msfg_components
            ).delete()
            
            # 鍒涘缓鎴栨洿鏂癕SFG涓殑閮ㄤ欢瀹氫箟
            created_count = 0
            updated_count = 0
            
            for component_name in msfg_components:
                component_def, created = ComponentDefinition.objects.get_or_create(
                    cmg_model=cmg_model,
                    component_name=component_name,
                    defaults={
                        'description': f'鏉ヨ嚜MSFG閰嶇疆: {active_msfg.name}',
                        'parameters': []
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    # 鏇存柊鎻忚堪浠ュ弽鏄犳潵婧?
                    component_def.description = f'鏉ヨ嚜MSFG閰嶇疆: {active_msfg.name}'
                    component_def.save()
                    updated_count += 1
        
        return {
            'success': True,
            'message': f'鍚屾瀹屾垚',
            'details': {
                'msfg_name': active_msfg.name,
                'components_count': len(msfg_components),
                'created_count': created_count,
                'updated_count': updated_count,
                'components': msfg_components
            }
        }
        
    except Exception as e:
        logger.error(f"鍚屾MSFG閮ㄤ欢瀹氫箟澶辫触: {e}")
        return {
            'success': False,
            'message': f'鍚屾澶辫触: {str(e)}'
        }


def get_unified_component_health(
    cmg_data: PHMData,
    test_scores: Dict[str, float]
) -> Dict[str, Any]:
    """鑾峰彇缁熶竴鐨勯儴浠跺仴搴风姸鎬?
    
    鍩轰簬婵€娲荤殑MSFG閰嶇疆璁＄畻閮ㄤ欢鍋ュ悍鐘舵€?
    """
    cmg_model = cmg_data.cmg.cmg_model
    
    # 鑾峰彇婵€娲荤殑MSFG閰嶇疆
    active_msfg = get_active_msfg_for_cmg_model(cmg_model)
    if not active_msfg:
        return {
            'component_results': {},
            'error': f'PHM妯″瀷 {cmg_model.model_name} 娌℃湁婵€娲荤殑MSFG閰嶇疆'
        }
    
    # 璁＄畻閮ㄤ欢鍋ュ悍鐘舵€?
    component_health = calculate_msfg_component_health(
        test_scores=test_scores,
        msfg_definition=active_msfg,
        include_unmapped_components=True
    )
    
    return {
        'component_results': component_health,
        'msfg_name': active_msfg.name,
        'msfg_id': active_msfg.id,
        'analysis_time': cmg_data.timestamp.isoformat() if cmg_data.timestamp else None
    }

