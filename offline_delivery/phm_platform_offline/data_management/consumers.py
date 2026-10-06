"""Real-time telemetry WebSocket consumers."""
import asyncio
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .models import PHM
from .realtime_cache import realtime_cache

class RealtimeDataConsumer(AsyncWebsocketConsumer):
    """Stream cached telemetry for one PHM."""
    async def connect(self):
        self.cmg_id = self.scope.get('url_route', {}).get('kwargs', {}).get('cmg_id')
        if self.cmg_id and not await self._exists(self.cmg_id):
            await self.close(code=4004); return
        self.group_name = f'realtime_cmg_{self.cmg_id}' if self.cmg_id else 'realtime_all'
        await self.channel_layer.group_add(self.group_name, self.channel_name); await self.accept()
        self.streaming = False; self.stream_task = None
        await self._send({'type':'connection_established','cmg_id':self.cmg_id})
    async def disconnect(self, close_code):
        self.streaming = False
        if self.stream_task and not self.stream_task.done(): self.stream_task.cancel()
        if getattr(self, 'group_name', None): await self.channel_layer.group_discard(self.group_name, self.channel_name)
    async def receive(self, text_data):
        try:
            data = json.loads(text_data); command = data.get('command')
            if command == 'start_stream':
                if not self.streaming: self.streaming = True; self.stream_task = asyncio.create_task(self._loop(float(data.get('interval', 1))))
                await self._send({'type':'stream_started','cmg_id':self.cmg_id})
            elif command == 'stop_stream': self.streaming = False; await self._send({'type':'stream_stopped','cmg_id':self.cmg_id})
            elif command == 'get_latest' and self.cmg_id:
                rows = await self._data(data.get('since_ms'), int(data.get('limit', 100))); await self._send({'type':'latest_data','cmg_id':self.cmg_id,'data':rows,'count':len(rows)})
            elif command == 'ping': await self._send({'type':'pong'})
            else: await self._send({'type':'error','message':'Unknown command'})
        except (ValueError, TypeError, json.JSONDecodeError) as exc: await self._send({'type':'error','message':str(exc)})
    async def _loop(self, interval):
        try:
            while self.streaming:
                if self.cmg_id:
                    rows = await self._data(None, 100)
                    if rows: await self._send({'type':'realtime_data','cmg_id':self.cmg_id,'data':rows,'timestamp':timezone.now().isoformat()})
                await asyncio.sleep(max(.1, interval))
        except asyncio.CancelledError: pass
    async def realtime_data_update(self, event): await self._send({'type':'realtime_data','cmg_id':event.get('cmg_id'),'data':event.get('data'),'timestamp':event.get('timestamp')})
    async def system_notification(self, event): await self._send({'type':'notification','level':event.get('level','info'),'message':event.get('message'),'timestamp':event.get('timestamp')})
    async def _send(self, payload): await self.send(text_data=json.dumps(payload, ensure_ascii=False, default=str))
    @database_sync_to_async
    def _exists(self, cmg_id): return PHM.objects.filter(cmg_id=cmg_id).exists()
    @database_sync_to_async
    def _data(self, since_ms=None, limit=100): return realtime_cache.get_recent_data(self.cmg_id, since_ms, max(1, min(limit, 1000)))

class SystemNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self): await self.channel_layer.group_add('system_notifications', self.channel_name); await self.accept()
    async def disconnect(self, close_code): await self.channel_layer.group_discard('system_notifications', self.channel_name)
    async def system_alert(self, event): await self.send(text_data=json.dumps({'type':'system_alert', **event}, ensure_ascii=False, default=str))
