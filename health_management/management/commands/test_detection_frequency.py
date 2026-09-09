"""
娴嬭瘯妫€娴嬮鐜囨帶鍒跺姛鑳界殑绠＄悊鍛戒护
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from data_management.models import PHM, PHMData
from health_management.detection_frequency_controller import detection_frequency_controller

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '娴嬭瘯妫€娴嬮鐜囨帶鍒跺姛鑳?

    def add_arguments(self, parser):
        parser.add_argument(
            '--cmg-id',
            type=str,
            help='PHM ID',
        )
        parser.add_argument(
            '--mode',
            type=str,
            choices=['high_frequency', 'medium_frequency', 'low_frequency', 'adaptive', 'disabled'],
            default='adaptive',
            help='妫€娴嬫ā寮?
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='娴嬭瘯鏁版嵁鐨勬椂闂磋寖鍥达紙灏忔椂锛?
        )

    def handle(self, *args, **options):
        cmg_id = options['cmg_id']
        mode = options['mode']
        hours = options['hours']

        if not cmg_id:
            self.stdout.write(self.style.ERROR('璇锋彁渚汣MG ID'))
            return

        try:
            # 鑾峰彇PHM
            cmg = PHM.objects.get(cmg_id=cmg_id)
            self.stdout.write(f"娴嬭瘯PHM: {cmg.name} ({cmg.cmg_id})")

            # 鑾峰彇娴嬭瘯鏁版嵁
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            records = PHMData.objects.filter(
                cmg=cmg,
                timestamp__range=(start_time, end_time)
            ).order_by('timestamp')

            total_records = records.count()
            self.stdout.write(f"鏁版嵁鑼冨洿: {start_time} 鍒?{end_time}")
            self.stdout.write(f"鎬昏褰曟暟: {total_records}")

            if total_records == 0:
                self.stdout.write(self.style.WARNING('娌℃湁鎵惧埌鏁版嵁璁板綍'))
                return

            # 涓存椂淇敼妫€娴嬫ā寮?
            original_config = detection_frequency_controller.config
            if mode != 'disabled':
                detection_frequency_controller.config.mode = detection_frequency_controller.DetectionMode(mode)
                detection_frequency_controller.config.enabled = True
            else:
                detection_frequency_controller.config.mode = detection_frequency_controller.DetectionMode.DISABLED
                detection_frequency_controller.config.enabled = False

            self.stdout.write(f"妫€娴嬫ā寮? {mode}")

            # 娴嬭瘯甯ч€夋嫨
            records_list = list(records)
            selected_indices = detection_frequency_controller.select_frames_for_detection(records_list)
            
            # 鑾峰彇妫€娴嬫憳瑕?
            summary = detection_frequency_controller.get_detection_summary(total_records, len(selected_indices))

            # 杈撳嚭缁撴灉
            self.stdout.write("\n" + "="*50)
            self.stdout.write("妫€娴嬮鐜囨帶鍒舵祴璇曠粨鏋?)
            self.stdout.write("="*50)
            self.stdout.write(f"鎬诲抚鏁? {summary['total_frames']}")
            self.stdout.write(f"閫変腑甯ф暟: {summary['selected_frames']}")
            self.stdout.write(f"妫€娴嬫瘮渚? {summary['detection_ratio']*100:.1f}%")
            self.stdout.write(f"鏃堕棿鑺傜渷: {summary['estimated_time_saving']}")
            self.stdout.write(f"妫€娴嬫ā寮? {summary['mode']}")
            self.stdout.write(f"鍚敤鐘舵€? {summary['enabled']}")

            # 鏄剧ず閫変腑鐨勫抚淇℃伅
            if selected_indices:
                self.stdout.write("\n閫変腑鐨勫抚:")
                for i, idx in enumerate(selected_indices[:10]):  # 鍙樉绀哄墠10涓?
                    record = records_list[idx]
                    self.stdout.write(f"  {i+1}. 绱㈠紩{idx}: {record.timestamp}")

                if len(selected_indices) > 10:
                    self.stdout.write(f"  ... 杩樻湁 {len(selected_indices) - 10} 甯?)

            # 鎭㈠鍘熷閰嶇疆
            detection_frequency_controller.config = original_config

            self.stdout.write(self.style.SUCCESS('\n娴嬭瘯瀹屾垚'))

        except PHM.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'PHM {cmg_id} 涓嶅瓨鍦?))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'娴嬭瘯澶辫触: {e}'))
            logger.error(f'娴嬭瘯妫€娴嬮鐜囨帶鍒跺け璐? {e}', exc_info=True)

