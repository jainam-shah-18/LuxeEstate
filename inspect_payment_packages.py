import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LuxeEstate.settings')
django.setup()

from payments.models import PaymentPackage

print('count', PaymentPackage.objects.count())
for pkg in PaymentPackage.objects.all():
    print(pkg.id, pkg.name, pkg.price, pkg.duration_days, pkg.description)
