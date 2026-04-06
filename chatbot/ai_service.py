"""
Enhanced chatbot AI service: multi-turn conversations, lead qualification, scheduling.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

import requests
from django.conf import settings


class ChatbotAIService:
    """Main AI chatbot service for LuxeEstate."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.timeout = 25
        self.max_tokens = 300
        self.model = "gpt-4o-mini"
    
    def get_system_prompt(self, conversation_context: Dict[str, Any], is_lead_qualified: bool = False) -> str:
        """Build dynamic system prompt based on conversation state."""
        base_prompt = """You are a professional, friendly, and efficient real estate assistant for LuxeEstate.
Your roles are:
1. Answer questions about properties and real estate
2. Identify and qualify interested buyers/renters
3. Help schedule property tours and consultations
4. Provide 24/7 customer support
5. Reduce administrative burden on agents

Communication guidelines:
- Be concise and helpful (max 100 words per response)
- Use the visitor's name when known
- Ask clarifying questions to understand needs
- Suggest next steps when appropriate (scheduling, agent contact)
- Maintain professional but friendly tone

Context information available:
- Visitor: {visitor_name}
- Property: {property_info}
""".format(
            visitor_name=conversation_context.get('visitor_name', 'Guest'),
            property_info=conversation_context.get('property', 'No specific property'),
        )
        
        if is_lead_qualified:
            base_prompt += """
LEAD QUALIFICATION STATE: This visitor appears to be a qualified lead.
- Focus on: Confirming interest, gathering additional preferences, scheduling tours
- Offer: Agent contact, virtual consultation, property recommendations
"""
        else:
            base_prompt += """
LEAD QUALIFICATION STATE: Visitor engagement phase.
- Focus on: Understanding needs, identifying property type preferences, budget
- Key questions: Property type? Budget range? Timeline? Buyer/Renter?
- Conversational: Keep responses conversational while gathering information
"""
        
        return base_prompt
    
    def detect_intent(self, user_message: str) -> str:
        """Detect user intent from message."""
        text = (user_message or "").strip().lower()
        
        # Intent patterns
        intent_patterns = {
            'pricing': r'(price|cost|how much|expensive|budget|afford)',
            'schedule': r'(schedule|book|tour|visit|appointment|time|when|available)',
            'document': r'(document|paper|proof|certificate|registration|agreement)',
            'property_type': r'(apartment|villa|house|plot|commercial|bedroom|bhk)',
            'location': r'(location|area|city|neighborhood|nearby|facilities)',
            'other': r'.*',
        }
        
        for intent, pattern in intent_patterns.items():
            if re.search(pattern, text):
                return intent
        
        return 'other'
    
    def extract_lead_info(self, conversation_history: list, user_message: str) -> Dict[str, Any]:
        """Extract lead qualification data from conversation."""
        extracted = {
            'name': None,
            'email': None,
            'phone': None,
            'buyer_type': None,
            'property_preference': None,
            'budget': None,
            'timeline': None,
        }
        
        # Simple pattern matching for demo (in production, use NLP/NER)
        text = user_message.lower()
        
        # Phone number pattern
        phone_pattern = r'\+?1?\d{9,15}'
        phone_match = re.search(phone_pattern, user_message)
        if phone_match:
            extracted['phone'] = phone_match.group(0)
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, user_message)
        if email_match:
            extracted['email'] = email_match.group(0)
        
        # Buyer type detection
        if any(k in text for k in ['buying', 'buy', 'purchase', 'owner']):
            extracted['buyer_type'] = 'buyer'
        elif any(k in text for k in ['renting', 'rent', 'lease', 'tenant']):
            extracted['buyer_type'] = 'renter'
        elif any(k in text for k in ['invest', 'investment', 'roi', 'return']):
            extracted['buyer_type'] = 'investor'
        
        # Property type detection
        property_types = {
            'apartment': ['apt', 'apartment', 'flat', '1bhk', '2bhk', '3bhk'],
            'villa': ['villa', 'bungalow'],
            'house': ['house', 'independent'],
            'plot': ['plot', 'land', 'vacant'],
            'commercial': ['commercial', 'office', 'retail', 'shop'],
        }
        for prop_type, keywords in property_types.items():
            if any(k in text for k in keywords):
                extracted['property_preference'] = prop_type
                break
        
        # Budget extraction (simple pattern)
        budget_pattern = r'(?:budget|price|range|rs|₹)\s*(?:of|is)?\s*(?:around|approx|upto|up to)?\s*(\d+(?:,\d+)?)\s*(?:to|-)?\s*(?:(\d+(?:,\d+)?))?\s*(?:lakh|cr|crore|lac)'
        budget_match = re.search(budget_pattern, text)
        if budget_match:
            extracted['budget'] = {
                'min': budget_match.group(1),
                'max': budget_match.group(2),
            }
        
        # Timeline detection
        timeline_keywords = {
            'immediate': ['urgent', 'asap', 'immediately', 'today', 'soon', 'week'],
            'soon': ['month', '2-3 months', 'next month'],
            'later': ['later', 'months', '3-6 months', 'year'],
            'flexible': ['flexible', 'exploring', 'just looking'],
        }
        for timeline, keywords in timeline_keywords.items():
            if any(k in text for k in keywords):
                extracted['timeline'] = timeline
                break
        
        return extracted
    
    def get_qualifying_questions(self, extracted_info: Dict[str, Any]) -> Optional[str]:
        """Generate qualifying questions based on missing info."""
        if not extracted_info.get('property_preference'):
            return "What type of property are you interested in? (Apartment, Villa, House, Plot, or Commercial space?)"
        
        if not extracted_info.get('budget'):
            return "What's your budget range? (Helps me find suitable properties)"
        
        if not extracted_info.get('timeline'):
            return "When are you looking to make a purchase or move? (Immediately, Soon, or Later?)"
        
        if not extracted_info.get('buyer_type'):
            return "Are you looking to buy, rent, or invest?"
        
        return None
    
    def generate_ai_response(
        self,
        user_message: str,
        conversation_context: Dict[str, Any],
        conversation_history: list,
        is_lead_qualified: bool = False,
    ) -> Dict[str, Any]:
        """Generate AI response using OpenAI API with conversation history."""
        
        if not self.openai_api_key:
            return self._generate_fallback_response(user_message, conversation_context)
        
        try:
            # Build messages for API
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt(conversation_context, is_lead_qualified),
                }
            ]
            
            # Add conversation history (last 5 messages to save tokens)
            for msg in conversation_history[-5:]:
                messages.append({
                    "role": "assistant" if msg['sender'] == 'bot' else "user",
                    "content": msg['message'],
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message,
            })
            
            # Call OpenAI API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            bot_reply = data["choices"][0]["message"]["content"].strip()
            
            return {
                'success': True,
                'message': bot_reply,
                'intent': self.detect_intent(user_message),
            }
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(user_message, conversation_context)
    
    def _generate_fallback_response(
        self,
        user_message: str,
        conversation_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback rule-based response when API is unavailable."""
        
        text = (user_message or "").strip().lower()
        intent = self.detect_intent(user_message)
        
        # Contextual fallback responses
        responses = {
            'pricing': "For exact pricing and negotiation details, let me connect you with our agent. What's the best way to reach you?",
            'schedule': "Great! I'd love to help schedule a tour. What's your preferred date and time?",
            'property_type': "I can help you find the perfect property! What's your budget range?",
            'location': "Location is crucial! Which cities or areas are you interested in?",
            'document': "Our agent can provide all necessary documentation. Shall I schedule a call to discuss?",
            'other': "Thanks for your message! To better assist you, could you tell me what type of property you're looking for?",
        }
        
        return {
            'success': True,
            'message': responses.get(intent, responses['other']),
            'intent': intent,
        }
    
    def should_qualify_lead(self, extracted_info: Dict[str, Any]) -> bool:
        """Determine if enough info collected to create lead."""
        required_fields = ['email', 'phone', 'property_preference', 'budget', 'timeline']
        filled = sum(1 for field in required_fields if extracted_info.get(field))
        return filled >= 3  # At least 3 fields filled


class SchedulingService:
    """Handle tour/appointment scheduling."""
    
    @staticmethod
    def get_available_slots(property_id: int, days_ahead: int = 7) -> list:
        """Get available tour slots (mock implementation)."""
        slots = []
        start_date = datetime.now().date()
        
        for day_offset in range(days_ahead):
            current_date = start_date + timedelta(days=day_offset)
            # Skip weekends and Sundays
            if current_date.weekday() in [5, 6]:
                continue
            
            # Generate 4 slots per day: 10:00, 12:00, 14:00, 16:00
            for hour in [10, 12, 14, 16]:
                slot_datetime = datetime.combine(current_date, datetime.min.time()).replace(hour=hour)
                slots.append({
                    'datetime': slot_datetime.isoformat(),
                    'display': slot_datetime.strftime('%a, %b %d at %I:%M %p'),
                })
        
        return slots
    
    @staticmethod
    def suggest_next_steps(lead_info: Dict[str, Any], property_available: bool = True) -> str:
        """Suggest next steps based on lead info."""
        steps = []
        
        if property_available:
            steps.append("📅 Schedule a property tour")
        
        if lead_info.get('budget'):
            steps.append("💰 Discuss financing options")
        
        steps.append("👨‍💼 Connect with a dedicated agent")
        
        return " | ".join(steps)


# Backwards compatibility - keep original function
def chatbot_reply(user_message: str, property_title: str | None = None) -> str:
    """Legacy function for backwards compatibility."""
    service = ChatbotAIService()
    context = {
        'visitor_name': 'Guest',
        'property': property_title or 'general inquiry',
    }
    result = service.generate_ai_response(user_message, context, [])
    return result['message']
