#!/usr/bin/env python
"""
Verify Telegram + LuxeAI MCP Integration Setup

Run this script to test all components:
  python verify_telegram_setup.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LuxeEstate.settings')
django.setup()

from django.conf import settings
from properties.models import TelegramUser, Lead, Property
from properties.chatbot_service import LuxeChatbot
from properties.telegram_integration import get_or_create_telegram_session


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_settings():
    """Test if Telegram settings are configured"""
    print_header("1. TELEGRAM SETTINGS CHECK")
    
    tests = {
        'TELEGRAM_BOT_TOKEN': settings.TELEGRAM_BOT_TOKEN,
        'TELEGRAM_BOT_USERNAME': settings.TELEGRAM_BOT_USERNAME,
        'TELEGRAM_WEBHOOK_SECRET': settings.TELEGRAM_WEBHOOK_SECRET,
    }
    
    all_pass = True
    for key, value in tests.items():
        status = "✅ SET" if value else "❌ NOT SET"
        print(f"{key:30} → {status}")
        if not value:
            all_pass = False
    
    return all_pass


def test_database():
    """Test if TelegramUser model exists"""
    print_header("2. DATABASE MODEL CHECK")
    
    try:
        # Check if TelegramUser table exists
        count = TelegramUser.objects.count()
        print(f"✅ TelegramUser table exists")
        print(f"   Current records: {count}")
        
        # Check if Lead model is accessible
        lead_count = Lead.objects.count()
        print(f"✅ Lead table exists")
        print(f"   Current records: {lead_count}")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        print(f"   Run: python manage.py migrate properties")
        return False


def test_chatbot():
    """Test if LuxeChatbot works"""
    print_header("3. LUXECHATBOT CHECK")
    
    try:
        bot = LuxeChatbot()
        print(f"✅ LuxeChatbot initialized")
        
        # Test simple message
        result = bot.process_message("Hi, how are you?")
        if result and ('response' in result or 'message' in result):
            print(f"✅ Chatbot responds to messages")
            response_text = result.get('response') or result.get('message', '')
            print(f"   Sample response: {response_text[:100]}...")
            return True
        else:
            print(f"⚠️  Chatbot returned unexpected format")
            return False
    
    except Exception as e:
        print(f"❌ Chatbot error: {e}")
        print(f"   Check NVIDIA NIM configuration")
        return False


def test_telegram_session():
    """Test Telegram session creation"""
    print_header("4. TELEGRAM SESSION CHECK")
    
    try:
        # Create test session
        test_telegram_id = 999999999
        
        # Try to get or create
        session = get_or_create_telegram_session(
            telegram_id=test_telegram_id,
            telegram_data={
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser'
            }
        )
        
        print(f"✅ TelegramSession created")
        print(f"   Telegram ID: {test_telegram_id}")
        print(f"   Session ID: {session.user_obj.session_id}")
        
        # Test message processing
        response = session.process_message("Looking for 2BHK in Bangalore")
        if response and 'text' in response:
            print(f"✅ Session processes messages")
            print(f"   Intent detected: {response.get('intent')}")
            return True
        
    except Exception as e:
        print(f"❌ Session error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_properties():
    """Test if Property data exists"""
    print_header("5. PROPERTY DATABASE CHECK")
    
    try:
        total = Property.objects.filter(is_active=True).count()
        print(f"✅ Property table exists")
        print(f"   Active properties: {total}")
        
        if total == 0:
            print(f"⚠️  No active properties found")
            print(f"   Add properties for testing property search in Telegram")
        
        # Check by city
        cities = Property.objects.filter(is_active=True).values_list('city', flat=True).distinct()
        if cities:
            print(f"✅ Properties found in cities: {', '.join(cities[:5])}")
        
        return True
    
    except Exception as e:
        print(f"❌ Property check error: {e}")
        return False


def test_migrations():
    """Check if TelegramUser migration is applied"""
    print_header("6. MIGRATION CHECK")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Get migration status
        out = StringIO()
        call_command('showmigrations', 'properties', stdout=out)
        output = out.getvalue()
        
        if '0007_telegramuser' in output:
            if '[X]' in output.split('0007_telegramuser')[0].split('\n')[-1]:
                print(f"✅ Migration 0007_telegramuser applied")
                return True
            else:
                print(f"⚠️  Migration 0007_telegramuser not applied")
                print(f"   Run: python manage.py migrate properties")
                return False
        else:
            print(f"⚠️  Migration 0007_telegramuser not found")
            return False
    
    except Exception as e:
        print(f"❌ Migration check error: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test:30} → {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED! Your Telegram + LuxeAI setup is ready!")
        print("\nNext steps:")
        print("1. Set your Telegram webhook:")
        print(f"   curl -X POST https://api.telegram.org/bot{{BOT_TOKEN}}/setWebhook \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"url\": \"https://yourdomain.com/properties/telegram/webhook/\"}}'")
        print("\n2. Visit your web app and click 'Connect with Telegram' button")
        print("\n3. Start chatting with your Telegram bot!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        print("Refer to TELEGRAM_MCP_SETUP.md for troubleshooting")
    
    return passed == total


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  LUXEESTATE TELEGRAM + MCP INTEGRATION VERIFICATION")
    print("="*60)
    
    results = {
        '1. Telegram Settings': test_settings(),
        '2. Database Models': test_database(),
        '3. LuxeChatbot': test_chatbot(),
        '4. Telegram Session': test_telegram_session(),
        '5. Property Data': test_properties(),
        '6. Migrations': test_migrations(),
    }
    
    all_pass = print_summary(results)
    
    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
