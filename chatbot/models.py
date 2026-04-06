from django.db import models
from django.conf import settings
from django.utils import timezone
from properties.models import Property


class ChatbotConversation(models.Model):
    """Stores AI chatbot conversations with website visitors."""
    
    visitor_name = models.CharField(max_length=255, null=True, blank=True)
    visitor_email = models.EmailField(null=True, blank=True)
    visitor_phone = models.CharField(max_length=20, null=True, blank=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Optional: link to authenticated user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chatbot_conversations'
    )
    
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chatbot_conversations',
        help_text="Property being inquired about (null for general inquiry)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.visitor_name or self.visitor_email or f"Visitor {self.id}"
        return f"Chat: {name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_context(self):
        """Build context for AI chatbot about this conversation."""
        context = {
            'visitor_name': self.visitor_name or 'Guest',
            'visitor_email': self.visitor_email,
            'visitor_phone': self.visitor_phone,
            'property': None,
            'is_qualified': getattr(self, 'lead', None) is not None,
        }
        if self.property:
            context['property'] = {
                'title': self.property.title,
                'type': self.property.get_property_type_display(),
                'price': str(self.property.price),
                'city': self.property.city,
                'address': self.property.address,
            }
        return context


class ChatbotMessage(models.Model):
    """Individual messages in chatbot conversation."""
    
    conversation = models.ForeignKey(
        ChatbotConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    sender = models.CharField(
        max_length=10,
        choices=[('user', 'User'), ('bot', 'AI Bot')],
        default='user'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional: store AI metadata
    ai_confidence = models.FloatField(null=True, blank=True)
    intent_detected = models.CharField(
        max_length=50,
        choices=[
            ('inquiry', 'General Inquiry'),
            ('pricing', 'Pricing Question'),
            ('schedule', 'Schedule Tour'),
            ('lead_qualify', 'Lead Qualification'),
            ('document', 'Document Request'),
            ('other', 'Other'),
        ],
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"


class Lead(models.Model):
    """Qualified leads captured from chatbot conversations."""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('scheduled', 'Appointment Scheduled'),
        ('closed', 'Closed'),
        ('lost', 'Lost'),
    ]
    
    conversation = models.OneToOneField(
        ChatbotConversation,
        on_delete=models.CASCADE,
        related_name='lead'
    )
    
    # Lead info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100, null=True, blank=True)
    
    # Property preferences
    interested_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interested_leads'
    )
    property_type_preference = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=Property.PROPERTY_TYPES
    )
    budget_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum budget"
    )
    budget_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum budget"
    )
    
    # Buyer profile
    buyer_type = models.CharField(
        max_length=20,
        choices=[
            ('buyer', 'Buyer'),
            ('renter', 'Renter'),
            ('agent', 'Agent'),
            ('investor', 'Investor'),
        ],
        null=True,
        blank=True
    )
    timeline = models.CharField(
        max_length=50,
        choices=[
            ('immediate', 'Immediate (0-2 weeks)'),
            ('soon', 'Soon (1-3 months)'),
            ('later', 'Later (3-6 months)'),
            ('flexible', 'Flexible/Exploring'),
        ],
        null=True,
        blank=True,
        help_text="Timeline for purchase/rent"
    )
    
    # Lead status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    # Assignment
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes from bot/agent")
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.status})"


class Appointment(models.Model):
    """Schedule property tours/consultations."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_tours'
    )
    
    appointment_type = models.CharField(
        max_length=50,
        choices=[
            ('property_tour', 'Property Tour'),
            ('consultation', 'Virtual Consultation'),
            ('document_review', 'Document Review'),
            ('follow_up', 'Follow-up Call'),
        ],
        default='property_tour'
    )
    
    scheduled_at = models.DateTimeField(help_text="Desired appointment datetime")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Agent assignment
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_appointments'
    )
    
    # Confirmation
    agent_confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmation_sent = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Tour notes or special requests")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"Tour: {self.lead.first_name} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"

    def is_upcoming(self):
        """Check if appointment is in the future."""
        return self.scheduled_at > timezone.now()


class ChatbotAnalytics(models.Model):
    """Track chatbot performance and metrics."""
    
    date = models.DateField(auto_now_add=True)
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    leads_qualified = models.IntegerField(default=0)
    appointments_scheduled = models.IntegerField(default=0)
    avg_conversation_duration = models.IntegerField(
        default=0,
        help_text="In seconds"
    )
    avg_messages_per_conversation = models.FloatField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Chatbot Analytics"

    def __str__(self):
        return f"Analytics - {self.date}"
