from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'chatbot'

router = DefaultRouter()
router.register(r'conversations', views.ChatbotConversationViewSet, basename='conversation')
router.register(r'leads', views.LeadViewSet, basename='lead')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('api/', include(router.urls)),
]
