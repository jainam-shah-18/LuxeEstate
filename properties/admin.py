from django.contrib import admin
from .models import Property, PropertyImage, PropertyReview, PropertyComparison


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'alt_text', 'is_primary', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_type', 'city', 'formatted_price', 'agent', 'views_count', 'rating', 'status', 'created_at')
    list_filter = ('property_type', 'city', 'status', 'furnishing', 'is_featured', 'is_active', 'created_at')
    search_fields = ('title', 'address', 'city', 'agent__username')
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'rating', 'total_reviews')
    inlines = [PropertyImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'property_type', 'status')
        }),
        ('Location', {
            'fields': ('city', 'state', 'address', 'pincode', 'latitude', 'longitude')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'area_sqft', 'furnishing')
        }),
        ('Pricing & Agent', {
            'fields': ('price', 'agent')
        }),
        ('Nearby Locations', {
            'fields': ('nearby_hospital', 'nearby_school', 'nearby_shopping_mall', 'nearby_railway_station'),
            'classes': ('collapse',)
        }),
        ('AI & Tags', {
            'fields': ('ai_generated_description', 'ai_tags'),
            'classes': ('collapse',)
        }),
        ('Statistics & Promotion', {
            'fields': ('views_count', 'rating', 'total_reviews', 'is_featured', 'is_promoted', 'promotion_until')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at', 'property')
    search_fields = ('property__title', 'alt_text')
    readonly_fields = ('uploaded_at',)


@admin.register(PropertyReview)
class PropertyReviewAdmin(admin.ModelAdmin):
    list_display = ('property', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'property')
    search_fields = ('property__title', 'reviewer__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PropertyComparison)
class PropertyComparisonAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'name')
    filter_horizontal = ('properties',)
    readonly_fields = ('created_at',)
