import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from payments.models import Invoice, Payment
from properties.models import Property


class PaymentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testagent',
            email='agent@example.com',
            password='secret123',
        )
        self.property = Property.objects.create(
            title='Test Villa',
            description='A test property',
            price=Decimal('2500000.00'),
            city='Mumbai',
            state='MH',
            address='Marine Drive',
            property_type='villa',
            status='available',
            agent=self.user,
        )
        self.payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            amount=Decimal('2500000.00'),
            razorpay_order_id='order_test_12345',
            status='pending',
        )

    @override_settings(PAYMENT_TEST_MODE=True, RAZORPAY_WEBHOOK_SECRET='test_webhook_secret')
    def test_webhook_marks_payment_completed_and_creates_invoice(self):
        payload = {
            'event': 'order.paid',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test_12345',
                        'order_id': self.payment.razorpay_order_id,
                    }
                }
            },
        }

        response = self.client.post(
            reverse('payments:webhook'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='fake_signature_for_test_mode',
        )

        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'completed')
        self.assertEqual(self.payment.razorpay_payment_id, 'pay_test_12345')
        self.assertEqual(Invoice.objects.filter(payment=self.payment).count(), 1)

    @override_settings(PAYMENT_TEST_MODE=True, RAZORPAY_WEBHOOK_SECRET='test_webhook_secret')
    def test_webhook_is_idempotent_for_duplicate_callbacks(self):
        payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test_idempotent',
                        'order_id': self.payment.razorpay_order_id,
                    }
                }
            },
        }

        webhook_url = reverse('payments:webhook')
        headers = {'HTTP_X_RAZORPAY_SIGNATURE': 'fake_signature_for_test_mode'}

        first = self.client.post(webhook_url, data=json.dumps(payload), content_type='application/json', **headers)
        second = self.client.post(webhook_url, data=json.dumps(payload), content_type='application/json', **headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Invoice.objects.filter(payment=self.payment).count(), 1)

    @override_settings(PAYMENT_TEST_MODE=True, RAZORPAY_WEBHOOK_SECRET='test_webhook_secret')
    def test_payment_gateway_webhook_alias_and_event_id_idempotency(self):
        payload = {
            'event': 'order.paid',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test_event_id',
                        'order_id': self.payment.razorpay_order_id,
                    }
                }
            },
        }

        headers = {
            'HTTP_X_RAZORPAY_SIGNATURE': 'fake_signature_for_test_mode',
            'HTTP_X_RAZORPAY_EVENT_ID': 'evt_test_123',
        }
        webhook_url = reverse('payments:payment_gateway_webhook')
        first = self.client.post(webhook_url, data=json.dumps(payload), content_type='application/json', **headers)
        second = self.client.post(webhook_url, data=json.dumps(payload), content_type='application/json', **headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Invoice.objects.filter(payment=self.payment).count(), 1)

    @override_settings(RAZORPAY_MAX_ORDER_AMOUNT_PAISE=50000000)
    @patch('payments.views.razorpay_client.order.create')
    def test_purchase_property_caps_order_amount_to_gateway_limit(self, mock_order_create):
        self.client.login(username='testagent', password='secret123')
        mock_order_create.return_value = {'id': 'order_cap_test_123'}

        response = self.client.get(reverse('payments:purchase_property', args=[self.property.id]))

        self.assertEqual(response.status_code, 200)
        mock_order_create.assert_called_once()
        sent_order_data = mock_order_create.call_args.kwargs['data']
        self.assertEqual(sent_order_data['amount'], 50000000)

        capped_payment = Payment.objects.get(razorpay_order_id='order_cap_test_123')
        self.assertEqual(capped_payment.amount, Decimal('500000.00'))
