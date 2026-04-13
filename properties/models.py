from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone
from django.db.models import F
import json


class Property(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('plot', 'Plot'),
        ('commercial', 'Commercial'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('farmland', 'Farmland'),
    ]
    
    FURNISHING_CHOICES = [
        ('unfurnished', 'Unfurnished'),
        ('semi-furnished', 'Semi-Furnished'),
        ('furnished', 'Furnished'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
    ]

    # Basic Information
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPES,
        db_index=True
    )
    
    # Property Details
    bedrooms = models.PositiveIntegerField(blank=True, null=True)
    bathrooms = models.PositiveIntegerField(blank=True, null=True)
    area_sqft = models.PositiveIntegerField(blank=True, null=True, help_text="Area in sq ft")
    furnishing = models.CharField(
        max_length=20,
        choices=FURNISHING_CHOICES,
        default='unfurnished'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    
    # Agent/Owner Information
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metrics
    views_count = models.PositiveIntegerField(default=0, db_index=True)
    
    # Rating and Reviews
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.PositiveIntegerField(default=0)

    # Nearby Locations (Places of Interest) - Enhanced structure
    nearby_hospital = models.JSONField(default=list, blank=True, help_text="List of nearby hospitals with distance")
    nearby_railway_station = models.JSONField(default=list, blank=True, help_text="List of nearby railway stations")
    nearby_shopping_mall = models.JSONField(default=list, blank=True)
    nearby_bus_stand = models.JSONField(default=list, blank=True)
    nearby_school = models.JSONField(default=list, blank=True)
    nearby_airport = models.JSONField(default=list, blank=True)
    nearby_park = models.JSONField(default=list, blank=True)
    nearby_supermarket = models.JSONField(default=list, blank=True)
    nearby_restaurant = models.JSONField(default=list, blank=True)
    nearby_other_places = models.JSONField(default=list, blank=True, help_text="Any other important nearby daily-life places")
    
    # Additional Nearby Locations
    nearby_gym = models.JSONField(default=list, blank=True)
    nearby_hospital_emergency = models.JSONField(default=list, blank=True)
    nearby_bank = models.JSONField(default=list, blank=True)
    nearby_atm = models.JSONField(default=list, blank=True)
    nearby_pharmacy = models.JSONField(default=list, blank=True)
    nearby_metro = models.JSONField(default=list, blank=True)
    nearby_university = models.JSONField(default=list, blank=True)
    nearby_theater = models.JSONField(default=list, blank=True)
    
    # Amenities
    amenities = models.JSONField(default=list, blank=True, help_text="List of amenities: parking, pool, gym, etc")
    
    # AI Generated Content
    ai_generated_description = models.TextField(blank=True, null=True)
    ai_tags = models.JSONField(default=list, blank=True, help_text="AI-generated tags for search")
    
    # Additional Amenities
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_promoted = models.BooleanField(default=False)
    promotion_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', '-created_at']),
            models.Index(fields=['property_type', '-price']),
            models.Index(fields=['-views_count']),
            models.Index(fields=['-rating']),
            models.Index(fields=['status', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} - {self.city}"

    def get_absolute_url(self):
        return reverse('properties:detail', kwargs={'pk': self.pk})

    @property
    def formatted_price(self):
        return f"₹{self.price:,.0f}"

    @property
    def get_property_type_display(self):
        return dict(self.PROPERTY_TYPES).get(self.property_type, self.property_type)
    
    def increment_views(self):
        """Atomically increment view count on every detail hit."""
        Property.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)
        self.refresh_from_db(fields=['views_count'])
    
    def get_nearby_locations_summary(self):
        """Get summary of nearby locations"""
        locations = {
            'Hospital': len(self.nearby_hospital) if self.nearby_hospital else 0,
            'Railway': len(self.nearby_railway_station) if self.nearby_railway_station else 0,
            'Shopping Mall': len(self.nearby_shopping_mall) if self.nearby_shopping_mall else 0,
            'School': len(self.nearby_school) if self.nearby_school else 0,
            'Airport': len(self.nearby_airport) if self.nearby_airport else 0,
        }
        return locations


class PropertyImage(models.Model):
    """Multiple images per property"""
    
    property = models.ForeignKey(
        Property,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='property_images/%Y/%m/%d/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    # AI Analysis
    ai_detected_features = models.JSONField(default=list, blank=True, help_text="Features detected by AI")
    ai_description = models.TextField(blank=True, null=True, help_text="AI-generated image description")
    ai_visual_signature = models.JSONField(
        default=dict,
        blank=True,
        help_text="Compact visual signature used for image similarity search",
    )

    class Meta:
        ordering = ['-is_primary', '-uploaded_at']

    def __str__(self):
        return f"Image for {self.property.title}"


class PropertyReview(models.Model):
    """Reviews and ratings for properties"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=100, blank=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('property', 'reviewer')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.property.title}"


class PropertyComparison(models.Model):
    """Users can compare multiple properties"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_comparisons')
    properties = models.ManyToManyField(Property)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"

