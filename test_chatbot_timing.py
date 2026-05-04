#!/usr/bin/env python
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LuxeEstate.settings')
django.setup()

from properties.chatbot_service import chatbot

print("=" * 60)
print("Testing Chatbot Response Times")
print("=" * 60)

test_messages = [
    "Hello",
    "Looking for 2BHK in Bangalore",
    "What's the price range?",
    "Schedule a site visit for tomorrow",
]

for msg in test_messages:
    print(f"\nMessage: {msg}")
    start = time.time()
    try:
        result = chatbot.process_message(msg)
        elapsed = time.time() - start
        response = result.get('message', '')[:80]
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Response: {response}...")
        print(f"  Model: {result.get('model', 'N/A')}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR after {elapsed:.2f}s: {str(e)[:100]}")

print("\n" + "=" * 60)
