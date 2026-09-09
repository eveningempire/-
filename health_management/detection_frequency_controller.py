"""
妫€娴嬮鐜囨帶鍒舵湇鍔?
鐢ㄤ簬浼樺寲澶ч噺鏁版嵁瀵煎叆鏃剁殑妫€娴嬫€ц兘锛岄€氳繃鎺у埗妫€娴嬮鐜囧噺灏戞娴嬮噺
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from django.utils import timezone
from data_management.models import PHMData
from data_management.config import get_config

logger = logging.getLogger(__name__)


class DetectionMode(Enum):
    """妫€娴嬫ā寮忔灇涓?""
    HIGH_FREQUENCY = "high_frequency"      # 楂橀妯″紡锛氭瘡绉掓娴?
    MEDIUM_FREQUENCY = "medium_frequency"  # 涓妯″紡锛?0绉掓娴?
    LOW_FREQUENCY = "low_frequency"        # 浣庨妯″紡锛?鍒嗛挓妫€娴?
    ADAPTIVE = "adaptive"                  # 鑷€傚簲妯″紡锛氭牴鎹暟鎹噺璋冩暣
    DISABLED = "disabled"                  # 绂佺敤棰戠巼鎺у埗锛堥€愬抚妫€娴嬶級


@dataclass
class DetectionConfig:
    """妫€娴嬮厤缃?""
    mode: DetectionMode
    interval_seconds: int
    frames_per_interval: int
    enabled: bool = True


class DetectionFrequencyController:
    """妫€娴嬮鐜囨帶鍒跺櫒"""
    
    def __init__(self):
        self.config = self._load_config()
        logger.info(f"妫€娴嬮鐜囨帶鍒跺櫒鍒濆鍖栧畬鎴愶紝妯″紡: {self.config.mode.value}")
    
    def _load_config(self) -> DetectionConfig:
        """鍔犺浇妫€娴嬮鐜囬厤缃?""
        try:
            freq_config = get_config('detection_frequency', {})
            enabled = freq_config.get('enabled', True)
            
            if not enabled:
                return DetectionConfig(
                    mode=DetectionMode.DISABLED,
                    interval_seconds=0,
                    frames_per_interval=1,
                    enabled=False
                )
            
            mode_name = freq_config.get('mode', 'adaptive')
            mode = DetectionMode(mode_name)
            
            if mode == DetectionMode.HIGH_FREQUENCY:
                config = freq_config.get('high_frequency', {})
                interval = config.get('interval_seconds', 1)
                frames = config.get('frames_per_interval', 1)
            elif mode == DetectionMode.MEDIUM_FREQUENCY:
                config = freq_config.get('medium_frequency', {})
                interval = config.get('interval_seconds', 30)
                frames = config.get('frames_per_interval', 1)
            elif mode == DetectionMode.LOW_FREQUENCY:
                config = freq_config.get('low_frequency', {})
                interval = config.get('interval_seconds', 60)
                frames = config.get('frames_per_interval', 1)
            elif mode == DetectionMode.ADAPTIVE:
                # 鑷€傚簲妯″紡闇€瑕佹牴鎹暟鎹噺鍔ㄦ€佺‘瀹?
                interval = 1  # 榛樿鍊硷紝浼氳鍔ㄦ€佽皟鏁?
                frames = 1
            else:
                # 绂佺敤妯″紡
                return DetectionConfig(
                    mode=DetectionMode.DISABLED,
                    interval_seconds=0,
                    frames_per_interval=1,
                    enabled=False
                )
            
            return DetectionConfig(
                mode=mode,
                interval_seconds=interval,
                frames_per_interval=frames,
                enabled=True
            )
            
        except Exception as e:
            logger.error(f"鍔犺浇妫€娴嬮鐜囬厤缃け璐? {e}")
            # 鍥為€€鍒扮鐢ㄦā寮?
            return DetectionConfig(
                mode=DetectionMode.DISABLED,
                interval_seconds=0,
                frames_per_interval=1,
                enabled=False
            )
    
    def get_adaptive_interval(self, total_frames: int) -> int:
        """鏍规嵁鏁版嵁閲忚幏鍙栬嚜閫傚簲妫€娴嬮棿闅?""
        try:
            freq_config = get_config('detection_frequency', {})
            adaptive_config = freq_config.get('adaptive', {})
            
            small_threshold = adaptive_config.get('small_dataset_threshold', 1000)
            medium_threshold = adaptive_config.get('medium_dataset_threshold', 5000)
            large_threshold = adaptive_config.get('large_dataset_threshold', 10000)
            
            small_interval = adaptive_config.get('small_dataset_interval', 1)
            medium_interval = adaptive_config.get('medium_dataset_interval', 30)
            large_interval = adaptive_config.get('large_dataset_interval', 60)
            
            if total_frames <= small_threshold:
                return small_interval
            elif total_frames <= medium_threshold:
                return medium_interval
            elif total_frames <= large_threshold:
                return large_interval
            else:
                return large_interval
                
        except Exception as e:
            logger.error(f"鑾峰彇鑷€傚簲闂撮殧澶辫触: {e}")
            return 30  # 榛樿30绉?
    
    def select_frames_for_detection(self, records: List[PHMData]) -> List[int]:
        """
        鏍规嵁妫€娴嬮鐜囬厤缃€夋嫨闇€瑕佹娴嬬殑甯х储寮?
        
        Args:
            records: 鎵€鏈夋暟鎹褰曞垪琛?
            
        Returns:
            闇€瑕佹娴嬬殑甯х储寮曞垪琛?
        """
        # 姣忔浣跨敤鏃堕噸鏂板姞杞介厤缃紝纭繚鑾峰彇鏈€鏂扮殑閰嶇疆
        current_config = self._load_config()
        
        if not current_config.enabled or current_config.mode == DetectionMode.DISABLED:
            # 绂佺敤棰戠巼鎺у埗锛屾娴嬫墍鏈夊抚
            return list(range(len(records)))
        
        if not records:
            return []
        
        total_frames = len(records)
        logger.info(f"寮€濮嬪抚閫夋嫨锛屾€诲抚鏁? {total_frames}")
        
        # 鑾峰彇妫€娴嬮棿闅?
        if current_config.mode == DetectionMode.ADAPTIVE:
            interval_seconds = self.get_adaptive_interval(total_frames)
            logger.info(f"鑷€傚簲妯″紡锛屾娴嬮棿闅? {interval_seconds}绉?)
        else:
            interval_seconds = current_config.interval_seconds
            logger.info(f"鍥哄畾妯″紡 {current_config.mode.value}锛屾娴嬮棿闅? {interval_seconds}绉?)
        
        if interval_seconds <= 0:
            # 闂撮殧涓?鎴栬礋鏁帮紝妫€娴嬫墍鏈夊抚
            return list(range(len(records)))
        
        # 浣跨敤鏂扮殑甯ч€夋嫨閫昏緫锛氭寜绉掑垎缁勶紝姣忛棿闅旂閫夋嫨涓€甯?
        selected_indices = self._select_frames_by_second_interval(records, interval_seconds)
        
        logger.info(f"甯ч€夋嫨瀹屾垚锛屾€诲抚鏁? {total_frames}锛岄€夋嫨甯ф暟: {len(selected_indices)}锛?
                   f"妫€娴嬫瘮渚? {len(selected_indices)/total_frames*100:.1f}%")
        
        return selected_indices
    
    def _select_frames_by_second_interval(self, records: List[PHMData], interval_seconds: int) -> List[int]:
        """
        鎸夌闂撮殧鍧囧寑閫夋嫨甯э細浠庢瘡闂撮殧绉掔殑鏁版嵁涓潎鍖€閫夋嫨涓€甯?
        
        Args:
            records: 鎵€鏈夋暟鎹褰曞垪琛?
            interval_seconds: 妫€娴嬮棿闅旓紙绉掞級
            
        Returns:
            閫夋嫨鐨勫抚绱㈠紩鍒楄〃
        """
        if not records:
            return []
        
        total_frames = len(records)
        
        # 璁＄畻鎬绘椂闂磋寖鍥?
        start_time = records[0].timestamp
        end_time = records[-1].timestamp
        total_seconds = (end_time - start_time).total_seconds()
        
        if total_seconds <= 0:
            # 鏃堕棿鑼冨洿澶皬锛岄€夋嫨涓棿甯?
            return [total_frames // 2]
        
        # 璁＄畻闇€瑕佹娴嬬殑甯ф暟
        # 渚嬪锛?00绉掓暟鎹紝30绉掗棿闅旓紝搴旇妫€娴?100/30 鈮?3 甯?
        target_detection_count = max(1, int(total_seconds / interval_seconds))
        
        # 璁＄畻甯ч棿闅旓紝纭繚鍧囧寑鍒嗗竷
        frame_interval = max(1, total_frames // target_detection_count)
        
        selected_indices = []
        
        # 鍧囧寑閫夋嫨甯?
        for i in range(0, total_frames, frame_interval):
            selected_indices.append(i)
            
            # 濡傛灉宸茬粡閫夋嫨浜嗚冻澶熺殑甯э紝鍋滄
            if len(selected_indices) >= target_detection_count:
                break
        
        # 纭繚閫夋嫨绗竴甯у拰鏈€鍚庝竴甯?
        if 0 not in selected_indices:
            selected_indices.insert(0, 0)
        if (total_frames - 1) not in selected_indices:
            selected_indices.append(total_frames - 1)
        
        # 鎺掑簭骞跺幓閲?
        selected_indices = sorted(list(set(selected_indices)))
        
        logger.info(f"鍧囧寑甯ч€夋嫨锛氭€诲抚鏁?{total_frames}锛屾椂闂磋寖鍥?{total_seconds:.1f}绉掞紝"
                   f"鐩爣妫€娴嬫暟 {target_detection_count}锛屽抚闂撮殧 {frame_interval}锛?
                   f"瀹為檯閫夋嫨 {len(selected_indices)} 甯?)
        
        return selected_indices
    
    def _find_closest_frame(self, records: List[PHMData], target_time: datetime) -> Optional[int]:
        """鎵惧埌鏈€鎺ヨ繎鐩爣鏃堕棿鐨勫抚绱㈠紩"""
        if not records:
            return None
        
        min_diff = float('inf')
        closest_index = None
        
        for i, record in enumerate(records):
            time_diff = abs((record.timestamp - target_time).total_seconds())
            if time_diff < min_diff:
                min_diff = time_diff
                closest_index = i
        
        return closest_index
    
    def get_detection_summary(self, total_frames: int, selected_frames: int) -> Dict[str, Any]:
        """鑾峰彇妫€娴嬫憳瑕佷俊鎭?""
        # 姣忔浣跨敤鏃堕噸鏂板姞杞介厤缃紝纭繚鑾峰彇鏈€鏂扮殑閰嶇疆
        current_config = self._load_config()
        
        if total_frames == 0:
            return {
                'total_frames': 0,
                'selected_frames': 0,
                'detection_ratio': 0.0,
                'reduction_ratio': 0.0,
                'mode': current_config.mode.value,
                'enabled': current_config.enabled
            }
        
        detection_ratio = selected_frames / total_frames
        reduction_ratio = 1.0 - detection_ratio
        
        return {
            'total_frames': total_frames,
            'selected_frames': selected_frames,
            'detection_ratio': detection_ratio,
            'reduction_ratio': reduction_ratio,
            'mode': current_config.mode.value,
            'enabled': current_config.enabled,
            'estimated_time_saving': f"{reduction_ratio*100:.1f}%"
        }


# 鍏ㄥ眬妫€娴嬮鐜囨帶鍒跺櫒瀹炰緥
detection_frequency_controller = DetectionFrequencyController()

