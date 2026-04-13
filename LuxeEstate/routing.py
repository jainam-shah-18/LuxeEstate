"""
WebSocket URL routing for Django Channels
"""
from django.urls import path
from messaging.consumers import ChatConsumer, NotificationConsumer

websocket_urlpatterns = [
    path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi(), name='ws_chat'),
    path('ws/notifications/', NotificationConsumer.as_asgi(), name='ws_notifications'),
]
