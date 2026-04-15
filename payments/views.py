from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from properties.models import Property
from .models import (
    Payment,
    PaymentPackage,
    Subscription,
    Invoice,
    PaymentAuditLog,
    PaymentWebhookEvent,
)
import razorpay
import json
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone
import uuid


# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

DEFAULT_RAZORPAY_MAX_AMOUNT_PAISE = 50_000_000  # Razorpay order API hard-limit (Rs 5,00,000)


def _audit_payment(payment, event, message='', metadata=None, status=None):
    PaymentAuditLog.objects.create(
        payment=payment,
        event=event,
        status=status or payment.status,
        message=message,
        metadata=metadata or {},
    )


def _complete_payment_transaction(payment, *, razorpay_payment_id=None, razorpay_signature=None):
    """
    Atomically mark payment as completed and ensure invoice exists.
    Returns (payment, invoice, invoice_created).
    """
    with transaction.atomic():
        locked_payment = (
            Payment.objects.select_for_update()
            .select_related('package', 'property')
            .get(pk=payment.pk)
        )

        if razorpay_payment_id:
            locked_payment.razorpay_payment_id = razorpay_payment_id
        if razorpay_signature:
            locked_payment.razorpay_signature = razorpay_signature
        locked_payment.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'updated_at'])

        if locked_payment.status != 'completed':
            locked_payment.mark_completed()
            locked_payment.refresh_from_db()

        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{locked_payment.id}"
        invoice, created = Invoice.objects.get_or_create(
            payment=locked_payment,
            defaults={
                'invoice_number': invoice_number,
                'due_date': timezone.now() + timedelta(days=30),
                'subtotal': locked_payment.amount,
                'total': locked_payment.amount,
                'is_paid': True,
                'paid_at': timezone.now(),
            },
        )
        if not created and not invoice.is_paid:
            invoice.is_paid = True
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=['is_paid', 'paid_at'])

        return locked_payment, invoice, created


