from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('request-otp/', views.request_otp, name='request_otp'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
