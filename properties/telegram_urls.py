from django.urls import path
from .telegram_views import telegram_webhook, telegram_setup

urlpatterns = [
    path('webhook/', telegram_webhook, name='telegram_webhook'),
    path('setup/', telegram_setup, name='telegram_setup'),
]