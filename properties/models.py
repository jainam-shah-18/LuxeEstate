from django.db import models
from django.conf import settings


class Property(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('house', 'Independent House'),
        ('plot', 'Plot/Land'),
        ('commercial', 'Commercial Space'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    city = models.CharField(max_length=100)
    address = models.TextField()
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    ai_generated_description = models.TextField(blank=True)
    seo_meta_description = models.CharField(max_length=320, blank=True)
    seo_keywords = models.JSONField(default=dict, blank=True)  # Stores keyword data
    image_features_json = models.JSONField(default=dict, blank=True)
    seo_score = models.PositiveIntegerField(default=0, blank=True)  # SEO quality score (0-100)

    def __str__(self):
        return f"{self.title} - {self.city}"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')

    def __str__(self):
        return f"Image for {self.property.title}"


class NearbyLocation(models.Model):
    PLACE_TYPES = [
        ('hospital', 'Hospital'),
        ('school', 'School'),
        ('college', 'College / University'),
        ('park', 'Park'),
        ('mall', 'Shopping Mall'),
        ('station', 'Railway Station'),
        ('metro', 'Metro Station'),
        ('airport', 'Airport'),
        ('supermarket', 'Supermarket'),
        ('restaurant', 'Restaurant'),
        ('bus_stand', 'Bus Stand'),
        ('gym', 'Gym / Fitness'),
        ('bank', 'Bank'),
        ('atm', 'ATM'),
        ('pharmacy', 'Pharmacy'),
        ('cinema', 'Cinema / Multiplex'),
        ('temple', 'Temple'),
        ('mosque', 'Mosque'),
        ('church', 'Church'),
        ('office_park', 'IT Park / Office Hub'),
        ('fuel', 'Petrol Pump'),
        ('other', 'Other'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='nearby_locations')
    place_type = models.CharField(max_length=50, choices=PLACE_TYPES)
    name = models.CharField(max_length=255)
    distance = models.CharField(max_length=50)
    place_id = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.distance}) near {self.property.title}"


class UserSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, blank=True)
    property_type = models.CharField(max_length=50, blank=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    feature = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} searched {self.city} {self.property_type}"


class UserView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(default=0)  # in seconds

    class Meta:
        unique_together = ('user', 'property')

    def __str__(self):
        return f"{self.user.email} viewed {self.property.title}"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferred_cities = models.JSONField(default=list, blank=True)  # list of cities
    preferred_property_types = models.JSONField(default=list, blank=True)  # list of types
    location_history = models.JSONField(default=list, blank=True)  # list of lat/lng or cities

    def __str__(self):
        return f"Profile for {self.user.email}"
