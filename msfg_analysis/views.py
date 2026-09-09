"""
澶氫俊鍙锋祦鍥?MSFG)鍒嗘瀽Django瑙嗗浘
鎻愪緵MSFG缂栬緫銆佸垎鏋愬拰缁撴灉鏌ヨ鐨凴EST API
"""

import json
import logging
from typing import Dict, List, Any, Optional
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.views.decorators.csrf import csrf_exempt

from data_management.models import PHM, PHMModel, PHMData
from .models import (
    MSFGDefinition, MSFGNode, MSFGEdge, MSFGAnalysisResult, TestPointRuleMapping, TestPointRule, TestPointComponentMapping, FaultComponentMapping, TestPointFaultMapping
)
from .serializers import (
    MSFGDefinitionSerializer, MSFGNodeSerializer, MSFGEdgeSerializer,
    MSFGAnalysisResultSerializer, TestPointRuleMappingSerializer, TestPointRuleSerializer, TestPointComponentMappingSerializer, FaultComponentMappingSerializer, TestPointFaultMappingSerializer
)
from .algorithms.msfg.fusion import fuse_test_to_fault, summarize_system
from .utils.json_validator import validate_msfg_graph
from .utils.graph_parser import normalize_and_parse_graph
from .utils.mapping_extractor import extract_mappings_from_graph # 瀵煎叆鏂扮殑鏄犲皠鎻愬彇鍣?
logger = logging.getLogger(__name__)


