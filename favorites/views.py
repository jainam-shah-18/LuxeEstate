from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from properties.models import Property

from .models import Favorite


@login_required
def favorite_list(request):
    favs = Favorite.objects.filter(user=request.user).select_related('property').order_by('-created_at')
    return render(request, 'favorites/list.html', {'favorites': favs})


@login_required
@require_POST
def favorite_toggle(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, property=prop)
    if not created:
        fav.delete()
        messages.info(request, 'Removed from favorites.')
    else:
        messages.success(request, 'Saved to favorites.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('properties:property_detail', pk=pk)
