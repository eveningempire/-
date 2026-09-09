"""
Redis鏈嶅姟妯″潡 - 缁熶竴绠＄悊Redis缂撳瓨鎿嶄綔
鎻愪緵鏁版嵁缂撳瓨銆佸疄鏃堕€氫俊銆佹€ц兘浼樺寲绛夊姛鑳?
"""

import json
import redis
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Redis杩炴帴姹?- 寤惰繜鍒濆鍖?
redis_client = None

def get_redis_client():
    """鑾峰彇Redis瀹㈡埛绔紝寤惰繜鍒濆鍖?""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=20
        )
    return redis_client

def get_channel_layer_safe():
    """瀹夊叏鑾峰彇channel layer"""
    try:
        return get_channel_layer()
    except Exception:
        return None


class RedisDataService:
    """Redis鏁版嵁鏈嶅姟绫?""
    
    # 缂撳瓨閿墠缂€
    CACHE_PREFIX = "cmg_platform"
    REALTIME_DATA_PREFIX = f"{CACHE_PREFIX}:realtime"
    PHM_DATA_PREFIX = f"{CACHE_PREFIX}:cmg_data"
    QUERY_CACHE_PREFIX = f"{CACHE_PREFIX}:query"
    STATS_PREFIX = f"{CACHE_PREFIX}:stats"
    PROGRESS_PREFIX = f"{CACHE_PREFIX}:progress"
    
    @classmethod
    def get_realtime_key(cls, cmg_id: str) -> str:
        """鑾峰彇瀹炴椂鏁版嵁Redis閿?""
        return f"{cls.REALTIME_DATA_PREFIX}:{cmg_id}"
    
    @classmethod
    def get_cmg_data_key(cls, cmg_id: str, date_str: str) -> str:
        """鑾峰彇PHM鏁版嵁缂撳瓨閿?""
        return f"{cls.PHM_DATA_PREFIX}:{cmg_id}:{date_str}"
    
    @classmethod
    def get_query_cache_key(cls, query_hash: str) -> str:
        """鑾峰彇鏌ヨ缂撳瓨閿?""
        return f"{cls.QUERY_CACHE_PREFIX}:{query_hash}"
    
    @classmethod
    def get_progress_key(cls, session_id: int) -> str:
        """鑾峰彇杩涘害缂撳瓨閿?""
        return f"{cls.PROGRESS_PREFIX}:session:{session_id}"

    def __init__(self):
        self.redis = get_redis_client()
        
    def ping(self) -> bool:
        """妫€鏌edis杩炴帴"""
        try:
            return self.redis.ping()
        except Exception:
            return False
    
    # 瀹炴椂鏁版嵁缂撳瓨鎿嶄綔
    def cache_realtime_data(self, cmg_id: str, data_points: List[Dict[str, Any]], 
                          max_points: int = 5000, ttl_hours: int = 24) -> bool:
        """缂撳瓨瀹炴椂鏁版嵁鍒癛edis"""
        try:
            key = self.get_realtime_key(cmg_id)
            pipe = self.redis.pipeline()
            
            # 浣跨敤鏈夊簭闆嗗悎瀛樺偍鏁版嵁锛屼互鏃堕棿鎴充负鍒嗘暟
            for point in data_points:
                timestamp_ms = int(datetime.fromisoformat(
                    point['timestamp'].replace('Z', '+00:00')
                ).timestamp() * 1000)
                
                data_json = json.dumps({
                    'timestamp': point['timestamp'],
                    'data': point.get('data', {})
                })
                
                pipe.zadd(key, {data_json: timestamp_ms})
            
            # 闄愬埗鏁版嵁閲忥紝淇濈暀鏈€鏂扮殑鏁版嵁
            pipe.zremrangebyrank(key, 0, -(max_points + 1))
            
            # 璁剧疆杩囨湡鏃堕棿
            pipe.expire(key, ttl_hours * 3600)
            
            pipe.execute()
            return True
            
        except Exception as e:
            print(f"Error caching realtime data: {e}")
            return False
    
    def get_realtime_data(self, cmg_id: str, since_ms: Optional[int] = None, 
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """浠嶳edis鑾峰彇瀹炴椂鏁版嵁"""
        try:
            key = self.get_realtime_key(cmg_id)
            
            if since_ms:
                # 鑾峰彇鎸囧畾鏃堕棿鎴充箣鍚庣殑鏁版嵁
                raw_data = self.redis.zrangebyscore(
                    key, since_ms, '+inf', start=0, num=limit, withscores=False
                )
            else:
                # 鑾峰彇鏈€鏂扮殑鏁版嵁
                raw_data = self.redis.zrevrange(key, 0, limit - 1, withscores=False)
                raw_data = list(reversed(raw_data))  # 杞负鏃堕棿姝ｅ簭
            
            # 瑙ｆ瀽JSON鏁版嵁
            result = []
            for item in raw_data:
                try:
                    parsed = json.loads(item)
                    result.append(parsed)
                except json.JSONDecodeError:
                    continue
            
            return result
            
        except Exception as e:
            print(f"Error getting realtime data: {e}")
            return []
    
    def get_latest_timestamp(self, cmg_id: str) -> Optional[int]:
        """鑾峰彇PHM鏈€鏂版暟鎹椂闂存埑"""
        try:
            key = self.get_realtime_key(cmg_id)
            latest = self.redis.zrevrange(key, 0, 0, withscores=True)
            if latest:
                return int(latest[0][1])
            return None
        except Exception:
            return None
    
    # 鏌ヨ缁撴灉缂撳瓨
    def cache_query_result(self, query_hash: str, result_data: Any, ttl_minutes: int = 10) -> bool:
        """缂撳瓨鏌ヨ缁撴灉"""
        try:
            key = self.get_query_cache_key(query_hash)
            cached_data = {
                'data': result_data,
                'cached_at': timezone.now().isoformat(),
                'ttl': ttl_minutes
            }
            
            self.redis.setex(key, ttl_minutes * 60, json.dumps(cached_data, default=str))
            return True
            
        except Exception as e:
            print(f"Error caching query result: {e}")
            return False
    
    def get_cached_query_result(self, query_hash: str) -> Optional[Any]:
        """鑾峰彇缂撳瓨鐨勬煡璇㈢粨鏋?""
        try:
            key = self.get_query_cache_key(query_hash)
            cached = self.redis.get(key)
            
            if cached:
                data = json.loads(cached)
                return data['data']
            return None
            
        except Exception as e:
            print(f"Error getting cached query result: {e}")
            return None
    
    # PHM鏁版嵁缂撳瓨
    def cache_cmg_daily_data(self, cmg_id: str, date: datetime, data: List[Dict[str, Any]], 
                           ttl_hours: int = 6) -> bool:
        """缂撳瓨PHM鏃ユ暟鎹?""
        try:
            date_str = date.strftime('%Y-%m-%d')
            key = self.get_cmg_data_key(cmg_id, date_str)
            
            cached_data = {
                'cmg_id': cmg_id,
                'date': date_str,
                'data': data,
                'cached_at': timezone.now().isoformat(),
                'count': len(data)
            }
            
            self.redis.setex(key, ttl_hours * 3600, json.dumps(cached_data, default=str))
            return True
            
        except Exception as e:
            print(f"Error caching daily data: {e}")
            return False
    
    def get_cmg_daily_data(self, cmg_id: str, date: datetime) -> Optional[List[Dict[str, Any]]]:
        """鑾峰彇缂撳瓨鐨凜MG鏃ユ暟鎹?""
        try:
            date_str = date.strftime('%Y-%m-%d')
            key = self.get_cmg_data_key(cmg_id, date_str)
            
            cached = self.redis.get(key)
            if cached:
                data = json.loads(cached)
                return data['data']
            return None
            
        except Exception as e:
            print(f"Error getting cached daily data: {e}")
            return None
    
    # 缁熻淇℃伅缂撳瓨
    def update_cmg_stats(self, cmg_id: str, stats: Dict[str, Any]) -> bool:
        """鏇存柊PHM缁熻淇℃伅"""
        try:
            key = f"{self.STATS_PREFIX}:cmg:{cmg_id}"
            stats['updated_at'] = timezone.now().isoformat()
            
            self.redis.setex(key, 3600, json.dumps(stats, default=str))  # 1灏忔椂杩囨湡
            return True
            
        except Exception as e:
            print(f"Error updating PHM stats: {e}")
            return False
    
    def get_cmg_stats(self, cmg_id: str) -> Optional[Dict[str, Any]]:
        """鑾峰彇PHM缁熻淇℃伅"""
        try:
            key = f"{self.STATS_PREFIX}:cmg:{cmg_id}"
            cached = self.redis.get(key)
            
            if cached:
                return json.loads(cached)
            return None
            
        except Exception as e:
            print(f"Error getting PHM stats: {e}")
            return None
    
    # 绯荤粺缂撳瓨绠＄悊
    def clear_cmg_cache(self, cmg_id: str) -> bool:
        """娓呯┖鎸囧畾PHM鐨勬墍鏈夌紦瀛?""
        try:
            patterns = [
                f"{self.REALTIME_DATA_PREFIX}:{cmg_id}",
                f"{self.PHM_DATA_PREFIX}:{cmg_id}:*",
                f"{self.STATS_PREFIX}:cmg:{cmg_id}"
            ]
            
            for pattern in patterns:
                if '*' in pattern:
                    # 浣跨敤scan鍒犻櫎鍖归厤鐨勯敭
                    keys = self.redis.keys(pattern)
                    if keys:
                        self.redis.delete(*keys)
                else:
                    self.redis.delete(pattern)
            
            return True
            
        except Exception as e:
            print(f"Error clearing PHM cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """鑾峰彇缂撳瓨浣跨敤鎯呭喌"""
        try:
            info = self.redis.info('memory')
            
            # 缁熻鍚勭被鍨嬬紦瀛橀敭鏁伴噺
            realtime_keys = len(self.redis.keys(f"{self.REALTIME_DATA_PREFIX}:*"))
            data_keys = len(self.redis.keys(f"{self.PHM_DATA_PREFIX}:*"))
            query_keys = len(self.redis.keys(f"{self.QUERY_CACHE_PREFIX}:*"))
            stats_keys = len(self.redis.keys(f"{self.STATS_PREFIX}:*"))
            
            return {
                'redis_connected': True,
                'memory_used': info.get('used_memory_human', '0B'),
                'memory_peak': info.get('used_memory_peak_human', '0B'),
                'keys_count': {
                    'realtime_data': realtime_keys,
                    'cached_data': data_keys,
                    'query_cache': query_keys,
                    'statistics': stats_keys,
                    'total': realtime_keys + data_keys + query_keys + stats_keys
                },
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            return {
                'redis_connected': False,
                'error': str(e),
                'keys_count': {'total': 0}
            }
    
    # WebSocket閫氱煡
    def notify_realtime_update(self, cmg_id: str, data: List[Dict[str, Any]]) -> bool:
        """閫氱煡WebSocket瀹㈡埛绔湁鏂扮殑瀹炴椂鏁版嵁"""
        try:
            channel_layer = get_channel_layer_safe()
            if not channel_layer:
                return False
                
            # 鍙戦€佸埌鐗瑰畾PHM缁?
            async_to_sync(channel_layer.group_send)(
                f"realtime_cmg_{cmg_id}",
                {
                    'type': 'realtime_data_update',
                    'cmg_id': cmg_id,
                    'data': data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # 鍙戦€佸埌鍏ㄥ眬缁?
            async_to_sync(channel_layer.group_send)(
                "realtime_all",
                {
                    'type': 'realtime_data_update',
                    'cmg_id': cmg_id,
                    'data': data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending WebSocket notification: {e}")
            return False
    
    def notify_system_alert(self, level: str, message: str) -> bool:
        """鍙戦€佺郴缁熻鎶ラ€氱煡"""
        try:
            channel_layer = get_channel_layer_safe()
            if not channel_layer:
                return False
                
            async_to_sync(channel_layer.group_send)(
                "system_notifications",
                {
                    'type': 'system_alert',
                    'level': level,
                    'message': message,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending system alert: {e}")
            return False
    
    # 杩涘害绠＄悊
    def update_processing_progress(self, session_id: int, progress: float, processed: int, total: int, 
                                 status: str = None, message: str = None) -> bool:
        """鏇存柊澶勭悊杩涘害鍒癛edis"""
        try:
            key = self.get_progress_key(session_id)
            progress_data = {
                'session_id': session_id,
                'progress': progress,
                'processed': processed,
                'total': total,
                'status': status,
                'message': message,
                'updated_at': timezone.now().isoformat()
            }
            
            # 璁剧疆杩囨湡鏃堕棿涓?灏忔椂锛岄槻姝㈣繘搴︽暟鎹爢绉?
            self.redis.setex(key, 7200, json.dumps(progress_data, default=str))
            return True
            
        except Exception as e:
            print(f"Error updating processing progress: {e}")
            return False
    
    def get_processing_progress(self, session_id: int) -> Optional[Dict[str, Any]]:
        """鑾峰彇澶勭悊杩涘害"""
        try:
            key = self.get_progress_key(session_id)
            cached = self.redis.get(key)
            
            if cached:
                return json.loads(cached)
            return None
            
        except Exception as e:
            print(f"Error getting processing progress: {e}")
            return None
    
    def clear_processing_progress(self, session_id: int) -> bool:
        """娓呴櫎澶勭悊杩涘害"""
        try:
            key = self.get_progress_key(session_id)
            self.redis.delete(key)
            return True
            
        except Exception as e:
            print(f"Error clearing processing progress: {e}")
            return False


# 鍏ㄥ眬Redis鏈嶅姟瀹炰緥
redis_service = RedisDataService()


def generate_query_hash(params: Dict[str, Any]) -> str:
    """鐢熸垚鏌ヨ鍙傛暟鐨勫搱甯屽€肩敤浜庣紦瀛?""
    import hashlib
    
    # 鎺掑簭鍙傛暟浠ョ‘淇濅竴鑷存€?
    sorted_params = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(sorted_params.encode()).hexdigest()


def cache_database_query(query_params: Dict[str, Any], result_data: Any, ttl_minutes: int = 10) -> bool:
    """缂撳瓨鏁版嵁搴撴煡璇㈢粨鏋?""
    query_hash = generate_query_hash(query_params)
    return redis_service.cache_query_result(query_hash, result_data, ttl_minutes)


def get_cached_database_query(query_params: Dict[str, Any]) -> Optional[Any]:
    """鑾峰彇缂撳瓨鐨勬暟鎹簱鏌ヨ缁撴灉"""
    query_hash = generate_query_hash(query_params)
    return redis_service.get_cached_query_result(query_hash)

