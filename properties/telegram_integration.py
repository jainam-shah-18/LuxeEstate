"""
Telegram Integration with LuxeAI Chatbot

Handles:
- Telegram user session management
- Routing messages through LuxeChatbot
- Maintaining conversation context
- Property search and booking through Telegram
"""

import logging
from typing import Dict, Optional, Any
import uuid

from django.conf import settings
from django.utils import timezone

from .models import TelegramUser, Lead, Property
from .chatbot_service import LuxeChatbot

logger = logging.getLogger(__name__)


class TelegramSession:
    """Manages a Telegram user's chat session with LuxeAI"""
    
    def __init__(self, telegram_id: int, telegram_data: Optional[Dict[str, Any]] = None):
        """
        Initialize or retrieve a Telegram user session
        
        Args:
            telegram_id: Telegram user ID
            telegram_data: Optional Telegram user data (first_name, last_name, username)
        """
        self.telegram_id = telegram_id
        self.user_obj = None
        self.chatbot = LuxeChatbot()
        
        # Get or create TelegramUser
        self.user_obj, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'session_id': str(uuid.uuid4()),
                'telegram_username': telegram_data.get('username') if telegram_data else None,
                'telegram_first_name': telegram_data.get('first_name') if telegram_data else None,
                'telegram_last_name': telegram_data.get('last_name') if telegram_data else None,
            }
        )
        
        if created:
            logger.info(f"Created new TelegramUser: {telegram_id}")
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a message from Telegram user through LuxeAI chatbot
        
        Args:
            user_message: The message text from user
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get current conversation state
            conversation_state = self.user_obj.conversation_state or {}
            
            # Process through LuxeChatbot
            result = self.chatbot.process_message(
                user_message,
                conversation_state=conversation_state
            )
            
            # Extract response
            response_text = result.get('response') or result.get('message') or ''
            
            # Update conversation state with history limit (prevent echo/bloat)
            if result.get('conversation_state'):
                state = result['conversation_state']
                history = state.get('chat_history', [])
                if len(history) > 12:  # Max 6 turns (12 messages)
                    state['chat_history'] = history[-12:]
                    logger.info(f"Limited history from {len(history)} to 12 messages")
                self.user_obj.conversation_state = state
                self.user_obj.save(update_fields=['conversation_state'])
            
            # Update last message
            self.user_obj.update_last_message(user_message)
            
            # Build response with action buttons if needed
            response_data = {
                'text': response_text,
                'intent': result.get('intent'),
                'lead_data': result.get('lead', {}),
                'has_qualified_lead': result.get('qualified_lead', False),
                'keyboard': self._build_keyboard(result),
            }
            
            # If we have a qualified lead, try to create/update it
            if result.get('qualified_lead'):
                self._save_telegram_lead(result.get('lead', {}))
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}", exc_info=True)
            return {
                'text': "Sorry, I encountered an error. Please try again.",
                'intent': 'error',
                'keyboard': self._build_keyboard({}),
            }
    
    def _save_telegram_lead(self, lead_data: Dict[str, str]):
        """Save or update lead from Telegram user"""
        try:
            if not lead_data:
                return
            
            lead, created = Lead.objects.update_or_create(
                session_id=self.user_obj.session_id,
                defaults={
                    'name': lead_data.get('name'),
                    'contact': lead_data.get('contact'),
                    'intent': lead_data.get('intent'),
                    'budget': lead_data.get('budget'),
                    'location': lead_data.get('location'),
                    'property_type': lead_data.get('property_type'),
                    'bhk': lead_data.get('bhk'),
                    'source': 'telegram',
                }
            )
            
            # Link TelegramUser to Lead
            self.user_obj.lead = lead
            self.user_obj.save(update_fields=['lead'])
            
            lead.update_qualification()
            
            if created:
                logger.info(f"Created lead for Telegram user {self.telegram_id}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error saving telegram lead: {e}")
            return None
    
    def _build_keyboard(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build inline keyboard for Telegram response
        
        Args:
            result: Chatbot processing result
            
        Returns:
            Keyboard markup for Telegram API or None
        """
        intent = result.get('intent', '')
        
        keyboard_buttons = []
        
        # Add intent-specific buttons
        if intent == 'buy' or intent == 'rent':
            keyboard_buttons = [
                {'text': '🔍 Search Properties', 'callback_data': 'search_properties'},
                {'text': '📋 Show Results', 'callback_data': 'show_results'},
            ]
        
        if intent == 'appointment':
            keyboard_buttons = [
                {'text': '📅 Confirm Date/Time', 'callback_data': 'confirm_appointment'},
                {'text': '❌ Cancel', 'callback_data': 'cancel_appointment'},
            ]
        
        if result.get('qualified_lead'):
            keyboard_buttons.append(
                {'text': '📞 Book Call with Agent', 'callback_data': 'book_call'}
            )
        
        # Add general buttons
        keyboard_buttons.extend([
            {'text': '🏠 Browse Properties', 'callback_data': 'browse_properties'},
            {'text': '💬 Chat with Agent', 'callback_data': 'chat_agent'},
        ])
        
        if not keyboard_buttons:
            return None
        
        # Format for Telegram inline keyboard
        return {
            'inline_keyboard': [[btn] for btn in keyboard_buttons]
        }
    
    def search_properties(self, filters: Dict[str, Any]) -> list:
        """
        Search properties based on user criteria
        
        Args:
            filters: Search filters (city, property_type, budget, etc.)
            
        Returns:
            List of property objects
        """
        try:
            qs = Property.objects.filter(is_active=True)
            
            if filters.get('city'):
                qs = qs.filter(city__icontains=filters['city'])
            if filters.get('property_type'):
                qs = qs.filter(property_type=filters['property_type'])
            if filters.get('listing_type'):
                qs = qs.filter(listing_type=filters['listing_type'])
            if filters.get('bedrooms'):
                qs = qs.filter(bedrooms=filters['bedrooms'])
            if filters.get('min_price'):
                qs = qs.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                qs = qs.filter(price__lte=filters['max_price'])
            
            return list(qs[:5])  # Return max 5 properties
            
        except Exception as e:
            logger.error(f"Error searching properties: {e}")
            return []
    
    def format_property_for_telegram(self, prop: Property) -> str:
        """
        Format a property listing for Telegram message
        
        Args:
            prop: Property object
            
        Returns:
            Formatted string for Telegram
        """
        return (
            f"🏠 <b>{prop.title}</b>\n"
            f"📍 {prop.location}, {prop.city}\n"
            f"💰 ₹{prop.price:,.0f}\n"
            f"🛏️ {prop.bedrooms or 'N/A'} BHK | "
            f"🚿 {prop.bathrooms or 'N/A'} Bathroom\n"
            f"📐 {prop.area_sqft or 'N/A'} Sq.Ft.\n"
            f"⭐ Rating: {prop.rating}/5\n"
            f"🔗 <a href='{settings.SITE_URL}/property/{prop.id}/'>View Details</a>"
        )
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of this conversation"""
        return {
            'telegram_id': self.telegram_id,
            'session_id': self.user_obj.session_id,
            'messages_count': self.user_obj.message_count,
            'last_message_at': self.user_obj.last_message_at,
            'has_lead': self.user_obj.lead is not None,
            'lead_qualification': self.user_obj.lead.qualification_stage if self.user_obj.lead else None,
            'is_connected': self.user_obj.is_connected,
        }


def get_or_create_telegram_session(telegram_id: int, telegram_data: Optional[Dict] = None) -> TelegramSession:
    """
    Helper function to get or create a Telegram session
    
    Args:
        telegram_id: Telegram user ID
        telegram_data: Optional Telegram user data
        
    Returns:
        TelegramSession object
    """
    return TelegramSession(telegram_id, telegram_data)
