"""
Telegram Bot Handler for LuxeEstate

This module provides handlers for Telegram webhook updates and callbacks.
It integrates with the LuxeAI chatbot for property searches and conversations.
"""

import logging
import requests
import sys
import html
import re
from django.conf import settings
from .telegram_integration import get_or_create_telegram_session

logger = logging.getLogger(__name__)

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text, parse_mode='HTML', reply_markup=None):
    """Send a message to Telegram user with retry logic and proper encoding"""
    if not text or not chat_id:
        logger.error(f"[ERROR] Invalid message parameters: chat_id={chat_id}, text_len={len(text or '')}")
        print(f"[SEND_MESSAGE ERROR] Invalid params: chat_id={chat_id}, text_len={len(text or '')}", file=sys.stderr, flush=True)
        return False
    
    # HTML sanitization with fallback
    if parse_mode == 'HTML':
        try:
            text = html.escape(str(text))
        except Exception:
            parse_mode = None
    else:
        text = str(text)
    
    # Truncate message (Telegram limit is 4096)
    if len(text) > 4000:
        text = text[:3990] + "..."
    
    url = f"{BASE_URL}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    logger.info(f"[SEND] To {chat_id}: {text[:80] if len(text) > 80 else text}")
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            logger.info(f"[SEND OK] {chat_id}")
            return True
        else:
            logger.warning(f"[SEND FAIL {response.status_code}] {response.text[:100]}")
            # Final plain-text attempt
            payload.pop("parse_mode", None)
            response2 = requests.post(url, json=payload, timeout=10)
            if response2.status_code == 200:
                logger.info(f"[SEND PLAIN OK] {chat_id}")
                return True
    except Exception as e:
        logger.error(f"[SEND EXC] {chat_id}: {e}")
    
    logger.error(f"[SEND TOTAL FAIL] {chat_id}")
    return False


def send_property_carousel(chat_id, properties):
    """Send a carousel of properties to user"""
    if not properties:
        send_message(chat_id, "Sorry, no properties found matching your criteria.")
        return
    
    for prop in properties[:5]:  # Max 5 properties
        formatted = f"""
PROPERTY: {prop.title}
Location: {prop.location}, {prop.city}
Price: Rs {prop.price:,.0f}
Bedrooms: {prop.bedrooms or 'N/A'} | Bathrooms: {prop.bathrooms or 'N/A'}
Area: {prop.area_sqft or 'N/A'} Sq.Ft.
Rating: {prop.rating:.1f}/5

View Full Details: {settings.SITE_URL}/property/{prop.id}/
        """
        send_message(chat_id, formatted.strip())


