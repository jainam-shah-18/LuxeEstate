from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Pricing and packages
    path('pricing/', views.pricing, name='pricing'),
    path('purchase/<int:property_id>/', views.purchase_property, name='purchase_property'),
    
    # Payment flow
    path('create/<int:package_id>/', views.create_payment, name='create_payment'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('success/<int:payment_id>/', views.payment_success, name='success'),
    path('failed/<int:payment_id>/', views.payment_failed, name='failed'),
    
    # Property promotion
    path('promote/<int:property_id>/', views.promote_property, name='promote_property'),
    
    # Payment history
    path('history/', views.payment_history, name='history'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice'),
    
    # Subscriptions
    path('subscribe/<int:package_id>/', views.subscribe_to_package, name='subscribe'),
    path('subscription/', views.subscription_detail, name='subscription_detail'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # AJAX
    path('api/razorpay-key/', views.get_razorpay_key, name='razorpay_key'),
    path('webhook/razorpay/', views.webhook_razorpay, name='webhook'),
]
