#!/usr/bin/env python
"""Test Telegram bot setup and connectivity"""

import os
import django
import requests
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LuxeEstate.settings')
django.setup()

print("=" * 60)
print("Telegram Bot Configuration Check")
print("=" * 60)

# Check environment variables
bot_token = settings.TELEGRAM_BOT_TOKEN
bot_username = settings.TELEGRAM_BOT_USERNAME
webhook_secret = settings.TELEGRAM_WEBHOOK_SECRET

print(f"\n✓ TELEGRAM_BOT_TOKEN: {'***' + bot_token[-10:] if bot_token else '❌ NOT SET'}")
print(f"✓ TELEGRAM_BOT_USERNAME: {bot_username or '❌ NOT SET'}")
print(f"✓ TELEGRAM_WEBHOOK_SECRET: {'***' + webhook_secret[-5:] if webhook_secret else '❌ NOT SET'}")

if not bot_token:
    print("\n❌ ERROR: TELEGRAM_BOT_TOKEN is not set in .env file!")
    exit(1)

# Test API connectivity
print("\n" + "=" * 60)
print("Testing Telegram API Connectivity")
print("=" * 60)

url = f"https://api.telegram.org/bot{bot_token}/getMe"
try:
    response = requests.get(url, timeout=5)
    data = response.json()
    
    if data.get('ok'):
        bot_info = data.get('result', {})
        print(f"\n✅ Bot is active and responding!")
        print(f"   Bot ID: {bot_info.get('id')}")
        print(f"   Bot Username: @{bot_info.get('username')}")
        print(f"   Bot Name: {bot_info.get('first_name')}")
    else:
        print(f"\n❌ Telegram API error: {data.get('description')}")
        exit(1)
except Exception as e:
    print(f"\n❌ Failed to connect to Telegram API: {e}")
    exit(1)

# Check webhook status
print("\n" + "=" * 60)
print("Checking Webhook Status")
print("=" * 60)

url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
try:
    response = requests.get(url, timeout=5)
    data = response.json()
    
    if data.get('ok'):
        webhook_info = data.get('result', {})
        if webhook_info.get('url'):
            print(f"\n✅ Webhook registered!")
            print(f"   URL: {webhook_info.get('url')}")
            print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
        else:
            print(f"\n⚠️  No webhook registered")
    else:
        print(f"\n❌ Error checking webhook: {data.get('description')}")
except Exception as e:
    print(f"\n❌ Failed to check webhook: {e}")
    exit(1)

# Check database models
print("\n" + "=" * 60)
print("Checking Database Models")
print("=" * 60)

try:
    from properties.models import TelegramUser
    user_count = TelegramUser.objects.count()
    print(f"\n✅ TelegramUser table exists")
    print(f"   Total users: {user_count}")
except Exception as e:
    print(f"\n❌ Error accessing TelegramUser: {e}")

print("\n" + "=" * 60)
print("All checks completed!")
print("=" * 60)
