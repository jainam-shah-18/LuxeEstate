"""
Context processors for LuxeEstate templates

Provides global context variables for all templates
"""

from django.conf import settings


def telegram_bot_context(request):
    """Add Telegram bot information to all templates"""
    return {
        'telegram_bot_username': settings.TELEGRAM_BOT_USERNAME or '',
    }


def site_settings_context(request):
    """Add site settings to all templates"""
    return {
        'site_name': 'LuxeEstate',
        'base_url': settings.SITE_URL,
    }
