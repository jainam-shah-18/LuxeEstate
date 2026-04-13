from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # Home and listing
    path('', views.home, name='home'),
    path('list/', views.property_list, name='list'),
    path('search/', views.search, name='search'),
    
    # Property details and management
    path('detail/<int:pk>/', views.property_detail, name='detail'),
    path('detail/<int:pk>/route/', views.property_route_map, name='route_map'),
    path('add/', views.add_property, name='add_property'),
    path('edit/<int:pk>/', views.edit_property, name='edit_property'),
    path('delete/<int:pk>/', views.delete_property, name='delete_property'),
    path('my-properties/', views.my_properties, name='my_properties'),
    
    # Images
    path('image/<int:image_id>/delete/', views.delete_property_image, name='delete_image'),
    
    # AJAX/Utility
    path('api/cities/', views.get_cities, name='get_cities'),
    path('api/filter/', views.filter_properties, name='filter_properties'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/nearby-places/', views.fetch_nearby_places, name='nearby_places'),
    path('api/retry-geocode/<int:pk>/', views.retry_property_geocode, name='retry_geocode'),
    path('api/generate-description/', views.generate_ai_description, name='generate_ai_description'),
    path('api/chatbot/', views.chatbot_response, name='chatbot_response'),
    path('api/search-by-image/', views.search_by_image, name='search_by_image'),
    path('compare/', views.compare_properties, name='compare_properties'),
    path('add-to-comparison/<int:property_id>/', views.add_to_comparison, name='add_to_comparison'),
    path('comparison-list/', views.comparison_list, name='comparison_list'),
    path('clear-comparison/', views.clear_comparison, name='clear_comparison'),
]