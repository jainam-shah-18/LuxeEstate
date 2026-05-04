# LuxeEstate × Telegram Bot + MCP Integration Guide

## What this gives you

```
Telegram User
    │  types "Show me 2BHK villas in Ahmedabad under 1Cr"
    ▼
Telegram Bot (@YourLuxeBot)
    │  POST /api/telegram/webhook/
    ▼
Django  (telegram_views.py)
    │  calls LuxeChatbot.process_message()
    ▼
LuxeChatbot  (your existing chatbot_service.py)
    │  queries Property DB  +  NVIDIA NIM llama-3.1-8b
    ▼
Telegram Bot API  →  User sees reply + property cards + "Book a Call" button
```

Plus an optional **MCP Server** so Claude Desktop can call your live property
DB and chatbot as tools.

---

## Step 1 — Create your Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot` and follow prompts
3. Copy the **API token** (looks like `7123456789:AAF...`)
4. Optionally send `/setdescription` and `/setuserpic` to brand it

---

## Step 2 — Add environment variables

In `LuxeEstate_updated/.env` add:

```env
# Telegram
TELEGRAM_BOT_TOKEN=7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_BOT_USERNAME=LuxeEstateAIBot      # your bot's @username (no @)
TELEGRAM_WEBHOOK_SECRET=any-random-string  # optional extra security
```

---

## Step 3 — Copy the new files into your project

```
LuxeEstate_updated/
├── telegram_bot/               ← NEW folder
│   ├── __init__.py
│   ├── apps.py
│   ├── telegram_bot.py         ← core bot logic
│   ├── telegram_views.py       ← Django webhook view
│   ├── telegram_urls.py        ← URL config
│   └── static/
│       └── telegram_connect.js ← chatbot "Connect" button
└── mcp_server.py               ← NEW — MCP server (optional)
```

---

## Step 4 — Register the app and URLs

**`LuxeEstate/settings.py`** — add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'telegram_bot',   # ← add this
]

# Add these two lines anywhere in settings.py:
TELEGRAM_BOT_TOKEN    = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', '')
TELEGRAM_WEBHOOK_SECRET = os.environ.get('TELEGRAM_WEBHOOK_SECRET', '')

# Pass bot username to all templates:
# (add to your existing TEMPLATES > OPTIONS > context_processors, or use a context processor)
```

**`LuxeEstate/urls.py`** — add one line:
```python
from django.urls import path, include

urlpatterns = [
    ...
    path('api/telegram/', include('telegram_bot.telegram_urls')),  # ← add
]
```

---

## Step 5 — Add the "Connect with Telegram" button to your chatbot widget

In the template that renders your LuxeAI chatbot (e.g. `base.html`), add
**two lines**:

```html
<!-- 1. Tell the script your bot username -->
<script>window.LUXE_TELEGRAM_BOT_USERNAME = "{{ TELEGRAM_BOT_USERNAME }}";</script>

<!-- 2. Inject the button (just before </body>) -->
<script src="{% static 'telegram_connect.js' %}"></script>
```

The script auto-detects your chatbot header (`.chatbot-header`, `.chat-header`, etc.)
and appends a blue Telegram button. No CSS changes needed.

---

## Step 6 — Register the webhook (once, after deploying)

Your server must have a **public HTTPS URL**. Then visit:

```
https://yourdomain.com/api/telegram/setup/?action=register&url=https://yourdomain.com/api/telegram/webhook/
```

(Only accessible to Django staff/admin users.)

Or run from terminal:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://yourdomain.com/api/telegram/webhook/"
```

Verify it worked:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## Step 7 — Test in Telegram

1. Open Telegram → search your bot by @username
2. Send `/start`  — should greet you
3. Send: `Show me 3BHK apartments in Ahmedabad under 2 crore`
4. The bot queries your live DB + NIM and replies with property cards
5. Tap **📞 Book a Call** on any card — bot logs an appointment

---

## Step 8 (Optional) — MCP Server for Claude Desktop

Install the MCP package:
```bash
pip install mcp
```

Add to `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "luxeestate": {
      "command": "python",
      "args": ["/full/path/to/LuxeEstate_updated/mcp_server.py"],
      "env": {
        "DJANGO_SETTINGS_MODULE": "LuxeEstate.settings",
        "PYTHONPATH": "/full/path/to/LuxeEstate_updated"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see three new tools:
- `search_properties` — filter live listings
- `ask_luxe_ai` — full NIM-powered chatbot
- `book_call` — create leads/appointments

---

## How it all connects

```
┌─────────────────────────────────────────────────────────────┐
│                    LuxeEstate Django App                     │
│                                                              │
│  properties/chatbot_service.py  (LuxeChatbot)                │
│       │ calls NVIDIA NIM (llama-3.1-8b)                      │
│       │ queries Property, Lead, Appointment models           │
│       ▼                                                      │
│  /api/chatbot/          ← existing web chatbot               │
│  /api/telegram/webhook/ ← NEW Telegram bridge                │
│  mcp_server.py          ← NEW MCP tools                      │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
    Web Browser          Telegram App          Claude Desktop
   (LuxeAI widget)      (@YourLuxeBot)        (MCP tools)
```

The **same chatbot brain** (chatbot_service.py + NVIDIA NIM) powers all three
interfaces — no logic is duplicated.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't reply | Check webhook is registered: `getWebhookInfo`. Check Django logs. |
| `TELEGRAM_BOT_TOKEN` not found | Confirm `.env` is loaded by `python-dotenv` in `settings.py` |
| Webhook returns 403 | `TELEGRAM_WEBHOOK_SECRET` mismatch — clear it or set matching value |
| "Connect" button not visible | Check your chatbot header CSS class and adjust selector in `telegram_connect.js` line 30 |
| MCP tools not appearing | Restart Claude Desktop after editing config. Check `PYTHONPATH` is correct. |
| Property cards show no image | `send_property_card` sends text only; add `sendPhoto` call if you want images |