"""
妫€鏌SFG鐩稿叧鏁版嵁鐨勫懡浠?
鐢ㄤ簬浜嗚В鐜版湁鏁版嵁搴撲腑鐨勬暟鎹儏鍐?
"""

from django.core.management.base import BaseCommand
from data_management.models import PHM, PHMModel, PHMData
from msfg_analysis.models import (
    MSFGDefinition, MSFGNode, MSFGEdge, TestPointRule, 
    TestPointComponentMapping, MSFGAnalysisResult
)

class Command(BaseCommand):
    help = '妫€鏌SFG鐩稿叧鏁版嵁'
    
    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('寮€濮嬫鏌SFG鐩稿叧鏁版嵁')
            )
            
            # 妫€鏌MG妯″瀷鍜屽疄渚?
            self.check_cmg_data()
            
            # 妫€鏌SFG瀹氫箟
            self.check_msfg_definitions()
            
            # 妫€鏌ユ祴鐐硅鍒?
            self.check_testpoint_rules()
            
            # 妫€鏌ラ儴浠舵槧灏?
            self.check_component_mappings()
            
            # 妫€鏌ュ垎鏋愮粨鏋?
            self.check_analysis_results()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'妫€鏌ヨ繃绋嬩腑鍙戠敓閿欒: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def check_cmg_data(self):
        """妫€鏌MG鏁版嵁"""
        self.stdout.write("\n=== PHM鏁版嵁妫€鏌?===")
        
        cmg_models = PHMModel.objects.all()
        self.stdout.write(f"PHM妯″瀷鏁伴噺: {cmg_models.count()}")
        
        for model in cmg_models[:5]:  # 鏄剧ず鍓?涓?
            cmg_count = model.cmgs.count()
            data_count = PHMData.objects.filter(cmg__cmg_model=model).count()
            self.stdout.write(f"  妯″瀷: {model.model_name} - PHM鏁伴噺: {cmg_count}, 鏁版嵁鐐规暟閲? {data_count}")
        
        # 鏄剧ず涓€浜汣MG瀹炰緥
        cmgs = PHM.objects.all()[:3]
        for cmg in cmgs:
            recent_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp')[:1]
            if recent_data:
                data_sample = recent_data[0]
                self.stdout.write(f"  PHM {cmg.cmg_id}: 鏈€杩戞暟鎹?- {data_sample.timestamp}, 鍙傛暟鏁伴噺: {len(data_sample.data or {})}")
    
    def check_msfg_definitions(self):
        """妫€鏌SFG瀹氫箟"""
        self.stdout.write("\n=== MSFG瀹氫箟妫€鏌?===")
        
        msfg_defs = MSFGDefinition.objects.all()
        self.stdout.write(f"MSFG瀹氫箟鏁伴噺: {msfg_defs.count()}")
        
        for msfg in msfg_defs[:5]:
            nodes_count = msfg.nodes.count()
            edges_count = msfg.edges.count()
            test_nodes = msfg.nodes.filter(node_type='test').count()
            fault_nodes = msfg.nodes.filter(node_type='fault').count()
            
            self.stdout.write(f"  MSFG: {msfg.name} ({'娲昏穬' if msfg.is_active else '闈炴椿璺?})")
            self.stdout.write(f"    鑺傜偣: {nodes_count} (娴嬭瘯鐐? {test_nodes}, 鏁呴殰: {fault_nodes}), 杈? {edges_count}")
            self.stdout.write(f"    娴嬭瘯鐐瑰悕绉? {msfg.test_names}")
            self.stdout.write(f"    閮ㄤ欢鍚嶇О: {msfg.component_names}")
    
    def check_testpoint_rules(self):
        """妫€鏌ユ祴鐐硅鍒?""
        self.stdout.write("\n=== 娴嬬偣瑙勫垯妫€鏌?===")
        
        rules = TestPointRule.objects.all()
        self.stdout.write(f"娴嬬偣瑙勫垯鏁伴噺: {rules.count()}")
        
        active_rules = rules.filter(is_online=True)
        self.stdout.write(f"娲昏穬瑙勫垯鏁伴噺: {active_rules.count()}")
        
        # 鎸塎SFG鍒嗙粍鏄剧ず
        for msfg in MSFGDefinition.objects.filter(is_active=True)[:3]:
            msfg_rules = rules.filter(msfg_definition=msfg)
            self.stdout.write(f"  MSFG {msfg.name}: {msfg_rules.count()} 涓鍒?)
            
            for rule in msfg_rules[:3]:
                self.stdout.write(f"    瑙勫垯: {rule.test_name} - {rule.rule_id} ({'鍦ㄧ嚎' if rule.is_online else '绂荤嚎'})")
                self.stdout.write(f"      琛ㄨ揪寮? {rule.rule_expression[:50]}...")
    
    def check_component_mappings(self):
        """妫€鏌ラ儴浠舵槧灏?""
        self.stdout.write("\n=== 閮ㄤ欢鏄犲皠妫€鏌?===")
        
        mappings = TestPointComponentMapping.objects.all()
        self.stdout.write(f"閮ㄤ欢鏄犲皠鏁伴噺: {mappings.count()}")
        
        # 鎸塎SFG鍒嗙粍鏄剧ず
        for msfg in MSFGDefinition.objects.filter(is_active=True)[:3]:
            msfg_mappings = mappings.filter(msfg_definition=msfg)
            self.stdout.write(f"  MSFG {msfg.name}: {msfg_mappings.count()} 涓槧灏?)
            
            # 鎸夐儴浠跺垎缁?
            components = msfg_mappings.values_list('component_name', flat=True).distinct()
            for comp in components[:5]:
                comp_mappings = msfg_mappings.filter(component_name=comp)
                test_points = list(comp_mappings.values_list('test_point_name', flat=True))
                self.stdout.write(f"    閮ㄤ欢 {comp}: {len(test_points)} 涓祴鐐?- {test_points[:3]}")
    
    def check_analysis_results(self):
        """妫€鏌ュ垎鏋愮粨鏋?""
        self.stdout.write("\n=== 鍒嗘瀽缁撴灉妫€鏌?===")
        
        results = MSFGAnalysisResult.objects.all()
        self.stdout.write(f"鍒嗘瀽缁撴灉鏁伴噺: {results.count()}")
        
        if results.exists():
            recent_results = results.order_by('-created_at')[:3]
            for result in recent_results:
                self.stdout.write(f"  缁撴灉: {result.created_at} - 鍋ュ悍鍒嗘暟: {result.overall_health_score}")
                self.stdout.write(f"    MSFG: {result.msfg_definition.name}")
                self.stdout.write(f"    妫€娴嬫晠闅? {len(result.detected_faults)} 涓?)
                self.stdout.write(f"    鍏抽敭閮ㄤ欢: {len(result.critical_components)} 涓?)
        else:
            self.stdout.write("  鏆傛棤鍒嗘瀽缁撴灉")
        
        self.stdout.write(self.style.SUCCESS('\n鏁版嵁妫€鏌ュ畬鎴?))

