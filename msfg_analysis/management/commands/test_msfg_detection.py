"""
MSFG妫€娴嬬鍒扮娴嬭瘯鍛戒护
鐢ㄤ簬楠岃瘉淇鍚庣殑MSFG妯″潡鍔熻兘
"""

import json
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from data_management.models import PHM, PHMModel, PHMData
from msfg_analysis.models import (
    MSFGDefinition, MSFGNode, MSFGEdge, TestPointRule, 
    TestPointComponentMapping, MSFGAnalysisResult
)
from msfg_analysis.services.testpoint_scoring import calculate_msfg_test_scores
from msfg_analysis.services.component_mapping import build_msfg_component_mappings
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'MSFG妫€娴嬬鍒扮娴嬭瘯'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data', 
            action='store_true',
            help='鍒涘缓娴嬭瘯鏁版嵁'
        )
        parser.add_argument(
            '--test-scoring',
            action='store_true', 
            help='娴嬭瘯璇勫垎閫昏緫'
        )
        parser.add_argument(
            '--test-mapping',
            action='store_true',
            help='娴嬭瘯閮ㄤ欢鏄犲皠'
        )
        parser.add_argument(
            '--test-fusion',
            action='store_true',
            help='娴嬭瘯铻嶅悎绠楁硶'
        )
        parser.add_argument(
            '--test-full-pipeline',
            action='store_true',
            help='娴嬭瘯瀹屾暣娴佺▼'
        )
        parser.add_argument(
            '--cmg-model-id',
            type=int,
            help='鎸囧畾PHM妯″瀷ID'
        )
        parser.add_argument(
            '--use-existing-data',
            action='store_true',
            help='浣跨敤鐜版湁鏁版嵁搴撲腑鐨勬暟鎹繘琛屾祴璇?
        )
        
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('寮€濮婱SFG妫€娴嬬鍒扮娴嬭瘯')
        )
        
        try:
            if options['create_test_data']:
                self.stdout.write("鎵ц鍒涘缓娴嬭瘯鏁版嵁...")
                self.create_test_data()
            
            if options['test_scoring']:
                self.stdout.write("鎵ц娴嬭瘯璇勫垎閫昏緫...")
                self.test_scoring_logic(options.get('cmg_model_id'))
                
            if options['test_mapping']:
                self.stdout.write("鎵ц娴嬭瘯鏄犲皠閫昏緫...")
                self.test_mapping_logic(options.get('cmg_model_id'))
                
            if options['test_fusion']:
                self.stdout.write("鎵ц娴嬭瘯铻嶅悎绠楁硶...")
                self.test_fusion_algorithm(options.get('cmg_model_id'))
                
            if options['test_full_pipeline']:
                self.stdout.write("鎵ц瀹屾暣娴佺▼娴嬭瘯...")
                self.test_full_pipeline(options.get('cmg_model_id'))
                
            self.stdout.write(self.style.SUCCESS('娴嬭瘯瀹屾垚'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'娴嬭瘯杩囩▼涓彂鐢熼敊璇? {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def create_test_data(self):
        """鍒涘缓娴嬭瘯鏁版嵁"""
        self.stdout.write("鍒涘缓娴嬭瘯鏁版嵁...")
        
        try:
            with transaction.atomic():
                # 鍒涘缓鎴栬幏鍙朇MG妯″瀷
                cmg_model, created = PHMModel.objects.get_or_create(
                    model_name='TEST_MSFG_MODEL',
                    defaults={
                        'description': 'MSFG娴嬭瘯妯″瀷',
                        'is_active': True,
                        'is_custom': True
                    }
                )
                
                if created:
                    self.stdout.write(f"鍒涘缓浜咰MG妯″瀷: {cmg_model.model_name}")
                
                # 鍒涘缓PHM瀹炰緥
                cmg, created = PHM.objects.get_or_create(
                    cmg_id='TEST_PHM_001',
                    defaults={
                        'cmg_model': cmg_model,
                        'name': 'MSFG娴嬭瘯PHM',
                        'enabled': True
                    }
                )
                
                # 鍒涘缓MSFG瀹氫箟
                msfg_def, created = MSFGDefinition.objects.get_or_create(
                    cmg_model=cmg_model,
                    name='TEST_MSFG',
                    defaults={
                        'description': 'MSFG娴嬭瘯瀹氫箟',
                        'raw_graph_data': {},
                        'processed_graph_data': {},
                        'test_names': ['娴嬭瘯鐐?', '娴嬭瘯鐐?', '娴嬭瘯鐐?'],
                        'fault_names': ['鏁呴殰1', '鏁呴殰2', '鏁呴殰3'],
                        'component_names': ['閮ㄤ欢A', '閮ㄤ欢B'],
                        'is_active': True
                    }
                )
                
                if created:
                    # 鍒涘缓娴嬭瘯鑺傜偣
                    test_nodes = []
                    for i, name in enumerate(['娴嬭瘯鐐?', '娴嬭瘯鐐?', '娴嬭瘯鐐?']):
                        node = MSFGNode.objects.create(
                            msfg_definition=msfg_def,
                            node_id=f'test_{i+1}',
                            node_type='test',
                            name=name,
                            position_x=100 * i,
                            position_y=100
                        )
                        test_nodes.append(node)
                    
                    # 鍒涘缓鏁呴殰鑺傜偣
                    fault_nodes = []
                    for i, name in enumerate(['鏁呴殰1', '鏁呴殰2', '鏁呴殰3']):
                        node = MSFGNode.objects.create(
                            msfg_definition=msfg_def,
                            node_id=f'fault_{i+1}',
                            node_type='fault',
                            name=name,
                            position_x=100 * i,
                            position_y=200
                        )
                        fault_nodes.append(node)
                    
                    # 鍒涘缓杈?
                    for i, (test_node, fault_node) in enumerate(zip(test_nodes, fault_nodes)):
                        MSFGEdge.objects.create(
                            msfg_definition=msfg_def,
                            edge_id=f'edge_{i+1}',
                            source_node=test_node,
                            target_node=fault_node,
                            properties={'weight': 0.8}
                        )
                    
                    # 鍒涘缓娴嬭瘯鐐硅鍒?
                    for i, test_name in enumerate(['娴嬭瘯鐐?', '娴嬭瘯鐐?', '娴嬭瘯鐐?']):
                        TestPointRule.objects.create(
                            msfg_definition=msfg_def,
                            cmg_model=cmg_model,
                            test_name=test_name,
                            rule_id=f'rule_{i+1}',
                            rule_expression=f'abs(param{i+1}) / (abs(param{i+1}) + 10)',
                            weight=1.0,
                            is_online=True,
                            description=f'娴嬭瘯瑙勫垯{i+1}'
                        )
                    
                    # 鍒涘缓娴嬭瘯鐐?閮ㄤ欢鏄犲皠
                    mappings = [
                        ('娴嬭瘯鐐?', '閮ㄤ欢A', 1.0, 1.5, True),
                        ('娴嬭瘯鐐?', '閮ㄤ欢A', 0.8, 1.0, False),
                        ('娴嬭瘯鐐?', '閮ㄤ欢B', 1.2, 1.8, True),
                        ('娴嬭瘯鐐?', '閮ㄤ欢B', 1.0, 1.2, False),
                    ]
                    
                    for test_name, comp_name, weight, importance, is_critical in mappings:
                        TestPointComponentMapping.objects.create(
                            msfg_definition=msfg_def,
                            test_point_name=test_name,
                            component_name=comp_name,
                            mapping_type='one_to_many',
                            weight=weight,
                            component_type='other',
                            importance_weight=importance,
                            is_critical=is_critical,
                            description=f'{test_name} -> {comp_name} 娴嬭瘯鏄犲皠'
                        )
                
                # 鍒涘缓娴嬭瘯鏁版嵁鐐?
                test_data_points = [
                    {'param1': 5.0, 'param2': 12.0, 'param3': 3.0, 'param4': 8.0},
                    {'param1': 15.0, 'param2': 2.0, 'param3': 20.0, 'param4': 1.0},
                    {'param1': 0.5, 'param2': 25.0, 'param3': 7.0, 'param4': 15.0},
                ]
                
                for i, data in enumerate(test_data_points):
                    PHMData.objects.get_or_create(
                        cmg=cmg,
                        timestamp=timezone.now(),
                        data=data,
                        defaults={'results': {}}
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'娴嬭瘯鏁版嵁鍒涘缓瀹屾垚锛丆MG妯″瀷ID: {cmg_model.id}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'鍒涘缓娴嬭瘯鏁版嵁澶辫触: {e}')
            )
    
    def test_scoring_logic(self, cmg_model_id=None):
        """娴嬭瘯璇勫垎閫昏緫"""
        self.stdout.write("娴嬭瘯璇勫垎閫昏緫...")
        
        try:
            # 鑾峰彇娴嬭瘯鏁版嵁
            if cmg_model_id:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            else:
                cmg_model = PHMModel.objects.filter(model_name='TEST_MSFG_MODEL').first()
            
            if not cmg_model:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG妯″瀷锛岃鍏堣繍琛?--create-test-data'))
                return
            
            msfg_def = MSFGDefinition.objects.filter(
                cmg_model=cmg_model, is_active=True
            ).first()
            
            if not msfg_def:
                self.stdout.write(self.style.ERROR('鏈壘鍒版椿璺冪殑MSFG瀹氫箟锛岃鍏堣繍琛?--create-test-data'))
                return
            
            # 鑾峰彇娴嬭瘯鏁版嵁鐐?
            cmg = PHM.objects.filter(cmg_model=cmg_model).first()
            if not cmg:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG瀹炰緥锛岃鍏堣繍琛?--create-test-data'))
                return
                
            data_points = PHMData.objects.filter(cmg=cmg)[:3]
            
            if not data_points:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇曟暟鎹偣锛岃鍏堣繍琛?--create-test-data'))
                return
            
            self.stdout.write(f"娴嬭瘯 {len(data_points)} 涓暟鎹偣...")
            
            for i, data_point in enumerate(data_points):
                self.stdout.write(f"\n--- 鏁版嵁鐐?{i+1} ---")
                self.stdout.write(f"鏁版嵁: {data_point.data}")
                
                # 璁＄畻娴嬬偣鍒嗘暟
                test_scores = calculate_msfg_test_scores(data_point, msfg_def)
                
                self.stdout.write("娴嬬偣鍒嗘暟:")
                for test_name, score in test_scores.items():
                    self.stdout.write(f"  {test_name}: {score:.3f}")
                
                # 楠岃瘉鍒嗘暟鑼冨洿
                for test_name, score in test_scores.items():
                    if not (0.0 <= score <= 1.0):
                        self.stdout.write(
                            self.style.WARNING(f"璀﹀憡: {test_name} 鍒嗘暟瓒呭嚭鑼冨洿: {score}")
                        )
            
            self.stdout.write(self.style.SUCCESS("璇勫垎閫昏緫娴嬭瘯瀹屾垚"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'璇勫垎閫昏緫娴嬭瘯澶辫触: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def test_mapping_logic(self, cmg_model_id=None):
        """娴嬭瘯閮ㄤ欢鏄犲皠閫昏緫"""
        self.stdout.write("娴嬭瘯閮ㄤ欢鏄犲皠閫昏緫...")
        
        try:
            # 鑾峰彇娴嬭瘯鏁版嵁
            if cmg_model_id:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            else:
                cmg_model = PHMModel.objects.filter(model_name='TEST_MSFG_MODEL').first()
            
            if not cmg_model:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG妯″瀷锛岃鍏堣繍琛?--create-test-data'))
                return
                
            msfg_def = MSFGDefinition.objects.filter(
                cmg_model=cmg_model, is_active=True
            ).first()
            
            if not msfg_def:
                self.stdout.write(self.style.ERROR('鏈壘鍒版椿璺冪殑MSFG瀹氫箟锛岃鍏堣繍琛?--create-test-data'))
                return
            
            # 娴嬭瘯閮ㄤ欢鏄犲皠
            component_mappings = build_msfg_component_mappings(msfg_def)
            
            self.stdout.write("閮ㄤ欢鏄犲皠缁撴灉:")
            for comp_name, fault_names in component_mappings.items():
                self.stdout.write(f"  {comp_name}: {fault_names}")
            
            # 楠岃瘉鏄犲皠瀹屾暣鎬?
            expected_components = set(msfg_def.component_names or [])
            actual_components = set(component_mappings.keys())
            
            if expected_components != actual_components:
                missing = expected_components - actual_components
                extra = actual_components - expected_components
                if missing:
                    self.stdout.write(self.style.WARNING(f"缂哄け閮ㄤ欢: {missing}"))
                if extra:
                    self.stdout.write(self.style.WARNING(f"澶氫綑閮ㄤ欢: {extra}"))
            
            self.stdout.write(self.style.SUCCESS("閮ㄤ欢鏄犲皠娴嬭瘯瀹屾垚"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'閮ㄤ欢鏄犲皠娴嬭瘯澶辫触: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def test_fusion_algorithm(self, cmg_model_id=None):
        """娴嬭瘯铻嶅悎绠楁硶"""
        self.stdout.write("娴嬭瘯铻嶅悎绠楁硶...")
        
        try:
            # 鑾峰彇娴嬭瘯鏁版嵁
            if cmg_model_id:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            else:
                cmg_model = PHMModel.objects.filter(model_name='TEST_MSFG_MODEL').first()
            
            if not cmg_model:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG妯″瀷锛岃鍏堣繍琛?--create-test-data'))
                return
                
            msfg_def = MSFGDefinition.objects.filter(
                cmg_model=cmg_model, is_active=True
            ).first()
            
            if not msfg_def:
                self.stdout.write(self.style.ERROR('鏈壘鍒版椿璺冪殑MSFG瀹氫箟锛岃鍏堣繍琛?--create-test-data'))
                return
            
            cmg = PHM.objects.filter(cmg_model=cmg_model).first()
            if not cmg:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG瀹炰緥锛岃鍏堣繍琛?--create-test-data'))
                return
                
            data_point = PHMData.objects.filter(cmg=cmg).first()
            if not data_point:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇曟暟鎹偣锛岃鍏堣繍琛?--create-test-data'))
                return
            
            # 鑾峰彇MSFG缁勪欢
            test_nodes = list(msfg_def.nodes.filter(node_type='test'))
            fault_nodes = list(msfg_def.nodes.filter(node_type='fault'))
            edges = list(msfg_def.edges.all())
            
            # 璁＄畻娴嬬偣鍒嗘暟
            test_scores_dict = calculate_msfg_test_scores(data_point, msfg_def)
            test_scores = {name: [score] for name, score in test_scores_dict.items()}
            
            # 鑾峰彇閮ㄤ欢鏄犲皠
            component_mappings = build_msfg_component_mappings(msfg_def)
            
            # 杩愯铻嶅悎绠楁硶
            fusion_algorithm = AdvancedMSFGFusion(eps=1e-15, n_round=5)
            
            analysis_result = fusion_algorithm.run_advanced_analysis(
                test_scores=test_scores,
                test_nodes=test_nodes,
                fault_nodes=fault_nodes,
                edges=edges,
                component_mappings=component_mappings
            )
            
            # 鏄剧ず缁撴灉
            self.stdout.write("\n=== 铻嶅悎绠楁硶缁撴灉 ===")
            
            self.stdout.write("\n娴嬬偣缁撴灉:")
            for name, result in analysis_result['test_results'].items():
                self.stdout.write(f"  {name}: {result}")
            
            self.stdout.write("\n鏁呴殰缁撴灉:")
            for name, result in analysis_result['fault_results'].items():
                self.stdout.write(f"  {name}: {result}")
            
            self.stdout.write("\n閮ㄤ欢缁撴灉:")
            for name, result in analysis_result['component_results'].items():
                self.stdout.write(f"  {name}: 鍋ュ悍鍒嗘暟={result.get('health_score', 'N/A')}")
            
            self.stdout.write(f"\n绯荤粺缁撴灉:")
            system_results = analysis_result['system_results']
            self.stdout.write(f"  鏁翠綋鍋ュ悍搴? {system_results.get('overall_health', 'N/A')}")
            self.stdout.write(f"  閮ㄤ欢鏁伴噺: {system_results.get('component_count', 'N/A')}")
            
            self.stdout.write(self.style.SUCCESS("铻嶅悎绠楁硶娴嬭瘯瀹屾垚"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'铻嶅悎绠楁硶娴嬭瘯澶辫触: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def test_full_pipeline(self, cmg_model_id=None):
        """娴嬭瘯瀹屾暣娴佺▼"""
        self.stdout.write("娴嬭瘯瀹屾暣娴佺▼锛堝寘鎷暟鎹簱瀛樺偍锛?..")
        
        try:
            # 鑾峰彇娴嬭瘯鏁版嵁
            if cmg_model_id:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
            else:
                cmg_model = PHMModel.objects.filter(model_name='TEST_MSFG_MODEL').first()
            
            if not cmg_model:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG妯″瀷锛岃鍏堣繍琛?--create-test-data'))
                return
            
            cmg = PHM.objects.filter(cmg_model=cmg_model).first()
            if not cmg:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇旵MG瀹炰緥锛岃鍏堣繍琛?--create-test-data'))
                return
                
            data_point = PHMData.objects.filter(cmg=cmg).first()
            if not data_point:
                self.stdout.write(self.style.ERROR('鏈壘鍒版祴璇曟暟鎹偣锛岃鍏堣繍琛?--create-test-data'))
                return
            
            # 妯℃嫙鎵归噺澶勭悊鐨凪SFG妫€娴?
            from data_management.batch_processing import BatchFileProcessor
            
            processor = BatchFileProcessor()
            result = processor._run_msfg_detection(data_point, cmg)
            
            if result:
                self.stdout.write("\n=== 瀹屾暣娴佺▼缁撴灉 ===")
                self.stdout.write(f"鏁翠綋鍋ュ悍鍒嗘暟: {result['overall_health_score']}")
                self.stdout.write(f"妫€娴嬪埌鐨勬晠闅? {result['detected_faults']}")
                self.stdout.write(f"鍏抽敭閮ㄤ欢: {result['critical_components']}")
                
                # 娴嬭瘯鏁版嵁搴撳瓨鍌?
                msfg_def = MSFGDefinition.objects.get(id=result['msfg_definition_id'])
                
                # 鍒涘缓鍒嗘瀽缁撴灉璁板綍
                analysis_record = MSFGAnalysisResult.objects.create(
                    data_point=data_point,
                    msfg_definition=msfg_def,
                    test_results=result['test_results'],
                    fault_results=result['fault_results'],
                    system_results=result['system_results'],
                    component_results=result['component_results'],
                    overall_health_score=result['overall_health_score'],
                    detected_faults=result['detected_faults'],
                    critical_components=result['critical_components'],
                    analysis_details=result['analysis_details']
                )
                
                self.stdout.write(f"鍒嗘瀽缁撴灉宸蹭繚瀛橈紝ID: {analysis_record.id}")
                
                # 楠岃瘉鏁版嵁瀹屾暣鎬?
                saved_record = MSFGAnalysisResult.objects.get(id=analysis_record.id)
                
                if saved_record.overall_health_score != result['overall_health_score']:
                    self.stdout.write(self.style.WARNING("鍋ュ悍鍒嗘暟淇濆瓨涓嶄竴鑷?))
                
                if len(saved_record.component_results) != len(result['component_results']):
                    self.stdout.write(self.style.WARNING("閮ㄤ欢缁撴灉淇濆瓨涓嶅畬鏁?))
                
                self.stdout.write(self.style.SUCCESS("瀹屾暣娴佺▼娴嬭瘯鎴愬姛"))
            else:
                self.stdout.write(self.style.ERROR("MSFG妫€娴嬭繑鍥炵┖缁撴灉"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'瀹屾暣娴佺▼娴嬭瘯澶辫触: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

