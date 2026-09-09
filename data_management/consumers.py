"""
WebSocket娑堣垂鑰?- 瀹炴椂鏁版嵁鎺ㄩ€?
鏀寔瀹炴椂鏁版嵁娴佹帹閫佸埌鍓嶇
"""

import json
import asyncio
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta

from .models import PHM
from .realtime_cache import realtime_cache


class RealtimeDataConsumer(AsyncWebsocketConsumer):
    """瀹炴椂鏁版嵁WebSocket娑堣垂鑰?""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmg_id: Optional[str] = None
        self.group_name: Optional[str] = None
        self.is_streaming = False
        self.stream_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """WebSocket杩炴帴寤虹珛"""
        self.cmg_id = self.scope['url_route']['kwargs'].get('cmg_id')
        
        if self.cmg_id:
            # 楠岃瘉PHM鏄惁瀛樺湪
            cmg_exists = await self.check_cmg_exists(self.cmg_id)
            if not cmg_exists:
                await self.close(code=4004)
                return
                
            self.group_name = f"realtime_cmg_{self.cmg_id}"
        else:
            # 閫氱敤瀹炴椂鏁版嵁棰戦亾
            self.group_name = "realtime_all"
        
        # 鍔犲叆WebSocket缁?
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
        # 鍙戦€佽繛鎺ョ‘璁ゆ秷鎭?
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'cmg_id': self.cmg_id,
            'message': f'Connected to realtime data stream for PHM: {self.cmg_id or "ALL"}'
        }))

    async def disconnect(self, close_code):
        """WebSocket杩炴帴鏂紑"""
        if self.stream_task and not self.stream_task.done():
            self.stream_task.cancel()
            
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """鎺ユ敹鏉ヨ嚜WebSocket鐨勬秷鎭?""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'start_stream':
                await self.start_streaming(data)
            elif command == 'stop_stream':
                await self.stop_streaming()
            elif command == 'get_latest':
                await self.send_latest_data(data)
            elif command == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown command: {command}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error', 
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))

    async def start_streaming(self, data: Dict[str, Any]):
        """寮€濮嬪疄鏃舵暟鎹祦"""
        if self.is_streaming:
            return
            
        self.is_streaming = True
        interval = data.get('interval', 1.0)  # 榛樿1绉掗棿闅?
        
        # 鍚姩鏁版嵁娴佷换鍔?
        self.stream_task = asyncio.create_task(self.stream_data_loop(interval))
        
        await self.send(text_data=json.dumps({
            'type': 'stream_started',
            'interval': interval,
            'cmg_id': self.cmg_id
        }))

    async def stop_streaming(self):
        """鍋滄瀹炴椂鏁版嵁娴?""
        self.is_streaming = False
        
        if self.stream_task and not self.stream_task.done():
            self.stream_task.cancel()
            
        await self.send(text_data=json.dumps({
            'type': 'stream_stopped',
            'cmg_id': self.cmg_id
        }))

    async def stream_data_loop(self, interval: float):
        """鏁版嵁娴佸惊鐜?""
        last_timestamp_ms = None
        
        try:
            while self.is_streaming:
                # 鑾峰彇鏈€鏂版暟鎹?
                if self.cmg_id:
                    data = await self.get_realtime_data(self.cmg_id, last_timestamp_ms)
                    if data:
                        await self.send(text_data=json.dumps({
                            'type': 'realtime_data',
                            'cmg_id': self.cmg_id,
                            'data': data,
                            'timestamp': timezone.now().isoformat()
                        }))
                        
                        # 鏇存柊鏈€鍚庢椂闂存埑
                        if data:
                            last_point = max(data, key=lambda x: x['timestamp'])
                            last_timestamp_ms = int(datetime.fromisoformat(
                                last_point['timestamp'].replace('Z', '+00:00')
                            ).timestamp() * 1000)
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Stream error: {str(e)}'
            }))

    async def send_latest_data(self, data: Dict[str, Any]):
        """鍙戦€佹渶鏂版暟鎹?""
        limit = data.get('limit', 100)
        since_ms = data.get('since_ms')
        
        if self.cmg_id:
            latest_data = await self.get_realtime_data(self.cmg_id, since_ms, limit)
            await self.send(text_data=json.dumps({
                'type': 'latest_data',
                'cmg_id': self.cmg_id,
                'data': latest_data,
                'count': len(latest_data) if latest_data else 0
            }))

    # 鏁版嵁鎺ㄩ€佸鐞嗗櫒
    async def realtime_data_update(self, event):
        """澶勭悊瀹炴椂鏁版嵁鏇存柊浜嬩欢"""
        await self.send(text_data=json.dumps({
            'type': 'realtime_data',
            'cmg_id': event.get('cmg_id'),
            'data': event.get('data'),
            'timestamp': event.get('timestamp')
        }))

    async def system_notification(self, event):
        """澶勭悊绯荤粺閫氱煡浜嬩欢"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'level': event.get('level', 'info'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    # 鏁版嵁搴撴搷浣滄柟娉?
    @database_sync_to_async
    def check_cmg_exists(self, cmg_id: str) -> bool:
        """妫€鏌MG鏄惁瀛樺湪"""
        return PHM.objects.filter(cmg_id=cmg_id).exists()

    @database_sync_to_async
    def get_realtime_data(self, cmg_id: str, since_ms: Optional[int] = None, limit: int = 100):
        """鑾峰彇瀹炴椂鏁版嵁"""
        return realtime_cache.get_recent_data(cmg_id, since_ms, limit)
        
    @database_sync_to_async
    def get_cache_stats(self):
        """鑾峰彇缂撳瓨缁熻"""
        return realtime_cache.get_cache_stats()


class SystemNotificationConsumer(AsyncWebsocketConsumer):
    """绯荤粺閫氱煡WebSocket娑堣垂鑰?""
    
    async def connect(self):
        await self.channel_layer.group_add("system_notifications", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("system_notifications", self.channel_name)

    async def system_alert(self, event):
        """澶勭悊绯荤粺璀︽姤"""
        await self.send(text_data=json.dumps({
            'type': 'system_alert',
            'level': event['level'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

