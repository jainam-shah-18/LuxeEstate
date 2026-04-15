#!/usr/bin/env python
"""
Setup script to initialize payment packages for LuxeEstate
Run with: python setup_payment_packages.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LuxeEstate.settings')
django.setup()

from payments.models import PaymentPackage

def create_payment_packages():
    """Disable all existing payment packages."""
    deactivated_count = PaymentPackage.objects.filter(is_active=True).update(is_active=False)
    print("Promotional packages are disabled globally.")
    print(f"Deactivated {deactivated_count} active package(s).")

if __name__ == '__main__':
    try:
        create_payment_packages()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
