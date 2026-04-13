from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, UserPropertyView, SavedSearch


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'
    extra = 0
    fields = ('role', 'phone', 'email_verified', 'is_google_account', 'rating')


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'email_verified', 'phone', 'rating', 'created_at')
    list_filter = ('role', 'email_verified', 'is_google_account', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('otp_code', 'otp_created_at', 'created_at', 'updated_at')
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'role')
        }),
        ('Profile Details', {
            'fields': ('phone', 'bio', 'profile_picture', 'favorite_cities', 'preferred_property_type')
        }),
        ('Email Verification', {
            'fields': ('email_verified', 'otp_code', 'otp_created_at'),
            'classes': ('collapse',)
        }),
        ('Social Auth', {
            'fields': ('google_id', 'is_google_account'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('rating', 'total_reviews', 'last_login_ip')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserPropertyView)
class UserPropertyViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'viewed_at')
    list_filter = ('viewed_at', 'user')
    search_fields = ('user__username', 'property__title')
    readonly_fields = ('viewed_at',)


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'name')
    readonly_fields = ('created_at',)
