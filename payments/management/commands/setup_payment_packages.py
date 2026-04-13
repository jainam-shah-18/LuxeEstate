from django.core.management.base import BaseCommand
from payments.models import PaymentPackage


class Command(BaseCommand):
    help = 'Setup payment packages for property promotion'

    def handle(self, *args, **options):
        packages = [
            {
                'name': 'Standard Boost',
                'description': 'Give your listing short-term visibility with a 7-day real estate boost.',
                'price': 499,
                'duration_days': 7,
                'features': [
                    'Featured listing for 7 days',
                    'Email alerts to interested buyers',
                    'Basic listing analytics'
                ]
            },
            {
                'name': 'Extended Boost',
                'description': 'Maintain prominent listing exposure for 30 days with targeted visibility.',
                'price': 1499,
                'duration_days': 30,
                'features': [
                    'Featured listing for 30 days',
                    'Priority search placement',
                    'Buyer interest notifications',
                    'Listing performance insights'
                ]
            },
            {
                'name': 'Premium Boost',
                'description': 'Maximize reach with a premium 90-day promotion for your property.',
                'price': 2999,
                'duration_days': 90,
                'features': [
                    'Featured listing for 90 days',
                    'Top search placement',
                    'Premium listing badge',
                    'Detailed performance analytics'
                ]
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for pkg_data in packages:
            pkg, created = PaymentPackage.objects.update_or_create(
                name=pkg_data['name'],
                defaults={
                    'description': pkg_data['description'],
                    'price': pkg_data['price'],
                    'duration_days': pkg_data['duration_days'],
                    'features': pkg_data['features'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created: {pkg_data['name']} - ₹{pkg_data['price']}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"🔄 Updated: {pkg_data['name']} - ₹{pkg_data['price']}")
                )
        
        self.stdout.write(self.style.SUCCESS(f"\n✨ Setup Complete!"))
        self.stdout.write(f"   Created: {created_count} packages")
        self.stdout.write(f"   Updated: {updated_count} packages")
        self.stdout.write(f"   Total: {created_count + updated_count} packages")
        self.stdout.write(self.style.SUCCESS("   ✅ Payment packages are ready to use!"))
