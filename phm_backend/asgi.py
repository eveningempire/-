"""
ASGI config for phm_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

from __future__ import annotations

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path, re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phm_backend.settings")

# Initialize Django ASGI application early to ensure the AppRegistry is populated
django_asgi_app = get_asgi_application()

from data_management.consumers import RealtimeDataConsumer
from data_management.progress_consumer import ImportProgressConsumer, BatchProgressConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # 瀹炴椂鏁版嵁WebSocket
            re_path(r"^ws/realtime/(?P<cmg_id>[^/]+)/$", RealtimeDataConsumer.as_asgi()),
            re_path(r"^ws/realtime/$", RealtimeDataConsumer.as_asgi()),
            # 鏂囦欢瀵煎叆杩涘害WebSocket
            re_path(r"^ws/import-progress/(?P<session_id>\d+)/$", ImportProgressConsumer.as_asgi()),
            re_path(r"^ws/batch-progress/$", BatchProgressConsumer.as_asgi()),
        ])
    ),
})
