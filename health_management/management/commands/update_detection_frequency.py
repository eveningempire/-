"""
更新检测频率配置的管理命令
"""

import json
import logging
from django.core.management.base import BaseCommand
from data_management.config import get_config, update_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '更新检测频率配置'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['high_frequency', 'medium_frequency', 'low_frequency', 'adaptive', 'disabled'],
            help='检测模式'
        )
        parser.add_argument(
            '--enabled',
            type=str,
            choices=['true', 'false'],
            help='是否启用检测频率控制'
        )
        parser.add_argument(
            '--high-interval',
            type=int,
            help='高频模式间隔（秒）'
        )
        parser.add_argument(
            '--medium-interval',
            type=int,
            help='中频模式间隔（秒）'
        )
        parser.add_argument(
            '--low-interval',
            type=int,
            help='低频模式间隔（秒）'
        )
        parser.add_argument(
            '--small-threshold',
            type=int,
            help='小数据集阈值'
        )
        parser.add_argument(
            '--medium-threshold',
            type=int,
            help='中数据集阈值'
        )
        parser.add_argument(
            '--large-threshold',
            type=int,
            help='大数据集阈值'
        )
        parser.add_argument(
            '--show',
            action='store_true',
            help='显示当前配置'
        )

    def handle(self, *args, **options):
        try:
            # 获取当前配置
            current_config = get_config('detection_frequency', {})
            
            if options['show']:
                self.stdout.write("当前检测频率配置:")
                self.stdout.write(json.dumps(current_config, indent=2, ensure_ascii=False))
                return

            # 更新配置
            updated = False
            
            if options['mode']:
                current_config['mode'] = options['mode']
                updated = True
                self.stdout.write(f"检测模式更新为: {options['mode']}")

            if options['enabled'] is not None:
                current_config['enabled'] = options['enabled'].lower() == 'true'
                updated = True
                self.stdout.write(f"启用状态更新为: {current_config['enabled']}")

            if options['high_interval']:
                if 'high_frequency' not in current_config:
                    current_config['high_frequency'] = {}
                current_config['high_frequency']['interval_seconds'] = options['high_interval']
                updated = True
                self.stdout.write(f"高频间隔更新为: {options['high_interval']}秒")

            if options['medium_interval']:
                if 'medium_frequency' not in current_config:
                    current_config['medium_frequency'] = {}
                current_config['medium_frequency']['interval_seconds'] = options['medium_interval']
                updated = True
                self.stdout.write(f"中频间隔更新为: {options['medium_interval']}秒")

            if options['low_interval']:
                if 'low_frequency' not in current_config:
                    current_config['low_frequency'] = {}
                current_config['low_frequency']['interval_seconds'] = options['low_interval']
                updated = True
                self.stdout.write(f"低频间隔更新为: {options['low_interval']}秒")

            if options['small_threshold']:
                if 'adaptive' not in current_config:
                    current_config['adaptive'] = {}
                current_config['adaptive']['small_dataset_threshold'] = options['small_threshold']
                updated = True
                self.stdout.write(f"小数据集阈值更新为: {options['small_threshold']}")

            if options['medium_threshold']:
                if 'adaptive' not in current_config:
                    current_config['adaptive'] = {}
                current_config['adaptive']['medium_dataset_threshold'] = options['medium_threshold']
                updated = True
                self.stdout.write(f"中数据集阈值更新为: {options['medium_threshold']}")

            if options['large_threshold']:
                if 'adaptive' not in current_config:
                    current_config['adaptive'] = {}
                current_config['adaptive']['large_dataset_threshold'] = options['large_threshold']
                updated = True
                self.stdout.write(f"大数据集阈值更新为: {options['large_threshold']}")

            if updated:
                # 保存配置
                update_config('detection_frequency', current_config)
                self.stdout.write(self.style.SUCCESS('配置更新成功'))
                
                # 显示更新后的配置
                self.stdout.write("\n更新后的配置:")
                self.stdout.write(json.dumps(current_config, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(self.style.WARNING('没有提供任何更新参数，使用 --show 查看当前配置'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'更新配置失败: {e}'))
            logger.error(f'更新检测频率配置失败: {e}', exc_info=True)
