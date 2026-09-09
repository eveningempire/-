"""
瀹炴椂鏁版嵁缂撳瓨妯″潡 - 鍚庣甯搁┗鍐呭瓨缂撳瓨
鎻愪緵楂樻€ц兘鐨勫疄鏃舵暟鎹瓨鍌ㄥ拰妫€绱㈠姛鑳?
"""

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.utils import timezone


class RealtimeDataPoint:
    """瀹炴椂鏁版嵁鐐?""
    def __init__(self, timestamp: datetime, data: Dict[str, Any]):
        self.timestamp = timestamp
        self.data = data
        self.timestamp_ms = int(timestamp.timestamp() * 1000)  # 姣鏃堕棿鎴崇敤浜庡揩閫熸瘮杈?


class PHMRingBuffer:
    """PHM鐜舰缂撳啿鍖?- 鍥哄畾澶у皬锛岃嚜鍔ㄦ竻鐞嗘棫鏁版嵁"""
    
    def __init__(self, max_duration_minutes: int = 30, max_points: int = 15000):
        self.max_duration = timedelta(minutes=max_duration_minutes)
        self.max_points = max_points
        self.data = deque(maxlen=max_points)
        self.lock = threading.RLock()
        # 澧炲姞绱㈠紩浠ユ彁楂樻煡璇㈡€ц兘
        self._timestamp_index = {}  # timestamp_ms -> index_in_deque
        
    def add_point(self, point: RealtimeDataPoint):
        """娣诲姞鏁版嵁鐐?""
        with self.lock:
            self.data.append(point)
            self._cleanup_old_data()
    
    def add_points(self, points: List[RealtimeDataPoint]):
        """鎵归噺娣诲姞鏁版嵁鐐?""
        with self.lock:
            self.data.extend(points)
            self._cleanup_old_data()
    
    def _cleanup_old_data(self):
        """娓呯悊杩囨湡鏁版嵁"""
        if not self.data:
            return
            
        cutoff_time = timezone.now() - self.max_duration
        # 浠庡乏渚хЩ闄よ繃鏈熸暟鎹?
        while self.data and self.data[0].timestamp < cutoff_time:
            self.data.popleft()
    
    def get_recent_data(self, since_ms: Optional[int] = None, limit: int = 1000) -> List[RealtimeDataPoint]:
        """鑾峰彇鏈€杩戞暟鎹?- 浼樺寲鐗堟湰"""
        with self.lock:
            self._cleanup_old_data()
            
            if since_ms is None:
                # 杩斿洖鏈€杩戠殑limit鏉℃暟鎹?
                start_idx = max(0, len(self.data) - limit)
                return list(self.data)[start_idx:]
            
            # 浣跨敤浜屽垎鏌ユ壘浼樺寲since_ms鏌ヨ
            result = []
            # 浠庡悗寰€鍓嶆煡鎵撅紝鍥犱负閫氬父鏌ヨ鏈€杩戠殑鏁版嵁
            for i in range(len(self.data) - 1, -1, -1):
                point = self.data[i]
                if point.timestamp_ms > since_ms:
                    result.append(point)
                    if len(result) >= limit:
                        break
                else:
                    # 鐢变簬鏁版嵁鏄寜鏃堕棿鎺掑簭鐨勶紝鍙互鎻愬墠閫€鍑?
                    break
            
            return list(reversed(result))
    
    def get_data_in_range(self, start_time: datetime, end_time: datetime) -> List[RealtimeDataPoint]:
        """鑾峰彇鏃堕棿鑼冨洿鍐呯殑鏁版嵁"""
        with self.lock:
            self._cleanup_old_data()
            
            result = []
            for point in self.data:
                if start_time <= point.timestamp <= end_time:
                    result.append(point)
            
            return result
    
    def get_latest_timestamp(self) -> Optional[int]:
        """鑾峰彇鏈€鏂版暟鎹殑鏃堕棿鎴?姣)"""
        with self.lock:
            if self.data:
                return self.data[-1].timestamp_ms
            return None
    
    def size(self) -> int:
        """鑾峰彇褰撳墠鏁版嵁鐐规暟閲?""
        return len(self.data)


