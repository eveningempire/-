"""
Redis 服务模块 - 统一管理 Redis 缓存操作。

提供数据缓存、实时通信、性能优化和处理进度缓存等功能。
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone


# Redis 连接池 - 延迟初始化
redis_client = None


def get_redis_client():
    """获取 Redis 客户端，延迟初始化。"""
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
            max_connections=20,
        )
    return redis_client


def get_channel_layer_safe():
    """安全获取 channel layer。"""
    try:
        return get_channel_layer()
    except Exception:
        return None


class RedisDataService:
    """Redis 数据服务类。"""

    # 缓存键前缀
    CACHE_PREFIX = "cmg_platform"
    REALTIME_DATA_PREFIX = f"{CACHE_PREFIX}:realtime"
    PHM_DATA_PREFIX = f"{CACHE_PREFIX}:cmg_data"
    QUERY_CACHE_PREFIX = f"{CACHE_PREFIX}:query"
    STATS_PREFIX = f"{CACHE_PREFIX}:stats"
    PROGRESS_PREFIX = f"{CACHE_PREFIX}:progress"

    @classmethod
    def get_realtime_key(cls, cmg_id: str) -> str:
        """获取实时数据 Redis 键。"""
        return f"{cls.REALTIME_DATA_PREFIX}:{cmg_id}"

    @classmethod
    def get_cmg_data_key(cls, cmg_id: str, date_str: str) -> str:
        """获取 PHM 数据缓存键。"""
        return f"{cls.PHM_DATA_PREFIX}:{cmg_id}:{date_str}"

    @classmethod
    def get_query_cache_key(cls, query_hash: str) -> str:
        """获取查询缓存键。"""
        return f"{cls.QUERY_CACHE_PREFIX}:{query_hash}"

    @classmethod
    def get_progress_key(cls, session_id: int) -> str:
        """获取进度缓存键。"""
        return f"{cls.PROGRESS_PREFIX}:session:{session_id}"

    def __init__(self):
        self.redis = get_redis_client()

    def ping(self) -> bool:
        """检查 Redis 连接。"""
        try:
            return self.redis.ping()
        except Exception:
            return False

    def cache_realtime_data(
        self,
        cmg_id: str,
        data_points: List[Dict[str, Any]],
        max_points: int = 5000,
        ttl_hours: int = 24,
    ) -> bool:
        """缓存实时数据到 Redis。"""
        try:
            key = self.get_realtime_key(cmg_id)
            pipe = self.redis.pipeline()

            # 使用有序集合存储数据，以时间戳作为分数。
            for point in data_points:
                timestamp_ms = int(
                    datetime.fromisoformat(
                        point["timestamp"].replace("Z", "+00:00")
                    ).timestamp()
                    * 1000
                )

                data_json = json.dumps(
                    {
                        "timestamp": point["timestamp"],
                        "data": point.get("data", {}),
                    }
                )

                pipe.zadd(key, {data_json: timestamp_ms})

            # 限制数据量，保留最新数据。
            pipe.zremrangebyrank(key, 0, -(max_points + 1))

            # 设置过期时间。
            pipe.expire(key, ttl_hours * 3600)

            pipe.execute()
            return True

        except Exception as e:
            print(f"Error caching realtime data: {e}")
            return False

    def get_realtime_data(
        self,
        cmg_id: str,
        since_ms: Optional[int] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """从 Redis 获取实时数据。"""
        try:
            key = self.get_realtime_key(cmg_id)

            if since_ms:
                # 获取指定时间戳之后的数据。
                raw_data = self.redis.zrangebyscore(
                    key,
                    since_ms,
                    "+inf",
                    start=0,
                    num=limit,
                    withscores=False,
                )
            else:
                # 获取最新数据，并转换为时间正序。
                raw_data = self.redis.zrevrange(key, 0, limit - 1, withscores=False)
                raw_data = list(reversed(raw_data))

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
        """获取 PHM 最新数据时间戳。"""
        try:
            key = self.get_realtime_key(cmg_id)
            latest = self.redis.zrevrange(key, 0, 0, withscores=True)
            if latest:
                return int(latest[0][1])
            return None
        except Exception:
            return None

    def cache_query_result(
        self, query_hash: str, result_data: Any, ttl_minutes: int = 10
    ) -> bool:
        """缓存查询结果。"""
        try:
            key = self.get_query_cache_key(query_hash)
            cached_data = {
                "data": result_data,
                "cached_at": timezone.now().isoformat(),
                "ttl": ttl_minutes,
            }

            self.redis.setex(
                key, ttl_minutes * 60, json.dumps(cached_data, default=str)
            )
            return True

        except Exception as e:
            print(f"Error caching query result: {e}")
            return False

    def get_cached_query_result(self, query_hash: str) -> Optional[Any]:
        """获取缓存的查询结果。"""
        try:
            key = self.get_query_cache_key(query_hash)
            cached = self.redis.get(key)

            if cached:
                data = json.loads(cached)
                return data["data"]
            return None

        except Exception as e:
            print(f"Error getting cached query result: {e}")
            return None

    def cache_cmg_daily_data(
        self,
        cmg_id: str,
        date: datetime,
        data: List[Dict[str, Any]],
        ttl_hours: int = 6,
    ) -> bool:
        """缓存 PHM 日数据。"""
        try:
            date_str = date.strftime("%Y-%m-%d")
            key = self.get_cmg_data_key(cmg_id, date_str)

            cached_data = {
                "cmg_id": cmg_id,
                "date": date_str,
                "data": data,
                "cached_at": timezone.now().isoformat(),
                "count": len(data),
            }

            self.redis.setex(
                key, ttl_hours * 3600, json.dumps(cached_data, default=str)
            )
            return True

        except Exception as e:
            print(f"Error caching daily data: {e}")
            return False

    def get_cmg_daily_data(
        self, cmg_id: str, date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的 PHM 日数据。"""
        try:
            date_str = date.strftime("%Y-%m-%d")
            key = self.get_cmg_data_key(cmg_id, date_str)

            cached = self.redis.get(key)
            if cached:
                data = json.loads(cached)
                return data["data"]
            return None

        except Exception as e:
            print(f"Error getting cached daily data: {e}")
            return None

    def update_cmg_stats(self, cmg_id: str, stats: Dict[str, Any]) -> bool:
        """更新 PHM 统计信息。"""
        try:
            key = f"{self.STATS_PREFIX}:cmg:{cmg_id}"
            stats["updated_at"] = timezone.now().isoformat()

            self.redis.setex(key, 3600, json.dumps(stats, default=str))
            return True

        except Exception as e:
            print(f"Error updating PHM stats: {e}")
            return False

    def get_cmg_stats(self, cmg_id: str) -> Optional[Dict[str, Any]]:
        """获取 PHM 统计信息。"""
        try:
            key = f"{self.STATS_PREFIX}:cmg:{cmg_id}"
            cached = self.redis.get(key)

            if cached:
                return json.loads(cached)
            return None

        except Exception as e:
            print(f"Error getting PHM stats: {e}")
            return None

    def clear_cmg_cache(self, cmg_id: str) -> bool:
        """清空指定 PHM 的全部缓存。"""
        try:
            patterns = [
                f"{self.REALTIME_DATA_PREFIX}:{cmg_id}",
                f"{self.PHM_DATA_PREFIX}:{cmg_id}:*",
                f"{self.STATS_PREFIX}:cmg:{cmg_id}",
            ]

            for pattern in patterns:
                if "*" in pattern:
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
        """获取缓存使用情况。"""
        try:
            info = self.redis.info("memory")

            realtime_keys = len(self.redis.keys(f"{self.REALTIME_DATA_PREFIX}:*"))
            data_keys = len(self.redis.keys(f"{self.PHM_DATA_PREFIX}:*"))
            query_keys = len(self.redis.keys(f"{self.QUERY_CACHE_PREFIX}:*"))
            stats_keys = len(self.redis.keys(f"{self.STATS_PREFIX}:*"))

            return {
                "redis_connected": True,
                "memory_used": info.get("used_memory_human", "0B"),
                "memory_peak": info.get("used_memory_peak_human", "0B"),
                "keys_count": {
                    "realtime_data": realtime_keys,
                    "cached_data": data_keys,
                    "query_cache": query_keys,
                    "statistics": stats_keys,
                    "total": realtime_keys + data_keys + query_keys + stats_keys,
                },
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            return {
                "redis_connected": False,
                "error": str(e),
                "keys_count": {"total": 0},
            }

    def notify_realtime_update(
        self, cmg_id: str, data: List[Dict[str, Any]]
    ) -> bool:
        """通知 WebSocket 客户端有新的实时数据。"""
        try:
            channel_layer = get_channel_layer_safe()
            if not channel_layer:
                return False

            async_to_sync(channel_layer.group_send)(
                f"realtime_cmg_{cmg_id}",
                {
                    "type": "realtime_data_update",
                    "cmg_id": cmg_id,
                    "data": data,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            async_to_sync(channel_layer.group_send)(
                "realtime_all",
                {
                    "type": "realtime_data_update",
                    "cmg_id": cmg_id,
                    "data": data,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            return True

        except Exception as e:
            print(f"Error sending WebSocket notification: {e}")
            return False

    def notify_system_alert(self, level: str, message: str) -> bool:
        """发送系统警报通知。"""
        try:
            channel_layer = get_channel_layer_safe()
            if not channel_layer:
                return False

            async_to_sync(channel_layer.group_send)(
                "system_notifications",
                {
                    "type": "system_alert",
                    "level": level,
                    "message": message,
                    "timestamp": timezone.now().isoformat(),
                },
            )

            return True

        except Exception as e:
            print(f"Error sending system alert: {e}")
            return False

    def update_processing_progress(
        self,
        session_id: int,
        progress: float,
        processed: int,
        total: int,
        status: str = None,
        message: str = None,
    ) -> bool:
        """更新处理进度到 Redis。"""
        try:
            key = self.get_progress_key(session_id)
            progress_data = {
                "session_id": session_id,
                "progress": progress,
                "processed": processed,
                "total": total,
                "status": status,
                "message": message,
                "updated_at": timezone.now().isoformat(),
            }

            # 进度信息保留 2 小时，避免长期堆积。
            self.redis.setex(key, 7200, json.dumps(progress_data, default=str))
            return True

        except Exception as e:
            print(f"Error updating processing progress: {e}")
            return False

    def get_processing_progress(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取处理进度。"""
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
        """清除处理进度。"""
        try:
            key = self.get_progress_key(session_id)
            self.redis.delete(key)
            return True

        except Exception as e:
            print(f"Error clearing processing progress: {e}")
            return False


# 全局 Redis 服务实例
redis_service = RedisDataService()


def generate_query_hash(params: Dict[str, Any]) -> str:
    """为查询参数生成哈希值，用于缓存键。"""
    sorted_params = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(sorted_params.encode()).hexdigest()


def cache_database_query(
    query_params: Dict[str, Any], result_data: Any, ttl_minutes: int = 10
) -> bool:
    """缓存数据库查询结果。"""
    query_hash = generate_query_hash(query_params)
    return redis_service.cache_query_result(query_hash, result_data, ttl_minutes)


def get_cached_database_query(query_params: Dict[str, Any]) -> Optional[Any]:
    """获取缓存的数据库查询结果。"""
    query_hash = generate_query_hash(query_params)
    return redis_service.get_cached_query_result(query_hash)
