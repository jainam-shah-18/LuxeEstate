from django.conf import settings


def site_settings(request):
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
