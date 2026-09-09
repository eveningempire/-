#!/usr/bin/env python
"""
鍒濆鍖栨暟鎹簱缁熻淇℃伅
"""

import os
import sys
import django
from pathlib import Path

# 璁剧疆Django鐜
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import DatabaseStatistics, PHM
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_statistics():
    """鍒濆鍖栨暟鎹簱缁熻淇℃伅"""
    print("=== 鍒濆鍖栨暟鎹簱缁熻淇℃伅 ===")
    
    try:
        # 鍒锋柊鎵€鏈夌粺璁′俊鎭?
        DatabaseStatistics.refresh_all_statistics()
        
        # 鏄剧ず缁熻缁撴灉
        print("\n鍏ㄥ眬缁熻淇℃伅:")
        global_stats = DatabaseStatistics.get_statistics()
        for stat_type, stat_data in global_stats.items():
            print(f"  {stat_data['display_name']}: {stat_data['count']}")
        
        print("\n鎸塁MG缁熻淇℃伅:")
        cmgs = PHM.objects.all()
        for cmg in cmgs:
            print(f"\n  {cmg.name} ({cmg.cmg_id}):")
            cmg_stats = DatabaseStatistics.get_statistics(cmg)
            for stat_type, stat_data in cmg_stats.items():
                print(f"    {stat_data['display_name']}: {stat_data['count']}")
        
        print("\n鉁?缁熻淇℃伅鍒濆鍖栧畬鎴?)
        
    except Exception as e:
        print(f"鉂?鍒濆鍖栧け璐? {e}")

if __name__ == "__main__":
    init_statistics()

