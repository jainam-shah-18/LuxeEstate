import requests
from django.conf import settings

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    requests.post(url, json=payload)


def handle_update(update):
    """
    Handles incoming Telegram updates
    """

    try:
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")

        user_text = message.get("text", "")

        if not chat_id:
            return

        # Basic Replies
        if user_text == "/start":
            reply = (
                "🏡 Welcome to LuxeEstate AI!\n\n"
                "I can help you:\n"
                "• Find luxury properties\n"
                "• Connect with agents\n"
                "• Schedule visits\n"
                "• Answer real estate questions\n\n"
                "Type anything to begin ✨"
            )

        elif "hello" in user_text.lower() or "hi" in user_text.lower():
            reply = "👋 Hello! Welcome to LuxeEstate AI."

        else:
            reply = f"✨ You said: {user_text}"

        send_message(chat_id, reply)

    except Exception as e:
        print("Telegram Bot Error:", e)