class MSFGEditorView(viewsets.ViewSet):
    """MSFG缂栬緫鍣ㄨ鍥?""
    
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    
    @action(detail=False, methods=['get'], url_path='editor')
    def msfg_editor_page(self, request):
        """MSFG缂栬緫鍣ㄩ〉闈?""
        return render(request, 'msfg_analysis/msfg-edit.html')

    @action(detail=False, methods=['get'], url_path='inspect')
    def msfg_inspect_page(self, request):
        """MSFG缁撴瀯涓庢娴嬫祦绋嬫煡鐪嬮〉闈紙鎸傚湪缂栬緫妯″潡涓嬶級"""
        return render(request, 'msfg_analysis/msfg-inspect.html')
    
    @csrf_exempt
    @action(detail=False, methods=['get', 'post'], url_path='init-graph', renderer_classes=[JSONRenderer])
    def init_graph(self, request):
        """鍒濆鍖栧浘缁撴瀯"""
        if request.method == 'POST':
            # 鍏煎FormData鍜孞SON鏍煎紡
            if hasattr(request, 'data') and request.data:
                # DRF瑙ｆ瀽鐨勬暟鎹紙JSON锛?                obj = request.data.get('obj', 'cmg')
                cmg_model_id = request.data.get('cmg_model_id')
            else:
                # FormData鏍煎紡
                obj = request.POST.get('obj', 'cmg')
                cmg_model_id = request.POST.get('cmg_model_id')
        else:
            obj = request.query_params.get('obj', 'cmg')
            cmg_model_id = request.query_params.get('cmg_model_id')
        
        # 濡傛灉娌℃湁鎸囧畾PHM妯″瀷ID锛岃繑鍥為粯璁ょ殑绌虹粨鏋?        if not cmg_model_id:
            return Response({
                'SystemData': [{
                    'system_id': 1,
                    'parent_id': None,
                    'name': "root",
                    'data': {
                        "nodes": [
                            {"id": "t1", "type": "test-node", "text": {"value": "娓╁害瓒呴檺"}, "x": 100, "y": 120},
                            {"id": "t2", "type": "test-node", "text": {"value": "鐢垫祦娉㈠姩"}, "x": 100, "y": 200},
                            {"id": "f1", "type": "fault-node", "text": {"value": "杞存壙鏁呴殰"}, "x": 360, "y": 160}
                        ],
                        "edges": [
                            {"id": "e1", "sourceNodeId": "t1", "targetNodeId": "f1", "type": "polyline"},
                            {"id": "e2", "sourceNodeId": "t2", "targetNodeId": "f1", "type": "polyline"}
                        ]
                    }
                }],
                'currentSystemId': 1
            })
        
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
            
            # 灏濊瘯鑾峰彇鏈€鏂扮殑婵€娲荤殑MSFG閰嶇疆
            msfg_definition = MSFGDefinition.objects.filter(
                cmg_model=cmg_model, 
                is_active=True
            ).order_by('-updated_at').first()
            
            if msfg_definition and msfg_definition.raw_graph_data:
                return Response(msfg_definition.raw_graph_data)
            else:
                # 杩斿洖榛樿缁撴瀯
                return Response({
                    'SystemData': [{
                        'system_id': 1,
                        'parent_id': None,
                        'name': "root",
                        'data': {
                            "nodes": [
                                {"id": "t1", "type": "test-node", "text": {"value": "娓╁害瓒呴檺"}, "x": 100, "y": 120},
                                {"id": "t2", "type": "test-node", "text": {"value": "鐢垫祦娉㈠姩"}, "x": 100, "y": 200},
                                {"id": "f1", "type": "fault-node", "text": {"value": "杞存壙鏁呴殰"}, "x": 360, "y": 160}
                            ],
                            "edges": [
                                {"id": "e1", "sourceNodeId": "t1", "targetNodeId": "f1", "type": "polyline"},
                                {"id": "e2", "sourceNodeId": "t2", "targetNodeId": "f1", "type": "polyline"}
                            ]
                        }
                    }],
                    'currentSystemId': 1
                })
                
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @csrf_exempt
    @action(detail=False, methods=['post'], url_path='config-graph', renderer_classes=[JSONRenderer])
    def config_graph(self, request):
        """淇濆瓨鍥鹃厤缃?""
        # 鍏煎FormData鍜孞SON鏍煎紡
        if hasattr(request, 'data') and request.data:
            # DRF瑙ｆ瀽鐨勬暟鎹紙JSON锛?            cmg_model_id = request.data.get('cmg_model_id')
            graph_data = request.data.get('graphData')
            custom_name = request.data.get('configName', '')
        else:
            # FormData鏍煎紡
            cmg_model_id = request.POST.get('cmg_model_id')
            graph_data = request.POST.get('graphData')
            custom_name = request.POST.get('configName', '')
        
        if not cmg_model_id:
            return Response({'error': 'cmg_model_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if not graph_data:
            return Response({'error': 'graphData is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        try:
            if isinstance(graph_data, str):
                struct_raw = json.loads(graph_data)
            else:
                struct_raw = graph_data
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON in graphData'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # 鑾峰彇褰撳墠婵€娲荤殑MSFG瀹氫箟锛堢敤浜庡悗缁竻鐞嗭級
                old_active_msfg = MSFGDefinition.objects.filter(
                    cmg_model=cmg_model, 
                    is_active=True
                ).first()
                
                # 绂佺敤鏃х殑MSFG瀹氫箟
                MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).update(is_active=False)
                
                # --- 鉁?鏍稿績鏀归€狅細浣跨敤鏂扮殑鍥捐В鏋愬櫒 ---
                parsed_graph = normalize_and_parse_graph(struct_raw)
                if not parsed_graph:
                    return Response({'error': '鏃犳硶瑙ｆ瀽MSFG鍥剧粨鏋?}, status=status.HTTP_400_BAD_REQUEST)

                normalized_graph_json = parsed_graph['normalized_graph']
                
                # 浣跨敤瑙ｆ瀽鍣ㄦ彁鍙栫殑銆佸彲闈犵殑鍚嶇О鍒楄〃
                components = parsed_graph['component_names']
                test_names = parsed_graph['test_names']
                fault_names = parsed_graph['fault_names']
                
                # 鍒涘缓鏂扮殑MSFG瀹氫箟
                config_name = custom_name.strip() if custom_name else f"MSFG_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                msfg_definition = MSFGDefinition.objects.create(
                    cmg_model=cmg_model,
                    name=config_name,
                    description="MSFG閰嶇疆 - 鐢ㄦ埛瀵煎叆" if custom_name else "Auto-generated MSFG from editor",
                    raw_graph_data=normalized_graph_json, # 鉁?淇濆瓨瑙勮寖鍖栧悗鐨凧SON
                    processed_graph_data=normalized_graph_json, # 鉁?淇濆瓨瑙勮寖鍖栧悗鐨凧SON
                    test_names=test_names,
                    fault_names=fault_names,
                    component_names=components,
                    is_active=True
                )
                
                # 濡傛灉鏇存崲浜嗘縺娲荤殑MSFG閰嶇疆锛屾竻鐞嗘棫鐨勫垎鏋愮粨鏋滐紙鍙€夛級
                if old_active_msfg and old_active_msfg.id != msfg_definition.id:
                    logger.info(f"MSFG閰嶇疆浠?{old_active_msfg.name} 鏇存崲涓?{config_name}")
                    # 鍙互閫夋嫨鍒犻櫎鏃ч厤缃殑鍒嗘瀽缁撴灉锛屾垨鑰呮爣璁颁负杩囨湡
                    # MSFGAnalysisResult.objects.filter(msfg_definition=old_active_msfg).delete()
                    pass
                
                # 鉁?浼犻€掕В鏋愬悗鐨勮妭鐐瑰拰杈瑰垪琛ㄨ繘琛屼繚瀛?                self._save_nodes_and_edges(msfg_definition, parsed_graph['nodes'], parsed_graph['edges'])
                
                # 浠庢暟鎹鐞嗘ā鍧楁洿鏂扮粍浠跺畾涔?                self._update_component_definitions(cmg_model, components)
                
                # 鑷姩浠嶮SFG缁撴瀯鎻愬彇鏄犲皠鍏崇郴
                try:
                    # 1. 鎻愬彇鏁呴殰-閮ㄤ欢鏄犲皠鍜屾祴鐐?閮ㄤ欢鏄犲皠
                    from .algorithms.msfg.auto_mapping import update_msfg_mappings_from_structure
                    success = update_msfg_mappings_from_structure(msfg_definition)
                    if success:
                        logger.info(f"鎴愬姛浠嶮SFG缁撴瀯鑷姩鎻愬彇娴嬬偣-閮ㄤ欢鏄犲皠鍏崇郴")
                    else:
                        logger.warning(f"鑷姩鎻愬彇娴嬬偣-閮ㄤ欢鏄犲皠鍏崇郴澶辫触锛屼娇鐢ㄥ鐢ㄦ柟妗?)
                        # 澶囩敤鏂规锛氫娇鐢ㄥ師鏈夌殑鏄犲皠閫昏緫
                        from .algorithms.msfg.component_integration import ensure_msfg_component_mappings
                        ensure_msfg_component_mappings(msfg_definition)
                    
                    # 2. 鎻愬彇鏁呴殰-閮ㄤ欢鏄犲皠鍜屾祴鐐?鏁呴殰鏄犲皠
                    try:
                        from msfg_analysis.models import MSFGNode, MSFGEdge, FaultComponentMapping
                        
                        # 鑾峰彇鎵€鏈夎竟锛堝彧鏌ヨ涓€娆★紝閬垮厤閲嶅鏌ヨ锛?                        edges = MSFGEdge.objects.filter(msfg_definition=msfg_definition)
                        
                        with transaction.atomic():
                            # 鎻愬彇鏁呴殰-閮ㄤ欢鏄犲皠
                            fault_component_mappings = []
                            for edge in edges:
                                source_node = edge.source_node
                                target_node = edge.target_node
                                
                                if (source_node and target_node and 
                                    source_node.node_type == 'fault' and 
                                    target_node.node_type == 'component'):
                                    
                                    FaultComponentMapping.objects.get_or_create(
                                        msfg_definition=msfg_definition,
                                        fault_name=source_node.name,
                                        component_name=target_node.name,
                                        defaults={
                                            'weight': 1.0,
                                            'description': f'浠庡浘缁撴瀯鎻愬彇: {source_node.name} -> {target_node.name}'
                                        }
                                    )
                                    fault_component_mappings.append(f"{source_node.name} -> {target_node.name}")
                            
                            if fault_component_mappings:
                                logger.info(f"鎴愬姛鎻愬彇 {len(fault_component_mappings)} 涓晠闅?閮ㄤ欢鏄犲皠")
                            else:
                                logger.info("娌℃湁鎵惧埌鏁呴殰-閮ㄤ欢鏄犲皠")
                        
                        # 3. 璁板綍娴嬬偣-鏁呴殰鏄犲皠锛堜緵鐢ㄦ埛鎵嬪姩閰嶇疆锛?                        test_fault_mappings = []
                        for edge in edges:  # 浣跨敤鍚屼竴涓猠dges鍙橀噺
                            source_node = edge.source_node
                            target_node = edge.target_node
                            
                            if (source_node and target_node and 
                                source_node.node_type == 'test' and 
                                target_node.node_type == 'fault'):
                                
                                test_fault_mappings.append(f"{source_node.name} -> {target_node.name}")
                        
                        if test_fault_mappings:
                            logger.info(f"鍙戠幇 {len(test_fault_mappings)} 涓祴鐐?鏁呴殰鏄犲皠闇€瑕佹墜鍔ㄩ厤缃? {test_fault_mappings}")
                        else:
                            logger.info("娌℃湁鎵惧埌娴嬬偣-鏁呴殰鏄犲皠")
                                
                    except Exception as e:
                        logger.warning(f"鎻愬彇鏄犲皠鍏崇郴澶辫触: {e}")
                        
                except Exception as e:
                    logger.warning(f"鑷姩鎻愬彇鏄犲皠鍏崇郴澶辫触: {e}")
                    # 澶囩敤鏂规
                    try:
                        from .algorithms.msfg.component_integration import ensure_msfg_component_mappings
                        ensure_msfg_component_mappings(msfg_definition)
                    except Exception as e2:
                        logger.error(f"澶囩敤鏄犲皠鏂规涔熷け璐? {e2}")
                
                # 娓呯悊涓嶅湪MSFG.component_names涓殑鏄犲皠
                try:
                    self._cleanup_invalid_mappings(msfg_definition)
                except Exception as e:
                    logger.warning(f"娓呯悊鏃犳晥鏄犲皠澶辫触: {e}")
                
                # 鍚屾閮ㄤ欢瀹氫箟鍒拌鍒欐娴嬫ā鍧?                try:
                    from .algorithms.msfg.component_integration import sync_msfg_component_definitions
                    sync_result = sync_msfg_component_definitions(cmg_model)
                    logger.info(f"MSFG閮ㄤ欢鍚屾缁撴灉: {sync_result}")
                except Exception as e:
                    logger.warning(f"鍚屾MSFG閮ㄤ欢瀹氫箟澶辫触: {e}")
            
            return Response({
                'status': 'success', 
                'msfg_id': msfg_definition.id,
                'message': f'MSFG閰嶇疆 "{config_name}" 淇濆瓨鎴愬姛锛屽凡鑷姩鏇存柊閮ㄤ欢鏄犲皠'
            })
            
        except Exception as e:
            logger.error(f"淇濆瓨MSFG閰嶇疆澶辫触: {e}")
            return Response({'error': f'淇濆瓨澶辫触: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='validate-mappings')
    def validate_mappings(self, request):
        """楠岃瘉MSFG鏄犲皠瀹屾暣鎬?""
        try:
            msfg_definition_id = request.data.get('msfg_definition_id')
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            msfg_definition = MSFGDefinition.objects.get(id=msfg_definition_id)
            
            # 鑾峰彇鎵€鏈夋槧灏?            test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
            fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
            
            # 鍒嗘瀽鏄犲皠瀹屾暣鎬?            test_names = msfg_definition.test_names or []
            fault_names = msfg_definition.fault_names or []
            component_names = msfg_definition.component_names or []
            
            mapped_tests = set(test_component_mappings.values_list('test_point_name', flat=True))
            mapped_faults = set(fault_component_mappings.values_list('fault_name', flat=True))
            mapped_components = set()
            mapped_components.update(test_component_mappings.values_list('component_name', flat=True))
            mapped_components.update(fault_component_mappings.values_list('component_name', flat=True))
            
            unmapped_tests = [t for t in test_names if t not in mapped_tests]
            unmapped_faults = [f for f in fault_names if f not in mapped_faults]
            unmapped_components = [c for c in component_names if c not in mapped_components]
            
            # 璁＄畻瑕嗙洊鐜?            total_items = len(test_names) + len(fault_names)
            total_mappings = len(test_component_mappings) + len(fault_component_mappings)
            coverage = (total_mappings / total_items * 100) if total_items > 0 else 0
            
            validation_result = {
                'msfg_definition': {
                    'id': msfg_definition.id,
                    'name': msfg_definition.name,
                    'test_count': len(test_names),
                    'fault_count': len(fault_names),
                    'component_count': len(component_names)
                },
                'mapping_stats': {
                    'test_component_mappings': len(test_component_mappings),
                    'fault_component_mappings': len(fault_component_mappings),
                    'total_mappings': total_mappings,
                    'coverage_percentage': round(coverage, 1)
                },
                'validation_issues': {
                    'unmapped_tests': unmapped_tests,
                    'unmapped_faults': unmapped_faults,
                    'unmapped_components': unmapped_components
                },
                'validation_summary': {
                    'is_complete': len(unmapped_tests) == 0 and len(unmapped_faults) == 0,
                    'coverage_level': 'excellent' if coverage >= 90 else 'good' if coverage >= 70 else 'fair' if coverage >= 50 else 'poor'
                }
            }
            
            return Response(validation_result)
            
        except MSFGDefinition.DoesNotExist:
            return Response({'error': 'MSFG瀹氫箟涓嶅瓨鍦?}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"楠岃瘉鏄犲皠澶辫触: {e}")
            return Response({'error': f'楠岃瘉澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='test-mapping-logic')
    def test_mapping_logic(self, request):
        """娴嬭瘯MSFG鎺ㄧ悊閫昏緫"""
        try:
            msfg_definition_id = request.data.get('msfg_definition_id')
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            msfg_definition = MSFGDefinition.objects.get(id=msfg_definition_id)
            
            # 鑾峰彇MSFG鑺傜偣鍜岃竟
            test_nodes = list(MSFGNode.objects.filter(msfg_definition=msfg_definition, node_type='test'))
            fault_nodes = list(MSFGNode.objects.filter(msfg_definition=msfg_definition, node_type='fault'))
            edges = list(MSFGEdge.objects.filter(msfg_definition=msfg_definition))
            
            # 鑾峰彇鏄犲皠鍏崇郴
            test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
            fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
            
            # 鏋勫缓娴嬭瘯鏁版嵁
            test_scores = {node.name: [0.5] for node in test_nodes}  # 妯℃嫙娴嬭瘯鍒嗘暟
            
            # 鏋勫缓閮ㄤ欢鏄犲皠
            component_mappings = {}
            for mapping in fault_component_mappings:
                component_name = mapping.component_name
                if component_name not in component_mappings:
                    component_mappings[component_name] = []
                component_mappings[component_name].append(mapping.fault_name)
            
            # 娴嬭瘯鎺ㄧ悊閫昏緫
            from .algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            import time
            
            start_time = time.time()
            
            fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
            
            try:
                analysis_result = fusion_algorithm.run_advanced_analysis(
                    test_scores=test_scores,
                    test_nodes=test_nodes,
                    fault_nodes=fault_nodes,
                    edges=edges,
                    component_mappings=component_mappings
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                test_result = {
                    'success': True,
                    'execution_time': round(execution_time, 3),
                    'test_data': {
                        'test_nodes_count': len(test_nodes),
                        'fault_nodes_count': len(fault_nodes),
                        'edges_count': len(edges),
                        'component_mappings_count': len(component_mappings)
                    },
                    'analysis_result': {
                        'test_results_count': len(analysis_result.get('test_results', {})),
                        'fault_results_count': len(analysis_result.get('fault_results', {})),
                        'component_results_count': len(analysis_result.get('component_results', {})),
                        'system_results': analysis_result.get('system_results', {})
                    },
                    'mapping_validation': {
                        'test_component_mappings': len(test_component_mappings),
                        'fault_component_mappings': len(fault_component_mappings),
                        'mapped_components': list(component_mappings.keys())
                    }
                }
                
                return Response(test_result)
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                
                test_result = {
                    'success': False,
                    'execution_time': round(execution_time, 3),
                    'error': str(e),
                    'test_data': {
                        'test_nodes_count': len(test_nodes),
                        'fault_nodes_count': len(fault_nodes),
                        'edges_count': len(edges),
                        'component_mappings_count': len(component_mappings)
                    }
                }
                
                return Response(test_result, status=status.HTTP_400_BAD_REQUEST)
            
        except MSFGDefinition.DoesNotExist:
            return Response({'error': 'MSFG瀹氫箟涓嶅瓨鍦?}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"娴嬭瘯鎺ㄧ悊閫昏緫澶辫触: {e}")
            return Response({'error': f'娴嬭瘯澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='generate-mapping-report')
    def generate_mapping_report(self, request):
        """鐢熸垚鏄犲皠鍏崇郴鎶ュ憡"""
        try:
            msfg_definition_id = request.data.get('msfg_definition_id')
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            msfg_definition = MSFGDefinition.objects.get(id=msfg_definition_id)
            
            # 鑾峰彇鎵€鏈夋槧灏?            test_component_mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition)
            fault_component_mappings = FaultComponentMapping.objects.filter(msfg_definition=msfg_definition)
            
            # 鐢熸垚鎶ュ憡鏁版嵁
            report_data = {
                'report_info': {
                    'generated_at': timezone.now().isoformat(),
                    'msfg_definition_id': msfg_definition.id,
                    'msfg_definition_name': msfg_definition.name,
                    'cmg_model_name': msfg_definition.cmg_model.model_name if msfg_definition.cmg_model else 'Unknown'
                },
                'statistics': {
                    'test_names_count': len(msfg_definition.test_names or []),
                    'fault_names_count': len(msfg_definition.fault_names or []),
                    'component_names_count': len(msfg_definition.component_names or []),
                    'test_component_mappings_count': len(test_component_mappings),
                    'fault_component_mappings_count': len(fault_component_mappings),
                    'total_mappings_count': len(test_component_mappings) + len(fault_component_mappings)
                },
                'test_component_mappings': [
                    {
                        'id': mapping.id,
                        'test_point_name': mapping.test_point_name,
                        'component_name': mapping.component_name,
                        'weight': mapping.weight,
                        'importance_weight': mapping.importance_weight,
                        'is_critical': mapping.is_critical,
                        'description': mapping.description,
                        'created_at': mapping.created_at.isoformat(),
                        'updated_at': mapping.updated_at.isoformat()
                    }
                    for mapping in test_component_mappings
                ],
                'fault_component_mappings': [
                    {
                        'id': mapping.id,
                        'fault_name': mapping.fault_name,
                        'component_name': mapping.component_name,
                        'weight': mapping.weight,
                        'is_critical': mapping.is_critical,
                        'description': mapping.description,
                        'created_at': mapping.created_at.isoformat(),
                        'updated_at': mapping.updated_at.isoformat()
                    }
                    for mapping in fault_component_mappings
                ],
                'component_summary': self._generate_component_summary(msfg_definition, test_component_mappings, fault_component_mappings)
            }
            
            return Response(report_data)
            
        except MSFGDefinition.DoesNotExist:
            return Response({'error': 'MSFG瀹氫箟涓嶅瓨鍦?}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"鐢熸垚鏄犲皠鎶ュ憡澶辫触: {e}")
            return Response({'error': f'鐢熸垚鎶ュ憡澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_component_summary(self, msfg_definition, test_component_mappings, fault_component_mappings):
        """鐢熸垚閮ㄤ欢鏄犲皠鎽樿"""
        component_names = msfg_definition.component_names or []
        component_summary = {}
        
        for component_name in component_names:
            # 缁熻娴嬬偣鏄犲皠
            test_mappings = test_component_mappings.filter(component_name=component_name)
            test_points = [m.test_point_name for m in test_mappings]
            
            # 缁熻鏁呴殰鏄犲皠
            fault_mappings = fault_component_mappings.filter(component_name=component_name)
            faults = [m.fault_name for m in fault_mappings]
            
            # 璁＄畻鏉冮噸缁熻
            test_weights = [m.weight for m in test_mappings]
            fault_weights = [m.weight for m in fault_mappings]
            
            component_summary[component_name] = {
                'test_points': test_points,
                'faults': faults,
                'test_points_count': len(test_points),
                'faults_count': len(faults),
                'total_mappings': len(test_points) + len(faults),
                'avg_test_weight': sum(test_weights) / len(test_weights) if test_weights else 0,
                'avg_fault_weight': sum(fault_weights) / len(fault_weights) if fault_weights else 0,
                'is_critical': any(m.is_critical for m in test_mappings) or any(m.is_critical for m in fault_mappings)
            }
        
        return component_summary
    
    def _extract_component_names(self, data: Any) -> List[str]:
        """浠嶮SFG鏁版嵁涓彁鍙栫粍浠跺悕绉?""
        components = []
        try:
            def collect_from_nodes(nodes: List[dict]):
                for node in nodes or []:
                    node_type = str(node.get('type') or '')
                    # 璇嗗埆 subsystem-node/system-node/component-node 绛?                    if ('system' in node_type or 'component' in node_type) and 'root' not in node_type.lower():
                        name = (
                            (node.get('text') or {}).get('value') or 
                            node.get('name') or 
                            (node.get('properties') or {}).get('tableName') or 
                            node.get('id')
                        )
                        name = str(name).strip() if name else ''
                        if name and name.lower() not in ['root', 'system', '']:
                            components.append(name)

            if isinstance(data, dict):
                # 鐩存帴 nodes/edges 缁撴瀯
                collect_from_nodes(data.get('nodes') or [])
            elif isinstance(data, list):
                # SystemData 鍒楄〃锛氶亶鍘嗘墍鏈夌郴缁?                for sys_item in data:
                    if isinstance(sys_item, dict):
                        collect_from_nodes((sys_item.get('data') or {}).get('nodes') or [])
        except Exception as e:
            logger.error(f"鎻愬彇閮ㄤ欢鍚嶇О澶辫触: {e}")
        
        # 鍘婚噸骞朵繚鎸佺浉瀵归『搴?        seen = set()
        result = []
        for c in components:
            if c not in seen:
                seen.add(c)
                result.append(c)
        return result
    
    def _cleanup_invalid_mappings(self, msfg_definition: MSFGDefinition):
        """娓呯悊涓嶅湪MSFG.component_names涓殑鏄犲皠"""
        try:
            available_components = msfg_definition.component_names or []
            
            # 鏌ユ壘鏃犳晥鐨勬槧灏?            invalid_mappings = TestPointComponentMapping.objects.filter(
                msfg_definition=msfg_definition
            ).exclude(component_name__in=available_components)
            
            if invalid_mappings.exists():
                invalid_count = invalid_mappings.count()
                invalid_mappings.delete()
                logger.info(f"娓呯悊浜?{invalid_count} 涓棤鏁堢殑閮ㄤ欢鏄犲皠")
                
        except Exception as e:
            logger.error(f"娓呯悊鏃犳晥鏄犲皠澶辫触: {e}")
            raise
    
    def _extract_test_names(self, data: Any) -> List[str]:
        """浠嶮SFG鏁版嵁涓彁鍙栨祴璇曠偣鍚嶇О (姝ゆ柟娉曞皢琚純鐢紝閫昏緫宸茬Щ鑷砱raph_parser)"""
        test_names: List[str] = []
        try:
            def collect(nodes: List[dict]):
                for n in nodes or []:
                    ntype = str(n.get('type') or '')
                    if 'test' in ntype:
                        name = str((n.get('text') or {}).get('value') or n.get('name') or n.get('id'))
                        if name:
                            test_names.append(name)

            if isinstance(data, dict):
                collect(data.get('nodes') or [])
            elif isinstance(data, list):
                for sys_item in data:
                    if isinstance(sys_item, dict):
                        collect((sys_item.get('data') or {}).get('nodes') or [])
        except Exception:
            pass
        # 鍘婚噸
        seen = set()
        result = []
        for t in test_names:
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result
    
    def _extract_fault_names(self, data: Any) -> List[str]:
        """浠嶮SFG鏁版嵁涓彁鍙栨晠闅滃悕绉?(姝ゆ柟娉曞皢琚純鐢紝閫昏緫宸茬Щ鑷砱raph_parser)"""
        fault_names: List[str] = []
        try:
            def collect(nodes: List[dict]):
                for n in nodes or []:
                    ntype = str(n.get('type') or '')
                    if 'fault' in ntype:
                        name = str((n.get('text') or {}).get('value') or n.get('name') or n.get('id'))
                        if name:
                            fault_names.append(name)

            if isinstance(data, dict):
                collect(data.get('nodes') or [])
            elif isinstance(data, list):
                for sys_item in data:
                    if isinstance(sys_item, dict):
                        collect((sys_item.get('data') or {}).get('nodes') or [])
        except Exception:
            pass
        seen = set()
        result = []
        for f in fault_names:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result
    
    def _save_nodes_and_edges(self, msfg_definition: MSFGDefinition, nodes: List[Dict], edges: List[Dict]):
        """淇濆瓨鑺傜偣鍜岃竟淇℃伅鍒版暟鎹簱 (浣跨敤宸茶В鏋愮殑鑺傜偣鍜岃竟鍒楄〃)"""
        try:
            # 娓呯┖鏃ц妭鐐逛笌杈?            MSFGNode.objects.filter(msfg_definition=msfg_definition).delete()
            MSFGEdge.objects.filter(msfg_definition=msfg_definition).delete()
            
            # 淇濆瓨鑺傜偣
            id_to_node = {}
            for n in nodes:
                nid = str(n.get('id'))
                # 鉁?鏍稿績鏀归€狅細浣跨敤宸叉爣鍑嗗寲鐨?'category' 瀛楁鏉ョ‘瀹?node_type
                category = str(n.get('category', 'Component')).lower()
                
                if category == 'test':
                    node_type = 'test'
                elif category == 'fault':
                    node_type = 'fault'
                elif category == 'and':
                    node_type = 'and' # 鍋囪妯″瀷鏀寔 'and' 绫诲瀷
                else: # Component
                    node_type = 'component'
                
                # 鏀硅繘鐨勮妭鐐瑰悕绉版彁鍙栭€昏緫锛氫紭鍏堜娇鐢?properties.tableName
                props = n.get('properties') or {}
                name = (
                    props.get('tableName') or
                    (n.get('text') or {}).get('value') or 
                    n.get('name') or 
                    nid
                )
                name = str(name).strip() if name else nid
                x = float((n.get('x') or 0))
                y = float((n.get('y') or 0))
                
                node_obj = MSFGNode.objects.create(
                    msfg_definition=msfg_definition,
                    node_id=nid,
                    node_type=node_type, # 鉁?浣跨敤鍩轰簬 category 鐨勫彲闈犵被鍨?                    name=name,
                    position_x=x,
                    position_y=y,
                    properties=props,
                )
                id_to_node[nid] = node_obj
            
            # 淇濆瓨杈?            for e in edges:
                eid = str(e.get('id'))
                sid = str((e.get('sourceNodeId') or e.get('source') or ''))
                tid = str((e.get('targetNodeId') or e.get('target') or ''))
                if not sid or not tid or sid not in id_to_node or tid not in id_to_node:
                    continue
                MSFGEdge.objects.create(
                    msfg_definition=msfg_definition,
                    edge_id=eid,
                    source_node=id_to_node[sid],
                    target_node=id_to_node[tid],
                    edge_type=str(e.get('type') or ''),
                    properties=e.get('properties') or {},
                )
            
            # 鑷姩鏇存柊MSFG瀹氫箟鐨刢omponent_names瀛楁
            try:
                from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg
                components = extract_components_from_msfg(msfg_definition)
                if components:
                    msfg_definition.component_names = components
                    msfg_definition.save(update_fields=['component_names', 'updated_at'])
                    logger.info(f"鑷姩鏇存柊MSFG {msfg_definition.name} 鐨刢omponent_names: {components}")
            except Exception as e:
                logger.warning(f"鑷姩鏇存柊component_names澶辫触: {e}")
                
        except Exception as e:
            logger.error(f"瑙ｆ瀽MSFG鑺傜偣/杈瑰け璐? {e}")
    
    def _update_component_definitions(self, cmg_model: PHMModel, components: List[str]):
        """鏇存柊缁勪欢瀹氫箟"""
        from rule_detection.models import ComponentDefinition
        
        for comp_name in components:
            ComponentDefinition.objects.get_or_create(
                cmg_model=cmg_model,
                component_name=comp_name,
                defaults={
                    'description': f'From MSFG: {comp_name}',
                    'parameters': []
                }
            )

    @action(detail=True, methods=['post'], url_path='extract-mappings-from-graph')
    def extract_mappings_preview(self, request, pk=None):
        """
        浠庣粰瀹氱殑鍥剧粨鏋勪腑棰勮鍙彁鍙栫殑鏄犲皠鍏崇郴锛屼笉淇濆瓨浠讳綍鍐呭銆?        """
        try:
            msfg = self.get_object()
            graph_data = request.data.get('graphData')
            if not graph_data:
                return Response({'error': 'graphData is required'}, status=status.HTTP_400_BAD_REQUEST)

            # 1. 浣跨敤涓庝繚瀛樻椂鐩稿悓鐨勯€昏緫鏉ヨВ鏋愬拰瑙勮寖鍖栧浘
            parsed_graph = normalize_and_parse_graph(graph_data)
            if not parsed_graph:
                return Response({'error': '鏃犳硶瑙ｆ瀽MSFG鍥剧粨鏋?}, status=status.HTTP_400_BAD_REQUEST)

            # 2. 浠庤В鏋愬悗鐨勫浘涓彁鍙栨槧灏勫叧绯?            mappings = extract_mappings_from_graph(parsed_graph)

            # 3. 杩斿洖鎻愬彇鐨勬槧灏勪綔涓洪瑙?            return Response({
                'success': True,
                'message': 'Mappings extracted successfully (preview only).',
                'msfg_definition_id': msfg.id,
                'extracted_mappings': mappings
            })

        except Exception as e:
            logger.error(f"鎻愬彇鏄犲皠棰勮澶辫触: {e}")
            return Response({'error': f'鎻愬彇澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='d-matrix')
    def get_d_matrix(self, request, pk=None):
        """
        鑾峰彇MSFG鐨勬晠闅淒鐭╅樀鏁版嵁
        杩斿洖锛氱煩闃垫暟鎹€佹祴璇曠偣鍚嶇О銆佹晠闅滃悕绉般€佽瘖鏂垎鏋愮瓑
        """
        try:
            msfg = self.get_object()
            
            # 馃敡 淇锛氫娇鐢ㄧ粺涓€鐨勮妭鐐规彁鍙栭€昏緫
            from .algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            fusion = AdvancedMSFGFusion()
            
            # 浣跨敤淇鍚庣殑缁熶竴鑺傜偣鎻愬彇
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
            edges = list(msfg.edges.all())
            
            if not test_nodes or not fault_nodes:
                return Response({
                    'error': 'MSFG涓病鏈夋祴璇曠偣鎴栨晠闅滆妭鐐?
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 鏋勫缓D鐭╅樀锛堜娇鐢ㄤ慨澶嶅悗鐨勯€昏緫锛?            D_matrix, test_name_to_idx, fault_name_to_idx = fusion.build_d_matrix(test_nodes, fault_nodes, edges, msfg)
            
            # 杞崲涓哄瘑闆嗙煩闃?            import numpy as np
            dense_matrix = D_matrix.toarray()
            
            # 鑾峰彇鍚嶇О鍒楄〃
            test_names = [test_nodes[i].name for i in range(len(test_nodes))]
            fault_names = [fault_nodes[i].name for i in range(len(fault_nodes))]
            
            # 璁＄畻缁熻淇℃伅
            nonzero_count = np.count_nonzero(dense_matrix)
            
            # 璇婃柇缁撴瀯鍒嗘瀽
            diagnostic_analysis = fusion._analyze_diagnostic_structure(
                D_matrix=D_matrix,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                fused_test_scores={tn.name: 0.5 for tn in test_nodes}  # 浣跨敤榛樿鍊艰繘琛屽垎鏋?            )
            
            # 鏋勫缓鍝嶅簲鏁版嵁
            response_data = {
                'shape': dense_matrix.shape,
                'matrix': dense_matrix.tolist(),
                'test_names': test_names,
                'fault_names': fault_names,
                'test_count': len(test_names),
                'fault_count': len(fault_names),
                'nonzero_count': int(nonzero_count),
                'analysis': {
                    'detectable_faults': diagnostic_analysis.get('detectable_faults', []),
                    'isolable_faults': diagnostic_analysis.get('isolable_faults', []),
                    'indistinguishable_groups': diagnostic_analysis.get('indistinguishable_groups', [])
                }
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"鑾峰彇D鐭╅樀澶辫触: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'鑾峰彇D鐭╅樀澶辫触: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='analysis/preview')
    def analysis_preview(self, request, pk=None):
        """
        棰勮涓€娆¤缁嗘娴嬫祦绋嬶細
        杈撳叆: { test_scores?: {name: score}, use_rules?: bool, data_point_id?: int }
        浼樺厛浣跨敤 test_scores锛涜嫢鏈彁渚涗笖 use_rules=true 涓?data_point_id 鎻愪緵锛屽垯浠?scoring 璁＄畻銆?        杩斿洖锛欴鐭╅樀褰㈢姸銆佽瀺鍚堝悗鐨勬祴璇曞垎銆佹晠闅?妯＄硦姒傜巼銆佽瘖鏂粨鏋勫垎鏋愪笌閮ㄤ欢鍋ュ悍銆?        """
        try:
            msfg = self.get_object()
            test_scores = request.data.get('test_scores') or {}
            use_rules = bool(request.data.get('use_rules') or False)
            data_point_id = request.data.get('data_point_id')

            # 馃敡 淇锛氫娇鐢ㄧ粺涓€鐨勮妭鐐规彁鍙栭€昏緫
            from .algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            fusion = AdvancedMSFGFusion()
            
            # 浣跨敤淇鍚庣殑缁熶竴鑺傜偣鎻愬彇
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
            edges = list(msfg.edges.all())
            details = None
            if use_rules and not test_scores and data_point_id:
                try:
                    dp = PHMData.objects.get(id=data_point_id)
                    from .services.testpoint_scoring import TestPointScoringService
                    svc = TestPointScoringService()
                    det = svc.calculate_test_scores_with_details(dp, msfg)
                    details = det
                    test_scores = det.get('scores', {})
                except Exception as e:
                    logger.warning(f"瑙勫垯渚ц绠楁祴鐐硅瘎鍒嗗け璐? {e}")
                    test_scores = {}

            # 缁熶竴涓?name-> [score]
            test_scores_wrapped = {k: [float(v)] for k, v in test_scores.items()}

            # 馃敡 淇锛氫娇鐢ㄤ慨澶嶅悗鐨勯儴浠舵槧灏勬瀯寤?            comp_map = fusion._build_component_mappings(msfg)

            D_matrix, _, _ = fusion.build_d_matrix(test_nodes, fault_nodes, edges, msfg)

            # 铻嶅悎娴嬭瘯鍒嗘暟锛坣ame->float锛?            fused_test_scores = fusion.fuse_test_scores(test_scores_wrapped)
            test_scores_array = __import__('numpy').array([
                fused_test_scores.get(tn.name, 0.2) for tn in test_nodes
            ], dtype=__import__('numpy').float32)

            # 鏁呴殰涓庢ā绯婃鐜?            fusion._last_test_scores_array = test_scores_array
            fault_prob = fusion.calculate_fault_probability(D_matrix, test_scores_array)
            fuzzy_prob = fusion.calculate_fuzzy_probability(D_matrix, fault_prob)

            # 璇婃柇缁撴瀯鍒嗘瀽
            diag_struct = fusion._analyze_diagnostic_structure(
                D_matrix=D_matrix,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                fused_test_scores=fused_test_scores
            )

            # 閮ㄤ欢涓庣郴缁?            component_health = fusion.calculate_component_health(
                fault_prob=fault_prob,
                fuzzy_prob=fuzzy_prob,
                fault_nodes=fault_nodes,
                component_mappings=comp_map,
            )
            system_health = fusion.calculate_system_health(component_health)

            # D鐭╅樀淇℃伅
            coo = D_matrix.tocoo()
            nnz = int(coo.nnz)
            sample_n = min(200, nnz)
            sample = []
            if nnz:
                import random
                idxs = list(range(nnz))
                random.shuffle(idxs)
                idxs = idxs[:sample_n]
                # 鍚嶇О鏄犲皠
                test_order = [t.name for t in test_nodes]
                fault_order = [f.name for f in fault_nodes]
                for i in idxs:
                    r = int(coo.row[i]); c = int(coo.col[i]); v = float(coo.data[i])
                    sample.append({
                        'fault_index': r,
                        'fault': fault_order[r] if r < len(fault_order) else r,
                        'test_index': c,
                        'test': test_order[c] if c < len(test_order) else c,
                        'weight': v,
                    })
            pipeline = {
                'graph': {
                    'test_count': len(test_nodes),
                    'fault_count': len(fault_nodes),
                    'edge_count': len(edges),
                },
                'd_matrix': {
                    'shape': tuple(D_matrix.shape),
                    'nnz': nnz,
                    'nonzero_sample': sample,
                    'test_order': [t.name for t in test_nodes],
                    'fault_order': [f.name for f in fault_nodes],
                },
                'test_scores': {
                    'input': test_scores,
                    'fused': fused_test_scores,
                    'array': [float(x) for x in test_scores_array.tolist()],
                    'rule_details': details or {},
                },
                'fault_inference': {
                    'fault_probability': {fault_nodes[i].name: float(fault_prob[i]) for i in range(len(fault_nodes))},
                    'fuzzy_probability': {fault_nodes[i].name: float(fuzzy_prob[i]) for i in range(len(fault_nodes))},
                },
                'diagnostic': diag_struct,
                'components': {
                    'mappings': comp_map,
                    'health': component_health,
                },
                'system': system_health,
            }

            # 鍚屾椂杩斿洖 run_advanced_analysis 鐨勭粨鏋滐紝渚夸簬涓€鑷存€у姣?            result = fusion.run_advanced_analysis(
                test_scores=test_scores_wrapped,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                edges=edges,
                component_mappings=comp_map,
            )
            return Response({'result': result, 'pipeline': pipeline})
        except Exception as e:
            logger.error(f"analysis_preview 澶辫触: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='sync-components')
    def sync_components(self, request):
        """鍚屾MSFG閮ㄤ欢瀹氫箟鍒拌鍒欐娴嬫ā鍧?""
        cmg_model_id = request.data.get('cmg_model_id')
        if not cmg_model_id:
            return Response(
                {'error': 'cmg_model_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from data_management.models import PHMModel
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
            
            from .algorithms.msfg.component_integration import sync_msfg_component_definitions
            result = sync_msfg_component_definitions(cmg_model)
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except PHMModel.DoesNotExist:
            return Response(
                {'error': 'PHM model not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"鍚屾MSFG閮ㄤ欢瀹氫箟澶辫触: {e}")
            return Response(
                {'error': f'鍚屾澶辫触: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='ensure-mappings')
    def ensure_mappings(self, request, pk=None):
        """纭繚MSFG閰嶇疆鏈夊畬鏁寸殑娴嬭瘯鐐?閮ㄤ欢鏄犲皠"""
        try:
            msfg_definition = self.get_object()
            
            from .algorithms.msfg.component_integration import ensure_msfg_component_mappings
            ensure_msfg_component_mappings(msfg_definition)
            
            return Response({
                'success': True,
                'message': f'宸叉洿鏂癕SFG "{msfg_definition.name}" 鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠'
            })
            
        except Exception as e:
            logger.error(f"纭繚MSFG閮ㄤ欢鏄犲皠澶辫触: {e}")
            return Response(
                {'error': f'鎿嶄綔澶辫触: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='components')
    def components(self, request, pk=None):
        """鑾峰彇MSFG瀹氫箟涓殑缁勪欢淇℃伅"""
        try:
            msfg_definition = self.get_object()
            # 浼樺厛杩斿洖瀹氫箟涓殑缁勪欢鍚嶇О鍒楄〃
            components = list(msfg_definition.component_names or [])
            if not components:
                # 鍏滃簳锛氫粠鍥句腑鎻愬彇缁勪欢鑺傜偣
                component_nodes = msfg_definition.nodes.filter(node_type='component')
                components = [node.name for node in component_nodes]
            return Response({
                'components': components,
                'total': len(components)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='faults')
    def faults(self, request, pk=None):
        """杩斿洖璇SFG瀹氫箟鐨勬晠闅滃悕绉板垪琛?""
        try:
            msfg = self.get_object()
            faults = list(msfg.fault_names or [])
            return Response({'faults': faults, 'total': len(faults)})
        except Exception as e:
            logger.error(f"鑾峰彇MSFG鏁呴殰鍒楄〃澶辫触: {e}")
            return Response({'faults': [], 'total': 0})
    
    @action(detail=False, methods=['get'], url_path='component-mappings')
    def component_mappings(self, request):
        """鑾峰彇娴嬭瘯鐐?閮ㄤ欢鏄犲皠"""
        try:
            msfg_definition_id = request.query_params.get('msfg_definition_id')
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            mappings = TestPointComponentMapping.objects.filter(
                msfg_definition_id=msfg_definition_id
            ).values('id', 'test_point_name', 'component_name', 'mapping_type', 'weight', 'description')
            
            # 杞崲瀛楁鍚嶄互鍖归厤鍓嶇鏈熸湜
            result = []
            for mapping in mappings:
                result.append({
                    'id': mapping['id'],
                    'test_point': mapping['test_point_name'],
                    'component': mapping['component_name'],
                    'mapping_type': mapping['mapping_type'],
                    'weight': mapping['weight'],
                    'description': mapping['description']
                })
            
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='component-mappings/batch')
    def batch_component_mappings(self, request):
        """鎵归噺淇濆瓨娴嬭瘯鐐?閮ㄤ欢鏄犲皠"""
        try:
            msfg_definition_id = request.data.get('msfg_definition_id')
            mappings = request.data.get('mappings', [])
            
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # 鍒犻櫎鐜版湁鏄犲皠
                TestPointComponentMapping.objects.filter(msfg_definition_id=msfg_definition_id).delete()
                
                # 鍒涘缓鏂版槧灏勶紙鍘婚噸+瑙勮寖鍖栵紝閬垮厤鍞竴閿啿绐侊級
                new_mappings = []
                seen = set()
                for m in mappings:
                    tp = (m.get('test_point') or m.get('test_point_name') or '').strip()
                    comp = (m.get('component') or m.get('component_name') or '').strip()
                    if not tp or not comp:
                        continue
                    key = (tp, comp)
                    if key in seen:
                        continue
                    seen.add(key)
                    new_mappings.append(TestPointComponentMapping(
                        msfg_definition_id=msfg_definition_id,
                        test_point_name=tp,
                        component_name=comp,
                        mapping_type=(m.get('mapping_type') or 'one_to_one'),
                        weight=float(m.get('weight') or 1.0),
                        description=(m.get('description') or '')
                    ))
                
                if new_mappings:
                    TestPointComponentMapping.objects.bulk_create(new_mappings, ignore_conflicts=True)
            
            return Response({'message': '鏄犲皠淇濆瓨鎴愬姛', 'count': len(new_mappings)})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='fix-components')
    def fix_components(self, request):
        """淇MSFG閮ㄤ欢鎻愬彇闂"""
        try:
            cmg_model_id = request.data.get('cmg_model_id')
            if not cmg_model_id:
                return Response({'error': '缂哄皯cmg_model_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 鏌ユ壘PHM妯″瀷
            try:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            except PHMModel.DoesNotExist:
                return Response({'error': f'鎵句笉鍒癐D涓簕cmg_model_id}鐨凜MG妯″瀷'}, status=status.HTTP_404_NOT_FOUND)
            
            # 鏌ユ壘娲昏穬鐨凪SFG閰嶇疆
            active_msfg = MSFGDefinition.objects.filter(
                cmg_model=cmg_model,
                is_active=True
            ).order_by('-updated_at').first()
            
            if not active_msfg:
                return Response({'error': f'鎵句笉鍒皗cmg_model.model_name}鐨勬椿璺僊SFG閰嶇疆'}, status=status.HTTP_404_NOT_FOUND)
            
            # 浠嶫SON閰嶇疆鏂囦欢鎻愬彇閮ㄤ欢
            import os
            import json
            
            json_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "澶氫俊鍙锋祦鍥鹃厤缃?json")
            if not os.path.exists(json_file_path):
                return Response({'error': '鎵句笉鍒板淇″彿娴佸浘閰嶇疆.json鏂囦欢'}, status=status.HTTP_404_NOT_FOUND)
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 鎻愬彇閮ㄤ欢
            components = []
            if 'SystemData' in config_data:
                system_data = config_data['SystemData']
                for system_item in system_data:
                    if 'data' in system_item and 'nodes' in system_item['data']:
                        nodes = system_item['data']['nodes']
                        for node in nodes:
                            node_type = node.get('type', '')
                            if node_type == 'subsystem-node':
                                properties = node.get('properties', {})
                                table_name = properties.get('tableName', '')
                                if table_name and table_name.strip():
                                    components.append(table_name.strip())
            
            # 鍘婚噸骞舵帓搴?            components = sorted(list(set(components)))
            
            if not components:
                return Response({'error': '鏃犳硶浠嶫SON鏂囦欢鎻愬彇鍒伴儴浠?}, status=status.HTTP_400_BAD_REQUEST)
            
            # 鏇存柊MSFG鐨刢omponent_names瀛楁
            active_msfg.component_names = components
            active_msfg.save(update_fields=['component_names', 'updated_at'])
            
            # 鍒犻櫎鐜版湁鐨勭郴缁熻妭鐐?            from msfg_analysis.models import MSFGNode
            existing_system_nodes = MSFGNode.objects.filter(
                msfg_definition=active_msfg,
                node_type='system'
            )
            if existing_system_nodes.exists():
                existing_system_nodes.delete()
            
            # 鍒涘缓鏂扮殑绯荤粺鑺傜偣
            import uuid
            created_nodes = 0
            for i, component_name in enumerate(components):
                node = MSFGNode.objects.create(
                    node_id=str(uuid.uuid4()),
                    msfg_definition=active_msfg,
                    name=component_name,
                    node_type='system',
                    position_x=100 + (i % 5) * 200,
                    position_y=100 + (i // 5) * 150,
                    properties={'tableName': component_name}
                )
                created_nodes += 1
            
            # 閲嶆柊杩愯閮ㄤ欢鏄犲皠
            from msfg_analysis.algorithms.msfg.component_integration import ensure_msfg_component_mappings
            ensure_msfg_component_mappings(active_msfg)
            
            # 鑾峰彇鏄犲皠鏁伴噺
            from msfg_analysis.models import TestPointComponentMapping
            mappings_count = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg).count()
            
            return Response({
                'success': True,
                'message': f'鎴愬姛淇{cmg_model.model_name}鐨勯儴浠舵彁鍙栭棶棰?,
                'details': {
                    'model_name': cmg_model.model_name,
                    'msfg_name': active_msfg.name,
                    'components_count': len(components),
                    'system_nodes_created': created_nodes,
                    'mappings_count': mappings_count,
                    'components': components
                }
            })
            
        except Exception as e:
            logger.error(f"淇閮ㄤ欢鎻愬彇澶辫触: {e}")
            return Response({'error': f'淇澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """鍒犻櫎MSFG閰嶇疆锛屽悓鏃跺垹闄ょ浉鍏崇殑鑺傜偣鍜岃竟"""
        instance = self.get_object()
        
        # 濡傛灉鏄綋鍓嶆縺娲荤殑閰嶇疆锛岄渶瑕侀€夋嫨鍏朵粬閰嶇疆浣滀负婵€娲荤姸鎬?        if instance.is_active:
            other_msfg = MSFGDefinition.objects.filter(
                cmg_model=instance.cmg_model
            ).exclude(id=instance.id).first()
            
            if other_msfg:
                other_msfg.is_active = True
                other_msfg.save()
        
        # 鍒犻櫎鐩稿叧鐨勫垎鏋愮粨鏋?        from .models import MSFGAnalysisResult
        MSFGAnalysisResult.objects.filter(msfg_definition=instance).delete()
        
        # 璋冪敤鐖剁被鍒犻櫎鏂规硶
        return super().destroy(request, *args, **kwargs)


class MSFGNodeViewSet(viewsets.ModelViewSet):
    """MSFG鑺傜偣瑙嗗浘闆?""
    
    queryset = MSFGNode.objects.all()
    serializer_class = MSFGNodeSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        msfg_id = self.request.query_params.get('msfg_id')
        if msfg_id:
            queryset = queryset.filter(msfg_definition_id=msfg_id)
        
        node_type = self.request.query_params.get('node_type')
        if node_type:
            queryset = queryset.filter(node_type=node_type)
        
        return queryset.order_by('name')


class MSFGEdgeViewSet(viewsets.ModelViewSet):
    """MSFG杈硅鍥鹃泦"""
    
    queryset = MSFGEdge.objects.all()
    serializer_class = MSFGEdgeSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        msfg_id = self.request.query_params.get('msfg_id')
        if msfg_id:
            queryset = queryset.filter(msfg_definition_id=msfg_id)
        
        return queryset.order_by('edge_id')


class MSFGAnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """MSFG鍒嗘瀽缁撴灉瑙嗗浘闆?""
    
    queryset = MSFGAnalysisResult.objects.select_related(
        'data_point', 'data_point__cmg', 'msfg_definition'
    ).all()
    serializer_class = MSFGAnalysisResultSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # 鍏堟帓搴忥紝鍐嶅垏鐗?        queryset = super().get_queryset().order_by('-created_at')

        # 鎸塁MG杩囨护
        cmg_id = self.request.query_params.get('cmg_id')
        if cmg_id:
            queryset = queryset.filter(data_point__cmg__cmg_id=cmg_id)
            
            # 浼樺厛浣跨敤婵€娲荤殑 MSFG 閰嶇疆锛涜嫢鏃犳縺娲婚厤缃紝鍒欎笉棰濆闄愬埗锛屽睍绀鸿 PHM 鐨勬墍鏈夌粨鏋?            try:
                from data_management.models import PHM
                cmg = PHM.objects.get(cmg_id=cmg_id)
                active_msfg = MSFGDefinition.objects.filter(
                    cmg_model=cmg.cmg_model,
                    is_active=True
                ).order_by('-updated_at').first()
                if active_msfg:
                    queryset = queryset.filter(msfg_definition=active_msfg)
            except PHM.DoesNotExist:
                queryset = queryset.none()

        # 鎸夊仴搴峰垎鏁拌寖鍥磋繃婊?        min_health_score = self.request.query_params.get('min_health_score')
        if min_health_score:
            try:
                queryset = queryset.filter(overall_health_score__gte=float(min_health_score))
            except ValueError:
                pass

        max_health_score = self.request.query_params.get('max_health_score')
        if max_health_score:
            try:
                queryset = queryset.filter(overall_health_score__lte=float(max_health_score))
            except ValueError:
                pass

        # 鎸夋椂闂磋寖鍥磋繃婊?        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(data_point__timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(data_point__timestamp__lte=end_time)

        # 闄愬埗鏁伴噺锛堟帓搴忎箣鍚庯級锛氳嫢鏃犳椂闂存涓旀湭鎻愪緵limit锛岄粯璁よ繑鍥炴渶杩?00鏉?        limit = self.request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        elif not start_time and not end_time:
            queryset = queryset[:100]

        return queryset

    @action(detail=False, methods=['post'], url_path='analyze-point')
    def analyze_point(self, request):
        """瀵瑰崟鐐规祴璇曞垎鏁颁笌褰撳墠MSFG杩涜铻嶅悎锛岃繑鍥炵郴缁?鏁呴殰灞傜粨鏋溿€?
        璇锋眰浣? {
          cmg_model_id: int,
          msfg_id?: int  # 鍙€夛紝涓嶆彁渚涘垯鐢ㄦ渶杩戞縺娲荤殑瀹氫箟
          test_scores: { 娴嬭瘯鐐瑰悕绉? 鍒嗘暟(0..1) }
        }
        """
        cmg_model_id = request.data.get('cmg_model_id')
        test_scores = request.data.get('test_scores') or {}
        msfg_id = request.data.get('msfg_id')
        if not cmg_model_id:
            return Response({'error': 'cmg_model_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, status=status.HTTP_404_NOT_FOUND)
        if msfg_id:
            msfg = MSFGDefinition.objects.filter(id=msfg_id, cmg_model=cmg_model).first()
        else:
            msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).order_by('-updated_at').first()
        if not msfg:
            return Response({'error': 'MSFG definition not found'}, status=status.HTTP_404_NOT_FOUND)

        # 鏋勯€犳槧灏? test_id->name, fault_id->name, edges鍒楄〃
        nodes = list(msfg.nodes.all())
        edges_qs = list(msfg.edges.all())
        test_name_by_id = {n.node_id: n.name for n in nodes if n.node_type == 'test'}
        fault_name_by_id = {n.node_id: n.name for n in nodes if n.node_type == 'fault'}
        edges = [(e.source_node.node_id, e.target_node.node_id) for e in edges_qs]

        # 浣跨敤澧炲己鐨凪SFG鍒嗘瀽锛屽寘鍚儴浠跺仴搴风姸鎬佹帹鐞?        from .algorithms.msfg.fusion import enhanced_msfg_analysis
        
        analysis_result = enhanced_msfg_analysis(
            test_scores=test_scores,
            edges=edges,
            test_name_by_id=test_name_by_id,
            fault_name_by_id=fault_name_by_id,
            nodes=nodes,
            msfg_definition=msfg,
            include_component_analysis=True
        )
        
        return Response({
            'test_scores': test_scores,
            'fault_scores': analysis_result['fault_results'],
            'system': analysis_result['system_results'],
            'component_results': analysis_result['component_results'],
            'msfg_name': msfg.name,
            'analysis_metadata': analysis_result['analysis_metadata']
        })


class TestPointRuleMappingViewSet(viewsets.ModelViewSet):
    """瑙勫垯-娴嬭瘯鐐规槧灏?CRUD"""
    queryset = TestPointRuleMapping.objects.select_related('cmg_model', 'rule_definition').all()
    serializer_class = TestPointRuleMappingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        if cmg_model_id:
            qs = qs.filter(cmg_model_id=cmg_model_id)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            qs = qs.filter(rule_definition__rule_id=rule_id)
        return qs.order_by('rule_definition__rule_id')


class TestPointRuleViewSet(viewsets.ModelViewSet):
    """鐙珛 MSFG 娴嬬偣瑙勫垯 CRUD锛堜笉渚濊禆瑙勫垯妫€娴嬫ā鍧楋級銆?""
    queryset = TestPointRule.objects.select_related('cmg_model', 'msfg_definition').all()
    serializer_class = TestPointRuleSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """閲嶅啓 create 鏂规硶浠ユ崟鑾疯缁嗙殑楠岃瘉閿欒"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"TestPointRule鍒涘缓璇锋眰鏁版嵁: {request.data}")
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except serializers.ValidationError as e:
            logger.error(f"TestPointRule楠岃瘉閿欒: {e}")
            return Response({'error': str(e), 'details': e.detail if hasattr(e, 'detail') else str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"TestPointRule鍒涘缓寮傚父: {e}")
            return Response({'error': f'鍒涘缓澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        """鍒涘缓娴嬬偣瑙勫垯鏃惰嚜鍔ㄨ缃?msfg_definition"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 璁板綍楠岃瘉鍚庣殑鏁版嵁
        logger.info(f"楠岃瘉鍚庣殑鏁版嵁: {serializer.validated_data}")
        
        # 濡傛灉娌℃湁鏄庣‘鎸囧畾 msfg_definition锛屽垯浣跨敤娲昏穬鐨?MSFG 閰嶇疆
        msfg_definition = serializer.validated_data.get('msfg_definition')
        if not msfg_definition:
            cmg_model = serializer.validated_data.get('cmg_model')
            if cmg_model:
                logger.info(f"鏌ユ壘PHM妯″瀷: {cmg_model} (绫诲瀷: {type(cmg_model)})")
                
                # 纭繚 cmg_model 鏄?PHMModel 瀹炰緥
                if isinstance(cmg_model, int):
                    cmg_model_id = cmg_model
                elif hasattr(cmg_model, 'id'):
                    cmg_model_id = cmg_model.id
                else:
                    try:
                        cmg_model_id = int(cmg_model)
                    except (ValueError, TypeError):
                        cmg_model_id = None
                
                if cmg_model_id:
                    active_msfg = MSFGDefinition.objects.filter(
                        cmg_model_id=cmg_model_id,
                        is_active=True
                    ).order_by('-updated_at').first()
                    
                    logger.info(f"鎵惧埌鐨勬椿璺僊SFG: {active_msfg}")
                    
                    if active_msfg:
                        # 灏嗘壘鍒扮殑娲昏穬MSFG璁剧疆鍒伴獙璇佹暟鎹腑
                        serializer.validated_data['msfg_definition'] = active_msfg
                        logger.info(f"鑷姩璁剧疆MSFG瀹氫箟: {active_msfg.name}")
                    else:
                        # 鍏佽鍒涘缓娌℃湁MSFG瀹氫箟鐨勮鍒欙紝浣嗙粰鍑鸿鍛?                        logger.warning(f"娌℃湁鎵惧埌PHM妯″瀷ID {cmg_model_id}鐨勬椿璺僊SFG閰嶇疆锛屽垱寤鸿鍒欐椂msfg_definition涓簄ull")
                        serializer.validated_data['msfg_definition'] = None
                else:
                    raise serializers.ValidationError(f"鏃犳晥鐨凜MG妯″瀷ID: {cmg_model}")
            else:
                raise serializers.ValidationError("蹇呴』鎸囧畾PHM妯″瀷")
        
        # 淇濆瓨瀵硅薄
        serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        test_name = self.request.query_params.get('test_name')
        is_online = self.request.query_params.get('is_online')
        msfg_definition_id = self.request.query_params.get('msfg_definition_id')
        only_active_msfg = self.request.query_params.get('only_active_msfg', 'true')
        
        # 杩囨护PHM妯″瀷
        if cmg_model_id:
            qs = qs.filter(cmg_model_id=cmg_model_id)
            
        # 濡傛灉鎸囧畾浜嗙壒瀹氱殑MSFG瀹氫箟
        if msfg_definition_id:
            qs = qs.filter(msfg_definition_id=msfg_definition_id)
        # 榛樿鍙樉绀烘椿璺僊SFG閰嶇疆鐨勮鍒?        elif only_active_msfg.lower() == 'true' and cmg_model_id:
            # 鑾峰彇璇MG妯″瀷鐨勬椿璺僊SFG瀹氫箟
            active_msfg = MSFGDefinition.objects.filter(
                cmg_model_id=cmg_model_id, 
                is_active=True
            ).order_by('-updated_at').first()
            
            if active_msfg:
                qs = qs.filter(msfg_definition=active_msfg)
            else:
                # 濡傛灉娌℃湁娲昏穬鐨凪SFG閰嶇疆锛岃繑鍥炵┖缁撴灉
                qs = qs.none()
        
        if test_name:
            qs = qs.filter(test_name=test_name)
        if is_online is not None:
            qs = qs.filter(is_online=is_online.lower() == 'true')
            
        return qs.order_by('test_name', 'rule_id')


class TestPointComponentMappingViewSet(viewsets.ModelViewSet):
    """娴嬭瘯鐐?閮ㄤ欢鏄犲皠绠＄悊瑙嗗浘闆?""
    
    queryset = TestPointComponentMapping.objects.select_related('msfg_definition', 'msfg_definition__cmg_model').all()
    serializer_class = TestPointComponentMappingSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """鍒涘缓鏄犲皠鏃堕獙璇侀儴浠跺悕绉?""
        self._validate_component_name(serializer.validated_data)
        serializer.save()
    
    def perform_update(self, serializer):
        """鏇存柊鏄犲皠鏃堕獙璇侀儴浠跺悕绉?""
        self._validate_component_name(serializer.validated_data)
        serializer.save()
    
    def _validate_component_name(self, validated_data):
        """楠岃瘉閮ㄤ欢鍚嶇О鏄惁鍦∕SFG.component_names涓?""
        msfg_definition = validated_data.get('msfg_definition')
        component_name = validated_data.get('component_name')
        
        if msfg_definition and component_name:
            available_components = msfg_definition.component_names or []
            if component_name not in available_components:
                raise serializers.ValidationError(
                    f"閮ㄤ欢鍚嶇О '{component_name}' 涓嶅湪MSFG瀹氫箟涓€?
                    f"鍙敤閮ㄤ欢: {', '.join(available_components)}"
                )
    
    def get_queryset(self):
        qs = super().get_queryset()
        msfg_definition_id = self.request.query_params.get('msfg_definition_id')
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        component_name = self.request.query_params.get('component_name')
        component_type = self.request.query_params.get('component_type')
        
        # 妫€鏌?msfg_definition_id 鏄惁涓烘湁鏁堢殑鏁板瓧
        if msfg_definition_id and msfg_definition_id != 'null' and msfg_definition_id.isdigit():
            qs = qs.filter(msfg_definition_id=msfg_definition_id)
        
        if cmg_model_id and cmg_model_id != 'null' and cmg_model_id.isdigit():
            qs = qs.filter(msfg_definition__cmg_model_id=cmg_model_id)
            
        if component_name:
            qs = qs.filter(component_name__icontains=component_name)
            
        if component_type:
            qs = qs.filter(component_type=component_type)
        
        return qs.order_by('component_name', 'test_point_name')
    
    @action(detail=False, methods=['get'])
    def components(self, request):
        """鑾峰彇鎵€鏈夐儴浠跺悕绉板垪琛?""
        msfg_definition_id = request.query_params.get('msfg_definition_id')
        qs = self.get_queryset()
        
        if msfg_definition_id:
            qs = qs.filter(msfg_definition_id=msfg_definition_id)
            
        components = qs.values_list('component_name', flat=True).distinct().order_by('component_name')
        return Response(list(components))
    
    @action(detail=False, methods=['get'])
    def test_points(self, request):
        """鑾峰彇鎵€鏈夋祴璇曠偣鍚嶇О鍒楄〃"""
        msfg_definition_id = request.query_params.get('msfg_definition_id')
        qs = self.get_queryset()
        
        if msfg_definition_id:
            qs = qs.filter(msfg_definition_id=msfg_definition_id)
            
        test_points = qs.values_list('test_point_name', flat=True).distinct().order_by('test_point_name')
        return Response(list(test_points))
    
    @action(detail=False, methods=['get'], url_path='available-components')
    def available_components(self, request):
        """鑾峰彇鍙敤鐨勯儴浠跺垪琛紙鏉ヨ嚜MSFG.component_names锛?""
        try:
            # 鑾峰彇MSFG瀹氫箟ID
            msfg_definition_id = request.query_params.get('msfg_definition_id')
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # 鑾峰彇MSFG瀹氫箟
            msfg_definition = MSFGDefinition.objects.get(id=msfg_definition_id)
            
            # 杩斿洖MSFG涓畾涔夌殑閮ㄤ欢鍒楄〃
            component_names = msfg_definition.component_names or []
            
            return Response({
                'components': component_names,
                'count': len(component_names),
                'msfg_name': msfg_definition.name
            })
            
        except MSFGDefinition.DoesNotExist:
            return Response({'error': 'MSFG瀹氫箟涓嶅瓨鍦?}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"鑾峰彇鍙敤閮ㄤ欢鍒楄〃澶辫触: {e}")
            return Response({'error': f'鑾峰彇澶辫触: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='batch')
    def batch(self, request):
        """鎵归噺淇濆瓨娴嬭瘯鐐?閮ㄤ欢鏄犲皠锛堣矾寰勶細/msfg/component-mappings/batch/锛?""
        msfg_definition_id = request.data.get('msfg_definition_id')
        mappings = request.data.get('mappings') or []
        if not msfg_definition_id:
            return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            msfg_definition = MSFGDefinition.objects.get(id=msfg_definition_id)
        except MSFGDefinition.DoesNotExist:
            return Response({'error': '鏃犳晥鐨刴sfg_definition_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                TestPointComponentMapping.objects.filter(msfg_definition=msfg_definition).delete()
                to_create = []
                seen = set()
                for m in mappings:
                    tp = (m.get('test_point') or m.get('test_point_name') or '').strip()
                    comp = (m.get('component') or m.get('component_name') or '').strip()
                    if not tp or not comp:
                        continue
                    key = (tp, comp)
                    if key in seen:
                        continue
                    seen.add(key)
                    to_create.append(TestPointComponentMapping(
                        msfg_definition=msfg_definition,
                        test_point_name=tp,
                        component_name=comp,
                        mapping_type=m.get('mapping_type') or 'one_to_one',
                        weight=float(m.get('weight') or 1.0),
                        importance_weight=float(m.get('importance_weight') or 1.0),
                        is_critical=bool(m.get('is_critical') or False),
                        description=m.get('description') or ''
                    ))
                if to_create:
                    # 鍚屼竴鎵瑰唴鏃犻噸澶嶏紱鑻ヤ粛鏈夊苟鍙戝啿绐侊紝蹇界暐
                    TestPointComponentMapping.objects.bulk_create(to_create, ignore_conflicts=True)
            return Response({'saved': len(to_create)})
        except Exception as e:
            logger.error(f"鎵归噺淇濆瓨娴嬭瘯鐐规槧灏勫け璐? {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class FaultComponentMappingViewSet(viewsets.ModelViewSet):
    """鏁呴殰-閮ㄤ欢鏄犲皠绠＄悊瑙嗗浘闆?""

    queryset = FaultComponentMapping.objects.select_related('msfg_definition', 'msfg_definition__cmg_model').all()
    serializer_class = FaultComponentMappingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        msfg_definition_id = self.request.query_params.get('msfg_definition_id')
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        component_name = self.request.query_params.get('component_name')
        fault_name = self.request.query_params.get('fault_name')
        if msfg_definition_id and str(msfg_definition_id).isdigit():
            qs = qs.filter(msfg_definition_id=msfg_definition_id)
        if cmg_model_id and str(cmg_model_id).isdigit():
            qs = qs.filter(msfg_definition__cmg_model_id=cmg_model_id)
        if component_name:
            qs = qs.filter(component_name__icontains=component_name)
        if fault_name:
            qs = qs.filter(fault_name__icontains=fault_name)
        return qs.order_by('component_name', 'fault_name')

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_save(self, request):
        """鎵归噺淇濆瓨鏁呴殰-閮ㄤ欢鏄犲皠"""
        msfg_definition_id = request.data.get('msfg_definition_id')
        mappings = request.data.get('mappings') or []
        if not msfg_definition_id:
            return Response({'error': '缂哄皯msfg_definition_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            msfg_definition = MSFGDefinition.objects.get(id=msfg_definition_id)
        except MSFGDefinition.DoesNotExist:
            return Response({'error': '鏃犳晥鐨刴sfg_definition_id'}, status=status.HTTP_400_BAD_REQUEST)

        # 娓呯┖鍚庨噸寤猴紙骞跺幓閲嶉槻姝㈠敮涓€閿啿绐侊級
        with transaction.atomic():
            FaultComponentMapping.objects.filter(msfg_definition=msfg_definition).delete()
            new_objs = []
            seen = set()
            for m in mappings:
                fn = str(m.get('fault_name') or '').strip()
                comp = str(m.get('component') or '').strip()
                if not fn or not comp:
                    continue
                key = (fn, comp)
                if key in seen:
                    continue
                seen.add(key)
                new_objs.append(FaultComponentMapping(
                    msfg_definition=msfg_definition,
                    fault_name=fn,
                    component_name=comp,
                    mapping_type=m.get('mapping_type') or 'one_to_one',
                    weight=float(m.get('weight') or 1.0),
                    is_critical=bool(m.get('is_critical') or False),
                    description=m.get('description') or ''
                ))
            if new_objs:
                FaultComponentMapping.objects.bulk_create(new_objs, ignore_conflicts=True)
        return Response({'saved': len(new_objs)})


class TestPointFaultMappingViewSet(viewsets.ModelViewSet):
    """娴嬭瘯鐐?鏁呴殰鏄犲皠绠＄悊"""
    queryset = TestPointFaultMapping.objects.all()
    serializer_class = TestPointFaultMappingSerializer
    
    def get_queryset(self):
        queryset = TestPointFaultMapping.objects.all()
        msfg_definition_id = self.request.query_params.get('msfg_definition_id')
        if msfg_definition_id:
            queryset = queryset.filter(msfg_definition_id=msfg_definition_id)
        return queryset
    
    @action(detail=False, methods=['post'], url_path='batch')
    def batch_save(self, request):
        """鎵归噺淇濆瓨娴嬭瘯鐐?鏁呴殰鏄犲皠"""
        try:
            msfg_definition_id = request.data.get('msfg_definition_id')
            mappings = request.data.get('mappings', [])
            
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # 鍒犻櫎鐜版湁鏄犲皠
                TestPointFaultMapping.objects.filter(msfg_definition_id=msfg_definition_id).delete()
                
                # 鍒涘缓鏂版槧灏勶紙鍘婚噸+瑙勮寖鍖栵紝閬垮厤鍞竴閿啿绐侊級
                new_mappings = []
                seen = set()
                
                for mapping_data in mappings:
                    test_point_name = mapping_data.get('test_point_name', '').strip()
                    fault_name = mapping_data.get('fault_name', '').strip()
                    
                    if not test_point_name or not fault_name:
                        continue
                    
                    # 鍘婚噸妫€鏌?                    key = f"{test_point_name}-{fault_name}"
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    # 鍒涘缓鏄犲皠瀵硅薄
                    mapping = TestPointFaultMapping(
                        msfg_definition_id=msfg_definition_id,
                        test_point_name=test_point_name,
                        fault_name=fault_name,
                        mapping_type=mapping_data.get('mapping_type', 'one_to_one'),
                        weight=float(mapping_data.get('weight', 1.0)),
                        confidence=float(mapping_data.get('confidence', 0.8)),
                        is_critical=bool(mapping_data.get('is_critical', False)),
                        description=mapping_data.get('description', '')
                    )
                    new_mappings.append(mapping)
                
                # 鎵归噺鍒涘缓
                if new_mappings:
                    TestPointFaultMapping.objects.bulk_create(new_mappings)
                
                return Response({'saved': len(new_mappings)})
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def component_mappings_view(request):
    """閮ㄤ欢鏄犲皠绠＄悊椤甸潰"""
    return render(request, 'msfg_analysis/component_mappings.html')



# 鏂板锛歁SFG缁撴瀯涓庢娴嬫祦绋嬫煡鐪嬮〉闈?def msfg_inspect_view(request):
    return render(request, 'msfg_analysis/msfg-inspect.html')


class MSFGDefinitionViewSet(viewsets.ModelViewSet):
    """MSFG瀹氫箟瑙嗗浘闆?""
    
    queryset = MSFGDefinition.objects.all()
    serializer_class = MSFGDefinitionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        if cmg_model_id:
            queryset = queryset.filter(cmg_model_id=cmg_model_id)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-updated_at')

    @action(detail=True, methods=['get'], url_path='graph-inspect')
    def graph_inspect(self, request, pk=None):
        """
        杩斿洖璇SFG鐨勬祴鐐广€佹晠闅滅偣涓庢祴璇?>鏁呴殰鏄犲皠锛屼互鍙婇儴浠跺悕绉般€?        """
        try:
            msfg = self.get_object()
            nodes = list(msfg.nodes.all())
            edges = list(msfg.edges.all())
            test_names = [n.name for n in nodes if n.node_type == 'test']
            fault_names = [n.name for n in nodes if n.node_type == 'fault']
            # 鏋勫缓鏄犲皠
            mapping = {}
            test_by_id = {n.id: n for n in nodes if n.node_type == 'test'}
            fault_by_id = {n.id: n for n in nodes if n.node_type == 'fault'}
            for e in edges:
                if e.source_node_id in test_by_id and e.target_node_id in fault_by_id:
                    t = test_by_id[e.source_node_id].name
                    f = fault_by_id[e.target_node_id].name
                    mapping.setdefault(t, []).append(f)
            return Response({
                'msfg_id': msfg.id,
                'msfg_name': msfg.name,
                'components': msfg.component_names or [],
                'tests': test_names,
                'faults': fault_names,
                'test_to_fault': mapping,
            })
        except Exception as e:
            logger.error(f"graph_inspect 澶辫触: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='extract-mappings-from-graph')
    def extract_mappings_preview(self, request, pk=None):
        """
        浠庣粰瀹氱殑鍥剧粨鏋勪腑棰勮鍙彁鍙栫殑鏄犲皠鍏崇郴锛屼笉淇濆瓨浠讳綍鍐呭銆?        """
        try:
            msfg = self.get_object()
            graph_data = request.data.get('graphData')
            if not graph_data:
                return Response({'error': 'graphData is required'}, status=status.HTTP_400_BAD_REQUEST)

            # 1. 浣跨敤涓庝繚瀛樻椂鐩稿悓鐨勯€昏緫鏉ヨВ鏋愬拰瑙勮寖鍖栧浘
            parsed_graph = normalize_and_parse_graph(graph_data)
            if not parsed_graph:
                return Response({'error': '鏃犳硶瑙ｆ瀽MSFG鍥剧粨鏋?}, status=status.HTTP_400_BAD_REQUEST)

            # 2. 浠庤В鏋愬悗鐨勫浘涓彁鍙栨槧灏勫叧绯?            mappings = extract_mappings_from_graph(parsed_graph)

            # 3. 杩斿洖鎻愬彇鐨勬槧灏勪綔涓洪瑙?            return Response({
                'success': True,
                'message': 'Mappings extracted successfully (preview only).',
                'msfg_definition_id': msfg.id,
                'extracted_mappings': mappings
            })

        except Exception as e:
            logger.error(f"鎻愬彇鏄犲皠棰勮澶辫触: {e}")
            return Response({'error': f'鎻愬彇澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='d-matrix')
    def get_d_matrix(self, request, pk=None):
        """
        鑾峰彇MSFG鐨勬晠闅淒鐭╅樀鏁版嵁
        杩斿洖锛氱煩闃垫暟鎹€佹祴璇曠偣鍚嶇О銆佹晠闅滃悕绉般€佽瘖鏂垎鏋愮瓑
        """
        try:
            msfg = self.get_object()
            
            # 馃敡 淇锛氫娇鐢ㄧ粺涓€鐨勮妭鐐规彁鍙栭€昏緫
            from .algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            fusion = AdvancedMSFGFusion()
            
            # 浣跨敤淇鍚庣殑缁熶竴鑺傜偣鎻愬彇
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
            edges = list(msfg.edges.all())
            
            if not test_nodes or not fault_nodes:
                return Response({
                    'error': 'MSFG涓病鏈夋祴璇曠偣鎴栨晠闅滆妭鐐?
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 鏋勫缓D鐭╅樀锛堜娇鐢ㄤ慨澶嶅悗鐨勯€昏緫锛?            D_matrix, test_name_to_idx, fault_name_to_idx = fusion.build_d_matrix(test_nodes, fault_nodes, edges, msfg)
            
            # 杞崲涓哄瘑闆嗙煩闃?            import numpy as np
            dense_matrix = D_matrix.toarray()
            
            # 鑾峰彇鍚嶇О鍒楄〃
            test_names = [test_nodes[i].name for i in range(len(test_nodes))]
            fault_names = [fault_nodes[i].name for i in range(len(fault_nodes))]
            
            # 璁＄畻缁熻淇℃伅
            nonzero_count = np.count_nonzero(dense_matrix)
            
            # 璇婃柇缁撴瀯鍒嗘瀽
            diagnostic_analysis = fusion._analyze_diagnostic_structure(
                D_matrix=D_matrix,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                fused_test_scores={tn.name: 0.5 for tn in test_nodes}  # 浣跨敤榛樿鍊艰繘琛屽垎鏋?            )
            
            # 鏋勫缓鍝嶅簲鏁版嵁
            response_data = {
                'shape': dense_matrix.shape,
                'matrix': dense_matrix.tolist(),
                'test_names': test_names,
                'fault_names': fault_names,
                'test_count': len(test_names),
                'fault_count': len(fault_names),
                'nonzero_count': int(nonzero_count),
                'analysis': {
                    'detectable_faults': diagnostic_analysis.get('detectable_faults', []),
                    'isolable_faults': diagnostic_analysis.get('isolable_faults', []),
                    'indistinguishable_groups': diagnostic_analysis.get('indistinguishable_groups', [])
                }
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"鑾峰彇D鐭╅樀澶辫触: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'鑾峰彇D鐭╅樀澶辫触: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='analysis/preview')
    def analysis_preview(self, request, pk=None):
        """
        棰勮涓€娆¤缁嗘娴嬫祦绋嬶細
        杈撳叆: { test_scores?: {name: score}, use_rules?: bool, data_point_id?: int }
        浼樺厛浣跨敤 test_scores锛涜嫢鏈彁渚涗笖 use_rules=true 涓?data_point_id 鎻愪緵锛屽垯浠?scoring 璁＄畻銆?        杩斿洖锛欴鐭╅樀褰㈢姸銆佽瀺鍚堝悗鐨勬祴璇曞垎銆佹晠闅?妯＄硦姒傜巼銆佽瘖鏂粨鏋勫垎鏋愪笌閮ㄤ欢鍋ュ悍銆?        """
        try:
            msfg = self.get_object()
            test_scores = request.data.get('test_scores') or {}
            use_rules = bool(request.data.get('use_rules') or False)
            data_point_id = request.data.get('data_point_id')

            # 馃敡 淇锛氫娇鐢ㄧ粺涓€鐨勮妭鐐规彁鍙栭€昏緫
            from .algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
            fusion = AdvancedMSFGFusion()
            
            # 浣跨敤淇鍚庣殑缁熶竴鑺傜偣鎻愬彇
            test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
            edges = list(msfg.edges.all())
            details = None
            if use_rules and not test_scores and data_point_id:
                try:
                    dp = PHMData.objects.get(id=data_point_id)
                    from .services.testpoint_scoring import TestPointScoringService
                    svc = TestPointScoringService()
                    det = svc.calculate_test_scores_with_details(dp, msfg)
                    details = det
                    test_scores = det.get('scores', {})
                except Exception as e:
                    logger.warning(f"瑙勫垯渚ц绠楁祴鐐硅瘎鍒嗗け璐? {e}")
                    test_scores = {}

            # 缁熶竴涓?name-> [score]
            test_scores_wrapped = {k: [float(v)] for k, v in test_scores.items()}

            # 馃敡 淇锛氫娇鐢ㄤ慨澶嶅悗鐨勯儴浠舵槧灏勬瀯寤?            comp_map = fusion._build_component_mappings(msfg)

            D_matrix, _, _ = fusion.build_d_matrix(test_nodes, fault_nodes, edges, msfg)

            # 铻嶅悎娴嬭瘯鍒嗘暟锛坣ame->float锛?            fused_test_scores = fusion.fuse_test_scores(test_scores_wrapped)
            test_scores_array = __import__('numpy').array([
                fused_test_scores.get(tn.name, 0.2) for tn in test_nodes
            ], dtype=__import__('numpy').float32)

            # 鏁呴殰涓庢ā绯婃鐜?            fusion._last_test_scores_array = test_scores_array
            fault_prob = fusion.calculate_fault_probability(D_matrix, test_scores_array)
            fuzzy_prob = fusion.calculate_fuzzy_probability(D_matrix, fault_prob)

            # 璇婃柇缁撴瀯鍒嗘瀽
            diag_struct = fusion._analyze_diagnostic_structure(
                D_matrix=D_matrix,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                fused_test_scores=fused_test_scores
            )

            # 閮ㄤ欢涓庣郴缁?            component_health = fusion.calculate_component_health(
                fault_prob=fault_prob,
                fuzzy_prob=fuzzy_prob,
                fault_nodes=fault_nodes,
                component_mappings=comp_map,
            )
            system_health = fusion.calculate_system_health(component_health)

            # D鐭╅樀淇℃伅
            coo = D_matrix.tocoo()
            nnz = int(coo.nnz)
            sample_n = min(200, nnz)
            sample = []
            if nnz:
                import random
                idxs = list(range(nnz))
                random.shuffle(idxs)
                idxs = idxs[:sample_n]
                # 鍚嶇О鏄犲皠
                test_order = [t.name for t in test_nodes]
                fault_order = [f.name for f in fault_nodes]
                for i in idxs:
                    r = int(coo.row[i]); c = int(coo.col[i]); v = float(coo.data[i])
                    sample.append({
                        'fault_index': r,
                        'fault': fault_order[r] if r < len(fault_order) else r,
                        'test_index': c,
                        'test': test_order[c] if c < len(test_order) else c,
                        'weight': v,
                    })
            pipeline = {
                'graph': {
                    'test_count': len(test_nodes),
                    'fault_count': len(fault_nodes),
                    'edge_count': len(edges),
                },
                'd_matrix': {
                    'shape': tuple(D_matrix.shape),
                    'nnz': nnz,
                    'nonzero_sample': sample,
                    'test_order': [t.name for t in test_nodes],
                    'fault_order': [f.name for f in fault_nodes],
                },
                'test_scores': {
                    'input': test_scores,
                    'fused': fused_test_scores,
                    'array': [float(x) for x in test_scores_array.tolist()],
                    'rule_details': details or {},
                },
                'fault_inference': {
                    'fault_probability': {fault_nodes[i].name: float(fault_prob[i]) for i in range(len(fault_nodes))},
                    'fuzzy_probability': {fault_nodes[i].name: float(fuzzy_prob[i]) for i in range(len(fault_nodes))},
                },
                'diagnostic': diag_struct,
                'components': {
                    'mappings': comp_map,
                    'health': component_health,
                },
                'system': system_health,
            }

            # 鍚屾椂杩斿洖 run_advanced_analysis 鐨勭粨鏋滐紝渚夸簬涓€鑷存€у姣?            result = fusion.run_advanced_analysis(
                test_scores=test_scores_wrapped,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                edges=edges,
                component_mappings=comp_map,
            )
            return Response({'result': result, 'pipeline': pipeline})
        except Exception as e:
            logger.error(f"analysis_preview 澶辫触: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='sync-components')
    def sync_components(self, request):
        """鍚屾MSFG閮ㄤ欢瀹氫箟鍒拌鍒欐娴嬫ā鍧?""
        cmg_model_id = request.data.get('cmg_model_id')
        if not cmg_model_id:
            return Response(
                {'error': 'cmg_model_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from data_management.models import PHMModel
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
            
            from .algorithms.msfg.component_integration import sync_msfg_component_definitions
            result = sync_msfg_component_definitions(cmg_model)
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except PHMModel.DoesNotExist:
            return Response(
                {'error': 'PHM model not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"鍚屾MSFG閮ㄤ欢瀹氫箟澶辫触: {e}")
            return Response(
                {'error': f'鍚屾澶辫触: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='ensure-mappings')
    def ensure_mappings(self, request, pk=None):
        """纭繚MSFG閰嶇疆鏈夊畬鏁寸殑娴嬭瘯鐐?閮ㄤ欢鏄犲皠"""
        try:
            msfg_definition = self.get_object()
            
            from .algorithms.msfg.component_integration import ensure_msfg_component_mappings
            ensure_msfg_component_mappings(msfg_definition)
            
            return Response({
                'success': True,
                'message': f'宸叉洿鏂癕SFG "{msfg_definition.name}" 鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠'
            })
            
        except Exception as e:
            logger.error(f"纭繚MSFG閮ㄤ欢鏄犲皠澶辫触: {e}")
            return Response(
                {'error': f'鎿嶄綔澶辫触: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='components')
    def components(self, request, pk=None):
        """鑾峰彇MSFG瀹氫箟涓殑缁勪欢淇℃伅"""
        try:
            msfg_definition = self.get_object()
            # 浼樺厛杩斿洖瀹氫箟涓殑缁勪欢鍚嶇О鍒楄〃
            components = list(msfg_definition.component_names or [])
            if not components:
                # 鍏滃簳锛氫粠鍥句腑鎻愬彇缁勪欢鑺傜偣
                component_nodes = msfg_definition.nodes.filter(node_type='component')
                components = [node.name for node in component_nodes]
            return Response({
                'components': components,
                'total': len(components)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='faults')
    def faults(self, request, pk=None):
        """杩斿洖璇SFG瀹氫箟鐨勬晠闅滃悕绉板垪琛?""
        try:
            msfg = self.get_object()
            faults = list(msfg.fault_names or [])
            return Response({'faults': faults, 'total': len(faults)})
        except Exception as e:
            logger.error(f"鑾峰彇MSFG鏁呴殰鍒楄〃澶辫触: {e}")
            return Response({'faults': [], 'total': 0})
    
    @action(detail=False, methods=['get'], url_path='component-mappings')
    def component_mappings(self, request):
        """鑾峰彇娴嬭瘯鐐?閮ㄤ欢鏄犲皠"""
        try:
            msfg_definition_id = request.query_params.get('msfg_definition_id')
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            mappings = TestPointComponentMapping.objects.filter(
                msfg_definition_id=msfg_definition_id
            ).values('id', 'test_point_name', 'component_name', 'mapping_type', 'weight', 'description')
            
            # 杞崲瀛楁鍚嶄互鍖归厤鍓嶇鏈熸湜
            result = []
            for mapping in mappings:
                result.append({
                    'id': mapping['id'],
                    'test_point': mapping['test_point_name'],
                    'component': mapping['component_name'],
                    'mapping_type': mapping['mapping_type'],
                    'weight': mapping['weight'],
                    'description': mapping['description']
                })
            
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='component-mappings/batch')
    def batch_component_mappings(self, request):
        """鎵归噺淇濆瓨娴嬭瘯鐐?閮ㄤ欢鏄犲皠"""
        try:
            msfg_definition_id = request.data.get('msfg_definition_id')
            mappings = request.data.get('mappings', [])
            
            if not msfg_definition_id:
                return Response({'error': '缂哄皯msfg_definition_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # 鍒犻櫎鐜版湁鏄犲皠
                TestPointComponentMapping.objects.filter(msfg_definition_id=msfg_definition_id).delete()
                
                # 鍒涘缓鏂版槧灏勶紙鍘婚噸+瑙勮寖鍖栵紝閬垮厤鍞竴閿啿绐侊級
                new_mappings = []
                seen = set()
                for m in mappings:
                    tp = (m.get('test_point') or m.get('test_point_name') or '').strip()
                    comp = (m.get('component') or m.get('component_name') or '').strip()
                    if not tp or not comp:
                        continue
                    key = (tp, comp)
                    if key in seen:
                        continue
                    seen.add(key)
                    new_mappings.append(TestPointComponentMapping(
                        msfg_definition_id=msfg_definition_id,
                        test_point_name=tp,
                        component_name=comp,
                        mapping_type=(m.get('mapping_type') or 'one_to_one'),
                        weight=float(m.get('weight') or 1.0),
                        description=(m.get('description') or '')
                    ))
                
                if new_mappings:
                    TestPointComponentMapping.objects.bulk_create(new_mappings, ignore_conflicts=True)
            
            return Response({'message': '鏄犲皠淇濆瓨鎴愬姛', 'count': len(new_mappings)})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='fix-components')
    def fix_components(self, request):
        """淇MSFG閮ㄤ欢鎻愬彇闂"""
        try:
            cmg_model_id = request.data.get('cmg_model_id')
            if not cmg_model_id:
                return Response({'error': '缂哄皯cmg_model_id鍙傛暟'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 鏌ユ壘PHM妯″瀷
            try:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            except PHMModel.DoesNotExist:
                return Response({'error': f'鎵句笉鍒癐D涓簕cmg_model_id}鐨凜MG妯″瀷'}, status=status.HTTP_404_NOT_FOUND)
            
            # 鏌ユ壘娲昏穬鐨凪SFG閰嶇疆
            active_msfg = MSFGDefinition.objects.filter(
                cmg_model=cmg_model,
                is_active=True
            ).order_by('-updated_at').first()
            
            if not active_msfg:
                return Response({'error': f'鎵句笉鍒皗cmg_model.model_name}鐨勬椿璺僊SFG閰嶇疆'}, status=status.HTTP_404_NOT_FOUND)
            
            # 浠嶫SON閰嶇疆鏂囦欢鎻愬彇閮ㄤ欢
            import os
            import json
            
            json_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "澶氫俊鍙锋祦鍥鹃厤缃?json")
            if not os.path.exists(json_file_path):
                return Response({'error': '鎵句笉鍒板淇″彿娴佸浘閰嶇疆.json鏂囦欢'}, status=status.HTTP_404_NOT_FOUND)
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 鎻愬彇閮ㄤ欢
            components = []
            if 'SystemData' in config_data:
                system_data = config_data['SystemData']
                for system_item in system_data:
                    if 'data' in system_item and 'nodes' in system_item['data']:
                        nodes = system_item['data']['nodes']
                        for node in nodes:
                            node_type = node.get('type', '')
                            if node_type == 'subsystem-node':
                                properties = node.get('properties', {})
                                table_name = properties.get('tableName', '')
                                if table_name and table_name.strip():
                                    components.append(table_name.strip())
            
            # 鍘婚噸骞舵帓搴?            components = sorted(list(set(components)))
            
            if not components:
                return Response({'error': '鏃犳硶浠嶫SON鏂囦欢鎻愬彇鍒伴儴浠?}, status=status.HTTP_400_BAD_REQUEST)
            
            # 鏇存柊MSFG鐨刢omponent_names瀛楁
            active_msfg.component_names = components
            active_msfg.save(update_fields=['component_names', 'updated_at'])
            
            # 鍒犻櫎鐜版湁鐨勭郴缁熻妭鐐?            from msfg_analysis.models import MSFGNode
            existing_system_nodes = MSFGNode.objects.filter(
                msfg_definition=active_msfg,
                node_type='system'
            )
            if existing_system_nodes.exists():
                existing_system_nodes.delete()
            
            # 鍒涘缓鏂扮殑绯荤粺鑺傜偣
            import uuid
            created_nodes = 0
            for i, component_name in enumerate(components):
                node = MSFGNode.objects.create(
                    node_id=str(uuid.uuid4()),
                    msfg_definition=active_msfg,
                    name=component_name,
                    node_type='system',
                    position_x=100 + (i % 5) * 200,
                    position_y=100 + (i // 5) * 150,
                    properties={'tableName': component_name}
                )
                created_nodes += 1
            
            # 閲嶆柊杩愯閮ㄤ欢鏄犲皠
            from msfg_analysis.algorithms.msfg.component_integration import ensure_msfg_component_mappings
            ensure_msfg_component_mappings(active_msfg)
            
            # 鑾峰彇鏄犲皠鏁伴噺
            from msfg_analysis.models import TestPointComponentMapping
            mappings_count = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg).count()
            
            return Response({
                'success': True,
                'message': f'鎴愬姛淇{cmg_model.model_name}鐨勯儴浠舵彁鍙栭棶棰?,
                'details': {
                    'model_name': cmg_model.model_name,
                    'msfg_name': active_msfg.name,
                    'components_count': len(components),
                    'system_nodes_created': created_nodes,
                    'mappings_count': mappings_count,
                    'components': components
                }
            })
            
        except Exception as e:
            logger.error(f"淇閮ㄤ欢鎻愬彇澶辫触: {e}")
            return Response({'error': f'淇澶辫触: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


