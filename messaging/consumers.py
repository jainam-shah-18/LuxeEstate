"""
WebSocket consumers for real-time chat using Django Channels
"""
import json
import logging
from urllib.parse import urlparse
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.conf import settings
from .models import Message, Conversation, ChatNotification
from properties.models import Property
from datetime import datetime

logger = logging.getLogger(__name__)


def _is_allowed_ws_origin(scope):
    raw_headers = dict(scope.get('headers', []))
    origin = raw_headers.get(b'origin', b'').decode('utf-8')
    if not origin:
        return False
    hostname = urlparse(origin).hostname
    if not hostname:
        return False
    allowed_hosts = set(settings.ALLOWED_HOSTS or [])
    allowed_hosts.update({'localhost', '127.0.0.1'})
    if '*' in allowed_hosts or hostname in allowed_hosts:
        return True
    for allowed in allowed_hosts:
        if allowed.startswith('.') and hostname.endswith(allowed):
            return True
    return False


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time messaging between users
    Handles individual conversation rooms
    """
    connected_users = {}

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        if not self.user.is_authenticated or not _is_allowed_ws_origin(self.scope):
            await self.close()
            return
        
        if self.conversation_id is None:
            await self.close()
            return
        
        # Verify user is part of this conversation
        if not await self.verify_user_access():
            await self.close()
            return
        
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        self.connected_users.setdefault(self.conversation_id, set()).add(self.user.id)
        
        # Send user joined notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )
        
        logger.info(f"User {self.user.username} connected to conversation {self.conversation_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if not hasattr(self, 'room_group_name'):
            return

        if getattr(self, 'conversation_id', None) in self.connected_users:
            self.connected_users[self.conversation_id].discard(self.user.id)
            if not self.connected_users[self.conversation_id]:
                self.connected_users.pop(self.conversation_id, None)

        # Send user left notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'username': self.user.username,
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.username} disconnected from conversation")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read':
                await self.handle_read(data)
            elif message_type == 'delivered':
                await self.handle_delivered(data)
            elif message_type == 'is_typing':
                await self.handle_is_typing(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def handle_chat_message(self, data):
        """Process incoming chat message"""
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return
        
        # Save message to database
        message_obj = await self.save_message(message_text, data.get('message_type', 'text'))
        
        if message_obj:
            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_obj.message,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'sender_avatar': await self.get_user_avatar(),
                    'timestamp': message_obj.created_at.isoformat(),
                    'message_id': message_obj.id,
                    'message_type': message_obj.message_type,
                }
            )

            if await self.is_user_online(message_obj.recipient_id):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'delivery_receipt',
                        'message_id': message_obj.id,
                        'status': 'delivered',
                        'sender_id': self.user.id,
                        'timestamp': message_obj.created_at.isoformat(),
                    }
                )
            
            # Create notification for recipient
            await self.create_notification(message_obj)
    
    async def handle_typing(self, data):
        """Handle user typing indicator"""
        await self.handle_is_typing(data)
    
    async def handle_is_typing(self, data):
        """Notify others that user is typing"""
        is_typing = data.get('is_typing', True)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'username': self.user.username,
                'is_typing': is_typing,
            }
        )
    
    async def handle_read(self, data):
        """Mark messages as read"""
        message_ids = data.get('message_ids', [])
        if message_ids:
            read_ids, read_at = await self.mark_as_read(message_ids)
            if read_ids:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'delivery_receipt',
                        'message_ids': read_ids,
                        'status': 'read',
                        'reader_id': self.user.id,
                        'timestamp': read_at,
                    }
                )

    async def handle_delivered(self, data):
        """Forward delivery receipts to conversation participants."""
        message_id = data.get('message_id')
        if not message_id:
            return

        if await self.is_message_recipient(message_id):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delivery_receipt',
                    'message_id': message_id,
                    'status': 'delivered',
                    'reader_id': self.user.id,
                    'timestamp': datetime.now().isoformat(),
                }
            )
    
    # Event handlers for group messages
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'sender_avatar': event.get('sender_avatar', ''),
            'timestamp': event['timestamp'],
            'message_id': event.get('message_id'),
            'message_type': event.get('message_type', 'text'),
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'username': event['username'],
                'is_typing': event.get('is_typing', True),
            }))
    
    async def user_join(self, event):
        """Notify user joined"""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_join',
                'username': event['username'],
            }))
    
    async def user_leave(self, event):
        """Notify user left"""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_leave',
                'username': event['username'],
            }))

    async def delivery_receipt(self, event):
        """Send delivery/read receipts to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'delivery_receipt',
            'message_id': event.get('message_id'),
            'message_ids': event.get('message_ids', []),
            'status': event.get('status', 'sent'),
            'timestamp': event.get('timestamp'),
            'reader_id': event.get('reader_id'),
            'sender_id': event.get('sender_id'),
        }))
    
    # Database operations
    
    @database_sync_to_async
    def verify_user_access(self):
        """Verify user has access to this conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return (self.user == conversation.initiator or 
                    self.user == conversation.recipient)
        except Conversation.DoesNotExist:
            logger.warning(f"Conversation {self.conversation_id} not found")
            return False
    
    @database_sync_to_async
    def save_message(self, message_text, message_type='text'):
        """Save message to database"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            
            # Determine recipient
            recipient = (conversation.recipient if self.user == conversation.initiator 
                        else conversation.initiator)
            
            message_obj = Message.objects.create(
                conversation=conversation,
                property=conversation.property,
                sender=self.user,
                recipient=recipient,
                message=message_text,
                message_type=message_type
            )
            
            return message_obj
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return None
    
    @database_sync_to_async
    def create_notification(self, message_obj):
        """Create notification for recipient"""
        try:
            ChatNotification.objects.create(
                user=message_obj.recipient,
                message=message_obj,
                is_read=False
            )
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
    
    @database_sync_to_async
    def mark_as_read(self, message_ids):
        """Mark messages as read"""
        try:
            messages = Message.objects.filter(
                id__in=message_ids,
                recipient=self.user
            )
            updated_ids = []
            for msg in messages:
                msg.mark_as_read()
                ChatNotification.objects.filter(message=msg).update(is_read=True)
                updated_ids.append(msg.id)
            return updated_ids, datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}")
            return [], None

    @database_sync_to_async
    def is_message_recipient(self, message_id):
        try:
            return Message.objects.filter(id=message_id, recipient=self.user).exists()
        except Exception:
            return False

    async def is_user_online(self, user_id):
        return user_id in self.connected_users.get(self.conversation_id, set())
    
    @database_sync_to_async
    def get_user_avatar(self):
        """Get user's profile picture URL"""
        try:
            if self.user.profile.profile_picture:
                return self.user.profile.profile_picture.url
        except:
            pass
        return ''


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    Sends general notifications to individual users
    """
    
    async def connect(self):
        """Handle notification consumer connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated or not _is_allowed_ws_origin(self.scope):
            await self.close()
            return
        
        self.notification_group_name = f'notifications_{self.user.id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.username} connected to notifications")
    
    async def disconnect(self, close_code):
        """Handle notification consumer disconnection"""
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user.username} disconnected from notifications")
    
    async def notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'link': event.get('link', ''),
            'icon': event.get('icon', 'info'),
            'timestamp': datetime.now().isoformat(),
        }))