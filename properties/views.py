import json
import base64
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import F, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
import requests

from messaging.models import ChatThread

from properties.ai_services import (
    analyze_property_image,
    chatbot_reply,
    generate_property_description,
    generate_comprehensive_seo_data,
    merge_image_features,
    recommend_for_user,
    seo_snippet,
    detect_property_features_advanced,
    search_properties_by_features,
)

from .forms import NearbyLocationFormSet, PropertyForm, PropertyImageFormSet, UserProfileForm
from .models import Property, PropertyImage, UserSearch, UserView, UserProfile, UserSearch, UserView, UserProfile


def home(request):
    featured_qs = Property.objects.select_related('agent').prefetch_related('images')
    featured = list(featured_qs.filter(is_featured=True).order_by('-created_at')[:8])
    if len(featured) < 4:
        featured = list(featured_qs.order_by('-views_count', '-created_at')[:8])
    total_listings = Property.objects.count()
    city_count = Property.objects.values('city').distinct().count()
    return render(
        request,
        'properties/home.html',
        {
            'featured': featured,
            'total_listings': total_listings,
            'city_count': city_count,
            'property_types': Property.PROPERTY_TYPES,
        },
    )


def property_list(request):
    qs = Property.objects.select_related('agent').prefetch_related('images')
    city = request.GET.get('city', '').strip()
    ptype = request.GET.get('property_type', '').strip()
    min_p = request.GET.get('min_price')
    max_p = request.GET.get('max_price')
    feature = request.GET.get('feature', '').strip()

    if city:
        qs = qs.filter(city__icontains=city)
    if ptype:
        qs = qs.filter(property_type=ptype)
    if min_p:
        try:
            qs = qs.filter(price__gte=min_p)
        except (ValueError, TypeError):
            pass
    if max_p:
        try:
            qs = qs.filter(price__lte=max_p)
        except (ValueError, TypeError):
            pass
    if feature:
        qs = qs.filter(
            Q(description__icontains=feature)
            | Q(title__icontains=feature)
            | Q(ai_generated_description__icontains=feature)
            | Q(image_features_json__icontains=feature)
        )

    # Track user search
    if request.user.is_authenticated and (city or ptype or min_p or max_p or feature):
        UserSearch.objects.create(
            user=request.user,
            city=city,
            property_type=ptype,
            min_price=min_p if min_p else None,
            max_price=max_p if max_p else None,
            feature=feature,
        )

    ctx = {
        'properties': qs.order_by('-is_featured', '-created_at'),
        'filters': {
            'city': city,
            'property_type': ptype,
            'min_price': min_p or '',
            'max_price': max_p or '',
            'feature': feature,
        },
        'property_types': Property.PROPERTY_TYPES,
    }
    return render(request, 'properties/list.html', ctx)


def property_detail(request, pk):
    prop = get_object_or_404(
        Property.objects.select_related('agent').prefetch_related('images', 'nearby_locations'),
        pk=pk,
    )
    session_key = f'property_viewed_{pk}'
    if not request.session.get(session_key):
        Property.objects.filter(pk=pk).update(views_count=F('views_count') + 1)
        prop.refresh_from_db(fields=['views_count'])
        request.session[session_key] = True

    # Track user view
    if request.user.is_authenticated:
        UserView.objects.get_or_create(
            user=request.user,
            property=prop,
            defaults={'timestamp': None}  # will auto set
        )

    from favorites.models import Favorite

    is_fav = False
    if request.user.is_authenticated:
        is_fav = Favorite.objects.filter(user=request.user, property=prop).exists()

    thread = None
    if request.user.is_authenticated and request.user != prop.agent:
        thread = ChatThread.objects.filter(property=prop, buyer=request.user).first()

    recommended = recommend_for_user(request.user, limit=6, exclude_pk=prop.pk)

    return render(
        request,
        'properties/detail.html',
        {
            'property': prop,
            'is_favorite': is_fav,
            'chat_thread': thread,
            'recommended': recommended,
        },
    )


@login_required
def ai_chat(request):
    return render(request, 'properties/ai_chat.html')


