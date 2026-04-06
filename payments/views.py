import json

import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import RazorpayOrder


def _client():
    key = getattr(settings, 'RAZORPAY_KEY_ID', '') or ''
    secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '') or ''
    if not key or not secret:
        return None
    return razorpay.Client(auth=(key, secret))


@login_required
def premium_checkout(request):
    """Demo: premium listing boost (₹499)."""
    return render(request, 'payments/checkout.html', {
        'amount_paise': 49900,
        'title': 'Premium listing visibility',
    })


@login_required
@require_POST
def create_order(request):
    client = _client()
    if client is None:
        return JsonResponse({'error': 'Razorpay is not configured.'}, status=503)

    try:
        body = json.loads(request.body.decode() or '{}')
    except json.JSONDecodeError:
        body = {}
    amount = int(body.get('amount_paise') or 49900)
    if amount < 100:
        return HttpResponseBadRequest('Invalid amount')

    order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'receipt': f'lux_{request.user.id}_{amount}',
        'notes': {'user_id': request.user.id},
    })

    RazorpayOrder.objects.create(
        user=request.user,
        amount_paise=amount,
        razorpay_order_id=order['id'],
        notes=order.get('notes') or {},
    )

    return JsonResponse({
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'key_id': settings.RAZORPAY_KEY_ID,
    })


@require_POST
def verify_payment(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Auth required'}, status=401)

    client = _client()
    if client is None:
        return JsonResponse({'error': 'Razorpay is not configured.'}, status=503)

    try:
        payload = json.loads(request.body.decode() or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    order_id = payload.get('razorpay_order_id')
    pay_id = payload.get('razorpay_payment_id')
    signature = payload.get('razorpay_signature')
    if not all([order_id, pay_id, signature]):
        return HttpResponseBadRequest('Missing fields')

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': pay_id,
            'razorpay_signature': signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'ok': False, 'error': 'Bad signature'}, status=400)

    RazorpayOrder.objects.filter(razorpay_order_id=order_id, user=request.user).update(
        status='paid',
        razorpay_payment_id=pay_id,
    )
    return JsonResponse({'ok': True})
