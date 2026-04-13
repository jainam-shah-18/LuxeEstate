"""
WebSocket routing for messaging app
"""
from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # Chat consumer for conversations
    path('ws/chat/<int:conversation_id>/', consumers.ChatConsumer.as_asgi(), name='ws_chat'),
    
    # Notification consumer
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi(), name='ws_notifications'),
    
    # Fallback (legacy support)
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]