def retry_webhook_event(webhook_event):
    """
    Reprocess a stored webhook event from PaymentWebhookEvent payload.
    Intended for manual admin retries of failed events.
    """
    data = webhook_event.payload or {}
    event_name = data.get('event')
    payload_data = data.get('payload', {})

    if event_name in {'payment.authorized', 'payment.captured', 'order.paid'}:
        payment_entity = payload_data.get('payment', {}).get('entity', {})
        order_entity = payload_data.get('order', {}).get('entity', {})
        order_id = payment_entity.get('order_id') or order_entity.get('id')
        payment_id = payment_entity.get('id')

        if not order_id:
            webhook_event.status = 'failed'
            webhook_event.error_message = 'Missing order identifier in webhook payload'
            webhook_event.processed_at = timezone.now()
            webhook_event.save(update_fields=['status', 'error_message', 'processed_at', 'updated_at'])
            return {'status': 'failed', 'reason': 'missing_order_id'}

        payment = Payment.objects.filter(razorpay_order_id=order_id).first()
        if not payment:
            webhook_event.event_name = event_name
            webhook_event.razorpay_order_id = order_id
            webhook_event.razorpay_payment_id = payment_id
            webhook_event.status = 'ignored'
            webhook_event.processed_at = timezone.now()
            webhook_event.save(
                update_fields=[
                    'event_name',
                    'razorpay_order_id',
                    'razorpay_payment_id',
                    'status',
                    'processed_at',
                    'updated_at',
                ]
            )
            return {'status': 'ignored', 'reason': 'payment_not_found'}

        with transaction.atomic():
            payment, _, invoice_created = _complete_payment_transaction(
                payment,
                razorpay_payment_id=payment_id,
            )
            webhook_event.event_name = event_name
            webhook_event.razorpay_order_id = order_id
            webhook_event.razorpay_payment_id = payment_id
            webhook_event.status = 'processed'
            webhook_event.error_message = ''
            webhook_event.processed_at = timezone.now()
            webhook_event.save(
                update_fields=[
                    'event_name',
                    'razorpay_order_id',
                    'razorpay_payment_id',
                    'status',
                    'error_message',
                    'processed_at',
                    'updated_at',
                ]
            )
        _audit_payment(
            payment,
            event='webhook_processed_retry',
            message='Webhook payment state reprocessed from admin retry.',
            metadata={'event': event_name, 'razorpay_payment_id': payment_id},
            status='completed',
        )
        if invoice_created:
            _audit_payment(
                payment,
                event='invoice_created_retry',
                message='Invoice created during webhook retry.',
                metadata={'invoice_number': payment.invoice.invoice_number},
                status='completed',
            )
        return {'status': 'processed', 'event': event_name}

    if event_name in {'payment.failed'}:
        payment_entity = payload_data.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        with transaction.atomic():
            payment = Payment.objects.filter(razorpay_order_id=order_id).first() if order_id else None
            if payment:
                payment.status = 'failed'
                payment.razorpay_payment_id = payment_id or payment.razorpay_payment_id
                payment.notes = f"Webhook failure event retry: {event_name}"
                payment.save(update_fields=['status', 'razorpay_payment_id', 'notes', 'updated_at'])
                _audit_payment(
                    payment,
                    event='webhook_failed_retry',
                    message='Webhook failure reprocessed from admin retry.',
                    metadata={'event': event_name, 'razorpay_payment_id': payment_id},
                    status='failed',
                )
            webhook_event.event_name = event_name
            webhook_event.razorpay_order_id = order_id
            webhook_event.razorpay_payment_id = payment_id
            webhook_event.status = 'processed'
            webhook_event.error_message = ''
            webhook_event.processed_at = timezone.now()
            webhook_event.save(
                update_fields=[
                    'event_name',
                    'razorpay_order_id',
                    'razorpay_payment_id',
                    'status',
                    'error_message',
                    'processed_at',
                    'updated_at',
                ]
            )
        return {'status': 'processed', 'event': event_name}

    if event_name and event_name.startswith('transaction.'):
        transaction_entity = payload_data.get('transaction', {}).get('entity', {})
        source_entity = transaction_entity.get('source', {}) if isinstance(transaction_entity, dict) else {}
        transaction_id = transaction_entity.get('id')
        order_id = source_entity.get('order_id') or source_entity.get('id')

        with transaction.atomic():
            webhook_event.event_name = event_name
            webhook_event.transaction_id = transaction_id
            webhook_event.razorpay_order_id = order_id
            webhook_event.status = 'processed'
            webhook_event.error_message = ''
            webhook_event.processed_at = timezone.now()

            payment = Payment.objects.filter(razorpay_order_id=order_id).first() if order_id else None
            if payment:
                _audit_payment(
                    payment,
                    event='transaction_webhook_processed_retry',
                    message='Transaction webhook reprocessed from admin retry.',
                    metadata={
                        'event': event_name,
                        'transaction_id': transaction_id,
                        'source_entity': source_entity.get('entity'),
                    },
                    status=payment.status,
                )
                webhook_event.razorpay_payment_id = payment.razorpay_payment_id
            webhook_event.save(
                update_fields=[
                    'event_name',
                    'transaction_id',
                    'razorpay_order_id',
                    'razorpay_payment_id',
                    'status',
                    'error_message',
                    'processed_at',
                    'updated_at',
                ]
            )
        return {'status': 'processed', 'event': event_name, 'transaction_id': transaction_id}

    webhook_event.event_name = event_name or webhook_event.event_name
    webhook_event.status = 'ignored'
    webhook_event.error_message = ''
    webhook_event.processed_at = timezone.now()
    webhook_event.save(update_fields=['event_name', 'status', 'error_message', 'processed_at', 'updated_at'])
    return {'status': 'ignored', 'event': event_name}


# ============================================
# Package & Pricing Views
# ============================================

def pricing(request):
    """View all pricing packages"""
    packages = PaymentPackage.objects.none()
    
    # Check if user has subscription
    user_subscription = None
    if request.user.is_authenticated:
        user_subscription = request.user.subscription if hasattr(request.user, 'subscription') else None
    
    context = {
        'packages': packages,
        'user_subscription': user_subscription,
    }
    return render(request, 'payments/pricing.html', context)


