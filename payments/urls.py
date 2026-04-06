from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('premium/', views.premium_checkout, name='premium_checkout'),
    path('create-order/', views.create_order, name='create_order'),
    path('verify/', views.verify_payment, name='verify_payment'),
]
