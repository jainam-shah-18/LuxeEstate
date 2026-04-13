from django.db import models
from django.contrib.auth.models import User
from properties.models import Property
from django.utils import timezone


class PaymentPackage(models.Model):
    """Premium packages for property promotion"""
    DURATION_CHOICES = [
        (7, '7 Days'),
        (14, '14 Days'),
        (30, '30 Days'),
        (90, '90 Days'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    duration_days = models.IntegerField(choices=DURATION_CHOICES)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class Payment(models.Model):
    """Payment transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Transaction details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    package = models.ForeignKey(PaymentPackage, on_delete=models.SET_NULL, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    # Payment info
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_signature = models.CharField(max_length=256, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment method
    payment_method = models.CharField(max_length=50, default='razorpay')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.razorpay_order_id} - {self.status}"
    
    def mark_completed(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Apply promotion to property if applicable
        if self.package and self.property:
            self.property.is_promoted = True
            self.property.promotion_until = timezone.now() + timezone.timedelta(days=self.package.duration_days)
            self.property.save()


class Subscription(models.Model):
    """Premium subscription for agents"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    package = models.ForeignKey(PaymentPackage, on_delete=models.SET_NULL, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-end_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    def is_active_subscription(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and self.end_date > timezone.now()
    
    def renew(self):
        """Renew subscription"""
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timezone.timedelta(days=self.package.duration_days)
        self.status = 'active'
        self.save()


class Invoice(models.Model):
    """Invoices for payments"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    
    # Details
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Status
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"


class PaymentAuditLog(models.Model):
    """Immutable-ish audit trail for payment lifecycle events."""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='audit_logs')
    event = models.CharField(max_length=64)
    status = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment.razorpay_order_id} - {self.event}"
