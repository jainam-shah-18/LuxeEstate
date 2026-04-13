from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversations
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Contacting agents
    path('contact/<int:property_id>/', views.contact_agent, name='contact'),
    path('send/<int:property_id>/', views.send_message, name='send_message'),
    
    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_read'),
    
    # Legacy URLs (backward compatibility)
    path('list/', views.contact_list, name='contact_list'),
    path('chat/<int:property_id>/', views.chat, name='chat'),
]