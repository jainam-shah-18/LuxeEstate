from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser

from .models import ChatbotConversation, ChatbotMessage, Lead, Appointment
from .serializers import (
    ChatbotConversationSerializer,
    ChatbotMessageSerializer,
    LeadSerializer,
    AppointmentSerializer,
)
from .ai_service import ChatbotAIService, SchedulingService
from properties.models import Property


class ChatbotConversationViewSet(viewsets.ModelViewSet):
    """API endpoints for chatbot conversations."""
    
    queryset = ChatbotConversation.objects.all()
    serializer_class = ChatbotConversationSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def start_conversation(self, request):
        """Start a new chatbot conversation."""
        visitor_name = request.data.get('visitor_name')
        visitor_email = request.data.get('visitor_email')
        visitor_phone = request.data.get('visitor_phone')
        property_id = request.data.get('property_id')
        
        # Create conversation
        conversation_data = {
            'visitor_name': visitor_name,
            'visitor_email': visitor_email,
            'visitor_phone': visitor_phone,
            'visitor_ip': self._get_client_ip(request),
            'is_active': True,
        }
        
        if property_id:
            try:
                conversation_data['property'] = Property.objects.get(pk=property_id)
            except Property.DoesNotExist:
                return Response(
                    {'error': 'Property not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        conversation = ChatbotConversation.objects.create(**conversation_data)
        
        # Send greeting
        ai_service = ChatbotAIService()
        context = conversation.get_context()
        greeting = "Hello! 👋 I'm your LuxeEstate assistant. How can I help you find your perfect property today?"
        
        ChatbotMessage.objects.create(
            conversation=conversation,
            sender='bot',
            message=greeting,
        )
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def send_message(self, request, pk=None):
        """Send a message in conversation and get AI response."""
        try:
            conversation = self.get_object()
            user_message = request.data.get('message', '').strip()
            
            if not user_message:
                return Response(
                    {'error': 'Message cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save user message
            ChatbotMessage.objects.create(
                conversation=conversation,
                sender='user',
                message=user_message,
            )
            
            # Get conversation history
            history = list(conversation.messages.values('sender', 'message').order_by('timestamp'))
            
            # Detect intent and extract lead info
            ai_service = ChatbotAIService()
            intent = ai_service.detect_intent(user_message)
            extracted_info = ai_service.extract_lead_info(history, user_message)
            is_qualified = ai_service.should_qualify_lead(extracted_info)
            
            # Generate AI response
            context = conversation.get_context()
            response_data = ai_service.generate_ai_response(
                user_message,
                context,
                history,
                is_lead_qualified=hasattr(conversation, 'lead'),
            )
            
            # Save AI response
            bot_message = ChatbotMessage.objects.create(
                conversation=conversation,
                sender='bot',
                message=response_data.get('message', 'Thank you for your message. An agent will respond shortly.'),
                intent_detected=intent,
            )
            
            # Update conversation context
            if not conversation.visitor_name and extracted_info.get('name'):
                conversation.visitor_name = extracted_info['name']
                conversation.save()
            
            # Create or update lead if qualified
            if is_qualified and not hasattr(conversation, 'lead'):
                self._create_lead_from_conversation(conversation, extracted_info)
            
            return Response({
                'conversation_id': conversation.id,
                'message_id': bot_message.id,
                'bot_response': response_data.get('message', 'Thank you for your message. An agent will respond shortly.'),
                'intent': intent,
                'is_qualified': is_qualified,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error in send_message: {e}")
            import traceback
            traceback.print_exc()
            
            # Return error response with fallback message
            return Response({
                'error': 'An error occurred while processing your message.',
                'bot_response': 'Thank you for your message. An agent will respond shortly.',
                'conversation_id': pk,
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def end_conversation(self, request, pk=None):
        """End the conversation."""
        conversation = self.get_object()
        conversation.is_active = False
        conversation.ended_at = timezone.now()
        conversation.save()
        
        return Response({
            'status': 'Conversation ended',
            'conversation_id': conversation.id,
        })
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def get_history(self, request, pk=None):
        """Get conversation message history."""
        conversation = self.get_object()
        messages = ChatbotMessage.objects.filter(conversation=conversation).order_by('timestamp')
        serializer = ChatbotMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _create_lead_from_conversation(self, conversation, extracted_info):
        """Create a lead record from conversation."""
        first_name = extracted_info.get('name', 'Unknown').split()[0]
        last_name = ' '.join(extracted_info.get('name', 'Unknown').split()[1:]) or 'Prospect'
        
        lead = Lead.objects.create(
            conversation=conversation,
            first_name=first_name,
            last_name=last_name,
            email=extracted_info.get('email') or conversation.visitor_email or 'not_provided@example.com',
            phone=extracted_info.get('phone') or conversation.visitor_phone or '',
            buyer_type=extracted_info.get('buyer_type'),
            property_type_preference=extracted_info.get('property_preference'),
            timeline=extracted_info.get('timeline'),
            interested_property=conversation.property,
            status='new',
        )
        
        return lead


class LeadViewSet(viewsets.ModelViewSet):
    """API endpoints for managing leads."""
    
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter leads based on user role."""
        if self.request.user.is_staff:
            return Lead.objects.all()
        return Lead.objects.filter(assigned_agent=self.request.user) | Lead.objects.filter(
            assigned_agent__isnull=True, status='new'
        )
    
    @action(detail=True, methods=['post'])
    def assign_to_me(self, request, pk=None):
        """Assign lead to current user."""
        lead = self.get_object()
        lead.assigned_agent = request.user
        if lead.status == 'new':
            lead.status = 'contacted'
        lead.save()
        return Response(LeadSerializer(lead).data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update lead status."""
        lead = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Lead.STATUS_CHOICES):
            lead.status = new_status
            lead.save()
            return Response(LeadSerializer(lead).data)
        
        return Response(
            {'error': 'Invalid status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def send_recommendations(self, request, pk=None):
        """Send property recommendations to lead."""
        lead = self.get_object()
        
        # Get properties matching lead preferences
        filters = Q()
        if lead.property_type_preference:
            filters &= Q(property_type=lead.property_type_preference)
        if lead.budget_min and lead.budget_max:
            filters &= Q(price__gte=lead.budget_min, price__lte=lead.budget_max)
        
        recommended_properties = Property.objects.filter(filters)[:5]
        
        return Response({
            'lead_id': lead.id,
            'recommendations_sent': True,
            'properties': [
                {
                    'id': p.id,
                    'title': p.title,
                    'price': str(p.price),
                    'type': p.get_property_type_display(),
                    'city': p.city,
                }
                for p in recommended_properties
            ],
        })


class AppointmentViewSet(viewsets.ModelViewSet):
    """API endpoints for managing appointments."""
    
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter appointments."""
        if self.request.user.is_staff:
            return Appointment.objects.all()
        return Appointment.objects.filter(
            Q(assigned_agent=self.request.user) |
            Q(lead__assigned_agent=self.request.user)
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def schedule_tour(self, request):
        """Schedule a property tour from chatbot."""
        lead_id = request.data.get('lead_id')
        property_id = request.data.get('property_id')
        scheduled_at = request.data.get('scheduled_at')
        appointment_type = request.data.get('appointment_type', 'property_tour')
        notes = request.data.get('notes', '')
        
        try:
            lead = Lead.objects.get(pk=lead_id)
            property_obj = Property.objects.get(pk=property_id) if property_id else None
        except (Lead.DoesNotExist, Property.DoesNotExist):
            return Response(
                {'error': 'Lead or Property not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        appointment = Appointment.objects.create(
            lead=lead,
            property=property_obj or lead.interested_property,
            appointment_type=appointment_type,
            scheduled_at=scheduled_at,
            notes=notes,
        )
        
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm appointment."""
        appointment = self.get_object()
        appointment.status = 'confirmed'
        appointment.agent_confirmed_at = timezone.now()
        appointment.confirmation_sent = True
        appointment.assigned_agent = request.user
        appointment.save()
        
        return Response(AppointmentSerializer(appointment).data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available_slots(self, request):
        """Get available tour slots."""
        property_id = request.query_params.get('property_id')
        days_ahead = int(request.query_params.get('days_ahead', 7))
        
        if not property_id:
            return Response(
                {'error': 'property_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        slots = SchedulingService.get_available_slots(property_id, days_ahead)
        return Response({'available_slots': slots})
