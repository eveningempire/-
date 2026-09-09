"""
Django绠＄悊鍛戒护锛氬垱寤烘祴璇旾MS妯″瀷
鐢ㄤ簬蹇€熺敓鎴愪竴涓畝鍗曠殑IMS妯″瀷浠ユ祴璇曟娴嬪姛鑳?
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import numpy as np

from data_management.models import PHM, PHMData, PHMModel
from health_management.models import IMSModel
from health_management.algorithms.IMS.ims_algorithm import create_ims_model


class Command(BaseCommand):
    help = '鍒涘缓娴嬭瘯IMS妯″瀷'

    def add_arguments(self, parser):
        parser.add_argument('--cmg-model-id', type=int, help='PHM妯″瀷ID')
        parser.add_argument('--cmg-id', type=str, help='PHM ID锛堝鏋滄寚瀹氾紝灏嗕娇鐢ㄨPHM鐨勬暟鎹級')
        parser.add_argument('--days', type=int, default=7, help='浣跨敤鏈€杩戝灏戝ぉ鐨勬暟鎹繘琛岃缁冿紙榛樿7澶╋級')
        parser.add_argument('--min-samples', type=int, default=100, help='鏈€灏戦渶瑕佺殑鏍锋湰鏁帮紙榛樿100锛?)

    def handle(self, *args, **options):
        cmg_model_id = options.get('cmg_model_id')
        cmg_id = options.get('cmg_id')
        days = options['days']
        min_samples = options['min_samples']

        try:
            # 纭畾瑕佷娇鐢ㄧ殑PHM鍜孋MGModel
            if cmg_id:
                cmg = PHM.objects.get(cmg_id=cmg_id)
                cmg_model = cmg.cmg_model
                self.stdout.write(f"浣跨敤鎸囧畾鐨凜MG: {cmg_id}")
            elif cmg_model_id:
                cmg_model = PHMModel.objects.get(id=cmg_model_id)
                # 鎵惧埌璇ユā鍨嬩笅鐨勭涓€涓狢MG
                cmg = PHM.objects.filter(cmg_model=cmg_model).first()
                if not cmg:
                    self.stdout.write(self.style.ERROR(f"PHM妯″瀷 {cmg_model_id} 涓嬫病鏈塁MG"))
                    return
                self.stdout.write(f"浣跨敤PHM妯″瀷 {cmg_model.model_name} 涓嬬殑PHM: {cmg.cmg_id}")
            else:
                # 浣跨敤绗竴涓湁鏁版嵁鐨凜MG
                cmg = PHM.objects.filter(data__isnull=False).first()
                if not cmg:
                    self.stdout.write(self.style.ERROR("娌℃湁鎵惧埌鏈夋暟鎹殑PHM"))
                    return
                cmg_model = cmg.cmg_model
                self.stdout.write(f"鑷姩閫夋嫨PHM: {cmg.cmg_id}")

            # 鑾峰彇璁粌鏁版嵁
            end_time = timezone.now()
            start_time = end_time - timedelta(days=days)
            
            training_data = PHMData.objects.filter(
                cmg=cmg,
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('timestamp')

            if training_data.count() < min_samples:
                self.stdout.write(self.style.ERROR(
                    f"璁粌鏁版嵁涓嶈冻锛氶渶瑕佽嚦灏憑min_samples}鏉¤褰曪紝褰撳墠浠呮湁{training_data.count()}鏉?
                ))
                return

            self.stdout.write(f"鎵惧埌 {training_data.count()} 鏉¤缁冩暟鎹?)

            # 鍒嗘瀽鍙敤鍙傛暟
            all_params = set()
            for data in training_data[:1000]:  # 鍙栨牱鍒嗘瀽鍙傛暟
                if isinstance(data.data, dict):
                    all_params.update(data.data.keys())

            # 杩囨护鏁板€煎瀷鍙傛暟
            numeric_params = self._filter_numeric_params(training_data, list(all_params))
            
            if len(numeric_params) < 2:
                self.stdout.write(self.style.ERROR(
                    f"鏈夋晥鍙傛暟涓嶈冻锛氶渶瑕佽嚦灏?涓暟鍊煎瀷鍙傛暟锛屽綋鍓嶄粎鏈墈len(numeric_params)}涓?
                ))
                return

            self.stdout.write(f"閫夋嫨鍙傛暟: {numeric_params}")

            # 鍑嗗璁粌鏁版嵁鐭╅樀
            data_matrix = []
            for data in training_data:
                row = [data.data.get(param, float('nan')) for param in numeric_params]
                data_matrix.append(row)

            data_matrix = np.array(data_matrix, dtype=np.float32)

            # 绉婚櫎鍖呭惈杩囧NaN鐨勮
            valid_threshold = len(numeric_params) * 0.7
            valid_mask = np.sum(~np.isnan(data_matrix), axis=1) >= valid_threshold
            clean_data = data_matrix[valid_mask]

            if len(clean_data) < min_samples:
                self.stdout.write(self.style.ERROR(
                    f"娓呯悊鍚庤缁冩暟鎹笉瓒筹細浠呮湁{len(clean_data)}鏉℃湁鏁堣褰?
                ))
                return

            self.stdout.write(f"鏈夋晥璁粌鏁版嵁: {len(clean_data)} 鏉?)

            # 鍒涘缓鍜岃缁冩ā鍨?
            model_config = {
                "contamination": 0.1,       # 閫傚綋鎻愰珮寮傚父姣斾緥浠ヤ究娴嬭瘯
                "n_estimators": 100,        # 瓒冲鐨勬爲鏁伴噺
                "max_samples": "auto",
                "max_features": 0.8,
                "bootstrap": False,
                "random_state": 42,
                "scaler_type": "standard"
            }

            self.stdout.write("寮€濮嬭缁僆MS妯″瀷...")
            model = create_ims_model(numeric_params, model_config)
            model.fit(clean_data, save=False)

            # 鍋滅敤鐜版湁鐨勬縺娲绘ā鍨?
            IMSModel.objects.filter(cmg_model=cmg_model, is_active=True).update(is_active=False)
            self.stdout.write("宸插仠鐢ㄧ幇鏈夌殑婵€娲绘ā鍨?)

            # 鍒涘缓鏁版嵁搴撹褰?
            model_name = f"Test_IMS_{cmg_model.model_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            ims_model = IMSModel.objects.create(
                cmg_model=cmg_model,
                name=model_name,
                parameters=numeric_params,
                model_config=model_config,
                model_data=model.to_json(),
                threshold=float(model.threshold_value) if model.threshold_value else 0.5,
                is_active=True
            )

            self.stdout.write(self.style.SUCCESS(
                f"娴嬭瘯IMS妯″瀷鍒涘缓鎴愬姛锛乗n"
                f"妯″瀷ID: {ims_model.id}\n"
                f"妯″瀷鍚嶇О: {model_name}\n"
                f"鍙傛暟鏁伴噺: {len(numeric_params)}\n"
                f"璁粌鏍锋湰: {len(clean_data)}\n"
                f"寮傚父闃堝€? {model.threshold_value:.4f}\n"
                f"PHM妯″瀷: {cmg_model.model_name}"
            ))

            # 娓呯┖IMS鏈嶅姟缂撳瓨
            from health_management.ims_service import ims_service
            ims_service.clear_cache()
            self.stdout.write("宸叉竻绌篒MS鏈嶅姟缂撳瓨")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"鍒涘缓娴嬭瘯妯″瀷澶辫触: {e}"))
            import traceback
            traceback.print_exc()

    def _filter_numeric_params(self, training_data, available_params):
        """杩囨护鏁板€煎瀷鍙傛暟"""
        numeric_params = []
        
        for param in available_params:
            values = []
            for data in training_data[:500]:  # 鍙栨牱妫€鏌?
                if isinstance(data.data, dict) and param in data.data:
                    val = data.data[param]
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        continue
            
            if len(values) > 10:  # 鑷冲皯鏈?0涓湁鏁堟暟鍊?
                values = np.array(values)
                # 妫€鏌ユ柟宸?
                if np.var(values) > 1e-6:
                    numeric_params.append(param)
        
        return numeric_params[:10]  # 鏈€澶氶€夋嫨10涓弬鏁颁互閬垮厤缁村害杩囬珮