class RealtimeDataCache:
    """瀹炴椂鏁版嵁缂撳瓨绠＄悊鍣?""
    
    def __init__(self):
        self.cmg_buffers: Dict[str, PHMRingBuffer] = defaultdict(lambda: PHMRingBuffer())
        self.lock = threading.RLock()
        self._cleanup_timer = None
        self._start_cleanup_timer()
    
    def add_data(self, cmg_id: str, timestamp: datetime, data: Dict[str, Any]):
        """娣诲姞鍗曚釜鏁版嵁鐐?""
        point = RealtimeDataPoint(timestamp, data)
        self.cmg_buffers[cmg_id].add_point(point)
    
    def add_batch_data(self, cmg_id: str, batch_data: List[Tuple[datetime, Dict[str, Any]]]):
        """鎵归噺娣诲姞鏁版嵁"""
        points = [RealtimeDataPoint(ts, data) for ts, data in batch_data]
        self.cmg_buffers[cmg_id].add_points(points)
    
    def get_recent_data(self, cmg_id: str, since_ms: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """鑾峰彇PHM鐨勬渶杩戞暟鎹?""
        buffer = self.cmg_buffers.get(cmg_id)
        if not buffer:
            return []
        
        points = buffer.get_recent_data(since_ms, limit)
        return [
            {
                'timestamp': point.timestamp.isoformat(),
                'data': point.data
            }
            for point in points
        ]
    
    def get_data_in_range(self, cmg_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """鑾峰彇鏃堕棿鑼冨洿鍐呯殑鏁版嵁"""
        buffer = self.cmg_buffers.get(cmg_id)
        if not buffer:
            return []
        
        points = buffer.get_data_in_range(start_time, end_time)
        return [
            {
                'timestamp': point.timestamp.isoformat(),
                'data': point.data
            }
            for point in points
        ]
    
    def get_latest_timestamp(self, cmg_id: str) -> Optional[int]:
        """鑾峰彇PHM鏈€鏂版暟鎹椂闂存埑"""
        buffer = self.cmg_buffers.get(cmg_id)
        if buffer:
            return buffer.get_latest_timestamp()
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """鑾峰彇缂撳瓨缁熻淇℃伅"""
        stats = {}
        total_points = 0
        
        for cmg_id, buffer in self.cmg_buffers.items():
            size = buffer.size()
            total_points += size
            latest_ts = buffer.get_latest_timestamp()
            
            stats[cmg_id] = {
                'data_points': size,
                'latest_timestamp': latest_ts,
                'latest_time': datetime.fromtimestamp(latest_ts / 1000).isoformat() if latest_ts else None
            }
        
        stats['total'] = {
            'cmg_count': len(self.cmg_buffers),
            'total_data_points': total_points,
            'memory_usage_mb': total_points * 0.001  # 绮楃暐浼扮畻
        }
        
        return stats
    
    def clear_cmg_cache(self, cmg_id: str):
        """娓呯┖鎸囧畾PHM鐨勭紦瀛?""
        if cmg_id in self.cmg_buffers:
            del self.cmg_buffers[cmg_id]
    
    def _start_cleanup_timer(self):
        """鍚姩瀹氭湡娓呯悊瀹氭椂鍣?""
        def cleanup():
            try:
                # 娓呯悊杩囨湡鏁版嵁
                for buffer in self.cmg_buffers.values():
                    buffer._cleanup_old_data()
                
                # 绉婚櫎绌虹殑缂撳啿鍖?
                empty_cmgs = [cmg_id for cmg_id, buffer in self.cmg_buffers.items() if buffer.size() == 0]
                for cmg_id in empty_cmgs:
                    del self.cmg_buffers[cmg_id]
                
            except Exception as e:
                print(f"Cleanup error: {e}")
            finally:
                # 閲嶆柊璁剧疆瀹氭椂鍣?
                self._cleanup_timer = threading.Timer(300, cleanup)  # 姣?鍒嗛挓娓呯悊涓€娆?
                self._cleanup_timer.daemon = True
                self._cleanup_timer.start()
        
        self._cleanup_timer = threading.Timer(300, cleanup)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()


# 鍏ㄥ眬瀹炴椂鏁版嵁缂撳瓨瀹炰緥
realtime_cache = RealtimeDataCache()

