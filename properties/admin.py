from django.contrib import admin
from .models import Property, PropertyImage, PropertyReview, PropertyComparison, Lead, Appointment, TelegramUser


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


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'intent', 'qualification_stage', 'status', 'source', 'created_at')
    list_filter = ('qualification_stage', 'status', 'source', 'intent', 'created_at')
    search_fields = ('name', 'contact', 'location', 'session_id')
    readonly_fields = ('created_at', 'updated_at', 'score')
    
    fieldsets = (
        ('Lead Information', {
            'fields': ('name', 'contact', 'intent', 'source', 'session_id')
        }),
        ('Property Criteria', {
            'fields': ('location', 'property_type', 'bhk', 'budget')
        }),
        ('Qualification & Status', {
            'fields': ('qualification_stage', 'status', 'score', 'assigned_agent')
        }),
        ('Notes & History', {
            'fields': ('notes', 'ip_address', 'created_at', 'updated_at', 'last_contacted'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('lead', 'property', 'scheduled_datetime', 'status', 'assigned_agent', 'created_at')
    list_filter = ('status', 'scheduled_datetime', 'created_at')
    search_fields = ('lead__name', 'property__title')
    readonly_fields = ('created_at', 'updated_at', 'confirmed_at', 'completed_at')
    
    fieldsets = (
        ('Lead & Property', {
            'fields': ('lead', 'property')
        }),
        ('Appointment Details', {
            'fields': ('scheduled_datetime', 'duration_minutes', 'status')
        }),
        ('Assignment & Confirmation', {
            'fields': ('assigned_agent', 'confirmation_sent', 'reminder_sent', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_username', 'telegram_first_name', 'message_count', 'last_active_at', 'is_connected', 'lead')
    list_filter = ('is_connected', 'language', 'last_active_at', 'connection_started_at')
    search_fields = ('telegram_username', 'telegram_first_name', 'telegram_id', 'session_id')
    readonly_fields = ('telegram_id', 'session_id', 'connection_started_at', 'last_active_at', 'message_count')
    
    fieldsets = (
        ('Telegram Profile', {
            'fields': ('telegram_id', 'telegram_username', 'telegram_first_name', 'telegram_last_name')
        }),
        ('Session Information', {
            'fields': ('session_id', 'conversation_state', 'last_message_text')
        }),
        ('Activity', {
            'fields': ('message_count', 'last_message_at', 'last_active_at', 'is_connected')
        }),
        ('Linked Data', {
            'fields': ('lead', 'language', 'receive_notifications')
        }),
        ('Timeline', {
            'fields': ('connection_started_at',),
            'classes': ('collapse',)
        }),
    )

