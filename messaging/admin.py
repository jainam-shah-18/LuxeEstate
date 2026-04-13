from django.contrib import admin
from .models import Message, Conversation, ChatNotification, AgentResponse


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at', 'read_at')
    fields = ('sender', 'recipient', 'property', 'message', 'message_type', 'is_read', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('property', 'initiator', 'recipient', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('property__title', 'initiator__username', 'recipient__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]
    fieldsets = (
        ('Participants', {
            'fields': ('property', 'initiator', 'recipient')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'property', 'conversation', 'message_type', 'is_read', 'created_at')
    list_filter = ('is_read', 'message_type', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'property__title', 'message')
    readonly_fields = ('created_at', 'read_at')
    fieldsets = (
        ('Message Details', {
            'fields': ('conversation', 'property', 'sender', 'recipient', 'message', 'message_type')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at', 'read_at')
        }),
        ('Attachments', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatNotification)
class ChatNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message__sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message__sender__username')
    readonly_fields = ('created_at',)


@admin.register(AgentResponse)
class AgentResponseAdmin(admin.ModelAdmin):
    list_display = ('agent', 'title', 'created_at')
    list_filter = ('agent', 'created_at')
    search_fields = ('agent__username', 'title')
    readonly_fields = ('created_at',)
