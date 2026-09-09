"""
绠＄悊鍛戒护锛氬悓姝SFG閮ㄤ欢瀹氫箟
纭繚鎵€鏈塁MG妯″瀷鐨勯儴浠跺畾涔夐兘鏉ヨ嚜浜庢縺娲荤殑MSFG閰嶇疆
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from data_management.models import PHMModel
from msfg_analysis.algorithms.msfg.component_integration import (
    sync_msfg_component_definitions,
    ensure_msfg_component_mappings,
    get_active_msfg_for_cmg_model
)


class Command(BaseCommand):
    help = '鍚屾MSFG閮ㄤ欢瀹氫箟鍒拌鍒欐娴嬫ā鍧楋紝纭繚閮ㄤ欢鏉ユ簮缁熶竴'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cmg-model-id',
            type=int,
            help='鎸囧畾瑕佸悓姝ョ殑PHM妯″瀷ID锛岀暀绌哄垯鍚屾鎵€鏈夋ā鍨?
        )
        parser.add_argument(
            '--ensure-mappings',
            action='store_true',
            help='纭繚MSFG閰嶇疆鏈夊畬鏁寸殑娴嬭瘯鐐?閮ㄤ欢鏄犲皠'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='鍙樉绀哄皢瑕佹墽琛岀殑鎿嶄綔锛屼笉瀹為檯淇敼鏁版嵁'
        )

    def handle(self, *args, **options):
        cmg_model_id = options.get('cmg_model_id')
        ensure_mappings = options.get('ensure_mappings', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('馃攳 骞茶繍琛屾ā寮忥細鍙樉绀烘搷浣滐紝涓嶄慨鏀规暟鎹?)
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

        for cmg_model in cmg_models:
            self.stdout.write(f'\n馃搳 澶勭悊PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})')
            
            try:
                # 妫€鏌ユ槸鍚︽湁婵€娲荤殑MSFG閰嶇疆
                active_msfg = get_active_msfg_for_cmg_model(cmg_model)
                if not active_msfg:
                    self.stdout.write(
                        self.style.WARNING(f'  鈿狅笍  娌℃湁婵€娲荤殑MSFG閰嶇疆锛岃烦杩?)
                    )
                    continue

                self.stdout.write(f'  鉁?鎵惧埌婵€娲荤殑MSFG閰嶇疆: {active_msfg.name}')

                # 纭繚娴嬭瘯鐐?閮ㄤ欢鏄犲皠
                if ensure_mappings:
                    if not dry_run:
                        ensure_msfg_component_mappings(active_msfg)
                    self.stdout.write(f'  馃敡 {"妯℃嫙" if dry_run else ""}鏇存柊娴嬭瘯鐐?閮ㄤ欢鏄犲皠')

                # 鍚屾閮ㄤ欢瀹氫箟
                if not dry_run:
                    sync_result = sync_msfg_component_definitions(cmg_model)
                    
                    if sync_result['success']:
                        details = sync_result['details']
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  鉁?鍚屾鎴愬姛: {details["components_count"]} 涓儴浠?'
                                f'(鏂板缓: {details["created_count"]}, 鏇存柊: {details["updated_count"]})'
                            )
                        )
                        self.stdout.write(f'     閮ㄤ欢鍒楄〃: {", ".join(details["components"])}')
                        total_success += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  鉂?鍚屾澶辫触: {sync_result["message"]}')
                        )
                        total_error += 1
                else:
                    # 骞茶繍琛屾ā寮忥細鍙樉绀哄皢瑕佸悓姝ョ殑閮ㄤ欢
                    from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg
                    components = extract_components_from_msfg(active_msfg)
                    
                    self.stdout.write(
                        f'  馃攳 灏嗚鍚屾 {len(components)} 涓儴浠? {", ".join(components)}'
                    )
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
                self.style.SUCCESS(f'馃攳 骞茶繍琛屽畬鎴? {total_success} 涓ā鍨嬪彲鍚屾, {total_error} 涓湁闂')
            )
            self.stdout.write('瑕佸疄闄呮墽琛屽悓姝ワ紝璇风Щ闄?--dry-run 鍙傛暟')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'馃帀 鍚屾瀹屾垚: {total_success} 涓垚鍔? {total_error} 涓け璐?)
            )
        
        if total_error > 0:
            self.stdout.write(
                self.style.WARNING('馃挕 鎻愮ず锛氭湁閮ㄥ垎妯″瀷鍚屾澶辫触锛岃妫€鏌ュ搴旂殑MSFG閰嶇疆鏄惁姝ｇ‘')
            )

