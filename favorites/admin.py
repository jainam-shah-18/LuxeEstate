from django.contrib import admin
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    list_filter = ('user', 'property', 'created_at')
    search_fields = ('user__username', 'property__title')
    readonly_fields = ('created_at',)
