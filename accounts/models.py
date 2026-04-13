from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
import random
import string

class Profile(models.Model):
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('owner', 'Owner'),
        ('agent', 'Agent'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # OTP and Email Verification
    email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Social Authentication
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    is_google_account = models.BooleanField(default=False)
    
    # Location Preferences
    favorite_cities = models.TextField(blank=True, null=True, help_text="Comma-separated cities")
    preferred_property_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Rating (for agents)
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Metadata
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        return self.otp_code
    
    def verify_otp(self, code):
        """Verify OTP code"""
        return self.otp_code == code

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class UserPropertyView(models.Model):
    """Track user views on properties"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_views')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='viewed_by')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'property')
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user.username} viewed {self.property.title}"


class SavedSearch(models.Model):
    """Save user's search filters"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    query = models.JSONField()  # Store search filters as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