def handle_update(update):
    """
    Handles incoming Telegram updates and routes through LuxeAI chatbot
    
    Args:
        update: Telegram update dictionary containing message data
    """
    print(f"[STEP 1] handle_update CALLED!", file=sys.stderr, flush=True)
    logger.warning("[INFO] handle_update called with update")
    
    chat_id = None
    try:
        print(f"[STEP 2] About to extract message", file=sys.stderr, flush=True)
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        user = message.get("from", {})
        user_text = message.get("text", "").strip()
        print(f"[STEP 3] Extracted: chat_id={chat_id}, user_text={user_text[:30]}", file=sys.stderr, flush=True)
        logger.warning(f"[MSG] Received message from chat_id={chat_id}, text='{user_text[:50]}'")
        
        if not chat_id or not user_text:
            print(f"[STEP EARLY RETURN] Missing chat_id or user_text", file=sys.stderr, flush=True)
            logger.warning(f"[WARN] Missing chat_id ({chat_id}) or user_text ({len(user_text) if user_text else 0})")
            return
        
        print(f"[STEP 4] About to create session", file=sys.stderr, flush=True)
        # Get or create Telegram session
        telegram_id = user.get("id")
        telegram_data = {
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name'),
            'username': user.get('username'),
        }
        
        session = get_or_create_telegram_session(telegram_id, telegram_data)
        print(f"[STEP 5] Session created", file=sys.stderr, flush=True)
        logger.warning(f"[OK] Session created for telegram_id={telegram_id}")
        
        # Handle /start command
        if user_text == "/start":
            reply = (
                "Welcome to LuxeEstate AI!\n\n"
                "I can help you:\n"
                "* Find luxury properties\n"
                "* Get pricing information\n"
                "* Schedule property visits\n"
                "* Answer real estate questions\n"
                "* Connect with our agents\n\n"
                "Just type your property requirements or questions!"
            )
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': 'Search Properties', 'callback_data': 'search_start'},
                        {'text': 'Chat with Agent', 'callback_data': 'chat_agent'},
                    ],
                    [
                        {'text': 'Book a Call', 'callback_data': 'book_call'},
                        {'text': 'FAQ', 'callback_data': 'show_faq'},
                    ]
                ]
            }
            send_message(chat_id, reply, reply_markup=keyboard)
            return
        
        # Handle /help command
        if user_text == "/help":
            reply = (
                "How to use LuxeEstate AI:\n\n"
                "Natural Conversation:\n"
                "Just ask me about properties! Examples:\n"
                "* 'Show me 2BHK apartments in Bangalore'\n"
                "* 'What's the budget for villas in Mumbai?'\n"
                "* 'I want to rent a house in Pune'\n\n"
                "Available Commands:\n"
                "/start - Restart\n"
                "/help - This message\n"
                "/search - Advanced search\n"
                "/mycalls - View my scheduled calls\n"
                "/myproperties - My favorite properties\n"
            )
            send_message(chat_id, reply)
            return
        
        # Handle common greetings
        greetings = ['hi', 'hello', 'hey', 'namaste', 'greetings', 'howdy', 'hola', 'bonjour']
        if user_text.lower() in greetings:
            reply = (
                "Hi there! Welcome to LuxeEstate AI!\n\n"
                "I can help you find the perfect property. What are you looking for?\n\n"
                "Examples of what you can ask:\n"
                "* 2BHK apartment in Bangalore\n"
                "* Villas in Mumbai under 1 crore\n"
                "* House for rent in Pune\n"
                "* Properties in Ahmedabad\n\n"
                "Or use /help for more information."
            )
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': 'Search Properties', 'callback_data': 'search_start'},
                        {'text': 'Chat with Agent', 'callback_data': 'chat_agent'},
                    ]
                ]
            }
            send_message(chat_id, reply, reply_markup=keyboard)
            return
        
        # Process regular message through LuxeAI chatbot
        logger.warning(f"[CHATBOT] Processing message through chatbot: '{user_text[:50]}'")
        print(f"[STEP 6] About to call session.process_message", file=sys.stderr, flush=True)
        try:
            response_data = session.process_message(user_text)
            print(f"[STEP 7] Got response_data: {response_data is not None}", file=sys.stderr, flush=True)
            response_text = response_data.get('text', "I didn't quite understand. Could you please rephrase?")
            
            # Clean response text from any prefixes
            response_text = re.sub(r'^\[.*?\]\s*[^:\n]+:\s*', '', response_text, flags=re.MULTILINE).strip()
            
            logger.info(f"[BOT FIX] Cleaned response ({len(response_text)} chars): {response_text[:100]}")
            print(f"[BOT FIX] Response cleaned & ready, len={len(response_text)}", file=sys.stderr, flush=True)
        except Exception as e:
            logger.error(f"[ERROR] Error processing chatbot message: {e}", exc_info=True)
            print(f"[STEP ERROR] Exception in process_message: {str(e)}", file=sys.stderr, flush=True)
            response_text = (
                "Our system encountered an issue processing your request. "
                "An agent will contact you shortly to assist!"
            )
            send_message(chat_id, response_text)
            return
        
        # Check if user searched for properties
        if response_data.get('intent') in ['buy', 'rent', 'invest']:
            lead_data = response_data.get('lead_data', {})
            
            # Try to search properties if we have enough criteria
            if lead_data.get('location') and (lead_data.get('intent') or user_text):
                try:
                    properties = session.search_properties({
                        'city': lead_data.get('location'),
                        'property_type': lead_data.get('property_type'),
                        'bedrooms': int(lead_data.get('bhk', '0').split()[0]) if lead_data.get('bhk') else None,
                        'listing_type': 'sale' if lead_data.get('intent') == 'buy' else 'rent',
                    })
                    
                    if properties:
                        response_text += "\n\nHere are some matching properties:\n"
                        send_message(chat_id, response_text)
                        send_property_carousel(chat_id, properties)
                        return
                except Exception as e:
                    logger.error(f"Error searching properties: {e}")
        
        # Add keyboard for qualified leads
        keyboard = response_data.get('keyboard')
        send_message(chat_id, response_text, reply_markup=keyboard)
        
        # If we have a hot lead, notify about booking a call
        if response_data.get('has_qualified_lead'):
            followup = (
                "Great! I have all the information needed!\n\n"
                "Would you like to:\n"
                "1) Schedule a callback from our agent?\n"
                "2) Continue chatting with me?"
            )
            keyboard = {
                'inline_keyboard': [
                    [
                        {'text': 'Book Call', 'callback_data': 'book_call'},
                        {'text': 'Continue Chat', 'callback_data': 'continue_chat'},
                    ]
                ]
            }
            send_message(chat_id, followup, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"[ERROR] Telegram Handler Error: {e}", exc_info=True)
        if chat_id:
            send_message(chat_id, "Sorry, something went wrong. Please try again or contact support.", parse_mode='Markdown')


def handle_callback_query(callback_query):
    """
    Handle Telegram callback queries (button clicks)
    
    Args:
        callback_query: Telegram callback query dictionary
    """
    try:
        callback_id = callback_query.get('id')
        chat_id = callback_query['from'].get('id')
        data = callback_query.get('data', '')
        
        session = get_or_create_telegram_session(chat_id)
        
        if data == 'search_start':
            reply = "Tell me what property you're looking for!\n\nFor example:\n* 2BHK apartment in Bangalore\n* Villa in Mumbai under 1 crore\n* House for rent in Pune"
            send_message(chat_id, reply)
        
        elif data == 'book_call':
            reply = (
                "Book a Call with Our Agent\n\n"
                "Please provide your contact number:\n"
                "Just reply with your phone number (10 digits)"
            )
            send_message(chat_id, reply)
        
        elif data == 'chat_agent':
            reply = "You will be connected with an agent shortly. Please wait..."
            send_message(chat_id, reply)
        
        elif data == 'show_faq':
            reply = (
                "Frequently Asked Questions:\n\n"
                "Q: How do I schedule a site visit?\n"
                "A: Just ask me to schedule a visit for a property, and I'll help!\n\n"
                "Q: What's the average property price?\n"
                "A: It varies by location. Tell me your city and I can give you details!\n\n"
                "Q: Do you have rental properties?\n"
                "A: Yes! Just tell me you want to rent instead of buy."
            )
            send_message(chat_id, reply)
        
        # Answer callback query to remove loading state
        url = f"{BASE_URL}/answerCallbackQuery"
        requests.post(url, json={"callback_query_id": callback_id}, timeout=5)
    
    except Exception as e:
        logger.error(f"Error handling callback query: {e}", exc_info=True)
