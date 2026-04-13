from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # Analytics
    path('users/', views.user_analytics, name='users'),
    path('properties/', views.property_analytics, name='properties'),
    path('revenue/', views.revenue_analytics, name='revenue'),
    path('engagement/', views.engagement_analytics, name='engagement'),
]
