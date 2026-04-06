from django.urls import path

from . import views

app_name = 'favorites'

urlpatterns = [
    path('', views.favorite_list, name='list'),
    path('toggle/<int:pk>/', views.favorite_toggle, name='toggle'),
]
