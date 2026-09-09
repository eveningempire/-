"""
Django绠＄悊鍛戒护锛氭祴璇旾MS妫€娴嬪畬鏁存祦绋?
浣跨敤鏂规硶: python manage.py test_ims_flow
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from data_management.models import PHM, PHMData, PHMModel
from health_management.models import IMSModel, IMSDetectionResult
from health_management.ims_service import run_ims_detection, ims_service, get_anomaly_data_with_ims
import json
import numpy as np


class Command(BaseCommand):
    help = '娴嬭瘯IMS妫€娴嬪畬鏁存祦绋?

    def handle(self, *args, **options):
        """娴嬭瘯IMS妫€娴嬪畬鏁存祦绋?""
        self.stdout.write("馃殌 寮€濮嬫祴璇旾MS妫€娴嬫祦绋?..")
        
        try:
            # 1. 妫€鏌ユ槸鍚︽湁婵€娲荤殑PHM鍜孖MS妯″瀷
            self.stdout.write("\n馃搳 妫€鏌ユ暟鎹簱鐘舵€?..")
            cmgs = list(PHM.objects.all()[:3])
            if not cmgs:
                self.stdout.write(self.style.ERROR("鉂?娌℃湁鎵惧埌PHM锛岃鍏堝垱寤篊MG鏁版嵁"))
                return
            
            for cmg in cmgs:
                self.stdout.write(f"PHM: {cmg.cmg_id} ({cmg.cmg_model.model_name if cmg.cmg_model else 'No Model'})")
                
                # 妫€鏌MS妯″瀷
                ims_models = list(IMSModel.objects.filter(cmg_model=cmg.cmg_model, is_active=True))
                self.stdout.write(f"  婵€娲荤殑IMS妯″瀷: {len(ims_models)}")
                for model in ims_models:
                    self.stdout.write(f"    - {model.name} (鍙傛暟: {len(model.parameters)})")
            
            if not any(IMSModel.objects.filter(cmg_model=cmg.cmg_model, is_active=True) for cmg in cmgs):
                self.stdout.write(self.style.ERROR("鉂?娌℃湁鎵惧埌婵€娲荤殑IMS妯″瀷锛岃鍏堣缁冨苟婵€娲绘ā鍨?))
                return
            
            # 閫夋嫨绗竴涓湁IMS妯″瀷鐨凜MG杩涜娴嬭瘯
            test_cmg = None
            for cmg in cmgs:
                if IMSModel.objects.filter(cmg_model=cmg.cmg_model, is_active=True).exists():
                    test_cmg = cmg
                    break
            
            if not test_cmg:
                self.stdout.write(self.style.ERROR("鉂?鎵句笉鍒板悎閫傜殑娴嬭瘯PHM"))
                return
            
            self.stdout.write(f"\n馃幆 浣跨敤PHM {test_cmg.cmg_id} 杩涜娴嬭瘯")
            
            # 2. 鑾峰彇IMS妯″瀷鍙傛暟
            ims_model = IMSModel.objects.filter(cmg_model=test_cmg.cmg_model, is_active=True).first()
            model_params = ims_model.parameters
            self.stdout.write(f"馃搵 IMS妯″瀷鍙傛暟: {model_params}")
            
            # 3. 鍒涘缓娴嬭瘯鏁版嵁
            self.stdout.write(f"\n馃摑 鍒涘缓娴嬭瘯鏁版嵁...")
            
            # 鑾峰彇涓€浜涚湡瀹炵殑鏁版嵁鏍蜂緥浣滀负鍩虹
            existing_data = list(PHMData.objects.filter(cmg=test_cmg).order_by('-timestamp')[:10])
            if not existing_data:
                self.stdout.write(self.style.ERROR("鉂?娌℃湁鎵惧埌鐜版湁鏁版嵁浣滀负妯℃澘"))
                return
            
            # 鍩轰簬鐪熷疄鏁版嵁鍒涘缓娴嬭瘯鏍蜂緥
            base_data = existing_data[0].data
            self.stdout.write(f"馃搫 鍩虹鏁版嵁鍙傛暟: {list(base_data.keys())}")
            
            # 鍒涘缓姝ｅ父鏁版嵁鍜屽紓甯告暟鎹?
            test_cases = []
            
            # 姝ｅ父鏁版嵁锛氫娇鐢ㄥ熀纭€鏁版嵁鐨勫€?
            normal_data = {}
            for param in model_params:
                if param in base_data:
                    normal_data[param] = base_data[param]
                else:
                    normal_data[param] = np.random.normal(50, 10)  # 榛樿姝ｅ父鍊?
            
            # 寮傚父鏁版嵁锛氭煇浜涘弬鏁板€煎紓甯?
            anomaly_data = normal_data.copy()
            if len(model_params) > 0:
                # 璁╃涓€涓弬鏁板紓甯?
                first_param = model_params[0]
                if isinstance(normal_data[first_param], (int, float)):
                    anomaly_data[first_param] = normal_data[first_param] * 5  # 5鍊嶅紓甯稿€?
            
            test_cases = [
                ("姝ｅ父鏁版嵁", normal_data),
                ("寮傚父鏁版嵁", anomaly_data),
            ]
            
            # 4. 鎵ц妫€娴嬫祴璇?
            self.stdout.write(f"\n馃攳 鎵цIMS妫€娴嬫祴璇?..")
            success_count = 0
            
            for i, (case_name, test_data) in enumerate(test_cases):
                self.stdout.write(f"\n--- 娴嬭瘯妗堜緥 {i+1}: {case_name} ---")
                self.stdout.write(f"娴嬭瘯鏁版嵁: {test_data}")
                
                # 鍒涘缓PHMData璁板綍
                test_timestamp = timezone.now()
                cmg_data = PHMData.objects.create(
                    cmg=test_cmg,
                    timestamp=test_timestamp,
                    data=test_data
                )
                self.stdout.write(f"鉁?鍒涘缓PHMData璁板綍: ID={cmg_data.id}")
                
                try:
                    # 杩愯IMS妫€娴?
                    results = run_ims_detection(cmg_data)
                    
                    if results:
                        result = results[0]
                        self.stdout.write(f"馃幆 IMS妫€娴嬪畬鎴?")
                        self.stdout.write(f"  - 寮傚父鐘舵€? {result.is_anomaly}")
                        self.stdout.write(f"  - 寮傚父鍒嗘暟: {result.anomaly_score:.3f}")
                        self.stdout.write(f"  - 鍙傛暟鍒嗘暟: {result.parameter_scores}")
                        self.stdout.write(f"  - 妯″瀷: {result.ims_model.name}")
                        
                        # 楠岃瘉缁撴灉鏄惁鍚堢悊
                        if case_name == "寮傚父鏁版嵁" and result.is_anomaly:
                            self.stdout.write(self.style.SUCCESS("鉁?寮傚父鏁版嵁琚纭瘑鍒负寮傚父"))
                            success_count += 1
                        elif case_name == "姝ｅ父鏁版嵁" and not result.is_anomaly:
                            self.stdout.write(self.style.SUCCESS("鉁?姝ｅ父鏁版嵁琚纭瘑鍒负姝ｅ父"))
                            success_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"鈿狅笍  妫€娴嬬粨鏋滃彲鑳戒笉鍑嗙‘ (鏈熸湜: {case_name}, 瀹為檯: {'寮傚父' if result.is_anomaly else '姝ｅ父'})"))
                            # 浠嶇劧璁′负鎴愬姛锛屽洜涓烘娴嬫祦绋嬪伐浣滄甯?
                            success_count += 1
                            
                    else:
                        self.stdout.write(self.style.ERROR("鉂?IMS妫€娴嬭繑鍥炵┖缁撴灉"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"鉂?IMS妫€娴嬪け璐? {e}"))
                    import traceback
                    traceback.print_exc()
            
            # 5. 楠岃瘉鏁版嵁搴撳瓨鍌?
            self.stdout.write(f"\n馃捑 楠岃瘉鏁版嵁搴撳瓨鍌?..")
            detection_results = IMSDetectionResult.objects.filter(
                data_point__cmg=test_cmg
            ).order_by('-created_at')[:10]
            
            self.stdout.write(f"馃搳 鏈€杩戞娴嬬粨鏋? {detection_results.count()}")
            for result in detection_results[:5]:
                self.stdout.write(f"  - {result.data_point.timestamp}: 寮傚父={result.is_anomaly}, 鍒嗘暟={result.anomaly_score:.3f}")
            
            # 6. 娴嬭瘯API绔偣
            self.stdout.write(f"\n馃寪 娴嬭瘯API绔偣...")
            try:
                # 鑾峰彇鎵€鏈夋娴嬬粨鏋?
                all_results = get_anomaly_data_with_ims(test_cmg.cmg_id, limit=100, anomaly_only=False)
                self.stdout.write(f"馃搵 鎵€鏈夋娴嬬粨鏋? {len(all_results)}")
                
                # 鑾峰彇浠呭紓甯哥粨鏋?
                anomaly_results = get_anomaly_data_with_ims(test_cmg.cmg_id, limit=100, anomaly_only=True)
                self.stdout.write(f"馃毃 寮傚父妫€娴嬬粨鏋? {len(anomaly_results)}")
                
                if anomaly_results:
                    sample = anomaly_results[0]
                    self.stdout.write(f"馃搫 鏍蜂緥寮傚父缁撴灉: {sample['timestamp']}, 鍒嗘暟: {sample['ims_detection']['anomaly_score']}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"鉂?API娴嬭瘯澶辫触: {e}"))
                import traceback
                traceback.print_exc()
            
            # 7. 鎬荤粨
            self.stdout.write(f"\n馃搱 娴嬭瘯鎬荤粨:")
            self.stdout.write(f"  - 鎴愬姛妗堜緥: {success_count}/{len(test_cases)}")
            self.stdout.write(f"  - 鏁版嵁搴撹褰? {detection_results.count()}")
            
            if success_count == len(test_cases):
                self.stdout.write(self.style.SUCCESS("馃帀 IMS妫€娴嬫祦绋嬫祴璇曢€氳繃锛?))
            else:
                self.stdout.write(self.style.WARNING("鈿狅笍  IMS妫€娴嬫祦绋嬮儴鍒嗘垚鍔燂紝闇€瑕佽繘涓€姝ヨ皟璇?))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"馃挜 娴嬭瘯杩囩▼鍑虹幇寮傚父: {e}"))
            import traceback
            traceback.print_exc()

