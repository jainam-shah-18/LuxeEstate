from django.contrib import admin

from .models import ChatMessage, ChatThread, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('property', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read',)


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ('property', 'buyer', 'agent', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'is_ai_bot', 'created_at')
