from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from properties.models import Property
from .models import Favorite

@require_http_methods(["POST"])
def toggle_favorite(request, property_id):
    # Handle AJAX requests from unauthenticated users
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to add favorites'
        }, status=401)
    
    if not request.user.is_authenticated:
        return redirect(f'{settings.LOGIN_URL}?next=/favorites/list/')
    
    try:
        property = get_object_or_404(Property, pk=property_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, property=property)
        
        if not created:
            # Favorite exists, remove it
            favorite.delete()
            is_favorite = False
            message = 'Removed from favorites.'
        else:
            # New favorite created
            is_favorite = True
            message = 'Added to favorites.'
        
        messages.success(request, message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'is_favorite': is_favorite, 
                'message': message
            })
        
        return redirect('properties:detail', pk=property_id)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)
        messages.error(request, f'Error toggling favorite: {str(e)}')
        return redirect('properties:detail', pk=property_id)

@require_http_methods(["POST"])
def add_favorite(request, property_id):
    # Handle AJAX requests from unauthenticated users
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to add favorites'
        }, status=401)
    
    if not request.user.is_authenticated:
        return redirect(f'{settings.LOGIN_URL}?next=/favorites/list/')
    
    try:
        property = get_object_or_404(Property, pk=property_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, property=property)
        message = 'Added to favorites.'
        messages.success(request, message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': message
            })
        
        return redirect('properties:detail', pk=property_id)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)
        messages.error(request, f'Error adding to favorites: {str(e)}')
        return redirect('properties:detail', pk=property_id)

@require_http_methods(["POST"])
def remove_favorite(request, property_id):
    # Handle AJAX requests from unauthenticated users
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to remove favorites'
        }, status=401)
    
    if not request.user.is_authenticated:
        return redirect(f'{settings.LOGIN_URL}?next=/favorites/list/')
    
    try:
        property = get_object_or_404(Property, pk=property_id)
        Favorite.objects.filter(user=request.user, property=property).delete()
        message = 'Removed from favorites.'
        messages.success(request, message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': message
            })
        
        return redirect('properties:detail', pk=property_id)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)
        messages.error(request, f'Error removing from favorites: {str(e)}')
        return redirect('properties:detail', pk=property_id)

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('property')
    return render(request, 'favorites/list.html', {'favorites': favorites})
