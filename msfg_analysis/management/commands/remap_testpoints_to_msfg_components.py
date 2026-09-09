"""
绠＄悊鍛戒护锛氶噸鏂版槧灏勬祴璇曠偣鍒癕SFG閮ㄤ欢
纭繚鎵€鏈夋祴璇曠偣閮芥槧灏勫埌浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import (
    extract_components_from_msfg,
    _infer_component_from_test_name
)


class Command(BaseCommand):
    help = '閲嶆柊鏄犲皠娴嬭瘯鐐瑰埌MSFG閮ㄤ欢锛岀‘淇濅娇鐢ㄤ粠MSFG缁撴瀯涓彁鍙栫殑閮ㄤ欢'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cmg-model-id',
            type=int,
            help='鎸囧畾瑕侀噸鏂版槧灏勭殑PHM妯″瀷ID锛岀暀绌哄垯澶勭悊鎵€鏈夋ā鍨?
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='寮哄埗閲嶆柊鍒涘缓鎵€鏈夋槧灏勶紙鍒犻櫎鐜版湁鏄犲皠锛?
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='鍙樉绀哄皢瑕佹墽琛岀殑鎿嶄綔锛屼笉瀹為檯淇敼鏁版嵁'
        )

    def handle(self, *args, **options):
        cmg_model_id = options.get('cmg_model_id')
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('馃攳 骞茶繍琛屾ā寮忥細鍙樉绀烘搷浣滐紝涓嶄慨鏀规暟鎹?)
            )

        if force:
            self.stdout.write(
                self.style.WARNING('鈿狅笍 寮哄埗妯″紡锛氬皢鍒犻櫎鐜版湁鏄犲皠骞堕噸鏂板垱寤?)
            )

        # 鑾峰彇瑕佸鐞嗙殑PHM妯″瀷
        if cmg_model_id:
            try:
                cmg_models = [PHMModel.objects.get(id=cmg_model_id)]
                self.stdout.write(f'澶勭悊鎸囧畾鐨凜MG妯″瀷: {cmg_models[0].model_name}')
            except PHMModel.DoesNotExist:
                raise CommandError(f'PHM妯″瀷ID {cmg_model_id} 涓嶅瓨鍦?)
        else:
            cmg_models = PHMModel.objects.all()
            self.stdout.write(f'澶勭悊鎵€鏈塁MG妯″瀷锛屽叡 {cmg_models.count()} 涓?)

        total_success = 0
        total_error = 0
        total_mappings_created = 0
        total_mappings_updated = 0

        for cmg_model in cmg_models:
            self.stdout.write(f'\n馃搳 澶勭悊PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})')
            
            try:
                # 鑾峰彇婵€娲荤殑MSFG閰嶇疆
                active_msfg = MSFGDefinition.objects.filter(
                    cmg_model=cmg_model,
                    is_active=True
                ).order_by('-updated_at').first()
                
                if not active_msfg:
                    self.stdout.write(
                        self.style.WARNING(f'  鈿狅笍  娌℃湁婵€娲荤殑MSFG閰嶇疆锛岃烦杩?)
                    )
                    continue

                self.stdout.write(f'  鉁?鎵惧埌婵€娲荤殑MSFG閰嶇疆: {active_msfg.name}')

                # 鎻愬彇MSFG閮ㄤ欢
                available_components = extract_components_from_msfg(active_msfg)
                self.stdout.write(f'  馃敡 MSFG閮ㄤ欢鍒楄〃: {", ".join(available_components)}')

                # 鑾峰彇娴嬭瘯鐐瑰垪琛?
                test_names = active_msfg.test_names or []
                self.stdout.write(f'  馃摑 娴嬭瘯鐐规暟閲? {len(test_names)}')

                if not test_names:
                    self.stdout.write(
                        self.style.WARNING(f'  鈿狅笍  娌℃湁娴嬭瘯鐐癸紝璺宠繃')
                    )
                    continue

                mappings_created = 0
                mappings_updated = 0

                if not dry_run:
                    with transaction.atomic():
                        # 濡傛灉鏄己鍒舵ā寮忥紝鍒犻櫎鐜版湁鏄犲皠
                        if force:
                            deleted_count = TestPointComponentMapping.objects.filter(
                                msfg_definition=active_msfg
                            ).delete()[0]
                            self.stdout.write(f'  馃棏锔? 鍒犻櫎浜?{deleted_count} 涓幇鏈夋槧灏?)

                        # 鑾峰彇鐜版湁鏄犲皠
                        existing_mappings = {}
                        if not force:
                            for mapping in TestPointComponentMapping.objects.filter(msfg_definition=active_msfg):
                                existing_mappings[mapping.test_point_name] = mapping

                        # 澶勭悊姣忎釜娴嬭瘯鐐?
                        for test_name in test_names:
                            # 鎺ㄦ柇鏈€浣抽儴浠舵槧灏?
                            component_name, component_type = _infer_component_from_test_name(
                                test_name, available_components
                            )

                            if test_name in existing_mappings:
                                # 鏇存柊鐜版湁鏄犲皠
                                mapping = existing_mappings[test_name]
                                old_component = mapping.component_name
                                
                                if old_component != component_name:
                                    mapping.component_name = component_name
                                    mapping.component_type = component_type
                                    mapping.description = f'閲嶆柊鏄犲皠锛歿test_name} 鈫?{component_name}'
                                    mapping.save()
                                    mappings_updated += 1
                                    self.stdout.write(f'    鈫?鏇存柊鏄犲皠: {test_name} ({old_component} 鈫?{component_name})')
                            else:
                                # 鍒涘缓鏂版槧灏?
                                TestPointComponentMapping.objects.create(
                                    msfg_definition=active_msfg,
                                    test_point_name=test_name,
                                    component_name=component_name,
                                    component_type=component_type,
                                    importance_weight=1.0,
                                    is_critical=False,
                                    description=f'鑷姩鏄犲皠锛歿test_name} 鈫?{component_name}'
                                )
                                mappings_created += 1
                                self.stdout.write(f'    鉃?鍒涘缓鏄犲皠: {test_name} 鈫?{component_name} ({component_type})')
                else:
                    # 骞茶繍琛屾ā寮忥細鍙樉绀哄皢瑕佸垱寤虹殑鏄犲皠
                    for test_name in test_names:
                        component_name, component_type = _infer_component_from_test_name(
                            test_name, available_components
                        )
                        self.stdout.write(f'    馃攳 灏嗘槧灏? {test_name} 鈫?{component_name} ({component_type})')
                    mappings_created = len(test_names)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  鉁?{"妯℃嫙" if dry_run else ""}瀹屾垚: '
                        f'鍒涘缓 {mappings_created} 涓槧灏? 鏇存柊 {mappings_updated} 涓槧灏?
                    )
                )
                
                total_mappings_created += mappings_created
                total_mappings_updated += mappings_updated
                total_success += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  鉂?澶勭悊澶辫触: {str(e)}')
                )
                total_error += 1

        # 鏄剧ず鎬荤粨
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'馃攳 骞茶繍琛屽畬鎴? {total_success} 涓ā鍨嬪彲澶勭悊, {total_error} 涓湁闂\n'
                    f'   棰勮鍒涘缓 {total_mappings_created} 涓槧灏刓n'
                    f'   瑕佸疄闄呮墽琛岋紝璇风Щ闄?--dry-run 鍙傛暟'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'馃帀 閲嶆柊鏄犲皠瀹屾垚: {total_success} 涓垚鍔? {total_error} 涓け璐n'
                    f'   鍒涘缓浜?{total_mappings_created} 涓柊鏄犲皠\n'
                    f'   鏇存柊浜?{total_mappings_updated} 涓幇鏈夋槧灏?
                )
            )
        
        if total_error > 0:
            self.stdout.write(
                self.style.WARNING('馃挕 鎻愮ず锛氭湁閮ㄥ垎妯″瀷澶勭悊澶辫触锛岃妫€鏌ュ搴旂殑MSFG閰嶇疆鏄惁姝ｇ‘')
            )