# ============================================
# Payment Creation & Checkout
# ============================================

@login_required
def promote_property(request, property_id):
    """Promote a property"""
    get_object_or_404(Property, pk=property_id, agent=request.user)
    messages.info(request, 'Promotional plans are currently unavailable.')
    return redirect('properties:detail', pk=property_id)


@login_required
def purchase_property(request, property_id):
    """Create a direct payment for property purchase"""
    property = get_object_or_404(Property, pk=property_id, is_active=True)

    try:
        max_amount_paise = int(
            getattr(settings, 'RAZORPAY_MAX_ORDER_AMOUNT_PAISE', DEFAULT_RAZORPAY_MAX_AMOUNT_PAISE)
        )
        property_amount_paise = int(
            (Decimal(str(property.price)) * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        )
        payable_amount_paise = min(property_amount_paise, max_amount_paise)
        payable_amount_rupees = (Decimal(payable_amount_paise) / Decimal('100')).quantize(Decimal('0.01'))

        order_data = {
            'amount': payable_amount_paise,
            'currency': 'INR',
            'receipt': str(uuid.uuid4()),
            'notes': {
                'user_id': request.user.id,
                'property_id': property.id,
            }
        }

        # Always create a real Razorpay order.
        # Test mode should rely on Razorpay test keys, not synthetic order IDs.
        razorpay_order = razorpay_client.order.create(data=order_data)

        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                package=None,
                property=property,
                amount=payable_amount_rupees,
                razorpay_order_id=razorpay_order['id'],
                status='pending',
            )
            _audit_payment(
                payment,
                event='order_created',
                message='Razorpay order created for direct property payment.',
                metadata={'property_id': property.id},
            )

        if payable_amount_paise < property_amount_paise:
            messages.warning(
                request,
                f'Razorpay allows up to Rs {max_amount_paise // 100:,} per order. '
                f'Checkout is opened for Rs {payable_amount_rupees:,} as the payable amount.'
            )

        context = {
            'payment': payment,
            'package': None,
            'property': property,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_amount_paise': payable_amount_paise,
            'razorpay_callback_url': request.build_absolute_uri(reverse('payments:verify_payment_callback')),
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'user_email': request.user.email,
            'user_name': request.user.get_full_name() or request.user.username,
            'user_phone': request.user.profile.phone or '',
            'test_mode': settings.PAYMENT_TEST_MODE,
        }

        return render(request, 'payments/checkout.html', context)

    except Exception as e:
        messages.error(request, f'Error creating payment: {str(e)}')
        return redirect('properties:detail', pk=property_id)


@login_required
def create_payment(request, package_id):
    """Create payment for promotion"""
    _ = package_id
    messages.info(request, 'Promotional plans are currently unavailable.')
    return redirect('payments:pricing')


# ============================================
# Payment Verification & Callback
# ============================================

def _verify_payment_payload(request):
    """
    Shared Razorpay verification logic for both in-site POST and
    cross-origin callback POST.
    Returns (success, payment).
    """
    # Get payment details from request
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not razorpay_order_id:
        return False, None

    # Get payment from database
    payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
    _audit_payment(
        payment,
        event='verify_attempt',
        message='Verification request received.',
        metadata={'has_signature': bool(razorpay_signature), 'has_payment_id': bool(razorpay_payment_id)},
    )

    if settings.PAYMENT_TEST_MODE:
        # Skip signature verification in test mode
        _audit_payment(
            payment,
            event='verify_skipped_test_mode',
            message='Signature verification skipped in test mode.',
            metadata={'razorpay_payment_id': razorpay_payment_id},
        )
    else:
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except Exception as e:
            # Signature verification failed
            with transaction.atomic():
                locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)
                locked_payment.status = 'failed'
                locked_payment.notes = f'Verification failed: {str(e)}'
                locked_payment.save(update_fields=['status', 'notes', 'updated_at'])
            _audit_payment(
                payment,
                event='verify_failed',
                message='Payment signature verification failed.',
                metadata={'error': str(e)},
                status='failed',
            )
            return False, payment

    # Payment verified successfully (or skipped in test mode)
    payment, _, invoice_created = _complete_payment_transaction(
        payment,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )
    _audit_payment(
        payment,
        event='verify_success',
        message='Payment signature verified successfully.',
        metadata={'razorpay_payment_id': razorpay_payment_id},
        status='completed',
    )
    if invoice_created:
        _audit_payment(
            payment,
            event='invoice_created',
            message='Invoice created after successful verification.',
            metadata={'invoice_number': payment.invoice.invoice_number},
            status='completed',
        )
    return True, payment

