from rest_framework import serializers
from .models import ChatbotConversation, ChatbotMessage, Lead, Appointment


class ChatbotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotMessage
        fields = ['id', 'sender', 'message', 'timestamp', 'intent_detected', 'ai_confidence']
        read_only_fields = ['timestamp', 'intent_detected', 'ai_confidence']


class ChatbotConversationSerializer(serializers.ModelSerializer):
    messages = ChatbotMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatbotConversation
        fields = [
            'id', 'visitor_name', 'visitor_email', 'visitor_phone',
            'property', 'messages', 'message_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class LeadSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    property_name = serializers.CharField(source='interested_property.title', read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'city', 'interested_property', 'property_name', 'property_type_preference',
            'budget_min', 'budget_max', 'buyer_type', 'timeline', 'status',
            'assigned_agent', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class AppointmentSerializer(serializers.ModelSerializer):
    lead_name = serializers.SerializerMethodField()
    property_title = serializers.CharField(source='property.title', read_only=True)
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'lead', 'lead_name', 'property', 'property_title',
            'appointment_type', 'scheduled_at', 'status', 'assigned_agent',
            'agent_confirmed_at', 'confirmation_sent', 'notes',
            'is_upcoming', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_lead_name(self, obj):
        return f"{obj.lead.first_name} {obj.lead.last_name}"
    
    def get_is_upcoming(self, obj):
        return obj.is_upcoming()
