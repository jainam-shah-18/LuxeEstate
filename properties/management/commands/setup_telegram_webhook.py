"""
Management command to set up or manage Telegram webhook

Usage:
    python manage.py setup_telegram_webhook --action register --url https://yourdomain.com/api/telegram/webhook/
    python manage.py setup_telegram_webhook --action info
    python manage.py setup_telegram_webhook --action delete
"""

import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup and manage Telegram webhook'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            default='info',
            help='Action: register, unregister, or info (default: info)'
        )
        parser.add_argument(
            '--url',
            type=str,
            default='',
            help='Webhook URL (required for register action)'
        )

    def handle(self, *args, **options):
        bot_token = settings.TELEGRAM_BOT_TOKEN
        
        if not bot_token:
            raise CommandError('TELEGRAM_BOT_TOKEN not configured in .env')
        
        action = options['action'].lower()
        webhook_url = options['url']
        
        if action == 'register':
            if not webhook_url:
                raise CommandError('--url is required for register action')
            self.register_webhook(bot_token, webhook_url)
        
        elif action == 'unregister' or action == 'delete':
            self.delete_webhook(bot_token)
        
        elif action == 'info':
            self.get_webhook_info(bot_token)
        
        else:
            raise CommandError(f'Invalid action: {action}. Use: register, unregister, or info')
    
    def register_webhook(self, bot_token, webhook_url):
        """Register webhook with Telegram"""
        self.stdout.write(self.style.WARNING(f'Registering webhook: {webhook_url}'))
        
        try:
            api_url = f'https://api.telegram.org/bot{bot_token}/setWebhook'
            response = requests.post(api_url, json={"url": webhook_url}, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook registered successfully!')
                )
                self.stdout.write(f"Response: {result.get('result', {})}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed: {result.get('description', 'Unknown error')}")
                )
                raise CommandError(result.get('description', 'Unknown error'))
        
        except Exception as e:
            raise CommandError(f'Error: {str(e)}')
    
    def delete_webhook(self, bot_token):
        """Delete/unregister webhook from Telegram"""
        self.stdout.write(self.style.WARNING('Deleting webhook...'))
        
        try:
            api_url = f'https://api.telegram.org/bot{bot_token}/deleteWebhook'
            response = requests.post(api_url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook deleted successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed: {result.get('description', 'Unknown error')}")
                )
                raise CommandError(result.get('description', 'Unknown error'))
        
        except Exception as e:
            raise CommandError(f'Error: {str(e)}')
    
    def get_webhook_info(self, bot_token):
        """Get webhook information from Telegram"""
        self.stdout.write('Checking webhook status...')
        
        try:
            api_url = f'https://api.telegram.org/bot{bot_token}/getWebhookInfo'
            response = requests.get(api_url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                info = result.get('result', {})
                
                self.stdout.write(self.style.SUCCESS('📋 Webhook Info:'))
                self.stdout.write(f"  URL: {info.get('url', 'Not set')}")
                self.stdout.write(f"  Has Custom Certificate: {info.get('has_custom_certificate', False)}")
                self.stdout.write(f"  Pending Update Count: {info.get('pending_update_count', 0)}")
                
                if info.get('pending_update_count', 0) > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  {info['pending_update_count']} pending updates waiting to be processed"
                        )
                    )
                else:
                    self.stdout.write(self.style.SUCCESS('✅ All updates have been processed'))
                
                if info.get('last_error_message'):
                    self.stdout.write(
                        self.style.ERROR(f"Last Error: {info['last_error_message']}")
                    )
            else:
                raise CommandError(result.get('description', 'Unknown error'))
        
        except Exception as e:
            raise CommandError(f'Error: {str(e)}')