@require_POST
def verify_payment(request):
    """Verify Razorpay payment"""
    try:
        success, payment = _verify_payment_payload(request)
        if not payment:
            messages.error(request, 'Invalid payment request.')
            return redirect('payments:pricing')

        if not success:
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('payments:failed', payment_id=payment.id)

        messages.success(request, 'Payment successful!')
        return redirect('payments:success', payment_id=payment.id)
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
        return redirect('payments:pricing')


@csrf_exempt
@require_POST
def verify_payment_callback(request):
    """
    Razorpay redirect callback endpoint.
    Must be CSRF-exempt because Razorpay POSTs from api.razorpay.com.
    """
    try:
        success, payment = _verify_payment_payload(request)
        if not payment:
            return redirect('payments:pricing')
        if not success:
            return redirect('payments:failed', payment_id=payment.id)
        return redirect('payments:success', payment_id=payment.id)
    except Exception:
        return redirect('payments:pricing')


@login_required
def payment_success(request, payment_id):
    """Payment success page"""
    payment = get_object_or_404(Payment, pk=payment_id, user=request.user)
    
    context = {
        'payment': payment,
        'invoice': payment.invoice if hasattr(payment, 'invoice') else None,
    }
    return render(request, 'payments/success.html', context)


@login_required
def payment_failed(request, payment_id):
    """Payment failed page"""
    payment = get_object_or_404(Payment, pk=payment_id, user=request.user)
    
    context = {
        'payment': payment,
    }
    return render(request, 'payments/failed.html', context)


# ============================================
# Payment History
# ============================================

