from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from accounts.views import agent_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls')),
    path('accounts/profile/', RedirectView.as_view(url='/auth/profile/', permanent=False)),
    path('accounts/change-password/', RedirectView.as_view(pattern_name='account_change_password', permanent=False)),
    path('accounts/', include('allauth.urls')),
    path('properties/search/', RedirectView.as_view(pattern_name='properties:search', permanent=False)),
    path('', include('properties.urls')),
    path('favorites/', include('favorites.urls')),
    path('messaging/', include('messaging.urls')),
    path('payments/', include('payments.urls')),
    path('dashboard/', include('admin_dashboard.urls')),
    path('agents/', agent_list, name='agents'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('cookies/', TemplateView.as_view(template_name='cookies.html'), name='cookies'),
    path('sitemap/', TemplateView.as_view(template_name='sitemap.html'), name='sitemap'),
    path('api/telegram/', include('properties.telegram_urls')),]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
