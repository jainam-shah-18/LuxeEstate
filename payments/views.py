from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from properties.models import Property
from .models import Payment, PaymentPackage, Subscription, Invoice, PaymentAuditLog
import razorpay
import json
from datetime import timedelta
from django.utils import timezone
import uuid


# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def _audit_payment(payment, event, message='', metadata=None, status=None):
    PaymentAuditLog.objects.create(
        payment=payment,
        event=event,
        status=status or payment.status,
        message=message,
        metadata=metadata or {},
    )


# ============================================
# Package & Pricing Views
# ============================================

def pricing(request):
    """View all pricing packages"""
    packages = PaymentPackage.objects.filter(is_active=True).order_by('price')
    
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
    property = get_object_or_404(Property, pk=property_id, agent=request.user)
    
    if request.method == 'GET':
        packages = PaymentPackage.objects.filter(is_active=True).order_by('price')
        return render(request, 'payments/promote_property.html', {
            'property': property,
            'packages': packages,
        })
    
    return redirect('properties:detail', pk=property_id)


@login_required
def purchase_property(request, property_id):
    """Create a direct payment for property purchase"""
    property = get_object_or_404(Property, pk=property_id, is_active=True)

    try:
        order_data = {
            'amount': int(float(property.price) * 100),
            'currency': 'INR',
            'receipt': str(uuid.uuid4()),
            'notes': {
                'user_id': request.user.id,
                'property_id': property.id,
            }
        }

        if settings.PAYMENT_TEST_MODE:
            mock_order_id = f'order_test_{uuid.uuid4().hex[:14]}'
            razorpay_order = {
                'id': mock_order_id,
                'amount': order_data['amount'],
                'currency': order_data['currency'],
                'receipt': order_data['receipt'],
                'status': 'created'
            }
        else:
            razorpay_order = razorpay_client.order.create(data=order_data)

        payment = Payment.objects.create(
            user=request.user,
            package=None,
            property=property,
            amount=property.price,
            razorpay_order_id=razorpay_order['id'],
            status='pending',
        )
        _audit_payment(
            payment,
            event='order_created',
            message='Razorpay order created for direct property payment.',
            metadata={'property_id': property.id},
        )

        context = {
            'payment': payment,
            'package': None,
            'property': property,
            'razorpay_order_id': razorpay_order['id'],
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
    package = get_object_or_404(PaymentPackage, pk=package_id, is_active=True)
    property_id = request.GET.get('property_id')
    property = None
    
    if property_id:
        property = get_object_or_404(Property, pk=property_id, agent=request.user)
    
    # Create Razorpay order
    try:
        order_data = {
            'amount': int(float(package.price) * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': str(uuid.uuid4()),
            'notes': {
                'user_id': request.user.id,
                'package_id': package.id,
                'property_id': property.id if property else None,
            }
        }
        
        if settings.PAYMENT_TEST_MODE:
            # Mock order for test mode; use Razorpay checkout without requiring actual order verification
            mock_order_id = f'order_test_{uuid.uuid4().hex[:14]}'
            razorpay_order = {
                'id': mock_order_id,
                'amount': order_data['amount'],
                'currency': order_data['currency'],
                'receipt': order_data['receipt'],
                'status': 'created'
            }
        else:
            razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            package=package,
            property=property,
            amount=package.price,
            razorpay_order_id=razorpay_order['id'],
            status='pending',
        )
        _audit_payment(
            payment,
            event='order_created',
            message='Razorpay order created and checkout initialized.',
            metadata={'package_id': package.id, 'property_id': property.id if property else None},
        )
        
        context = {
            'payment': payment,
            'package': package,
            'property': property,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'user_email': request.user.email,
            'user_name': request.user.get_full_name() or request.user.username,
            'user_phone': request.user.profile.phone or '',
            'test_mode': settings.PAYMENT_TEST_MODE,
        }
        
        return render(request, 'payments/checkout.html', context)
    
    except Exception as e:
        messages.error(request, f'Error creating payment: {str(e)}')
        return redirect('payments:pricing')


# ============================================
# Payment Verification & Callback
# ============================================

@require_POST
def verify_payment(request):
    """Verify Razorpay payment"""
    try:
        # Get payment details from request
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Get payment from database
        payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
        _audit_payment(
            payment,
            event='verify_attempt',
            message='Verification request received.',
            metadata={'has_signature': bool(razorpay_signature), 'has_payment_id': bool(razorpay_payment_id)},
        )
        
        # Verify signature
        body = razorpay_order_id + '|' + razorpay_payment_id
        
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
                payment.status = 'failed'
                payment.notes = f'Verification failed: {str(e)}'
                payment.save()
                _audit_payment(
                    payment,
                    event='verify_failed',
                    message='Payment signature verification failed.',
                    metadata={'error': str(e)},
                    status='failed',
                )
                
                messages.error(request, 'Payment verification failed. Please contact support.')
                return redirect('payments:failed', payment_id=payment.id)
        
        # Payment verified successfully (or skipped in test mode)
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.mark_completed()
        _audit_payment(
            payment,
            event='verify_success',
            message='Payment signature verified successfully.',
            metadata={'razorpay_payment_id': razorpay_payment_id},
            status='completed',
        )
        
        # Create invoice
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{payment.id}"
        Invoice.objects.create(
            payment=payment,
            invoice_number=invoice_number,
            due_date=timezone.now() + timedelta(days=30),
            subtotal=payment.amount,
            total=payment.amount,
            is_paid=True,
            paid_at=timezone.now(),
        )
        
        messages.success(request, 'Payment successful! Property promotion activated.')
        
        if payment.property:
            return redirect('properties:detail', pk=payment.property.pk)
        else:
            return redirect('payments:pricing')
    
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
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
    package = get_object_or_404(PaymentPackage, pk=package_id, is_active=True)
    
    # Check if user already has active subscription
    try:
        subscription = request.user.subscription
        if subscription.is_active_subscription():
            messages.warning(request, 'You already have an active subscription.')
            return redirect('payments:subscription_detail')
    except:
        pass
    
    # Create payment for subscription
    context = {
        'package': package,
        'is_subscription': True,
    }
    return render(request, 'payments/subscribe.html', context)


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


@require_POST
def webhook_razorpay(request):
    """Razorpay webhook endpoint"""
    try:
        signature = request.headers.get('X-Razorpay-Signature', '')
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        payload = request.body.decode('utf-8')

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
        
        # Verify event
        if data.get('event') in {'payment.authorized', 'payment.captured'}:
            order_id = data.get('payload', {}).get('order', {}).get('entity', {}).get('id')
            payment_id = data.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
            
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.razorpay_payment_id = payment_id
                if payment.status != 'completed':
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                payment.save(update_fields=['razorpay_payment_id', 'status', 'completed_at', 'updated_at'])
                _audit_payment(
                    payment,
                    event='webhook_processed',
                    message='Webhook payment state processed.',
                    metadata={'event': data.get('event'), 'razorpay_payment_id': payment_id},
                )
            except Payment.DoesNotExist:
                pass
        
        return JsonResponse({'status': 'received'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
