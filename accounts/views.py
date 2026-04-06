import random
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from .forms import CustomUserCreationForm, OTPVerificationForm, LoginForm
from .models import EmailOTP, CustomUser
from django.conf import settings

def send_otp_email(email, otp):
    subject = "Your LuxeEstate Account OTP"
    message = f"Your OTP for registration is {otp}. Please enter this to verify your account."
    email_from = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@luxeestate.com'
    send_mail(subject, message, email_from, [email])

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Deactivate until verified
            user.save()
            
            # Generate OTP
            otp = f"{random.randint(100000, 999999)}"
            EmailOTP.objects.update_or_create(email=user.email, defaults={'otp': otp})
            send_otp_email(user.email, otp)
            
            request.session['registration_email'] = user.email
            messages.success(request, 'Registration successful. Please check your email for the OTP.')
            return redirect('accounts:verify_otp', email=user.email)
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_otp(request, email):
    otp_record = EmailOTP.objects.filter(email=email).first()
    otp_expiry_minutes = 10

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_input = form.cleaned_data.get('otp')
            try:
                otp_record = EmailOTP.objects.get(email=email)
                if otp_record.created_at < timezone.now() - timedelta(minutes=otp_expiry_minutes):
                    otp_record.delete()
                    messages.error(request, 'OTP expired. Please request a new OTP.')
                    return redirect('accounts:resend_otp', email=email)
                if otp_record.otp == otp_input:
                    user = CustomUser.objects.get(email=email)
                    user.is_verified = True
                    user.is_active = True
                    user.save()
                    otp_record.delete()
                    
                    login(request, user)
                    messages.success(request, 'Account verified successfully!')
                    return redirect('properties:home')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
            except EmailOTP.DoesNotExist:
                messages.error(request, 'No OTP session found. Please register again.')
    else:
        form = OTPVerificationForm()
    
    return render(
        request,
        'accounts/verify_otp.html',
        {
            'form': form,
            'email': email,
            'otp_record': otp_record,
            'otp_expiry_minutes': otp_expiry_minutes,
        },
    )


def resend_otp(request, email):
    user = CustomUser.objects.filter(email=email, is_verified=False).first()
    if not user:
        messages.info(request, 'This account is already verified or does not exist.')
        return redirect('accounts:login')

    otp = f"{random.randint(100000, 999999)}"
    EmailOTP.objects.update_or_create(email=user.email, defaults={'otp': otp})
    send_otp_email(user.email, otp)
    messages.success(request, 'A new OTP has been sent to your email.')
    return redirect('accounts:verify_otp', email=user.email)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_verified:
                    login(request, user)
                    messages.success(request, f"Welcome back, {email}!")
                    return redirect('properties:home')
                else:
                    messages.error(request, 'Please verify your email before logging in.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('properties:home')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'profile_user': request.user})
