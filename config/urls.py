"""
URL configuration for LuxeEstate.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('oauth/', include('allauth.urls')),
    path('favorites/', include('favorites.urls')),
    path('messages/', include('messaging.urls')),
    path('payments/', include('payments.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    path('chatbot/', include('chatbot.dashboard_urls')),
    path('', include('properties.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