@login_required
@require_http_methods(['POST'])
def ai_chat_api(request):
    try:
        msg = ''
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = json.loads(request.body.decode() or '{}')
                msg = body.get('message', '')
            except json.JSONDecodeError:
                msg = ''
        else:
            msg = request.POST.get('message', '')
        
        if not msg:
            return JsonResponse({
                'reply': 'Please enter a message to continue.'
            })
        
        reply = chatbot_reply(msg, property_title=None)
        return JsonResponse({'reply': reply})
    except Exception as e:
        print(f"Error in ai_chat_api: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'reply': "Thanks for your message. For detailed answers, please use Contact Agent or continue in live chat with the listing owner."
        }, status=200)


@login_required
def user_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated! AI recommendations will improve.')
            return redirect('properties:recommendations')
    else:
        form = UserProfileForm(instance=profile)

    # Get user stats for display
    search_count = UserSearch.objects.filter(user=request.user).count()
    view_count = UserView.objects.filter(user=request.user).count()
    favorite_count = 0
    try:
        from favorites.models import Favorite
        favorite_count = Favorite.objects.filter(user=request.user).count()
    except:
        pass

    context = {
        'form': form,
        'search_count': search_count,
        'view_count': view_count,
        'favorite_count': favorite_count,
    }
    return render(request, 'properties/user_profile.html', context)


@login_required
def recommendations(request):
    recommended = recommend_for_user(request.user, limit=24)
    return render(request, 'properties/recommendations.html', {'recommended': recommended})


@login_required
@require_http_methods(['GET', 'POST'])
def image_upload(request):
    """Display magical image upload page for visual search."""
    if request.method == 'POST':
        return image_search(request)
    return render(request, 'properties/image_upload.html')


@login_required
@require_POST
def image_analyze_api(request):
    """
    API endpoint to analyze an uploaded image and detect features.
    Returns JSON with detected features, categories, and confidence scores.
    """
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'No image provided',
                    'features': [],
                    'categories': {}
                },
                status=400
            )
        
        # Analyze the image for property features
        analysis = detect_property_features_advanced(image_file)
        
        # Track that user performed a visual search
        if request.user.is_authenticated:
            feature_names = ', '.join([f.get('name', '') for f in analysis.get('features', [])[:3]])
            UserSearch.objects.create(
                user=request.user,
                feature=f"Visual search: {feature_names}"
            )
        
        return JsonResponse(analysis)
    
    except Exception as e:
        print(f"Error in image_analyze_api: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse(
            {
                'success': False,
                'message': f'Error analyzing image: {str(e)}',
                'features': [],
                'categories': {}
            },
            status=500
        )


@login_required
@require_http_methods(['GET'])
def image_search_results(request):
    """
    Display search results based on detected image features.
    Query params: features (JSON string of feature IDs), original_image (base64)
    """
    try:
        import base64
        from urllib.parse import unquote_plus
        
        # Get features from query params
        features_param = request.GET.get('features', '[]')
        try:
            features_data = json.loads(features_param)
        except:
            features_data = []
        
        # Get original image base64 if provided
        original_image = request.GET.get('image')
        
        # Search for matching properties
        properties = search_properties_by_features(features_data, limit=24)
        
        # Get feature details for display
        feature_names = [f.get('name', '') for f in features_data]
        
        return render(
            request,
            'properties/image_search_results.html',
            {
                'properties': properties,
                'detected_features': features_data,
                'feature_names': ', '.join(feature_names),
                'original_image': original_image,
                'result_count': len(properties),
            }
        )
    
    except Exception as e:
        print(f"Error in image_search_results: {e}")
        messages.error(request, 'Error loading search results')
        return redirect('properties:image_upload')


