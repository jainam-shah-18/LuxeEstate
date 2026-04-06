import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from messaging.models import ChatMessage, ChatThread


@database_sync_to_async
def get_thread_and_role(user, thread_id):
    try:
        t = ChatThread.objects.select_related('property', 'buyer', 'agent').get(pk=thread_id)
    except ChatThread.DoesNotExist:
        return None, None
    if user.pk == t.buyer_id:
        return t, 'buyer'
    if user.pk == t.agent_id:
        return t, 'agent'
    return None, None


@database_sync_to_async
def save_chat_message(thread: ChatThread, user, body: str):
    return ChatMessage.objects.create(thread=thread, sender=user, body=body, is_ai_bot=False)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return

        try:
            self.thread_id = int(self.scope['url_route']['kwargs']['thread_id'])
        except (KeyError, TypeError, ValueError):
            await self.close(code=4400)
            return

        thread, role = await get_thread_and_role(user, self.thread_id)
        if thread is None:
            await self.close(code=4403)
            return

        self.thread = thread
        self.role = role
        self.room_group_name = f'chat_{self.thread_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        body = (data.get('message') or '').strip()
        if not body:
            return
        user = self.scope['user']
        msg = await save_chat_message(self.thread, user, body)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'payload': {
                    'kind': 'message',
                    'body': body,
                    'sender_id': user.id,
                    'sender_email': getattr(user, 'email', ''),
                    'created': msg.created_at.isoformat(),
                    'is_ai_bot': False,
                },
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['payload']))
