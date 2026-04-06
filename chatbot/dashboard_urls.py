from django.urls import path
from . import dashboard_views

app_name = 'chatbot_dashboard'

urlpatterns = [
    path('dashboard/', dashboard_views.ChatbotDashboardView.as_view(), name='dashboard'),
]
