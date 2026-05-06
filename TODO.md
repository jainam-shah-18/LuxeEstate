# Telegram Chatbot Fix - Approved Plan Breakdown

## Step 1: [PENDING] Fix telegram_bot.py core issues
- Add missing `import re`
- Wrap property search in try/except with fallback
- Fix send_message HTML handling (better escaping + plain fallback)
- Add dedicated phone number handler

## Step 2: [PENDING] Enhance chatbot_service.py search
- Improve _query_from_lead price parsing ("15 crore" → 150000000)
- Fuzzy city matching for "north goa"
- Ensure deterministic fallback works when NIM fails

## Step 3: [PENDING] Seed DB with test properties
```python
python manage.py shell
Property.objects.create(title="Test Villa North Goa", city="North Goa", property_type="villa", price=120000000, ...)
```

## Step 4: [PENDING] Test end-to-end
- Restart server
- Test "/start" → "villa in north goa under 15 crore" → listings/info (NO ERROR)
- Test phone number → lead save + confirmation

## Step 5: [PENDING] Production hardening
- Add more logging
- Rate limiting
- Webhook verification

