from django.core.management.base import BaseCommand
from properties.chatbot_service import chatbot


class Command(BaseCommand):
    help = 'Send automated follow-ups for leads and appointments'

    def handle(self, *args, **options):
        self.stdout.write('Sending automated follow-ups...')
        chatbot.send_automated_followups()
        self.stdout.write(self.style.SUCCESS('Automated follow-ups completed.'))