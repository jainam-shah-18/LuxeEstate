from django.urls import path

from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.property_list, name='property_list'),
    path('search/image/', views.image_search, name='image_search'),
    path('search/image/api/', views.image_analyze_api, name='image_analyze_api'),
    path('search/image/results/', views.image_search_results, name='image_search_results'),
    path('ai/chat/', views.ai_chat, name='ai_chat'),
    path('ai/chat/api/', views.ai_chat_api, name='ai_chat_api'),
    path('ai/recommendations/', views.recommendations, name='recommendations'),
    path('ai/image-upload/', views.image_upload, name='image_upload'),
    path('ai/generate-description/', views.generate_description_api, name='generate_description_api'),
    path('profile/', views.user_profile, name='user_profile'),
    path('ai/nearby-places/', views.nearby_places_api, name='nearby_places_api'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('property/add/', views.property_create, name='property_create'),
    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('property/<int:pk>/chatbot/', views.chatbot_api, name='chatbot_api'),
]
