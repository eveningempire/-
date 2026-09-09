"""
鍒涘缓榛樿鐨勪笓瀹惰鍒欑敤浜庢祴璇?
鍩轰簬甯歌鐨凜MG閬ユ祴鍙傛暟璁捐瑙勫垯
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from data_management.models import PHMModel
from rule_detection.models import FaultDefinition, RuleDefinition


class Command(BaseCommand):
    help = '鍒涘缓榛樿鐨勪笓瀹惰鍒欑敤浜庢祴璇?

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            type=str,
            default='PHM_Default',
            help='PHM妯″瀷鍚嶇О锛岄粯璁や负PHM_Default'
        )

    def handle(self, *args, **options):
        model_name = options['model_name']
        
        # 鑾峰彇鎴栧垱寤篊MG妯″瀷
        cmg_model, created = PHMModel.objects.get_or_create(
            model_name=model_name,
            defaults={
                'description': '榛樿PHM妯″瀷锛岀敤浜庢祴璇曡鍒欐娴?,
                'cmg_type_id': 1  # 鍋囪宸插瓨鍦ㄧ被鍨?
            }
        )
        
        if created:
            self.stdout.write(f"鉁?鍒涘缓浜嗘柊鐨凜MG妯″瀷: {model_name}")
        else:
            self.stdout.write(f"馃攧 浣跨敤鐜版湁PHM妯″瀷: {model_name}")

        # 鍒犻櫎鐜版湁鐨勮鍒欙紙濡傛灉閲嶆柊杩愯鍛戒护锛?
        FaultDefinition.objects.filter(cmg_model=cmg_model).delete()
        self.stdout.write("馃棏锔?娓呯悊鐜版湁瑙勫垯")

        with transaction.atomic():
            # 瀹氫箟鏁呴殰绫诲瀷鍜屽搴旇鍒?
            default_rules = [
                # 娓╁害鐩稿叧鏁呴殰
                {
                    'fault_name': '娓╁害杩囬珮鏁呴殰',
                    'fault_level': 'HIGH',
                    'component': '娓╁害浼犳劅鍣?,
                    'description': '绯荤粺娓╁害瓒呰繃瀹夊叏闃堝€?,
                    'rules': [
                        {
                            'rule_id': 'TEMP_HIGH_001',
                            'expression': 'value_highT > 30.0',
                            'description': '楂樻俯浼犳劅鍣ㄨ鏁拌繃楂樻姤璀?,
                            'related_parameters': ['value_highT']
                        },
                        {
                            'rule_id': 'TEMP_HIGH_002', 
                            'expression': 'value_lowI > 3.0 and value_highT > 25.0',
                            'description': '娓╁害涓庣數娴佽仈鍚堝紓甯告娴?,
                            'related_parameters': ['value_lowI', 'value_highT']
                        }
                    ]
                },
                
                # 鐢垫祦鐩稿叧鏁呴殰
                {
                    'fault_name': '鐢垫祦寮傚父鏁呴殰',
                    'fault_level': 'MEDIUM',
                    'component': '鐢垫祦浼犳劅鍣?,
                    'description': '绯荤粺鐢垫祦瓒呭嚭姝ｅ父鑼冨洿',
                    'rules': [
                        {
                            'rule_id': 'CURRENT_HIGH_001',
                            'expression': 'value_highI > 1.0',
                            'description': '楂樼數娴佷紶鎰熷櫒寮傚父',
                            'related_parameters': ['value_highI']
                        },
                        {
                            'rule_id': 'CURRENT_LOW_001',
                            'expression': 'value_lowI > 4.0',
                            'description': '浣庣數娴佷紶鎰熷櫒寮傚父',
                            'related_parameters': ['value_lowI']
                        }
                    ]
                },
                
                # 杞€熺浉鍏虫晠闅?
                {
                    'fault_name': '杞€熷紓甯告晠闅?, 
                    'fault_level': 'HIGH',
                    'component': '杞€熶紶鎰熷櫒',
                    'description': '闄€铻鸿浆閫熷亸绂绘甯稿伐浣滆寖鍥?,
                    'rules': [
                        {
                            'rule_id': 'SPEED_LOW_001',
                            'expression': 'w < 5900.0',
                            'description': '杞€熻繃浣庢晠闅?,
                            'related_parameters': ['w']
                        },
                        {
                            'rule_id': 'SPEED_HIGH_001',
                            'expression': 'w > 6100.0', 
                            'description': '杞€熻繃楂樻晠闅?,
                            'related_parameters': ['w']
                        }
                    ]
                },
                
                # 鎸姩鐩稿叧鏁呴殰
                {
                    'fault_name': '鎸姩寮傚父鏁呴殰',
                    'fault_level': 'MEDIUM',
                    'component': '鎸姩浼犳劅鍣?,
                    'description': '绯荤粺鎸姩瓒呭嚭姝ｅ父鑼冨洿',
                    'rules': [
                        {
                            'rule_id': 'VIBRATION_001',
                            'expression': 'u > 30.0',
                            'description': '鎸姩骞呭€煎紓甯?,
                            'related_parameters': ['u']
                        }
                    ]
                },
                
                # 绮樺害鐩稿叧鏁呴殰
                {
                    'fault_name': '娑︽粦绯荤粺鏁呴殰',
                    'fault_level': 'HIGH',
                    'component': '娑︽粦绯荤粺',
                    'description': '娑︽粦娌圭矘搴﹀紓甯?,
                    'rules': [
                        {
                            'rule_id': 'VISCOSITY_001',
                            'expression': 'viscosity_estimated > 20.0',
                            'description': '娑︽粦娌圭矘搴﹁繃楂?,
                            'related_parameters': ['viscosity_estimated']
                        },
                        {
                            'rule_id': 'VISCOSITY_002',
                            'expression': 'viscosity_estimated < 10.0',
                            'description': '娑︽粦娌圭矘搴﹁繃浣?,
                            'related_parameters': ['viscosity_estimated']
                        }
                    ]
                },
                
                # 澶嶅悎鏁呴殰妫€娴?
                {
                    'fault_name': '绯荤粺缁煎悎鏁呴殰',
                    'fault_level': 'CRITICAL',
                    'component': '缁煎悎绯荤粺',
                    'description': '澶氫釜鍙傛暟鍚屾椂寮傚父',
                    'rules': [
                        {
                            'rule_id': 'SYSTEM_CRITICAL_001',
                            'expression': 'value_highT > 28.0 and w < 5950.0',
                            'description': '楂樻俯涓旇浆閫熷紓甯哥殑涓ラ噸鏁呴殰',
                            'related_parameters': ['value_highT', 'w']
                        },
                        {
                            'rule_id': 'SYSTEM_CRITICAL_002',
                            'expression': 'value_highI > 0.8 and value_lowI > 3.5 and u > 28.0',
                            'description': '鐢垫祦鍜屾尟鍔ㄥ悓鏃跺紓甯?,
                            'related_parameters': ['value_highI', 'value_lowI', 'u']
                        }
                    ]
                }
            ]

            # 鍒涘缓鏁呴殰瀹氫箟鍜岃鍒?
            for fault_config in default_rules:
                # 鍒涘缓鏁呴殰瀹氫箟
                fault_def = FaultDefinition.objects.create(
                    cmg_model=cmg_model,
                    fault_name=fault_config['fault_name'],
                    fault_level=fault_config['fault_level'],
                    component=fault_config['component'],
                    description=fault_config['description']
                )
                
                self.stdout.write(f"馃搵 鍒涘缓鏁呴殰瀹氫箟: {fault_config['fault_name']}")
                
                # 鍒涘缓瀵瑰簲鐨勮鍒?
                for rule_config in fault_config['rules']:
                    rule_def = RuleDefinition.objects.create(
                        cmg_model=cmg_model,
                        fault_definition=fault_def,
                        rule_id=rule_config['rule_id'],
                        rule_expression=rule_config['expression'],
                        source='expert',
                        plan_description=rule_config['description'],
                        is_online=True,
                        is_new=True,
                        is_editable=True,
                        related_parameters=rule_config['related_parameters']
                    )
                    
                    self.stdout.write(f"  鉁?鍒涘缓瑙勫垯: {rule_config['rule_id']} - {rule_config['expression']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n馃帀 鎴愬姛鍒涘缓榛樿瑙勫垯闆嗭紒\n"
                f"馃搳 鏁呴殰绫诲瀷鏁伴噺: {len(default_rules)}\n"
                f"馃搹 瑙勫垯鎬绘暟: {sum(len(f['rules']) for f in default_rules)}\n"
                f"馃幆 PHM妯″瀷: {model_name}\n"
                f"\n馃挕 杩欎簺瑙勫垯鍩轰簬甯歌鐨凜MG閬ユ祴鍙傛暟璁捐锛屽寘鎷細\n"
                f"   - 娓╁害浼犳劅鍣?(value_highT)\n"
                f"   - 鐢垫祦浼犳劅鍣?(value_highI, value_lowI)\n"
                f"   - 杞€熶紶鎰熷櫒 (w)\n"
                f"   - 鎸姩浼犳劅鍣?(u)\n"
                f"   - 绮樺害浼拌 (viscosity_estimated)\n"
                f"\n馃敡 鎮ㄥ彲浠ラ€氳繃绠＄悊鐣岄潰鎴朅PI杩涗竴姝ヨ皟鏁磋繖浜涜鍒欍€?
            )
        )

