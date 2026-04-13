from django.contrib import admin
from .models import PaymentPackage, Payment, Subscription, Invoice


@admin.register(PaymentPackage)
class PaymentPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active')
    list_filter = ('is_active', 'duration_days')
    search_fields = ('name', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'razorpay_order_id', 'created_at')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('razorpay_order_id', 'user__email')
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'end_date')
    search_fields = ('user__email', 'user__username')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'payment', 'total', 'is_paid', 'invoice_date')
    list_filter = ('is_paid', 'invoice_date')
    search_fields = ('invoice_number', 'payment__razorpay_order_id')
    readonly_fields = ('invoice_number',)
