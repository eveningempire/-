"""
文件处理进度WebSocket消费者
支持实时推送文件上传和检测进度
"""

import json
import logging
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import ImportSession
from .batch_processing import batch_processor

logger = logging.getLogger(__name__)


class ImportProgressConsumer(AsyncWebsocketConsumer):
    """文件导入进度WebSocket消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id: Optional[int] = None
        self.group_name: Optional[str] = None
        
    async def connect(self):
        """WebSocket连接建立"""
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        
        if self.session_id:
            try:
                self.session_id = int(self.session_id)
                # 验证会话是否存在
                session_exists = await self.check_session_exists(self.session_id)
                if not session_exists:
                    await self.close(code=4004)
                    return
                    
                self.group_name = f"import_session_{self.session_id}"
            except (ValueError, TypeError):
                await self.close(code=4000)
                return
        else:
            await self.close(code=4000)
            return
        
        # 加入WebSocket组
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
        # 发送连接确认消息和当前状态
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'session_id': self.session_id,
            'message': f'Connected to import session {self.session_id} progress stream'
        }))
        
        # 发送当前状态
        current_status = await self.get_current_status()
        if current_status:
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'session_id': self.session_id,
                **current_status
            }))

    async def disconnect(self, close_code):
        """WebSocket连接断开"""
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """接收来自WebSocket的消息"""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'get_status':
                await self.send_current_status()
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

    async def send_current_status(self):
        """发送当前状态"""
        current_status = await self.get_current_status()
        if current_status:
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'session_id': self.session_id,
                **current_status,
                'timestamp': timezone.now().isoformat()
            }))

    # 进度更新处理器（从group_send调用）
    async def progress_update(self, event):
        """处理进度更新事件"""
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'session_id': event.get('session_id'),
            'progress': event.get('progress'),
            'processed': event.get('processed'),
            'total': event.get('total'),
            'timestamp': event.get('timestamp')
        }))

    async def status_change(self, event):
        """处理状态变更事件"""
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'session_id': event.get('session_id'),
            'status': event.get('status'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    async def detection_result(self, event):
        """处理检测结果事件"""
        await self.send(text_data=json.dumps({
            'type': 'detection_result',
            'session_id': event.get('session_id'),
            'detection_type': event.get('detection_type'),
            'result': event.get('result'),
            'timestamp': event.get('timestamp')
        }))

    async def processing_complete(self, event):
        """处理完成事件"""
        await self.send(text_data=json.dumps({
            'type': 'processing_complete',
            'session_id': event.get('session_id'),
            'summary': event.get('summary'),
            'timestamp': event.get('timestamp')
        }))

    # 数据库操作方法
    @database_sync_to_async
    def check_session_exists(self, session_id: int) -> bool:
        """检查导入会话是否存在"""
        return ImportSession.objects.filter(id=session_id).exists()

    @database_sync_to_async
    def get_current_status(self) -> Optional[Dict[str, Any]]:
        """获取当前会话状态"""
        try:
            if not self.session_id:
                return None
            
            # 先尝试从批量处理器获取
            status_data = batch_processor.get_session_status(self.session_id)
            if status_data:
                return status_data
            
            # 如果批量处理器没有数据，从数据库获取
            session = ImportSession.objects.get(id=self.session_id)
            return {
                'id': session.id,
                'status': session.processing_status,
                'progress': session.processing_progress,
                'total_records': session.total_records,
                'processed_records': session.processed_records,
                'failed_records': session.failed_records,
                'error_message': session.error_message,
                'detection_summary': session.detection_summary,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            }
            
        except ImportSession.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return None


class BatchProgressConsumer(AsyncWebsocketConsumer):
    """批量处理进度WebSocket消费者（监控所有活动会话）"""
    
    async def connect(self):
        """WebSocket连接建立"""
        # 加入全局批量处理组
        await self.channel_layer.group_add("batch_processing", self.channel_name)
        await self.accept()
        
        # 发送连接确认消息
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to batch processing monitor'
        }))

    async def disconnect(self, close_code):
        """WebSocket连接断开"""
        await self.channel_layer.group_discard("batch_processing", self.channel_name)

    async def receive(self, text_data):
        """接收来自WebSocket的消息"""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'get_active_sessions':
                await self.send_active_sessions()
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

    async def send_active_sessions(self):
        """发送活动会话列表"""
        active_sessions = await self.get_active_sessions()
        await self.send(text_data=json.dumps({
            'type': 'active_sessions',
            'sessions': active_sessions,
            'timestamp': timezone.now().isoformat()
        }))

    # 批量处理事件处理器
    async def session_started(self, event):
        """处理会话开始事件"""
        await self.send(text_data=json.dumps({
            'type': 'session_started',
            'session_id': event.get('session_id'),
            'cmg_id': event.get('cmg_id'),
            'filename': event.get('filename'),
            'timestamp': event.get('timestamp')
        }))

    async def session_completed(self, event):
        """处理会话完成事件"""
        await self.send(text_data=json.dumps({
            'type': 'session_completed',
            'session_id': event.get('session_id'),
            'summary': event.get('summary'),
            'timestamp': event.get('timestamp')
        }))

    async def session_failed(self, event):
        """处理会话失败事件"""
        await self.send(text_data=json.dumps({
            'type': 'session_failed',
            'session_id': event.get('session_id'),
            'error': event.get('error'),
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def get_active_sessions(self) -> list:
        """获取活动会话列表"""
        try:
            active_sessions = []
            processing_statuses = [
                ImportSession.ProcessingStatus.PENDING,
                ImportSession.ProcessingStatus.PARSING,
                ImportSession.ProcessingStatus.STORING,
                ImportSession.ProcessingStatus.DETECTING
            ]
            
            sessions = ImportSession.objects.filter(
                processing_status__in=processing_statuses
            ).select_related('cmg').order_by('-timestamp')[:20]
            
            for session in sessions:
                active_sessions.append({
                    'id': session.id,
                    'cmg_id': session.cmg.cmg_id,
                    'cmg_name': session.cmg.name,
                    'status': session.processing_status,
                    'progress': session.processing_progress,
                    'total_records': session.total_records,
                    'processed_records': session.processed_records,
                    'started_at': session.started_at.isoformat() if session.started_at else None,
                    'filename': session.file.name if session.file else None
                })
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"获取活动会话失败: {e}")
            return []
