"""
瑙勫垯妫€娴婦jango瑙嗗浘
鎻愪緵瑙勫垯閰嶇疆銆佹娴嬪拰缁撴灉鏌ヨ鐨凴EST API
"""

import json
import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.views.decorators.csrf import csrf_exempt

from data_management.models import PHM, PHMModel, PHMData
from .models import (
    FaultDefinition, RuleDefinition, RuleDetectionResult, 
    ComponentDefinition
)
from .service import compute_component_health_for_model
from .serializers import (
    FaultDefinitionSerializer, RuleDefinitionSerializer,
    RuleDetectionResultSerializer, ComponentDefinitionSerializer
)
from rule_detection.algorithms.rule.enhanced_rule_parser import EnhancedRuleParser
from rule_detection.algorithms.rule.rule_parser import RuleParser

logger = logging.getLogger(__name__)


class RuleEditorView(viewsets.ViewSet):
    """瑙勫垯缂栬緫鍣ㄨ鍥?""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], url_path='editor')
    def rule_editor_page(self, request):
        """瑙勫垯缂栬緫鍣ㄩ〉闈?""
        from django.middleware.csrf import get_token
        # 纭繚CSRF token鍙敤
        get_token(request)
        response = render(request, 'rule_detection/rule-edit.html')
        response.template_name = 'rule_detection/rule-edit.html'
        return response
    
    @csrf_exempt
    @action(detail=False, methods=['post'], url_path='get-config')
    def get_config(self, request):
        """鑾峰彇瑙勫垯缂栬緫鍣ㄩ厤缃俊鎭?""
        cmg_model_id = request.data.get('cmg_model_id')
        
        if not cmg_model_id:
            return Response({'error': 'cmg_model_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # 鑾峰彇鏁呴殰鍚嶇О閰嶇疆
        fault_names = {}
        for fault in FaultDefinition.objects.filter(cmg_model=cmg_model):
            fault_names[fault.fault_name] = {
                'name': fault.fault_name,
                'component': fault.component,
                'level': fault.fault_level,
                'description': fault.description
            }
        
        # 鑾峰彇缁勪欢閰嶇疆
        components = {}
        for comp in ComponentDefinition.objects.filter(cmg_model=cmg_model):
            components[comp.component_name] = comp.component_name
        
        # 鑾峰彇鍙傛暟鍚嶇О锛堜粠鏈€杩戠殑鏁版嵁涓彁鍙栵級
        pnames = {}
        recent_data = PHMData.objects.filter(cmg__cmg_model=cmg_model).order_by('-timestamp').first()
        if recent_data and recent_data.data:
            for param_name in recent_data.data.keys():
                pnames[param_name] = param_name
        
        return Response({
            'faultNames': fault_names,
            'components': components,
            'pnames': pnames,
        })
    
    @csrf_exempt
    @action(detail=False, methods=['get', 'post'], url_path='init-all-rule')
    def init_all_rule(self, request):
        """鑾峰彇鎵€鏈夎鍒?""
        cmg_model_id = request.data.get('cmg_model_id') if request.method == 'POST' else request.GET.get('cmg_model_id')
        
        if not cmg_model_id:
            return Response({'error': 'cmg_model_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # 鑾峰彇鎵€鏈夎鍒欏畾涔?
        rules = RuleDefinition.objects.filter(cmg_model=cmg_model).select_related('fault_definition')
        
        table_data = []
        for rule in rules:
            table_data.append({
                'showId': rule.rule_id,
                'faultName': rule.fault_definition.fault_name,
                'faultLevel': rule.fault_definition.fault_level,
                'component': rule.fault_definition.component,
                'ruleExpress': rule.rule_expression,
                'source': rule.source,
                'planDescript': rule.plan_description,
                'ruleOnline': rule.is_online,
                'isNew': rule.is_new,
                'editable': rule.is_editable,
            })
        
        return Response(table_data)
    
    @csrf_exempt
    @action(detail=False, methods=['post'], url_path='config-rule')
    def config_rule(self, request):
        """淇濆瓨瑙勫垯閰嶇疆"""
        cmg_model_id = request.data.get('cmg_model_id')
        table_data_str = request.data.get('tableData', '')
        
        if not cmg_model_id:
            return Response({'error': 'cmg_model_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 鍏佽绌虹殑tableData锛堝垹闄ゆ墍鏈夎鍒欑殑鎯呭喌锛?
        if table_data_str is None:
            return Response({'error': 'tableData is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        try:
            # 澶勭悊绌哄瓧绗︿覆鐨勬儏鍐碉紙鍒犻櫎鎵€鏈夎鍒欙級
            if table_data_str == '' or table_data_str == '[]':
                table_data = []
            else:
                table_data = json.loads(table_data_str) if isinstance(table_data_str, str) else table_data_str
            
            if not isinstance(table_data, list):
                raise ValueError("tableData must be a list")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"瑙ｆ瀽tableData澶辫触: {e}, 鎺ユ敹鍒扮殑鏁版嵁: {table_data_str}")
            return Response({'error': f'Invalid tableData format: {str(e)}'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 鏋勫缓鍙傛暟鍒楄〃鐢ㄤ簬瑙ｆ瀽锛堝彇鏈€杩戜竴鏉℃暟鎹殑瀛楁锛?
        recent = PHMData.objects.filter(cmg__cmg_model=cmg_model).order_by('-timestamp').first()
        parameter_names = list(recent.data.keys()) if recent and isinstance(recent.data, dict) else []
        
        # 楠岃瘉瑙勫垯琛ㄨ揪寮?
        validation_errors = []
        for i, rule_data in enumerate(table_data):
            if not rule_data or not isinstance(rule_data, dict):
                continue
                
            rule_expression = rule_data.get('ruleExpress', '') or ''
            if not rule_expression:
                continue
                
            # 妫€鏌ユ槸鍚﹀寘鍚珮绾х粺璁″嚱鏁?
            has_advanced_functions = any(func in rule_expression for func in [
                'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(', 'level('
            ])
            
            try:
                if has_advanced_functions:
                    # 浣跨敤澧炲己鐗堣В鏋愬櫒
                    parser = EnhancedRuleParser(parameter_names=parameter_names)
                    parsed_result = parser.parse(rule_expression)
                    
                    if parsed_result.error_count > 0:
                        error_messages = [msg['message'] for msg in parsed_result.log_messages if msg['type'] == 'error']
                        validation_errors.append({
                            'rule_index': i,
                            'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                            'fault_name': rule_data.get('faultName', ''),
                            'errors': error_messages
                        })
                else:
                    # 浣跨敤浼犵粺瑙ｆ瀽鍣?
                    parser = RuleParser(parameter_names=parameter_names)
                    parsed = parser.parse(rule_expression)
                    if not parsed:
                        validation_errors.append({
                            'rule_index': i,
                            'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                            'fault_name': rule_data.get('faultName', ''),
                            'errors': ['瑙勫垯琛ㄨ揪寮忚В鏋愬け璐?]
                        })
                        
            except Exception as e:
                validation_errors.append({
                    'rule_index': i,
                    'rule_id': rule_data.get('showId', f'瑙勫垯{i+1}'),
                    'fault_name': rule_data.get('faultName', ''),
                    'errors': [f'瑙勫垯楠岃瘉澶辫触: {str(e)}']
                })
        
        # 濡傛灉鏈夐獙璇侀敊璇紝杩斿洖閿欒淇℃伅
        if validation_errors:
            error_details = []
            for error in validation_errors:
                error_details.append(f"瑙勫垯 {error['rule_id']} ({error['fault_name']}): {'; '.join(error['errors'])}")
            
            return Response({
                'error': '瑙勫垯楠岃瘉澶辫触',
                'validation_errors': validation_errors,
                'error_details': error_details
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # 鍒犻櫎鐜版湁瑙勫垯锛堜繚鐣欏悓ID鏃堕伩鍏嶅敮涓€绾︽潫鍐茬獊锛岀◢鍚庢壒閲忓垱寤烘椂鍘婚噸锛?
                deleted_count = RuleDefinition.objects.filter(cmg_model=cmg_model).delete()[0]
                logger.info(f"鍒犻櫎浜?{deleted_count} 涓幇鏈夎鍒欙紝鍑嗗鍒涘缓 {len(table_data)} 涓柊瑙勫垯")
                
                # 鏋勫缓 鍙傛暟->缁勪欢 鏄犲皠锛屼究浜庣己鐪佺粍浠舵帹鏂?
                comp_param_map = {}
                for comp in ComponentDefinition.objects.filter(cmg_model=cmg_model):
                    params = comp.parameters if isinstance(comp.parameters, list) else []
                    for p in params:
                        if isinstance(p, str) and p:
                            comp_param_map[p] = comp.component_name

                # 鍒涘缓鎴栨洿鏂版晠闅滃畾涔夊拰瑙勫垯
                seen_rule_ids = set()
                for rule_data in table_data:
                    if not rule_data or not isinstance(rule_data, dict):
                        continue
                    fault_name = rule_data.get('faultName', '')
                    if not fault_name:
                        continue
                    
                    # 鍒涘缓鎴栬幏鍙栨晠闅滃畾涔?
                    fault_definition, created = FaultDefinition.objects.get_or_create(
                        cmg_model=cmg_model,
                        fault_name=fault_name,
                        defaults={
                            'fault_level': rule_data.get('faultLevel', 1),
                            'component': rule_data.get('component', ''),
                            'description': '',
                        }
                    )
                    
                    if not created:
                        # 鏇存柊鐜版湁鏁呴殰瀹氫箟
                        fault_definition.fault_level = rule_data.get('faultLevel', fault_definition.fault_level)
                        # 鑻ュ叆鍙傛湭鏄惧紡缁欏嚭缁勪欢锛屽悗缁皢灏濊瘯鏍规嵁鍙傛暟鎺ㄦ柇
                        incoming_component = rule_data.get('component')
                        if incoming_component:
                            fault_definition.component = incoming_component
                        fault_definition.save()
                    
                    # 瑙ｆ瀽瑙勫垯琛ㄨ揪寮忥紝鎻愬彇娑夊強鐨勫弬鏁?
                    related_parameters = []
                    rule_expression = rule_data.get('ruleExpress', '') or ''
                    
                    try:
                        # 妫€鏌ユ槸鍚﹀寘鍚珮绾х粺璁″嚱鏁?
                        has_advanced_functions = any(func in rule_expression for func in [
                            'mean(', 'std(', 'var(', 'mad(', 'rms(', 'slope(', 'diffmean(', 'diffstd(', 'ma(', 'ma_diff(', 'autocorr(', 'level('
                        ])
                        
                        if has_advanced_functions:
                            # 浣跨敤澧炲己鐗堣В鏋愬櫒
                            parser = EnhancedRuleParser(parameter_names=parameter_names)
                            parsed_result = parser.parse(rule_expression)
                            related_parameters = list(parsed_result.related_parameters)
                        else:
                            # 浣跨敤浼犵粺瑙ｆ瀽鍣?
                            parser = RuleParser(parameter_names=parameter_names)
                            parsed = parser.parse(rule_expression)
                            if parsed and isinstance(parsed.get('related_parameters'), list):
                                related_parameters = parsed['related_parameters']
                    except Exception as e:
                        logger.warning(f"瑙ｆ瀽瑙勫垯琛ㄨ揪寮忓け璐? {e}")
                        related_parameters = []

                    # 濡傛湭璁剧疆缁勪欢锛屼緷鎹秹鍙婂弬鏁板鏁拌〃鍐虫帹鏂粍浠?
                    if not fault_definition.component and related_parameters:
                        counter = {}
                        for p in related_parameters:
                            comp_name = comp_param_map.get(p)
                            if comp_name:
                                counter[comp_name] = counter.get(comp_name, 0) + 1
                        if counter:
                            inferred = max(counter.keys(), key=counter.get)
                            fault_definition.component = inferred
                            fault_definition.save()

                    # 鐢熸垚鎴栨竻娲楄鍒橧D
                    rule_id_val = (rule_data.get('showId') or '').strip()
                    if not rule_id_val:
                        rule_id_val = f"RULE_{uuid4().hex[:8]}"
                    # 鍘婚噸锛氬悓涓€ cmg_model 涓?rule_id 涓嶈兘閲嶅
                    if rule_id_val in seen_rule_ids:
                        continue
                    seen_rule_ids.add(rule_id_val)

                    # 鍒涘缓瑙勫垯瀹氫箟
                    RuleDefinition.objects.create(
                        cmg_model=cmg_model,
                        fault_definition=fault_definition,
                        rule_id=rule_id_val,
                        rule_expression=rule_expression,
                        source=rule_data.get('source', 'expert'),
                        plan_description=rule_data.get('planDescript', ''),
                        is_online=rule_data.get('ruleOnline', True),
                        is_new=rule_data.get('isNew', True),
                        is_editable=rule_data.get('editable', True),
                        related_parameters=related_parameters,
                    )
            
            return Response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"淇濆瓨瑙勫垯閰嶇疆澶辫触: {e}")
            return Response({'error': f'淇濆瓨澶辫触: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FaultDefinitionViewSet(viewsets.ModelViewSet):
    """鏁呴殰瀹氫箟瑙嗗浘闆?""
    
    queryset = FaultDefinition.objects.all()
    serializer_class = FaultDefinitionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        if cmg_model_id:
            queryset = queryset.filter(cmg_model_id=cmg_model_id)
        return queryset.order_by('fault_name')


class RuleDefinitionViewSet(viewsets.ModelViewSet):
    """瑙勫垯瀹氫箟瑙嗗浘闆?""
    
    queryset = RuleDefinition.objects.select_related('fault_definition', 'cmg_model').all()
    serializer_class = RuleDefinitionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        if cmg_model_id:
            queryset = queryset.filter(cmg_model_id=cmg_model_id)
        
        is_online = self.request.query_params.get('is_online')
        if is_online is not None:
            queryset = queryset.filter(is_online=is_online.lower() == 'true')
        
        return queryset.order_by('rule_id')


class RuleDetectionResultViewSet(viewsets.ReadOnlyModelViewSet):
    """瑙勫垯妫€娴嬬粨鏋滆鍥鹃泦"""
    
    queryset = RuleDetectionResult.objects.select_related(
        'data_point', 'data_point__cmg', 'rule_definition', 'fault_definition'
    ).all()
    serializer_class = RuleDetectionResultSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # 鍏堟帓搴忥紝鍐嶅垏鐗?
        queryset = super().get_queryset().order_by('-created_at')

        # 鎸塁MG杩囨护
        cmg_id = self.request.query_params.get('cmg_id')
        if cmg_id:
            queryset = queryset.filter(data_point__cmg__cmg_id=cmg_id)

        # 鎸夎鍒橧D杩囨护
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            queryset = queryset.filter(rule_definition__rule_id=rule_id)

        # 鎸夎Е鍙戠姸鎬佽繃婊?
        is_triggered = self.request.query_params.get('is_triggered')
        if is_triggered is not None:
            queryset = queryset.filter(is_triggered=is_triggered.lower() == 'true')

        # 鎸夋椂闂磋寖鍥磋繃婊?
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(data_point__timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(data_point__timestamp__lte=end_time)

        return queryset
    
    def list(self, request, *args, **kwargs):
        """閲嶅啓list鏂规硶鏀寔鍒嗛〉"""
        queryset = self.get_queryset()
        
        # 鑾峰彇鍒嗛〉鍙傛暟
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset')
        
        # 濡傛灉娌℃湁鍒嗛〉鍙傛暟锛屼娇鐢ㄥ師鏈夐€昏緫
        if not offset:
            if limit:
                try:
                    limit_val = int(limit)
                    queryset = queryset[:limit_val]
                except (TypeError, ValueError):
                    pass
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        # 鍒嗛〉閫昏緫
        try:
            limit = int(limit) if limit else 500
            offset = int(offset) if offset else 0
        except (TypeError, ValueError):
            limit = 500
            offset = 0
            
        # 鑾峰彇鎬绘暟
        total_count = queryset.count()
        
        # 鍒嗛〉鏁版嵁
        paginated_queryset = queryset[offset:offset + limit]
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'limit': limit,
            'offset': offset
        })


class HealthViewSet(viewsets.ViewSet):
    """缁勪欢鍋ュ悍搴︿笌绯荤粺鍋ュ悍搴﹁鍥鹃泦"""

    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='component-health')
    def component_health(self, request):
        cmg_model_id = request.query_params.get('cmg_model_id')
        if not cmg_model_id:
            return Response({'error': 'cmg_model_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            return Response({'error': 'PHM model not found'}, status=status.HTTP_404_NOT_FOUND)

        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        limit = request.query_params.get('limit')
        try:
            limit_val = int(limit) if limit else 1000
        except (TypeError, ValueError):
            limit_val = 1000

        result = compute_component_health_for_model(
            cmg_model,
            start_time=start_time,
            end_time=end_time,
            limit=limit_val,
        )
        return Response(result)


class ComponentDefinitionViewSet(viewsets.ModelViewSet):
    """缁勪欢瀹氫箟瑙嗗浘闆?""
    
    queryset = ComponentDefinition.objects.all()
    serializer_class = ComponentDefinitionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cmg_model_id = self.request.query_params.get('cmg_model_id')
        if cmg_model_id:
            queryset = queryset.filter(cmg_model_id=cmg_model_id)
        return queryset.order_by('component_name')

