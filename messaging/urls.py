from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('contact/<int:pk>/', views.contact_agent, name='contact_agent'),
    path('chat/', views.chat_threads, name='chat_threads'),
    path('chat/<int:thread_id>/', views.chat_room, name='chat_room'),
    path('chat/start/<int:pk>/', views.start_chat, name='start_chat'),
]
