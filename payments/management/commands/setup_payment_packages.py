from django.core.management.base import BaseCommand
from payments.models import PaymentPackage


class Command(BaseCommand):
    help = 'Setup payment packages for property promotion'

    def handle(self, *args, **options):
        deactivated_count = PaymentPackage.objects.filter(is_active=True).update(is_active=False)
        self.stdout.write(self.style.WARNING("Promotional packages are disabled globally."))
        self.stdout.write(f"Deactivated {deactivated_count} active package(s).")
