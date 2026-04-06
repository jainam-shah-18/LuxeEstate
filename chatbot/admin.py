from django.contrib import admin
from django.utils.html import format_html
from .models import ChatbotConversation, ChatbotMessage, Lead, Appointment, ChatbotAnalytics


@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'visitor_info', 'property', 'message_count', 'is_active', 'created_at')
    list_filter = ('created_at', 'is_active', 'property')
    search_fields = ('visitor_name', 'visitor_email', 'visitor_phone')
    readonly_fields = ('created_at', 'updated_at', 'ended_at')
    
    fieldsets = (
        ('Visitor Info', {
            'fields': ('visitor_name', 'visitor_email', 'visitor_phone', 'visitor_ip', 'user')
        }),
        ('Context', {
            'fields': ('property',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at', 'ended_at')
        }),
    )
    
    def visitor_info(self, obj):
        return f"{obj.visitor_name or 'Anonymous'} ({obj.visitor_email or 'N/A'})"
    visitor_info.short_description = 'Visitor'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(ChatbotMessage)
class ChatbotMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'message_preview', 'intent_detected', 'timestamp')
    list_filter = ('sender', 'intent_detected', 'timestamp')
    search_fields = ('message', 'conversation__visitor_email')
    readonly_fields = ('timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'status_badge', 'buyer_type', 'timeline', 'assigned_agent', 'created_at')
    list_filter = ('status', 'buyer_type', 'timeline', 'created_at', 'assigned_agent')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'conversation')
    
    fieldsets = (
        ('Lead Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'city')
        }),
        ('Property Preferences', {
            'fields': ('interested_property', 'property_type_preference', 'budget_min', 'budget_max')
        }),
        ('Buyer Profile', {
            'fields': ('buyer_type', 'timeline')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_agent')
        }),
        ('Additional Info', {
            'fields': ('notes', 'conversation', 'created_at', 'updated_at')
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'
    
    def status_badge(self, obj):
        colors = {
            'new': '#FFA500',
            'contacted': '#4169E1',
            'qualified': '#32CD32',
            'scheduled': '#9370DB',
            'closed': '#808080',
            'lost': '#DC143C',
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('lead_name', 'property', 'appointment_type', 'scheduled_at', 'status_badge', 'assigned_agent')
    list_filter = ('status', 'appointment_type', 'scheduled_at', 'assigned_agent')
    search_fields = ('lead__first_name', 'lead__last_name', 'property__title')
    readonly_fields = ('created_at', 'updated_at', 'agent_confirmed_at')
    
    fieldsets = (
        ('Lead & Property', {
            'fields': ('lead', 'property')
        }),
        ('Appointment Details', {
            'fields': ('appointment_type', 'scheduled_at', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_agent', 'agent_confirmed_at', 'confirmation_sent')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def lead_name(self, obj):
        return f"{obj.lead.first_name} {obj.lead.last_name}"
    lead_name.short_description = 'Lead'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'confirmed': '#32CD32',
            'completed': '#4169E1',
            'cancelled': '#DC143C',
            'rescheduled': '#9370DB',
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(ChatbotAnalytics)
class ChatbotAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_conversations', 'total_messages', 'leads_qualified', 'appointments_scheduled', 'avg_messages_per_conversation')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_conversations', 'total_messages', 'leads_qualified', 'appointments_scheduled', 'avg_conversation_duration', 'avg_messages_per_conversation')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
