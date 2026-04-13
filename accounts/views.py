from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta
from .models import Profile
from .forms import CustomUserCreationForm, OTPVerificationForm, ProfileForm
from .utils import send_otp_email
import random
import string

OTP_VERIFY_MAX_ATTEMPTS = getattr(settings, 'OTP_VERIFY_MAX_ATTEMPTS', 5)
OTP_VERIFY_WINDOW_SECONDS = getattr(settings, 'OTP_VERIFY_WINDOW_SECONDS', 600)
OTP_RESEND_COOLDOWN_SECONDS = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)


def agent_list(request):
    """Public list of verified agent profiles."""
    agents = Profile.objects.select_related('user').filter(
        role='agent',
        email_verified=True
    ).order_by('-rating', '-total_reviews', 'user__first_name', 'user__username')
    return render(request, 'accounts/agent_list.html', {'agents': agents})


def _otp_verify_limit_key(user_id):
    return f'otp:verify:attempts:{user_id}'


def _otp_resend_limit_key(user_id):
    return f'otp:resend:last:{user_id}'


def _otp_email_user_message(error_code):
    """Human-readable hint after send_otp_email returns a failure code."""
    if error_code == "auth":
        return (
            "Could not send the OTP email: the SMTP server rejected the username or password (often "
            "shown as 535 in logs). For Gmail or Google Workspace you must use a 16-character App Password "
            "when 2‑Step Verification is on—set EMAIL_HOST_USER to your full email and EMAIL_HOST_PASSWORD "
            "to that app password in .env. Organization accounts may require an admin to allow SMTP / "
            "less secure apps. See https://support.google.com/mail/?p=BadCredentials"
        )
    if error_code == "tls":
        return (
            "Could not send the OTP email due to TLS certificate verification (see logs/django.log). "
            "If you see CERTIFICATE_VERIFY_FAILED or Basic Constraints, your network may be inspecting "
            "TLS—for local dev only, set EMAIL_SMTP_INSECURE_SKIP_VERIFY=True in .env, or add your "
            "corporate root CA via EMAIL_SMTP_CA_BUNDLE. Use EMAIL_BACKEND=LuxeEstate.smtp_backend.EmailBackend "
            "and install certifi."
        )
    return (
        "Could not send the OTP email. Open logs/django.log for the exact error and verify EMAIL_* settings."
    )


# ============================================
# Authentication Views
# ============================================

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('properties:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.save()
            
            # Update profile with role
            user.profile.role = form.cleaned_data.get('user_type', 'buyer')
            user.profile.save()
            
            # Generate OTP
            otp = user.profile.generate_otp()
            user.profile.otp_created_at = timezone.now()
            user.profile.save()
            
            # Send OTP via email
            otp_err = send_otp_email(
                user.email,
                otp,
                user.first_name or None,
            )
            if otp_err:
                messages.warning(
                    request,
                    'User created but the OTP email could not be sent. ' + _otp_email_user_message(otp_err),
                )

            # Store user ID in session for OTP verification
            request.session['user_id_for_otp'] = user.id
            if otp_err:
                messages.info(
                    request,
                    'After fixing email settings, use “Resend OTP” on the verification page.',
                )
            else:
                messages.success(
                    request,
                    'Registration successful! Please verify your email with the OTP sent to your inbox.',
                )
            return redirect('accounts:verify_otp')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_otp(request):
    """OTP verification view"""
    user_id = request.session.get('user_id_for_otp')
    if not user_id:
        messages.error(request, 'Invalid request. Please register again.')
        return redirect('accounts:register')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            # Check OTP validity
            otp_created = user.profile.otp_created_at
            if not otp_created or (timezone.now() - otp_created) > timedelta(minutes=10):
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('accounts:request_otp')
            
            # Verify OTP
            if user.profile.verify_otp(otp_code):
                user.profile.email_verified = True
                user.profile.otp_code = None
                user.profile.save()
                cache.delete(_otp_verify_limit_key(user.id))
                
                # Log user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['user_id_for_otp']
                next_page = request.session.pop('post_otp_redirect', 'accounts:complete_profile')
                
                messages.success(request, 'Email verified successfully! Welcome to LuxeEstate.')
                return redirect(next_page)
            else:
                attempt_key = _otp_verify_limit_key(user.id)
                attempts = cache.get(attempt_key, 0) + 1
                cache.set(attempt_key, attempts, timeout=OTP_VERIFY_WINDOW_SECONDS)
                if attempts >= OTP_VERIFY_MAX_ATTEMPTS:
                    messages.error(
                        request,
                        'Too many invalid OTP attempts. Please wait a few minutes and request a new OTP.'
                    )
                    return redirect('accounts:request_otp')
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': user.email})


def request_otp(request):
    """Request new OTP"""
    user_id = request.session.get('user_id_for_otp')
    if not user_id:
        return redirect('accounts:register')
    
    user = get_object_or_404(User, id=user_id)
    
    resend_key = _otp_resend_limit_key(user.id)
    if cache.get(resend_key):
        messages.warning(
            request,
            f'Please wait {OTP_RESEND_COOLDOWN_SECONDS} seconds before requesting another OTP.'
        )
        return redirect('accounts:verify_otp')

    # Generate new OTP
    otp = user.profile.generate_otp()
    user.profile.otp_created_at = timezone.now()
    user.profile.save()
    cache.set(resend_key, True, timeout=OTP_RESEND_COOLDOWN_SECONDS)
    
    # Send OTP via email
    otp_err = send_otp_email(user.email, otp, user.first_name or None)
    if otp_err:
        messages.error(request, _otp_email_user_message(otp_err))
    else:
        messages.success(request, 'New OTP sent to your email.')
    
    return redirect('accounts:verify_otp')


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('properties:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # Authenticate using email
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            profile = user.profile
            otp = profile.generate_otp()
            profile.otp_created_at = timezone.now()
            profile.save(update_fields=['otp_code', 'otp_created_at'])
            request.session['user_id_for_otp'] = user.id
            request.session['post_otp_redirect'] = request.GET.get('next') or 'properties:home'
            otp_err = send_otp_email(
                user.email,
                otp,
                user.first_name or None,
            )
            if otp_err:
                messages.error(request, _otp_email_user_message(otp_err))
            messages.warning(request, 'An OTP has been sent to your email. Enter it to complete login.')
            return redirect('accounts:verify_otp')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('properties:home')


# ============================================
# Profile Views
# ============================================

@login_required
def complete_profile(request):
    """Complete user profile after registration"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('properties:home')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/complete_profile.html', {'form': form})


@login_required
def profile_view(request):
    """View user profile"""
    return render(request, 'accounts/profile.html', {'profile': request.user.profile})


@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')


@login_required
def dashboard(request):
    """User dashboard"""
    if request.user.profile.role == 'agent':
        # Agent dashboard
        properties = request.user.properties.all()
        return render(request, 'accounts/agent_dashboard.html', {'properties': properties})
    else:
        # Buyer dashboard
        from favorites.models import Favorite
        favorites = Favorite.objects.filter(user=request.user)
        recent_views = request.user.property_views.all()[:10]
        return render(request, 'accounts/buyer_dashboard.html', {
            'favorites': favorites,
            'recent_views': recent_views
        })
