from django.contrib import admin
from .models import RazorpayOrder


@admin.register(RazorpayOrder)
class RazorpayOrderAdmin(admin.ModelAdmin):
    list_display = ('razorpay_order_id', 'user', 'amount_paise', 'status', 'created_at')
    search_fields = ('razorpay_order_id', 'user__email')