@login_required
@require_POST
def image_search(request):
    """
    Handle image upload and search.
    Accepts both POST with image file and redirects to results page.
    """
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            messages.error(request, 'Please choose an image to search with.')
            return redirect('properties:image_upload')
        
        # Ensure file pointer is at start
        image_file.seek(0)
        
        # Analyze the image for property features
        analysis = detect_property_features_advanced(image_file)
        
        if not analysis.get('success') or not analysis.get('features'):
            # Fallback to simple keyword search
            image_file.seek(0)
            result = analyze_property_image(image_file)
            labels = [x for x in (result.get('labels') or []) if x]
            feature = ''
            for label in labels:
                token = (label.split()[0] if label else '').strip()
                if len(token) >= 3:
                    feature = token
                    break
            if not feature and labels:
                feature = labels[0]
            if feature:
                url = f"{reverse('properties:property_list')}?feature={quote(feature)}"
                messages.success(request, f'Searching listings matching: {feature}')
                return redirect(url)
            else:
                messages.info(
                    request,
                    'Could not detect features from the image. Try another photo or use text search.',
                )
                return redirect('properties:property_list')
        
        # Prepare features for URL
        features_list = analysis.get('features', [])
        features_json = json.dumps(features_list)
        
        # Track the search
        feature_names = ', '.join([f.get('name', '') for f in features_list[:3]])
        if request.user.is_authenticated:
            UserSearch.objects.create(
                user=request.user,
                feature=f"Visual search: {feature_names}"
            )
        
        # Redirect to results page with features
        url = f"{reverse('properties:image_search_results')}?features={quote(features_json)}"
        messages.success(request, f'Searching listings with: {feature_names}')
        return redirect(url)
    
    except Exception as e:
        print(f"Error in image_search: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Error processing image. Please try again.')
        return redirect('properties:image_upload')


@login_required
@require_http_methods(['GET', 'POST'])
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        image_formset = PropertyImageFormSet(request.POST, request.FILES, prefix='images')
        nearby_formset = NearbyLocationFormSet(request.POST, prefix='nearby')
        if form.is_valid() and image_formset.is_valid() and nearby_formset.is_valid():
            prop = form.save(commit=False)
            prop.agent = request.user
            prop.save()
            image_formset.instance = prop
            image_formset.save()
            nearby_formset.instance = prop
            nearby_formset.save()

            # Generate comprehensive SEO data
            seo_data = generate_comprehensive_seo_data(prop)
            prop.ai_generated_description = seo_data["ai_generated_description"]
            prop.seo_meta_description = seo_data["seo_meta_description"]
            prop.seo_keywords = seo_data["seo_keywords"]
            prop.seo_score = seo_data["seo_score"]
            prop.save(update_fields=[
                'ai_generated_description',
                'seo_meta_description',
                'seo_keywords',
                'seo_score'
            ])

            # Analyze images for features
            for img in PropertyImage.objects.filter(property=prop):
                feats = analyze_property_image(img.image)
                merge_image_features(prop, feats.get('features') or [])

            messages.success(
                request,
                'Property published successfully with AI-generated SEO content!'
            )
            return redirect('properties:property_detail', pk=prop.pk)
    else:
        form = PropertyForm()
        image_formset = PropertyImageFormSet(prefix='images')
        nearby_formset = NearbyLocationFormSet(prefix='nearby')

    return render(
        request,
        'properties/property_form.html',
        {
            'form': form,
            'image_formset': image_formset,
            'nearby_formset': nearby_formset,
            'title': 'Post a property',
            'submit_label': 'Publish',
        },
    )


@login_required
@require_http_methods(['GET', 'POST'])
def property_edit(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if prop.agent_id != request.user.id:
        return HttpResponseForbidden('You cannot edit this listing.')

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=prop)
        image_formset = PropertyImageFormSet(request.POST, request.FILES, instance=prop, prefix='images')
        nearby_formset = NearbyLocationFormSet(request.POST, instance=prop, prefix='nearby')
        if form.is_valid() and image_formset.is_valid() and nearby_formset.is_valid():
            prop = form.save()
            image_formset.save()
            nearby_formset.save()

            # Regenerate comprehensive SEO data on update
            seo_data = generate_comprehensive_seo_data(prop)
            prop.ai_generated_description = seo_data["ai_generated_description"]
            prop.seo_meta_description = seo_data["seo_meta_description"]
            prop.seo_keywords = seo_data["seo_keywords"]
            prop.seo_score = seo_data["seo_score"]
            prop.save(update_fields=[
                'ai_generated_description',
                'seo_meta_description',
                'seo_keywords',
                'seo_score'
            ])

            # Re-analyze images for features
            for img in PropertyImage.objects.filter(property=prop):
                feats = analyze_property_image(img.image)
                merge_image_features(prop, feats.get('features') or [])

            messages.success(request, 'Listing updated with refreshed SEO content.')
            return redirect('properties:property_detail', pk=prop.pk)
    else:
        form = PropertyForm(instance=prop)
        image_formset = PropertyImageFormSet(instance=prop, prefix='images')
        nearby_formset = NearbyLocationFormSet(instance=prop, prefix='nearby')

    return render(
        request,
        'properties/property_form.html',
        {
            'form': form,
            'image_formset': image_formset,
            'nearby_formset': nearby_formset,
            'title': 'Edit property',
            'submit_label': 'Save changes',
            'property_obj': prop,
        },
    )


@login_required
@require_POST
def property_delete(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if prop.agent_id != request.user.id:
        return HttpResponseForbidden()
    prop.delete()
    messages.info(request, 'Listing removed.')
    return redirect('properties:home')


@require_http_methods(['POST'])
def image_search(request):
    """Upload an image; use Vision labels (when configured) to jump into keyword search."""
    image_file = request.FILES.get('image')
    if not image_file:
        messages.error(request, 'Please choose an image to search with.')
        return redirect('properties:property_list')

    result = analyze_property_image(image_file)
    labels = [x for x in (result.get('labels') or []) if x]
    feature = ''
    for label in labels:
        token = (label.split()[0] if label else '').strip()
        if len(token) >= 3:
            feature = token
            break
    if not feature and labels:
        feature = labels[0]
    if not feature:
        messages.info(
            request,
            'Could not detect keywords from the image. Try another photo or use text search.',
        )
        return redirect('properties:property_list')



@login_required
@require_POST
def chatbot_api(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    msg = ''
    if request.content_type and 'application/json' in request.content_type:
        try:
            body = json.loads(request.body.decode() or '{}')
            msg = body.get('message', '')
        except json.JSONDecodeError:
            msg = ''
    else:
        msg = request.POST.get('message', '')
    reply = chatbot_reply(msg, property_title=prop.title)
    return JsonResponse({'reply': reply})


@login_required
@login_required
@require_http_methods(['POST'])
def generate_description_api(request):
    """AJAX endpoint to generate AI property description."""
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body.decode() or '{}')
        else:
            body = request.POST

        title = body.get('title', '').strip()
        city = body.get('city', '').strip()
        property_type = body.get('property_type', '').strip()
        address = body.get('address', '').strip()
        price = body.get('price', '').strip()

        if not title or not city or not property_type:
            return JsonResponse({
                'error': 'Title, city, and property type are required.'
            }, status=400)

        # Create payload for AI generation
        payload = {
            'title': title,
            'city': city,
            'property_type': property_type,
            'address': address,
            'price': price,
        }

        description = generate_property_description(payload)

        return JsonResponse({
            'description': description
        })

    except Exception as e:
        print(f"Error generating description: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': 'Failed to generate description. Please try again.'
        }, status=500)


@require_http_methods(['GET'])
def nearby_places_api(request):
    """Return nearby essentials from Google Places based on coordinates."""
    key = (getattr(settings, 'GOOGLE_PLACES_API_KEY', '') or '').strip()
    if not key:
        return JsonResponse({'error': 'Google Places API is not configured.'}, status=503)

    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    if not lat or not lng:
        return JsonResponse({'error': 'lat and lng are required.'}, status=400)

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates.'}, status=400)

    # Google-supported place categories mapped to model place_type values.
    category_map = [
        ('hospital', 'hospital'),
        ('railway_station', 'station'),
        ('shopping_mall', 'mall'),
        ('bus_station', 'bus_stand'),
        ('school', 'school'),
        ('airport', 'airport'),
        ('park', 'park'),
        ('supermarket', 'supermarket'),
        ('restaurant', 'restaurant'),
    ]

    out = []
    session = requests.Session()
    for google_type, app_place_type in category_map:
        try:
            resp = session.get(
                'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
                params={
                    'key': key,
                    'location': f'{lat_f},{lng_f}',
                    'radius': 4500,
                    'type': google_type,
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            first = (data.get('results') or [None])[0]
            if not first:
                continue
            geom = first.get('geometry', {}).get('location', {})
            out.append(
                {
                    'place_type': app_place_type,
                    'name': first.get('name', ''),
                    'distance': '< 5 km',
                    'place_id': first.get('place_id', ''),
                    'latitude': geom.get('lat'),
                    'longitude': geom.get('lng'),
                }
            )
        except Exception:
            continue

    return JsonResponse({'items': out})
