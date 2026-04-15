from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from .models import PaymentPackage, Payment, Subscription, Invoice, PaymentWebhookEvent


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


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    change_form_template = 'admin/payments/paymentwebhookevent/change_form.html'
    list_display = (
        'event_name',
        'status',
        'transaction_id',
        'razorpay_order_id',
        'razorpay_payment_id',
        'processed_at',
        'created_at',
    )
    list_filter = ('status', 'event_name', 'created_at', 'processed_at')
    search_fields = (
        'payload_hash',
        'event_name',
        'transaction_id',
        'razorpay_order_id',
        'razorpay_payment_id',
    )
    readonly_fields = (
        'payload_hash',
        'event_name',
        'signature',
        'status',
        'transaction_id',
        'razorpay_order_id',
        'razorpay_payment_id',
        'payload',
        'error_message',
        'processed_at',
        'created_at',
        'updated_at',
    )
    actions = ('retry_failed_events',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/retry-now/',
                self.admin_site.admin_view(self.retry_now_view),
                name='payments_paymentwebhookevent_retry_now',
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, unquote(object_id))
        if obj:
            extra_context['retry_now_url'] = reverse(
                'admin:payments_paymentwebhookevent_retry_now',
                args=[obj.pk],
            )
            extra_context['show_retry_now'] = obj.status == 'failed'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def retry_now_view(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(
                reverse('admin:payments_paymentwebhookevent_change', args=[object_id])
            )

        webhook_event = self.get_object(request, unquote(object_id))
        if webhook_event is None:
            self.message_user(request, 'Webhook event not found.', level='ERROR')
            return HttpResponseRedirect(reverse('admin:payments_paymentwebhookevent_changelist'))

        if webhook_event.status != 'failed':
            self.message_user(
                request,
                'Only failed webhook events can be retried.',
                level='WARNING',
            )
            return HttpResponseRedirect(
                reverse('admin:payments_paymentwebhookevent_change', args=[webhook_event.pk])
            )

        from .views import retry_webhook_event

        try:
            retry_webhook_event(webhook_event)
            self.message_user(
                request,
                'Webhook event retried successfully.',
                level='SUCCESS',
            )
        except Exception as exc:
            webhook_event.error_message = f"Manual retry failed: {exc}"
            webhook_event.save(update_fields=['error_message', 'updated_at'])
            self.message_user(
                request,
                f"Retry failed: {exc}",
                level='ERROR',
            )

        return HttpResponseRedirect(
            reverse('admin:payments_paymentwebhookevent_change', args=[webhook_event.pk])
        )

    @admin.action(description='Retry selected failed webhook events')
    def retry_failed_events(self, request, queryset):
        from .views import retry_webhook_event

        success_count = 0
        failed_count = 0

        for webhook_event in queryset:
            if webhook_event.status != 'failed':
                continue
            try:
                retry_webhook_event(webhook_event)
                success_count += 1
            except Exception as exc:
                failed_count += 1
                webhook_event.error_message = f"Manual retry failed: {exc}"
                webhook_event.save(update_fields=['error_message', 'updated_at'])

        if success_count:
            self.message_user(
                request,
                f"Successfully retried {success_count} failed webhook event(s).",
                level='SUCCESS',
            )
        if failed_count:
            self.message_user(
                request,
                f"{failed_count} webhook event(s) still failed on retry. Check error_message.",
                level='ERROR',
            )
