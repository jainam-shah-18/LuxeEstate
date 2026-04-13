from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('toggle/<int:property_id>/', views.toggle_favorite, name='toggle'),
    path('add/<int:property_id>/', views.add_favorite, name='add_favorite'),
    path('remove/<int:property_id>/', views.remove_favorite, name='remove_favorite'),
    path('list/', views.favorite_list, name='favorite_list'),
]