@login_required
def payment_history(request):
    """View payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(payments, 10)
    page = request.GET.get('page')
    
    try:
        payments_page = paginator.page(page)
    except PageNotAnInteger:
        payments_page = paginator.page(1)
    except EmptyPage:
        payments_page = paginator.page(paginator.num_pages)
    
    context = {
        'payments': payments_page,
        'paginator': paginator,
    }
    return render(request, 'payments/history.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """View invoice details"""
    from .models import Invoice
    invoice = get_object_or_404(Invoice, pk=invoice_id, payment__user=request.user)
    
    context = {
        'invoice': invoice,
        'payment': invoice.payment,
    }
    return render(request, 'payments/invoice.html', context)


# ============================================
# Subscription Views
# ============================================

@login_required
def subscribe_to_package(request, package_id):
    """Subscribe to a package"""
    _ = package_id
    messages.info(request, 'Subscription packages are currently unavailable.')
    return redirect('payments:subscription_detail')


@login_required
def subscription_detail(request):
    """View subscription details"""
    try:
        subscription = request.user.subscription
    except:
        subscription = None
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'payments/subscription_detail.html', context)


@login_required
def cancel_subscription(request):
    """Cancel subscription"""
    try:
        subscription = request.user.subscription
        if request.method == 'POST':
            subscription.status = 'cancelled'
            subscription.save()
            messages.success(request, 'Subscription cancelled.')
            return redirect('payments:subscription_detail')
    except:
        messages.error(request, 'Subscription not found.')
        return redirect('properties:home')
    
    return render(request, 'payments/cancel_subscription.html', {'subscription': subscription})


# ============================================
# AJAX Endpoints
# ============================================

@login_required
def get_razorpay_key(request):
    """Get Razorpay key for frontend (AJAX)"""
    return JsonResponse({
        'key': settings.RAZORPAY_KEY_ID
    })


@csrf_exempt
@require_POST
def webhook_razorpay(request):
    """Razorpay webhook endpoint"""
    try:
        signature = request.headers.get('X-Razorpay-Signature', '')
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        raw_payload = request.body
        payload = raw_payload.decode('utf-8')
        webhook_event_id = request.headers.get('X-Razorpay-Event-Id', '')

        if not webhook_secret:
            return JsonResponse({'error': 'Webhook secret is not configured'}, status=503)

        if not signature:
            return JsonResponse({'error': 'Missing webhook signature'}, status=400)

        if not settings.PAYMENT_TEST_MODE:
            try:
                razorpay_client.utility.verify_webhook_signature(
                    payload,
                    signature,
                    webhook_secret
                )
            except Exception:
                return JsonResponse({'error': 'Invalid webhook signature'}, status=400)

        data = json.loads(payload)
        event_name = data.get('event')
        payload_data = data.get('payload', {})
        payload_hash = hashlib.sha256(raw_payload).hexdigest()

        if webhook_event_id:
            existing_by_event = PaymentWebhookEvent.objects.filter(transaction_id=webhook_event_id).exclude(status='failed').first()
            if existing_by_event:
                return JsonResponse({
                    'status': existing_by_event.status,
                    'event': existing_by_event.event_name,
                    'duplicate': True,
                    'event_id': webhook_event_id,
                })

        webhook_event, created = PaymentWebhookEvent.objects.get_or_create(
            payload_hash=payload_hash,
            defaults={
                'event_name': event_name or 'unknown',
                'signature': signature,
                'payload': data,
                'status': 'received',
                'transaction_id': webhook_event_id or None,
            },
        )

        if not created and webhook_event_id and not webhook_event.transaction_id:
            webhook_event.transaction_id = webhook_event_id
            webhook_event.save(update_fields=['transaction_id', 'updated_at'])

        if not created and webhook_event.status in {'processed', 'ignored'}:
            return JsonResponse({'status': webhook_event.status, 'event': webhook_event.event_name, 'duplicate': True})

        if event_name in {'payment.authorized', 'payment.captured', 'order.paid'}:
            payment_entity = payload_data.get('payment', {}).get('entity', {})
            order_entity = payload_data.get('order', {}).get('entity', {})
            order_id = (
                payment_entity.get('order_id')
                or order_entity.get('id')
            )
            payment_id = payment_entity.get('id')

            if not order_id:
                webhook_event.status = 'failed'
                webhook_event.error_message = 'Missing order identifier in webhook payload'
                webhook_event.processed_at = timezone.now()
                webhook_event.save(update_fields=['status', 'error_message', 'processed_at', 'updated_at'])
                return JsonResponse({'error': 'Missing order identifier in webhook payload'}, status=400)

            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
            except Payment.DoesNotExist:
                webhook_event.event_name = event_name
                webhook_event.razorpay_order_id = order_id
                webhook_event.razorpay_payment_id = payment_id
                webhook_event.status = 'ignored'
                webhook_event.processed_at = timezone.now()
                webhook_event.save(
                    update_fields=[
                        'event_name',
                        'razorpay_order_id',
                        'razorpay_payment_id',
                        'status',
                        'processed_at',
                        'updated_at',
                    ]
                )
                return JsonResponse({'status': 'ignored', 'reason': 'payment_not_found'})

            with transaction.atomic():
                payment, _, invoice_created = _complete_payment_transaction(
                    payment,
                    razorpay_payment_id=payment_id,
                )
                webhook_event.event_name = event_name
                webhook_event.razorpay_order_id = order_id
                webhook_event.razorpay_payment_id = payment_id
                webhook_event.status = 'processed'
                webhook_event.error_message = ''
                webhook_event.processed_at = timezone.now()
                webhook_event.save(
                    update_fields=[
                        'event_name',
                        'razorpay_order_id',
                        'razorpay_payment_id',
                        'status',
                        'error_message',
                        'processed_at',
                        'updated_at',
                    ]
                )
            _audit_payment(
                payment,
                event='webhook_processed',
                message='Webhook payment state processed.',
                metadata={'event': event_name, 'razorpay_payment_id': payment_id},
                status='completed',
            )
            if invoice_created:
                _audit_payment(
                    payment,
                    event='invoice_created',
                    message='Invoice created via webhook reconciliation.',
                    metadata={'invoice_number': payment.invoice.invoice_number},
                    status='completed',
                )
            return JsonResponse({'status': 'processed', 'event': event_name})

        if event_name in {'payment.failed'}:
            payment_entity = payload_data.get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            if order_id:
                with transaction.atomic():
                    payment = Payment.objects.filter(razorpay_order_id=order_id).first()
                    if payment:
                        payment.status = 'failed'
                        payment.razorpay_payment_id = payment_id or payment.razorpay_payment_id
                        payment.notes = f"Webhook failure event: {event_name}"
                        payment.save(update_fields=['status', 'razorpay_payment_id', 'notes', 'updated_at'])
                        _audit_payment(
                            payment,
                            event='webhook_failed',
                            message='Webhook indicated failed payment.',
                            metadata={'event': event_name, 'razorpay_payment_id': payment_id},
                            status='failed',
                        )
                    webhook_event.event_name = event_name
                    webhook_event.razorpay_order_id = order_id
                    webhook_event.razorpay_payment_id = payment_id
                    webhook_event.status = 'processed'
                    webhook_event.error_message = ''
                    webhook_event.processed_at = timezone.now()
                    webhook_event.save(
                        update_fields=[
                            'event_name',
                            'razorpay_order_id',
                            'razorpay_payment_id',
                            'status',
                            'error_message',
                            'processed_at',
                            'updated_at',
                        ]
                    )
            return JsonResponse({'status': 'processed', 'event': event_name})

        if event_name and event_name.startswith('transaction.'):
            transaction_entity = payload_data.get('transaction', {}).get('entity', {})
            source_entity = transaction_entity.get('source', {}) if isinstance(transaction_entity, dict) else {}
            transaction_id = transaction_entity.get('id')
            order_id = source_entity.get('order_id') or source_entity.get('id')

            with transaction.atomic():
                webhook_event.event_name = event_name
                webhook_event.transaction_id = transaction_id
                webhook_event.razorpay_order_id = order_id
                webhook_event.status = 'processed'
                webhook_event.error_message = ''
                webhook_event.processed_at = timezone.now()

                payment = None
                if order_id:
                    payment = Payment.objects.filter(razorpay_order_id=order_id).first()
                if payment:
                    _audit_payment(
                        payment,
                        event='transaction_webhook_processed',
                        message='Razorpay transaction webhook recorded.',
                        metadata={
                            'event': event_name,
                            'transaction_id': transaction_id,
                            'source_entity': source_entity.get('entity'),
                        },
                        status=payment.status,
                    )
                    webhook_event.razorpay_payment_id = payment.razorpay_payment_id
                webhook_event.save(
                    update_fields=[
                        'event_name',
                        'transaction_id',
                        'razorpay_order_id',
                        'razorpay_payment_id',
                        'status',
                        'error_message',
                        'processed_at',
                        'updated_at',
                    ]
                )
            return JsonResponse({'status': 'processed', 'event': event_name, 'transaction_id': transaction_id})
        
        webhook_event.event_name = event_name or webhook_event.event_name
        webhook_event.status = 'ignored'
        webhook_event.processed_at = timezone.now()
        webhook_event.save(update_fields=['event_name', 'status', 'processed_at', 'updated_at'])
        return JsonResponse({'status': 'ignored', 'event': event_name})
    except Exception as e:
        if 'webhook_event' in locals():
            webhook_event.status = 'failed'
            webhook_event.error_message = str(e)
            webhook_event.processed_at = timezone.now()
            webhook_event.save(update_fields=['status', 'error_message', 'processed_at', 'updated_at'])
        return JsonResponse({'error': str(e)}, status=400)
