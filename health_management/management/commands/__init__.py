"""
鏇存柊妫€娴嬮鐜囬厤缃殑绠＄悊鍛戒护
"""

import json
import logging
from django.core.management.base import BaseCommand
from data_management.config import get_config, update_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '鏇存柊妫€娴嬮鐜囬厤缃?

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['high_frequency', 'medium_frequency', 'low_frequency', 'adaptive', 'disabled'],
            help='妫€娴嬫ā寮?
        )
        parser.add_argument(
            '--enabled',
            type=str,
            choices=['true', 'false'],
            help='鏄惁鍚敤妫€娴嬮鐜囨帶鍒?
        )
        parser.add_argument(
            '--high-interval',
            type=int,
            help='楂橀妯″紡闂撮殧锛堢锛?
        )
        parser.add_argument(
            '--medium-interval',
            type=int,
            help='涓妯″紡闂撮殧锛堢锛?
        )
        parser.add_argument(
            '--low-interval',
            type=int,
            help='浣庨妯″紡闂撮殧锛堢锛?
        )
        parser.add_argument(
            '--small-threshold',
            type=int,
            help='灏忔暟鎹泦闃堝€?
        )
        parser.add_argument(
            '--medium-threshold',
            type=int,
            help='涓暟鎹泦闃堝€?
        )
        parser.add_argument(
            '--large-threshold',
            type=int,
            help='澶ф暟鎹泦闃堝€?
        )
        parser.add_argument(
            '--show',
            action='store_true',
            help='鏄剧ず褰撳墠閰嶇疆'
        )

    def handle(self, *args, **options):
        try:
            # 鑾峰彇褰撳墠閰嶇疆
            current_config = get_config('detection_frequency', {})
            
            if options['show']:
                self.stdout.write("褰撳墠妫€娴嬮鐜囬厤缃?")
                self.stdout.write(json.dumps(current_config, indent=2, ensure_ascii=False))
                return

            # 鏇存柊閰嶇疆
            updated = False
            
            if options['mode']:
                current_config['mode'] = options['mode']
                updated = True
                self.stdout.write(f"妫€娴嬫ā寮忔洿鏂颁负: {options['mode']}")

            if options['enabled'] is not None:
                current_config['enabled'] = options['enabled'].lower() == 'true'
                updated = True
                self.stdout.write(f"鍚敤鐘舵€佹洿鏂颁负: {current_config['enabled']}")

            if options['high_interval']:
                if 'high_frequency' not in current_config:
                    current_config['high_frequency'] = {}
                current_config['high_frequency']['interval_seconds'] = options['high_interval']
                updated = True
                self.stdout.write(f"楂橀闂撮殧鏇存柊涓? {options['high_interval']}绉?)

            if options['medium_interval']:
                if 'medium_frequency' not in current_config:
                    current_config['medium_frequency'] = {}
                current_config['medium_frequency']['interval_seconds'] = options['medium_interval']
                updated = True
                self.stdout.write(f"涓闂撮殧鏇存柊涓? {options['medium_interval']}绉?)

            if options['low_interval']:
                if 'low_frequency' not in current_config:
                    current_config['low_frequency'] = {}
                current_config['low_frequency']['interval_seconds'] = options['low_interval']
                updated = True
                self.stdout.write(f"浣庨闂撮殧鏇存柊涓? {options['low_interval']}绉?)

            if options['small_threshold']:
                if 'adaptive' not in current_config:
                    current_config['adaptive'] = {}
                current_config['adaptive']['small_dataset_threshold'] = options['small_threshold']
                updated = True
                self.stdout.write(f"灏忔暟鎹泦闃堝€兼洿鏂颁负: {options['small_threshold']}")

            if options['medium_threshold']:
                if 'adaptive' not in current_config:
                    current_config['adaptive'] = {}
                current_config['adaptive']['medium_dataset_threshold'] = options['medium_threshold']
                updated = True
                self.stdout.write(f"涓暟鎹泦闃堝€兼洿鏂颁负: {options['medium_threshold']}")

            if options['large_threshold']:
                if 'adaptive' not in current_config:
                    current_config['adaptive'] = {}
                current_config['adaptive']['large_dataset_threshold'] = options['large_threshold']
                updated = True
                self.stdout.write(f"澶ф暟鎹泦闃堝€兼洿鏂颁负: {options['large_threshold']}")

            if updated:
                # 淇濆瓨閰嶇疆
                update_config('detection_frequency', current_config)
                self.stdout.write(self.style.SUCCESS('閰嶇疆鏇存柊鎴愬姛'))
                
                # 鏄剧ず鏇存柊鍚庣殑閰嶇疆
                self.stdout.write("\n鏇存柊鍚庣殑閰嶇疆:")
                self.stdout.write(json.dumps(current_config, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(self.style.WARNING('娌℃湁鎻愪緵浠讳綍鏇存柊鍙傛暟锛屼娇鐢?--show 鏌ョ湅褰撳墠閰嶇疆'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'鏇存柊閰嶇疆澶辫触: {e}'))
            logger.error(f'鏇存柊妫€娴嬮鐜囬厤缃け璐? {e}', exc_info=True)

