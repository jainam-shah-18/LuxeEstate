"""
Payment processing utilities for Razorpay integration
"""
import os
import logging
import json
from decimal import Decimal
import razorpay

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """
    Handle payment processing through Razorpay
    """
    
    def __init__(self):
        self.client = self._init_razorpay_client()
    
    def _init_razorpay_client(self):
        """Initialize Razorpay client"""
        try:
            api_key = os.getenv('RAZORPAY_KEY_ID')
            api_secret = os.getenv('RAZORPAY_KEY_SECRET')
            test_mode = os.getenv('PAYMENT_TEST_MODE', 'False').lower() == 'true'
            
            if test_mode:
                logger.info("Payment test mode enabled - Razorpay client not initialized")
                return None
            elif api_key and api_secret:
                return razorpay.Client(auth=(api_key, api_secret))
            else:
                logger.warning("Razorpay credentials not found in environment variables")
                return None
        except Exception as e:
            logger.error(f"Error initializing Razorpay client: {str(e)}")
            return None
    
    def create_order(self, amount: Decimal, currency: str = 'INR', 
                    description: str = '', customer_data: dict = None) -> dict:
        """
        Create a Razorpay order
        
        Args:
            amount: Amount in Rupees (will be converted to paise)
            currency: Payment currency (default: INR)
            description: Order description
            customer_data: Customer details dict
        
        Returns:
            dict with order details or error
        """
        
        if not self.client:
            # Test mode - create mock order
            import uuid
            amount_paise = int(amount * 100)
            mock_order_id = f'order_test_{uuid.uuid4().hex[:14]}'
            mock_order = {
                'id': mock_order_id,
                'amount': amount_paise,
                'currency': currency,
                'receipt': f'Receipt#{int(amount)}',
                'status': 'created'
            }
            
            logger.info(f"Mock order created for test mode: {mock_order_id}")
            
            return {
                'success': True,
                'order_id': mock_order['id'],
                'amount': amount,
                'currency': currency,
                'order_data': mock_order
            }
        
        try:
            # Convert amount to paise (multiply by 100)
            amount_paise = int(amount * 100)
            
            order_data = {
                'amount': amount_paise,
                'currency': currency,
                'description': description,
                'receipt': f'Receipt#{int(amount)}',
            }
            
            if customer_data:
                order_data['customer_notify'] = True
            
            order = self.client.order.create(data=order_data)
            
            logger.info(f"Order created successfully: {order['id']}")
            
            return {
                'success': True,
                'order_id': order['id'],
                'amount': amount,
                'currency': currency,
                'order_data': order
            }
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_payment(self, order_id: str, payment_id: str, signature: str) -> dict:
        """
        Verify Razorpay payment signature
        
        Args:
            order_id: Razorpay Order ID
            payment_id: Razorpay Payment ID
            signature: Razorpay Signature from callback
        
        Returns:
            dict with verification result
        """
        
        if not self.client:
            # Test mode - skip verification
            logger.info(f"Payment verification skipped in test mode for order: {order_id}")
            return {'success': True, 'verified': True, 'test_mode': True}
        
        try:
            # Verify signature
            verified = self.client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            
            logger.info(f"Payment verification successful for order {order_id}")
            
            return {
                'success': True,
                'verified': True,
                'order_id': order_id,
                'payment_id': payment_id
            }
            
        except razorpay.BadRequestsError as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': 'Payment verification failed',
                'order_id': order_id
            }
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_payment(self, payment_id: str) -> dict:
        """
        Fetch payment details from Razorpay
        """
        
        if not self.client:
            return {'success': False, 'error': 'Payment gateway not configured'}
        
        try:
            payment = self.client.payment.fetch(payment_id)
            
            return {
                'success': True,
                'payment': payment
            }
            
        except Exception as e:
            logger.error(f"Error fetching payment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def refund_payment(self, payment_id: str, amount: Decimal = None, 
                      notes: dict = None) -> dict:
        """
        Refund a payment
        
        Args:
            payment_id: Payment ID to refund
            amount: Amount to refund (if partial), in Rupees
            notes: Additional notes for refund
        
        Returns:
            dict with refund details
        """
        
        if not self.client:
            return {'success': False, 'error': 'Payment gateway not configured'}
        
        try:
            refund_data = {}
            
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convert to paise
            
            if notes:
                refund_data['notes'] = notes
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            logger.info(f"Refund processed successfully for payment {payment_id}")
            
            return {
                'success': True,
                'refund': refund,
                'refund_id': refund['id']
            }
            
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return {'success': False, 'error': str(e)}


class PropertyPromotionPayment:
    """
    Handle payment for property promotions and featured listings
    """
    
    def __init__(self):
        self.processor = PaymentProcessor()
    
    def get_promotion_plans(self) -> list:
        """Get available promotion plans"""
        plans = [
            {
                'id': 'standard',
                'name': 'Standard Promotion',
                'price': 999,
                'duration_days': 7,
                'features': ['Featured listing', '7 days promotion'],
                'description': 'Get your property featured for 7 days'
            },
            {
                'id': 'premium',
                'name': 'Premium Promotion',
                'price': 2499,
                'duration_days': 30,
                'features': ['Featured listing', '30 days promotion', 'Priority search'],
                'description': 'Premium visibility for 30 days'
            },
            {
                'id': 'platinum',
                'name': 'Platinum Promotion',
                'price': 4999,
                'duration_days': 90,
                'features': ['Featured listing', '90 days promotion', 'Priority search', 'Top results'],
                'description': 'Maximum visibility for 90 days'
            }
        ]
        return plans
    
    def create_promotion_order(self, property_id: int, plan_id: str, user) -> dict:
        """Create order for property promotion"""
        
        try:
            plans = {plan['id']: plan for plan in self.get_promotion_plans()}
            
            if plan_id not in plans:
                return {'success': False, 'error': 'Invalid promotion plan'}
            
            plan = plans[plan_id]
            
            description = f"Promotion for Property #{property_id} - {plan['name']}"
            
            order_result = self.processor.create_order(
                amount=Decimal(plan['price']),
                description=description
            )
            
            if order_result['success']:
                return {
                    'success': True,
                    'order_id': order_result['order_id'],
                    'amount': plan['price'],
                    'plan': plan,
                    'property_id': property_id
                }
            else:
                return order_result
            
        except Exception as e:
            logger.error(f"Error creating promotion order: {str(e)}")
            return {'success': False, 'error': str(e)}


# Initialize global payment processor
payment_processor = PaymentProcessor()
promotion_payment = PropertyPromotionPayment()
