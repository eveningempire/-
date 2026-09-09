"""
娴嬭瘯瑙勫垯妫€娴嬪姛鑳?
浣跨敤榛樿瑙勫垯鍜屾ā鎷熸暟鎹繘琛屾祴璇?
"""

import json
import random
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.db import transaction

from data_management.models import PHMModel, PHM, PHMData
from rule_detection.models import RuleDefinition, FaultDefinition
from rule_detection.service import _get_compiled_rules_for_model
from rule_detection.algorithms.rule.rule_detector import evaluate_rules_on_point


class Command(BaseCommand):
    help = '娴嬭瘯瑙勫垯妫€娴嬪姛鑳?

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            type=str,
            default='PHM_Default',
            help='瑕佹祴璇曠殑PHM妯″瀷鍚嶇О'
        )
        parser.add_argument(
            '--test-count',
            type=int,
            default=10,
            help='鐢熸垚娴嬭瘯鏁版嵁鐨勬暟閲?
        )

    def handle(self, *args, **options):
        model_name = options['model_name']
        test_count = options['test_count']
        
        # 鑾峰彇PHM妯″瀷
        try:
            cmg_model = PHMModel.objects.get(model_name=model_name)
        except PHMModel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"鉂?鎵句笉鍒癈MG妯″瀷: {model_name}")
            )
            self.stdout.write("馃挕 璇峰厛杩愯: python manage.py create_default_rules")
            return

        # 鑾峰彇鎴栧垱寤烘祴璇旵MG
        cmg, created = PHM.objects.get_or_create(
            cmg_id=f"TEST_{model_name}",
            defaults={
                'cmg_model': cmg_model,
                'name': f'娴嬭瘯PHM_{model_name}',
                'enabled': True
            }
        )
        
        if created:
            self.stdout.write(f"鉁?鍒涘缓娴嬭瘯PHM: {cmg.name}")
        else:
            self.stdout.write(f"馃攧 浣跨敤鐜版湁娴嬭瘯PHM: {cmg.name}")

        # 鑾峰彇瑙勫垯淇℃伅
        rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
        fault_defs = FaultDefinition.objects.filter(cmg_model=cmg_model)
        
        self.stdout.write(f"\n馃搳 瑙勫垯妫€娴嬮厤缃?")
        self.stdout.write(f"   妯″瀷: {cmg_model.model_name}")
        self.stdout.write(f"   鏁呴殰绫诲瀷: {fault_defs.count()}")
        self.stdout.write(f"   瑙勫垯鏁伴噺: {rules.count()}")
        
        # 缂栬瘧瑙勫垯
        try:
            compiled_rules = _get_compiled_rules_for_model(cmg_model)
            self.stdout.write(f"鉁?鎴愬姛缂栬瘧 {len(compiled_rules)} 鏉¤鍒?)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"鉂?瑙勫垯缂栬瘧澶辫触: {e}")
            )
            return

        # 鐢熸垚娴嬭瘯鏁版嵁骞舵墽琛岃鍒欐娴?
        self.stdout.write(f"\n馃敩 寮€濮嬭鍒欐娴嬫祴璇?(鐢熸垚 {test_count} 涓祴璇曠偣):")
        
        test_scenarios = [
            # 姝ｅ父鏁版嵁
            {
                'name': '姝ｅ父宸ュ喌',
                'data': {
                    'value_highT': 25.0,
                    'value_highI': 0.5,
                    'value_lowI': 2.5,
                    'w': 6000.0,
                    'u': 26.0,
                    'viscosity_estimated': 15.0,
                    'mu_EHL_estimated': 0.05
                },
                'expected_faults': []
            },
            # 娓╁害寮傚父
            {
                'name': '娓╁害杩囬珮鏁呴殰',
                'data': {
                    'value_highT': 32.0,  # 瓒呰繃30.0闃堝€?
                    'value_highI': 0.5,
                    'value_lowI': 2.5,
                    'w': 6000.0,
                    'u': 26.0,
                    'viscosity_estimated': 15.0
                },
                'expected_faults': ['TEMP_HIGH_001']
            },
            # 鐢垫祦寮傚父
            {
                'name': '鐢垫祦寮傚父鏁呴殰',
                'data': {
                    'value_highT': 25.0,
                    'value_highI': 1.2,  # 瓒呰繃1.0闃堝€?
                    'value_lowI': 4.5,   # 瓒呰繃4.0闃堝€?
                    'w': 6000.0,
                    'u': 26.0,
                    'viscosity_estimated': 15.0
                },
                'expected_faults': ['CURRENT_HIGH_001', 'CURRENT_LOW_001']
            },
            # 杞€熷紓甯?
            {
                'name': '杞€熻繃浣庢晠闅?,
                'data': {
                    'value_highT': 25.0,
                    'value_highI': 0.5,
                    'value_lowI': 2.5,
                    'w': 5850.0,  # 浣庝簬5900.0闃堝€?
                    'u': 26.0,
                    'viscosity_estimated': 15.0
                },
                'expected_faults': ['SPEED_LOW_001']
            },
            # 澶嶅悎鏁呴殰
            {
                'name': '绯荤粺缁煎悎鏁呴殰',
                'data': {
                    'value_highT': 29.0,  # 楂樻俯
                    'value_highI': 0.9,   # 楂樼數娴?
                    'value_lowI': 3.8,    # 楂樹綆鐢垫祦
                    'w': 5940.0,          # 浣庤浆閫?
                    'u': 29.0,            # 楂樻尟鍔?
                    'viscosity_estimated': 25.0  # 楂樼矘搴?
                },
                'expected_faults': ['SYSTEM_CRITICAL_001', 'SYSTEM_CRITICAL_002']
            }
        ]

        total_triggered = 0
        total_tests = 0
        
        for scenario in test_scenarios:
            self.stdout.write(f"\n馃И 娴嬭瘯鍦烘櫙: {scenario['name']}")
            
            # 娣诲姞闅忔満鍣０浣挎暟鎹洿鐪熷疄
            test_data = {}
            for param, value in scenario['data'].items():
                noise = random.uniform(-0.1, 0.1) * value if value != 0 else random.uniform(-0.1, 0.1)
                test_data[param] = value + noise
            
            # 鎵ц瑙勫垯妫€娴?
            try:
                results = evaluate_rules_on_point(test_data, compiled_rules)
                total_tests += len(results)
                
                # 缁熻瑙﹀彂鐨勮鍒?
                triggered_rules = [r for r in results if r['is_triggered']]
                total_triggered += len(triggered_rules)
                
                # 鏄剧ず缁撴灉
                self.stdout.write(f"   鏁版嵁: {json.dumps(test_data, indent=2, default=str)}")
                self.stdout.write(f"   瑙勫垯璇勪及: {len(results)} 鏉¤鍒? {len(triggered_rules)} 鏉¤Е鍙?)
                
                if triggered_rules:
                    for rule in triggered_rules:
                        self.stdout.write(
                            f"   鈿狅笍  瑙﹀彂鏁呴殰: {rule['fault_name']} "
                            f"(瑙勫垯: {rule['rule_id']}, 绛夌骇: {rule['fault_level']})"
                        )
                else:
                    self.stdout.write("   鉁?鏃犳晠闅滄鍑?)
                    
                # 淇濆瓨娴嬭瘯鏁版嵁鍒版暟鎹簱
                with transaction.atomic():
                    cmg_data = PHMData.objects.create(
                        cmg=cmg,
                        timestamp=datetime.now(timezone.utc),
                        data=test_data,
                        results={
                            'rule_detection': results,
                            'test_scenario': scenario['name'],
                            'summary': {
                                'total_rules': len(results),
                                'triggered_rules': len(triggered_rules),
                                'fault_detected': len(triggered_rules) > 0
                            }
                        }
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   鉂?瑙勫垯妫€娴嬪け璐? {e}")
                )

        # 缁熻鎬荤粨
        self.stdout.write(
            self.style.SUCCESS(
                f"\n馃搱 娴嬭瘯鎬荤粨:\n"
                f"   娴嬭瘯鍦烘櫙: {len(test_scenarios)} 涓猏n"
                f"   瑙勫垯璇勪及: {total_tests} 娆n"
                f"   鏁呴殰瑙﹀彂: {total_triggered} 娆n"
                f"   瑙﹀彂鐜? {total_triggered/total_tests*100:.1f}%\n"
                f"\n馃捑 娴嬭瘯鏁版嵁宸蹭繚瀛樺埌鏁版嵁搴撲腑\n"
                f"馃搵 鎮ㄥ彲浠ラ€氳繃绠＄悊鐣岄潰鏌ョ湅璇︾粏鐨勬娴嬬粨鏋?
            )
        )

