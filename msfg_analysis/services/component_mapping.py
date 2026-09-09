"""
閮ㄤ欢鏄犲皠鏈嶅姟
姝ｇ‘澶勭悊娴嬬偣-閮ㄤ欢鏄犲皠鍏崇郴
"""

import logging
from typing import Dict, List, Set
from collections import defaultdict
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping

logger = logging.getLogger(__name__)

class ComponentMappingService:
    """閮ㄤ欢鏄犲皠鏈嶅姟"""
    
    def build_component_mappings(self, msfg_definition: MSFGDefinition) -> Dict[str, List[str]]:
        """
        鏋勫缓姝ｇ‘鐨勯儴浠舵槧灏勫叧绯?        
        Args:
            msfg_definition: MSFG瀹氫箟
            
        Returns:
            Dict[str, List[str]]: component_name -> [fault_names] 鐨勬槧灏?        """
        try:
            # 鑾峰彇鎵€鏈夋祴鐐?閮ㄤ欢鏄犲皠
            mappings = TestPointComponentMapping.objects.filter(
                msfg_definition=msfg_definition
            ).select_related('msfg_definition')
            
            if not mappings.exists():
                logger.warning(f"MSFG {msfg_definition.name} 娌℃湁娴嬬偣-閮ㄤ欢鏄犲皠")
                return self._create_fallback_component_mappings(msfg_definition)
            
            # 鑾峰彇MSFG鐨勬晠闅滆妭鐐?            fault_nodes = list(msfg_definition.nodes.filter(node_type='fault'))
            fault_names = [node.name for node in fault_nodes]
            
            if not fault_names:
                logger.warning(f"MSFG {msfg_definition.name} 娌℃湁鏁呴殰鑺傜偣")
                return {}
            
            # 鏋勫缓娴嬬偣鍒伴儴浠剁殑鏄犲皠
            testpoint_to_components = defaultdict(list)
            for mapping in mappings:
                testpoint_to_components[mapping.test_point_name].append({
                    'component': mapping.component_name,
                    'weight': mapping.weight,
                    'importance': mapping.importance_weight,
                    'is_critical': mapping.is_critical
                })
            
            # 鏋勫缓閮ㄤ欢鍒版晠闅滅殑鏄犲皠
            component_to_faults = self._build_component_fault_mappings(
                msfg_definition, testpoint_to_components, fault_names
            )
            
            logger.info(f"鏋勫缓閮ㄤ欢鏄犲皠瀹屾垚: {len(component_to_faults)} 涓儴浠?)
            return component_to_faults
            
        except Exception as e:
            logger.error(f"鏋勫缓閮ㄤ欢鏄犲皠澶辫触: {e}")
            return self._create_fallback_component_mappings(msfg_definition)
    
    def _build_component_fault_mappings(self, 
                                       msfg_definition: MSFGDefinition,
                                       testpoint_to_components: Dict[str, List[Dict]],
                                       fault_names: List[str]) -> Dict[str, List[str]]:
        """
        鏋勫缓閮ㄤ欢鍒版晠闅滅殑鏄犲皠鍏崇郴
        
        Args:
            msfg_definition: MSFG瀹氫箟
            testpoint_to_components: 娴嬬偣鍒伴儴浠剁殑鏄犲皠
            fault_names: 鏁呴殰鍚嶇О鍒楄〃
            
        Returns:
            Dict[str, List[str]]: 閮ㄤ欢鍒版晠闅滅殑鏄犲皠
        """
        component_to_faults = defaultdict(set)
        
        # 鑾峰彇MSFG鐨勮竟鍏崇郴
        edges = list(msfg_definition.edges.select_related('source_node', 'target_node'))
        
        # 鏋勫缓娴嬬偣鍒版晠闅滅殑鏄犲皠
        testpoint_to_faults = defaultdict(list)
        for edge in edges:
            if (edge.source_node.node_type == 'test' and 
                edge.target_node.node_type == 'fault'):
                testpoint_to_faults[edge.source_node.name].append(edge.target_node.name)
        
        # 閫氳繃娴嬬偣-鏁呴殰-閮ㄤ欢鐨勪紶閫掑叧绯绘瀯寤烘槧灏?        for testpoint_name, component_infos in testpoint_to_components.items():
            # 鑾峰彇璇ユ祴鐐硅繛鎺ョ殑鏁呴殰
            connected_faults = testpoint_to_faults.get(testpoint_name, [])
            
            if not connected_faults:
                # 濡傛灉娌℃湁鐩存帴杩炴帴鐨勬晠闅滐紝灏濊瘯鏅鸿兘鍖归厤
                connected_faults = self._find_matching_faults(testpoint_name, fault_names)
            
            # 灏嗘晠闅滃垎閰嶇粰鐩稿叧閮ㄤ欢
            for component_info in component_infos:
                component_name = component_info['component']
                for fault_name in connected_faults:
                    component_to_faults[component_name].add(fault_name)
        
        # 澶勭悊娌℃湁娴嬬偣鏄犲皠鐨勬晠闅?        unmapped_faults = set(fault_names) - set().union(*[faults for faults in component_to_faults.values()])
        if unmapped_faults:
            logger.info(f"鍙戠幇 {len(unmapped_faults)} 涓湭鏄犲皠鐨勬晠闅滐紝杩涜鏅鸿兘鍒嗛厤")
            self._assign_unmapped_faults(unmapped_faults, component_to_faults)
        
        # 杞崲涓哄垪琛ㄦ牸寮?        result = {comp: list(faults) for comp, faults in component_to_faults.items()}
        
        # 纭繚鍖呭惈鎵€鏈塎SFG瀹氫箟鐨勭粍浠?        msfg_component_names = msfg_definition.component_names or []
        for comp_name in msfg_component_names:
            if comp_name not in result:
                result[comp_name] = []
        
        # 濡傛灉瀛樺湪鏈垎閰嶇殑鏁呴殰涓旀湁绌虹粍浠讹紝杩涜鏅鸿兘鍒嗛厤
        assigned_faults = set().union(*[set(v) for v in result.values()]) if result else set()
        remaining_unmapped_faults = set(fault_names) - assigned_faults
        empty_components = [c for c, fs in result.items() if not fs]
        if empty_components and remaining_unmapped_faults:
            try:
                self._assign_faults_to_empty_components(empty_components, remaining_unmapped_faults, result, fault_names)
            except AttributeError:
                # 鍚戝悗鍏煎锛氳嫢鏂规硶涓嶅瓨鍦ㄥ垯蹇界暐
                logger.debug("_assign_faults_to_empty_components 鏈疄鐜帮紝璺宠繃绌虹粍浠舵櫤鑳藉垎閰?)
        
        # 璁板綍鏄犲皠缁撴灉
        for comp, faults in result.items():
            logger.debug(f"閮ㄤ欢 {comp}: {len(faults)} 涓晠闅?- {faults[:3]}{'...' if len(faults) > 3 else ''}")
        
        return result
    
    def _find_matching_faults(self, testpoint_name: str, fault_names: List[str]) -> List[str]:
        """
        涓烘祴鐐瑰鎵惧尮閰嶇殑鏁呴殰锛堟櫤鑳藉尮閰嶏級
        
        Args:
            testpoint_name: 娴嬬偣鍚嶇О
            fault_names: 鎵€鏈夋晠闅滃悕绉?            
        Returns:
            List[str]: 鍖归厤鐨勬晠闅滃悕绉板垪琛?        """
        matching_faults = []
        testpoint_lower = testpoint_name.lower()
        
        # 鎻愬彇娴嬬偣鍚嶇О涓殑鍏抽敭璇?        import re
        testpoint_keywords = set(re.findall(r'\w+', testpoint_lower))
        
        for fault_name in fault_names:
            fault_lower = fault_name.lower()
            fault_keywords = set(re.findall(r'\w+', fault_lower))
            
            # 妫€鏌ュ叧閿瘝閲嶅彔
            common_keywords = testpoint_keywords & fault_keywords
            if common_keywords:
                matching_faults.append(fault_name)
                continue
            
            # 妫€鏌ュ寘鍚叧绯?            if any(keyword in fault_lower for keyword in testpoint_keywords):
                matching_faults.append(fault_name)
                continue
            
            if any(keyword in testpoint_lower for keyword in fault_keywords):
                matching_faults.append(fault_name)
        
        if not matching_faults:
            logger.debug(f"娴嬬偣 {testpoint_name} 娌℃湁鎵惧埌鍖归厤鐨勬晠闅?)
        else:
            logger.debug(f"娴嬬偣 {testpoint_name} 鍖归厤鍒?{len(matching_faults)} 涓晠闅?)
        
        return matching_faults
    
    def _assign_unmapped_faults(self, unmapped_faults: Set[str], component_to_faults: Dict[str, Set[str]]):
        """
        鍒嗛厤鏈槧灏勭殑鏁呴殰鍒扮浉鍏抽儴浠?        
        Args:
            unmapped_faults: 鏈槧灏勭殑鏁呴殰闆嗗悎
            component_to_faults: 閮ㄤ欢鍒版晠闅滅殑鏄犲皠锛堜細琚慨鏀癸級
        """
        # 鍩轰簬鏁呴殰鍚嶇О鐨勬櫤鑳藉垎閰嶈鍒?        assignment_rules = {
            '杞存壙': ['杞存壙', 'bearing', '杞存俯', '娓╁害'],
            '鐢垫満': ['鐢垫満', 'motor', '杞€?, '閫熷害', 'rpm'],
            '鐢垫簮': ['鐢靛帇', 'voltage', '鐢垫簮', 'power', 'v'],
            '鎺у埗鍣?: ['鎺у埗', 'control', '妗嗘灦', '澹虫俯'],
            '鐢垫祦閲囨牱': ['鐢垫祦', 'current', 'a', '閲囨牱'],
            '浼犳劅鍣?: ['浼犳劅', 'sensor', '妫€娴?],
            '鍏朵粬': []  # 榛樿鍒嗙被
        }
        
        for fault_name in unmapped_faults:
            fault_lower = fault_name.lower()
            assigned = False
            
            # 灏濊瘯鏍规嵁瑙勫垯鍒嗛厤
            for component_pattern, keywords in assignment_rules.items():
                if keywords and any(keyword in fault_lower for keyword in keywords):
                    # 鎵惧埌鍖归厤鐨勯儴浠?                    matching_components = [comp for comp in component_to_faults.keys() 
                                         if component_pattern in comp or 
                                         any(keyword in comp.lower() for keyword in keywords)]
                    
                    if matching_components:
                        # 鍒嗛厤缁欑涓€涓尮閰嶇殑閮ㄤ欢
                        component_to_faults[matching_components[0]].add(fault_name)
                        logger.debug(f"鏅鸿兘鍒嗛厤: 鏁呴殰 {fault_name} -> 閮ㄤ欢 {matching_components[0]}")
                        assigned = True
                        break
            
            # 濡傛灉娌℃湁鍒嗛厤鎴愬姛锛屽垎閰嶇粰绗竴涓彲鐢ㄩ儴浠?            if not assigned and component_to_faults:
                first_component = list(component_to_faults.keys())[0]
                component_to_faults[first_component].add(fault_name)
                logger.debug(f"榛樿鍒嗛厤: 鏁呴殰 {fault_name} -> 閮ㄤ欢 {first_component}")
    
    def _assign_faults_to_empty_components(
        self,
        empty_components: List[str],
        unmapped_faults: Set[str],
        component_mappings: Dict[str, List[str]],
        all_fault_names: List[str]
    ) -> None:
        """
        灏嗘湭鏄犲皠鐨勬晠闅滃垎閰嶇粰褰撳墠娌℃湁浠讳綍鏁呴殰鐨勭粍浠讹紙灏卞湴淇敼 component_mappings锛夈€?        浼樺厛渚濇嵁鍚嶇О鍏抽敭璇嶅尮閰嶏紝鍏舵骞冲潎鍒嗛厤锛岄伩鍏嶆墦鐮村凡寤虹珛鐨勭粨鏋勬€ф槧灏勩€?        
        Args:
            empty_components: 鏃犳晠闅滅殑缁勪欢鍚嶇О鍒楄〃
            unmapped_faults: 鏈垎閰嶇殑鏁呴殰闆嗗悎
            component_mappings: 缁勪欢 -> 鏁呴殰鍒楄〃锛堜細琚慨鏀癸級
            all_fault_names: 鎵€鏈夋晠闅滃悕绉帮紙淇濈暀缁欏悗缁瓥鐣ユ墿灞曪級
        """
        if not empty_components or not unmapped_faults:
            return
        
        component_keywords = {
            'PHM': ['cmg', '绯荤粺', '鏁存満'],
            '鐢垫簮鏉?: ['鐢垫簮', '鐢靛帇', 'v', '渚涚數', '鐢靛姏', '29v', '100v'],
            '杞瓙鎺у埗鍣?: ['杞瓙', '鎺у埗'],
            '杞瓙椹卞姩鐢垫満': ['杞瓙', '椹卞姩', '鐢垫満', '椹揪', '杞€?, '鏃嬭浆'],
            '杞瓙鐢垫祦閲囨牱': ['杞瓙', '鐢垫祦', '閲囨牱'],
            '妗嗘灦鎺у埗鍣?: ['妗嗘灦', '鎺у埗', '澹虫俯', '妗嗘灦椹卞姩'],
            '鏃嬪彉瑙ｈ皟鏈虹': ['鏃嬪彉', '瑙ｈ皟', '鏈虹', '鏃嬭浆鍙樺帇鍣?],
            '鏃嬪彉SPI': ['鏃嬪彉', 'spi', '閫氫俊'],
            '1553B鎺ュ彛': ['1553', '鎺ュ彛', '閫氫俊', '鎬荤嚎'],
            '杞瓙杞存壙': ['杞存壙', '杞存俯', '娓╁害', '鍥虹揣绔?, '婊戝姩绔?],
            '妗嗘灦鐢垫祦閲囨牱': ['妗嗘灦', '鐢垫祦', '閲囨牱']
        }
        
        import re
        def calc_score(component_name: str, fault_name: str) -> int:
            comp_key = component_name.strip()
            comp_lower = comp_key.lower()
            fault_lower = fault_name.lower()
            keywords = component_keywords.get(comp_key, [comp_lower])
            score = 0
            for kw in keywords:
                if kw and kw in fault_lower:
                    score += 2
            if comp_lower in fault_lower or any(part and part in fault_lower for part in re.findall(r"[\w]+", comp_lower)):
                score += 3
            return score
        
        normalized_empty_components = [comp.strip() for comp in empty_components]
        still_unassigned: List[str] = []
        
        for fault in list(unmapped_faults):
            best_comp = None
            best_score = 0
            for comp in normalized_empty_components:
                score = calc_score(comp, fault)
                if score > best_score:
                    best_score = score
                    best_comp = comp
            if best_comp and best_score > 0:
                component_mappings[best_comp] = component_mappings.get(best_comp, [])
                component_mappings[best_comp].append(fault)
                unmapped_faults.discard(fault)
                logger.debug(f"绌虹粍浠舵櫤鑳藉垎閰? 鏁呴殰 {fault} -> 缁勪欢 {best_comp} (鍒嗘暟: {best_score})")
            else:
                still_unassigned.append(fault)
        
        if still_unassigned and normalized_empty_components:
            logger.info(f"骞冲潎鍒嗛厤 {len(still_unassigned)} 涓湭鍖归厤鏁呴殰鍒扮┖缁勪欢")
            for idx, fault in enumerate(still_unassigned):
                comp = normalized_empty_components[idx % len(normalized_empty_components)]
                component_mappings[comp] = component_mappings.get(comp, [])
                component_mappings[comp].append(fault)
                unmapped_faults.discard(fault)
                logger.debug(f"绌虹粍浠跺钩鍧囧垎閰? 鏁呴殰 {fault} -> 缁勪欢 {comp}")
    
    def _create_fallback_component_mappings(self, msfg_definition: MSFGDefinition) -> Dict[str, List[str]]:
        """
        鍒涘缓澶囩敤鐨勯儴浠舵槧灏勶紙褰撴甯告槧灏勪笉鍙敤鏃讹級
        
        Args:
            msfg_definition: MSFG瀹氫箟
            
        Returns:
            Dict[str, List[str]]: 澶囩敤閮ㄤ欢鏄犲皠
        """
        logger.info(f"涓篗SFG {msfg_definition.name} 鍒涘缓澶囩敤閮ㄤ欢鏄犲皠")
        
        # 鑾峰彇鏁呴殰鑺傜偣
        fault_nodes = list(msfg_definition.nodes.filter(node_type='fault'))
        fault_names = [node.name for node in fault_nodes]
        
        if not fault_names:
            logger.warning("娌℃湁鏁呴殰鑺傜偣锛屾棤娉曞垱寤哄鐢ㄦ槧灏?)
            return {}
        
        # 浣跨敤MSFG涓畾涔夌殑閮ㄤ欢鍚嶇О
        component_names = msfg_definition.component_names or []
        
        if not component_names:
            # 濡傛灉娌℃湁棰勫畾涔夐儴浠讹紝鍒涘缓榛樿閮ㄤ欢
            component_names = ['绯荤粺閮ㄤ欢1', '绯荤粺閮ㄤ欢2', '鍏朵粬閮ㄤ欢']
            logger.warning(f"MSFG娌℃湁瀹氫箟閮ㄤ欢鍚嶇О锛屼娇鐢ㄩ粯璁ら儴浠? {component_names}")
        
        # 骞冲潎鍒嗛厤鏁呴殰鍒伴儴浠?        component_mappings = {comp: [] for comp in component_names}
        
        for i, fault_name in enumerate(fault_names):
            component_index = i % len(component_names)
            component_name = component_names[component_index]
            component_mappings[component_name].append(fault_name)
        
        # 璁板綍鏄犲皠缁撴灉
        for comp, faults in component_mappings.items():
            logger.debug(f"澶囩敤鏄犲皠 - 閮ㄤ欢 {comp}: {len(faults)} 涓晠闅?)
        
        return component_mappings
    
    def get_component_weights(self, msfg_definition: MSFGDefinition) -> Dict[str, Dict[str, float]]:
        """
        鑾峰彇閮ㄤ欢鏉冮噸淇℃伅
        
        Args:
            msfg_definition: MSFG瀹氫箟
            
        Returns:
            Dict[str, Dict[str, float]]: 閮ㄤ欢鏉冮噸淇℃伅
        """
        component_weights = {}
        
        try:
            mappings = TestPointComponentMapping.objects.filter(
                msfg_definition=msfg_definition
            )
            
            for mapping in mappings:
                component_name = mapping.component_name
                if component_name not in component_weights:
                    component_weights[component_name] = {
                        'total_weight': 0.0,
                        'importance_weight': mapping.importance_weight,
                        'is_critical': mapping.is_critical,
                        'testpoint_count': 0
                    }
                
                component_weights[component_name]['total_weight'] += mapping.weight
                component_weights[component_name]['testpoint_count'] += 1
                
                # 鏇存柊鍏抽敭鎬э紙浠讳竴娴嬬偣涓哄叧閿垯閮ㄤ欢涓哄叧閿級
                if mapping.is_critical:
                    component_weights[component_name]['is_critical'] = True
        
        except Exception as e:
            logger.error(f"鑾峰彇閮ㄤ欢鏉冮噸澶辫触: {e}")
        
        return component_weights


def build_msfg_component_mappings(msfg_definition: MSFGDefinition) -> Dict[str, List[str]]:
    """
    鏋勫缓MSFG閮ㄤ欢鏄犲皠鐨勪究鎹峰嚱鏁?    
    Args:
        msfg_definition: MSFG瀹氫箟
        
    Returns:
        Dict[str, List[str]]: 閮ㄤ欢鏄犲皠瀛楀吀
    """
    service = ComponentMappingService()
    return service.build_component_mappings(msfg_definition)

