"""Property views and AI-powered image search backend."""
import json
import logging
import os
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .ai_utils import (
    comparison_engine,
    focus_visual_query_features,
    image_analyzer,
    market_analysis_engine,
    normalize_feature_set,
    normalize_visual_feature,
    search_suggestion_engine,
    visual_search_engine,
)
from .forms import PropertyForm
from .location_utils import OpenStreetMapAPI
from .models import Property, PropertyImage, PropertyReview

from accounts.models import UserPropertyView
from favorites.models import Favorite

logger = logging.getLogger(__name__)

PROPERTY_CREATOR_ROLES = {'buyer', 'agent', 'owner', 'admin'}

FEATURE_COMPATIBILITY_GROUPS = {
    'kitchen': {'kitchen', 'modular kitchen', 'open kitchen', 'closed kitchen'},
    'modular kitchen': {'modular kitchen'},
    'open kitchen': {'open kitchen'},
    'closed kitchen': {'closed kitchen'},
}

NEARBY_LOCATION_FIELDS = [
    'nearby_hospital',
    'nearby_railway_station',
    'nearby_shopping_mall',
    'nearby_bus_stand',
    'nearby_school',
    'nearby_airport',
    'nearby_park',
    'nearby_supermarket',
    'nearby_restaurant',
    'nearby_other_places',
    'nearby_gym',
    'nearby_hospital_emergency',
    'nearby_bank',
    'nearby_atm',
    'nearby_pharmacy',
    'nearby_metro',
    'nearby_university',
    'nearby_theater',
]


def _ensure_property_coordinates(property_obj, save: bool = True):
    if property_obj.latitude is not None and property_obj.longitude is not None:
        return

    if not any([property_obj.address, property_obj.city, property_obj.state]):
        return

    api = OpenStreetMapAPI()
    latitude, longitude = api.get_coordinates(
        property_obj.address or '',
        property_obj.city or '',
        property_obj.state or '',
    )

    if latitude is not None and longitude is not None:
        property_obj.latitude = latitude
        property_obj.longitude = longitude
        if save and property_obj.pk:
            property_obj.save(update_fields=['latitude', 'longitude'])


def _parse_nearby_input(raw_value):
    if not raw_value:
        return []

    normalized = str(raw_value).replace('\r\n', '\n').replace('\r', '\n')
    items = []
    for line in normalized.split('\n'):
        for part in line.split(','):
            value = part.strip()
            if value:
                items.append(value)
    return items


def _apply_nearby_locations_from_request(property_obj, request):
    for field_name in NEARBY_LOCATION_FIELDS:
        setattr(property_obj, field_name, _parse_nearby_input(request.POST.get(field_name, '')))


def _build_property_ai_payload(property_obj):
    return {
        'title': property_obj.title,
        'description': property_obj.description,
        'city': property_obj.city,
        'state': property_obj.state,
        'address': property_obj.address,
        'price': property_obj.price,
        'bedrooms': property_obj.bedrooms,
        'bathrooms': property_obj.bathrooms,
        'area_sqft': property_obj.area_sqft,
        'furnishing': property_obj.furnishing,
        'property_type': property_obj.property_type,
        'amenities': property_obj.amenities,
    }


def _generate_property_description(payload):
    title = payload.get('title', 'Property')
    city = payload.get('city', 'a great location')
    bedrooms = payload.get('bedrooms') or 'spacious'
    bathrooms = payload.get('bathrooms') or 'modern'
    area = payload.get('area_sqft') or 'generous'
    price = payload.get('price')
    price_label = f'₹{price:,.0f}' if price else 'Attractive pricing'
    furnishing = payload.get('furnishing', 'smartly appointed').replace('-', ' ')
    amenities = ', '.join(payload.get('amenities') or [])

    description = (
        f"{title} in {city} offers {bedrooms} bedroom(s), {bathrooms} bath(s), and approximately "
        f"{area} sq ft of premium living space. Priced at {price_label}, this listing boasts "
        f"{furnishing} interiors and curated amenities like {amenities or 'excellent lifestyle features'}. "
        "It is designed for modern buyers seeking comfort, style, and strong long-term value."
    )
    return description


def _generate_property_tags(payload):
    tags = []
    if payload.get('city'):
        tags.append(payload['city'].lower())
    if payload.get('property_type'):
        tags.append(payload['property_type'])
    if payload.get('bedrooms'):
        tags.append(f"{payload['bedrooms']}-bedroom")
    tags.extend(payload.get('amenities') or [])
    return [tag for tag in {tag.lower() for tag in tags} if tag]


def _extract_normalized_features(values):
    return normalize_feature_set(values)


def _collect_property_visual_features(property_obj):
    image_features = set()
    for image_obj in property_obj.images.all():
        image_features.update(_extract_normalized_features(image_obj.ai_detected_features))
    return image_features


def _collect_property_features(property_obj):
    features = set()
    features.update(_extract_normalized_features(property_obj.ai_tags))
    features.update(_extract_normalized_features(property_obj.amenities))
    features.update(_collect_property_visual_features(property_obj))
    return features


IMAGE_AMENITY_FEATURES = {
    'swimming pool', 'infinity pool', 'kitchen', 'modular kitchen',
    'open kitchen', 'closed kitchen', 'garden', 'balcony', 'rooftop terrace',
    'terrace', 'gym', 'bathroom', 'bedroom', 'living room',
    'parking garage', 'parking space', 'pool', 'patio', 'outdoor area'
}


def _extract_query_image_features(image_path: str):
    from .image_search_service import image_search_service

    analysis = image_search_service.analyse_image(image_path)
    detected = normalize_feature_set(analysis.detected_features)
    amenity_matches = sorted(feature for feature in detected if feature in IMAGE_AMENITY_FEATURES)
    if amenity_matches:
        return amenity_matches

    _, fallback = visual_search_engine.extract_query_features(image_path)
    if fallback:
        fallback_matches = sorted(feature for feature in fallback if feature in IMAGE_AMENITY_FEATURES)
        if fallback_matches:
            return fallback_matches

    return sorted(detected)


def _rank_properties_by_image_features(query_features, properties):
    query_set = set(normalize_feature_set(query_features))
    ranked = []
    for prop in properties:
        prop_features = set()
        for img in prop.images.all():
            prop_features.update(normalize_feature_set(img.ai_detected_features or []))

        matched = query_set & prop_features
        if not matched:
            continue

        ranked.append({
            'property_id': prop.id,
            'score': round(len(matched) / max(len(query_set), 1), 4),
            'matched_features': sorted(matched),
        })

    ranked.sort(key=lambda item: item['score'], reverse=True)
    return ranked


def _save_property_image_analysis(image_obj):
    if not image_obj or not getattr(image_obj, 'image', None):
        return

    try:
        analysis = image_analyzer.analyze_image(
            image_obj.image.path,
            original_filename=image_obj.image.name,
        )
        image_obj.ai_detected_features = analysis.get('detected_features', [])
        image_obj.ai_description = analysis.get('description', '')
        image_obj.ai_visual_signature = analysis.get('visual_signature', {})
        image_obj.save(update_fields=['ai_detected_features', 'ai_description', 'ai_visual_signature'])

        property_obj = image_obj.property
        existing_tags = set(property_obj.ai_tags or [])
        existing_tags.update(image_obj.ai_detected_features or [])
        property_obj.ai_tags = sorted(existing_tags)
        property_obj.save(update_fields=['ai_tags'])
    except Exception as exc:
        logger.warning('Image analysis failed for image %s: %s', image_obj.pk, exc)


def _paginate(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator


def _user_favorite_ids(request):
    if not request.user.is_authenticated:
        return set()
    return set(Favorite.objects.filter(user=request.user).values_list('property_id', flat=True))


def _get_recommended_properties(user, city=None, count=4):
    recommendations = Property.objects.filter(is_active=True)
    if city:
        recommendations = recommendations.filter(city__icontains=city)
    return recommendations.order_by('-views_count', '-rating', '-created_at')[:count]


@ensure_csrf_cookie
def home(request):
    featured_properties = Property.objects.filter(is_active=True, is_featured=True).order_by('-created_at')[:6]
    latest_properties = Property.objects.filter(is_active=True).order_by('-created_at')[:8]
    recommended_properties = []
    recommendation_prefill_hint = None

    if request.user.is_authenticated:
        recommended_properties = list(_get_recommended_properties(request.user, count=6))
        if not recommended_properties:
            recommended_properties = list(Property.objects.filter(is_active=True).order_by('-views_count', '-rating')[:6])
        recommendation_prefill_hint = 'These properties are popular with users on LuxeEstate.'

    context = {
        'featured_properties': featured_properties,
        'latest_properties': latest_properties,
        'recommended_properties': recommended_properties,
        'recommendation_prefill_hint': recommendation_prefill_hint,
        'total_properties': Property.objects.filter(is_active=True).count(),
    }
    return render(request, 'properties/home.html', context)


def property_list(request):
    properties = Property.objects.filter(is_active=True).order_by('-created_at')
    properties_page, paginator = _paginate(request, properties, per_page=12)

    context = {
        'properties': properties_page,
        'paginator': paginator,
        'favorite_ids': _user_favorite_ids(request),
    }
    return render(request, 'properties/list.html', context)


def search(request):
    properties = Property.objects.filter(is_active=True)
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    property_type = request.GET.get('property_type', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    bedrooms = request.GET.get('bedrooms', '').strip()
    bathrooms = request.GET.get('bathrooms', '').strip()
    image_match_ids = request.GET.get('image_match_ids', '').strip()
    image_features = request.GET.get('image_features', '').strip()
    image_search_active = bool(image_match_ids or image_features)

    if image_match_ids:
        ids = [int(pk) for pk in image_match_ids.split(',') if pk.isdigit()]
        properties = properties.filter(pk__in=ids)

    if image_features:
        query_features = [feature.strip() for feature in image_features.split(',') if feature.strip()]
        normalized_features = normalize_feature_set(query_features)
        strict_features = set(focus_visual_query_features(normalized_features))
        if strict_features:
            candidate_properties = list(properties.prefetch_related('images'))
            matching_ids = []
            for prop in candidate_properties:
                property_features = _collect_property_visual_features(prop) or _collect_property_features(prop)
                if property_features and all(
                    (feature in property_features or FEATURE_COMPATIBILITY_GROUPS.get(feature, set()).intersection(property_features))
                    for feature in strict_features
                ):
                    matching_ids.append(prop.id)
            properties = properties.filter(id__in=matching_ids)
        else:
            properties = properties.none()

    if query:
        properties = properties.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(city__icontains=query)
            | Q(address__icontains=query)
            | Q(ai_tags__icontains=query)
        )

    if city:
        properties = properties.filter(city__icontains=city)

    if property_type:
        properties = properties.filter(property_type=property_type)

    if min_price:
        try:
            properties = properties.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            properties = properties.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if bedrooms:
        try:
            properties = properties.filter(bedrooms=int(bedrooms))
        except ValueError:
            pass

    if bathrooms:
        try:
            properties = properties.filter(bathrooms=int(bathrooms))
        except ValueError:
            pass

    sort_by = request.GET.get('sort', '-created_at')
    if not image_search_active:
        properties = properties.order_by(sort_by)

    properties_page, paginator = _paginate(request, properties, per_page=12)

    recommended_properties = []
    recommendation_prefill_hint = None
    if request.user.is_authenticated:
        recommended_properties = list(_get_recommended_properties(request.user, city=city, count=4))
        recommendation_prefill_hint = 'Based on popular listings and your browsing history.'

    context = {
        'properties': properties_page,
        'paginator': paginator,
        'favorite_ids': _user_favorite_ids(request),
        'query': query,
        'city': city,
        'image_features': image_features,
        'image_search_active': image_search_active,
        'recommended_properties': recommended_properties,
        'recommendation_prefill_hint': recommendation_prefill_hint,
        'google_places_api_key': getattr(settings, 'GOOGLE_PLACES_API_KEY', ''),
    }
    return render(request, 'properties/search.html', context)


@ensure_csrf_cookie
def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, is_active=True)
    _ensure_property_coordinates(property_obj)

    if request.user.is_authenticated:
        UserPropertyView.objects.get_or_create(user=request.user, property=property_obj)

    property_obj.increment_views()
    images = property_obj.images.all()
    reviews = property_obj.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    nearby_properties = (
        Property.objects.filter(city=property_obj.city, is_active=True)
        .exclude(pk=property_obj.pk)
        .order_by('-views_count')[:5]
    )
    market_insights = market_analysis_engine.get_market_insights(property_obj)
    ai_feature_summary = sorted({feature for image in images for feature in (image.ai_detected_features or [])})
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, property=property_obj).exists()
    is_property_owner = request.user.is_authenticated and property_obj.agent == request.user

    context = {
        'property': property_obj,
        'images': images,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'nearby_properties': nearby_properties,
        'market_insights': market_insights,
        'ai_feature_summary': ai_feature_summary,
        'is_favorite': is_favorite,
        'is_property_owner': is_property_owner,
    }
    return render(request, 'properties/detail.html', context)


def property_route_map(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, is_active=True)
    _ensure_property_coordinates(property_obj)
    is_property_owner = request.user.is_authenticated and property_obj.agent == request.user
    return render(request, 'properties/route_map.html', {'property': property_obj, 'is_property_owner': is_property_owner})


@login_required
def add_property(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in PROPERTY_CREATOR_ROLES:
        messages.error(request, 'Your account type cannot add properties yet.')
        return redirect('properties:home')

    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.agent = request.user
            property_obj.latitude = request.POST.get('latitude') or None
            property_obj.longitude = request.POST.get('longitude') or None
            _ensure_property_coordinates(property_obj, save=False)
            property_obj.amenities = request.POST.getlist('amenities') or []
            _apply_nearby_locations_from_request(property_obj, request)
            payload = _build_property_ai_payload(property_obj)
            property_obj.ai_generated_description = _generate_property_description(payload)
            property_obj.ai_tags = _generate_property_tags(payload)
            property_obj.save()

            images = request.FILES.getlist('images')
            for index, image in enumerate(images):
                image_obj = PropertyImage.objects.create(
                    property=property_obj,
                    image=image,
                    is_primary=(index == 0),
                )
                _save_property_image_analysis(image_obj)

            messages.success(request, 'Property added successfully with AI image analysis enabled.')
            return redirect('properties:detail', pk=property_obj.pk)
    else:
        form = PropertyForm()

    return render(request, 'properties/add_edit.html', {
        'form': form,
        'google_places_api_key': getattr(settings, 'GOOGLE_PLACES_API_KEY', ''),
        'nearby_fields': NEARBY_LOCATION_FIELDS,
    })


@login_required
def edit_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, agent=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.latitude = request.POST.get('latitude') or None
            property_obj.longitude = request.POST.get('longitude') or None
            _ensure_property_coordinates(property_obj, save=False)
            property_obj.amenities = request.POST.getlist('amenities') or []
            _apply_nearby_locations_from_request(property_obj, request)
            payload = _build_property_ai_payload(property_obj)
            property_obj.ai_generated_description = _generate_property_description(payload)
            property_obj.ai_tags = _generate_property_tags(payload)
            property_obj.save()

            if 'images' in request.FILES:
                existing_primary = property_obj.images.filter(is_primary=True).exists()
                for index, image in enumerate(request.FILES.getlist('images')):
                    image_obj = PropertyImage.objects.create(
                        property=property_obj,
                        image=image,
                        is_primary=(not existing_primary and index == 0),
                    )
                    _save_property_image_analysis(image_obj)

            messages.success(request, 'Property updated successfully.')
            return redirect('properties:detail', pk=property_obj.pk)
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'properties/add_edit.html', {
        'form': form,
        'property': property_obj,
        'google_places_api_key': getattr(settings, 'GOOGLE_PLACES_API_KEY', ''),
        'nearby_fields': NEARBY_LOCATION_FIELDS,
    })


@login_required
def delete_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, agent=request.user)
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully.')
        return redirect('properties:home')
    return render(request, 'properties/delete.html', {'property': property_obj})


@login_required
def my_properties(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in PROPERTY_CREATOR_ROLES:
        messages.error(request, 'Your account type cannot access this page.')
        return redirect('properties:home')

    properties = request.user.properties.filter(is_active=True).order_by('-created_at')
    properties_page, paginator = _paginate(request, properties, per_page=12)

    return render(request, 'properties/my_properties.html', {
        'properties': properties_page,
        'paginator': paginator,
    })


@login_required
@require_POST
def delete_property_image(request, image_id):
    image_obj = get_object_or_404(PropertyImage, pk=image_id)
    property_obj = image_obj.property
    if property_obj.agent != request.user:
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    if image_obj.image:
        image_obj.image.delete(save=False)
    image_obj.delete()
    return JsonResponse({'success': True, 'message': 'Image deleted successfully.'})


def get_cities(request):
    query = request.GET.get('q', '').strip()
    cities = Property.objects.filter(is_active=True, city__icontains=query).values_list('city', flat=True).distinct()[:10]
    return JsonResponse({'cities': list(cities)})


@require_GET
def fetch_nearby_places(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    if not lat or not lng:
        return JsonResponse({'error': 'lat and lng are required.'}, status=400)

    try:
        latitude = float(lat)
        longitude = float(lng)
    except ValueError:
        return JsonResponse({'error': 'Invalid lat/lng format.'}, status=400)

    api = OpenStreetMapAPI()
    all_locations = api.get_all_nearby_locations(latitude, longitude, radius=2500)
    return JsonResponse(all_locations)


@require_POST
def retry_property_geocode(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, is_active=True)
    if property_obj.latitude is not None and property_obj.longitude is not None:
        return JsonResponse({'success': True, 'message': 'Coordinates already available.', 'latitude': property_obj.latitude, 'longitude': property_obj.longitude})

    _ensure_property_coordinates(property_obj, save=True)
    if property_obj.latitude is not None and property_obj.longitude is not None:
        return JsonResponse({'success': True, 'message': 'Coordinates resolved successfully.', 'latitude': property_obj.latitude, 'longitude': property_obj.longitude})

    return JsonResponse({'success': False, 'message': 'Could not resolve coordinates for this property.'}, status=400)


@require_POST
def generate_ai_description(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    data = {
        'title': payload.get('title', ''),
        'city': payload.get('city', ''),
        'address': payload.get('address', ''),
        'price': payload.get('price'),
        'bedrooms': payload.get('bedrooms'),
        'bathrooms': payload.get('bathrooms'),
        'area_sqft': payload.get('area_sqft'),
        'furnishing': payload.get('furnishing', ''),
        'amenities': payload.get('amenities') or [],
    }

    description = _generate_property_description(data)
    seo_title = f"{data.get('bedrooms') or 'Premium'} {data.get('city') or 'Property'} Listing | LuxeEstate"
    meta_description = description[:155]
    keywords = _generate_property_tags(data)

    return JsonResponse({'description': description, 'seo_title': seo_title, 'meta_description': meta_description, 'keywords': keywords})


@require_GET
def filter_properties(request):
    city = request.GET.get('city', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    property_type = request.GET.get('property_type', '').strip()

    properties = Property.objects.filter(is_active=True)
    if city:
        properties = properties.filter(city__icontains=city)
    if min_price:
        try:
            properties = properties.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            properties = properties.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if property_type:
        properties = properties.filter(property_type=property_type)

    data = {
        'count': properties.count(),
        'properties': list(properties.values('id', 'title', 'price', 'city', 'property_type')[:10]),
    }
    return JsonResponse(data)


@require_POST
def search_by_image(request):
    """
    AI-powered image search.
    Accepts one or more uploaded images, sends them to GPT-4o Vision to
    detect property features (pool, kitchen type, amenities, architecture
    style, etc.), then ranks active listings by feature overlap.
    """
    from .image_search_service import image_search_service

    uploaded_images = request.FILES.getlist('search_image')
    if not uploaded_images:
        single = request.FILES.get('search_image')
        if single:
            uploaded_images = [single]

    if not uploaded_images:
        return JsonResponse(
            {'success': False, 'message': 'Please upload at least one image.'},
            status=400,
        )

    active_properties = list(
        Property.objects.filter(is_active=True).prefetch_related('images')
    )
    if not active_properties:
        return JsonResponse(
            {'success': False, 'message': 'No active listings found.', 'detected_features': []},
        )

    tmp_paths = []
    combined_detected: list = []

    try:
        for uploaded_file in uploaded_images:
            suffix = os.path.splitext(uploaded_file.name or '')[-1] or '.jpg'
            tmp_file = NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_paths.append(tmp_file.name)
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_file.flush()
            tmp_file.close()

            detected_features = _extract_query_image_features(tmp_file.name)
            if not detected_features:
                logger.warning('Image analysis returned no features for %s', uploaded_file.name)
                continue

            combined_detected.extend(detected_features)

        # Deduplicate features
        seen_feats = set()
        unique_features = []
        for f in combined_detected:
            if f not in seen_feats:
                seen_feats.add(f)
                unique_features.append(f)

        if not unique_features:
            return JsonResponse({
                'success': False,
                'message': (
                    'Unable to detect property features from the image(s). '
                    'Please upload a clear amenity image such as a pool or kitchen. '
                    'The search only returns listings with matching amenity images.'
                ),
                'detected_features': [],
                'tips': [
                    'Use a clear, close-up photo of a specific amenity',
                    'Upload a swimming pool or kitchen image',
                    'Avoid very dark or blurry images',
                ]
            }, status=400)

        ranked = _rank_properties_by_image_features(unique_features, active_properties)
        if not ranked:
            return JsonResponse({
                'success': False,
                'message': 'No listings with the same amenity image were found. Try a different image.',
                'detected_features': unique_features,
                'match_count': 0,
            })

        matched_ids = [str(item['property_id']) for item in ranked]
        query_string = urlencode({
            'image_match_ids': ','.join(matched_ids),
            'image_features': ','.join(unique_features[:10]),
        })

        return JsonResponse({
            'success': True,
            'message': f'Found {len(matched_ids)} listings with matching amenity images.',
            'redirect_url': f"{reverse('properties:search')}?{query_string}",
            'detected_features': unique_features,
            'match_count': len(matched_ids),
            'top_matches': [
                {
                    'property_id': item['property_id'],
                    'score': round(item['score'], 3),
                    'matched_features': item['matched_features'],
                }
                for item in ranked[:5]
            ],
        })

    except Exception as exc:
        error_msg = str(exc)
        logger.error('AI image search failed: %s', exc, exc_info=True)
        
        # Check for specific error types
        if 'OPENAI_API_KEY' in error_msg or 'not configured' in error_msg.lower():
            return JsonResponse(
                {
                    'success': False, 
                    'message': (
                        'Image search feature is not properly configured. '
                        'Please contact the administrator to set it up.'
                    ),
                    'error_type': 'api_not_configured',
                },
                status=500,
            )
        elif 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
            return JsonResponse(
                {
                    'success': False, 
                    'message': 'Invalid OpenAI API key. Please contact the administrator.',
                    'error_type': 'api_auth_failed',
                },
                status=500,
            )
        else:
            return JsonResponse(
                {'success': False, 'message': 'Unable to process image search right now.'},
                status=500,
            )
    finally:
        for path in tmp_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


@require_GET
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = search_suggestion_engine.get_suggestions(query)
    return JsonResponse({'suggestions': suggestions})


def compare_properties(request):
    ids = request.GET.get('ids', '')
    selected_ids = [int(pk) for pk in ids.split(',') if pk.isdigit()]
    if not selected_ids:
        selected_ids = request.session.get('comparison_list', [])
    properties = list(Property.objects.filter(id__in=selected_ids, is_active=True))
    properties.sort(key=lambda p: selected_ids.index(p.id) if p.id in selected_ids else 0)

    if len(properties) < 2:
        messages.warning(request, 'Select at least two valid listings to compare.')
        return redirect('properties:list')

    def normalize(values):
        maximum = max(values) if values else 1
        return [round((value / maximum) * 100, 1) if maximum else 0 for value in values]

    location_scores = []
    price_scores = []
    layout_scores = []
    amenities_scores = []
    for prop in properties:
        nearby_count = sum(len(getattr(prop, field) or []) for field in NEARBY_LOCATION_FIELDS)
        location_scores.append(nearby_count + (2 if prop.city else 0))
        price_scores.append(float(prop.price or 0))
        layout_scores.append((prop.bedrooms or 0) * 20 + (prop.bathrooms or 0) * 15 + (prop.area_sqft or 0) / 50)
        furnishing_score = {'furnished': 30, 'semi-furnished': 20, 'unfurnished': 10}.get(prop.furnishing, 15)
        amenities_scores.append(len(prop.amenities or []) * 8 + furnishing_score)

    chart_data = {
        'labels': [p.title for p in properties],
        'location': normalize(location_scores),
        'price': normalize([100 - value if value else 100 for value in price_scores]),
        'layout': normalize(layout_scores),
        'amenities': normalize(amenities_scores),
    }
    summary = comparison_engine.get_comparison_summary(properties)
    return render(request, 'properties/compare.html', {'properties': properties, 'chart_data': chart_data, 'summary': summary})


def comparison_list(request):
    selected_ids = request.session.get('comparison_list', [])
    properties = Property.objects.filter(id__in=selected_ids, is_active=True)
    return render(request, 'properties/comparison_list.html', {
        'properties': properties,
        'selected_ids': selected_ids,
        'comparison_count': len(selected_ids),
    })


@require_POST
def add_to_comparison(request, property_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login to compare properties.'}, status=401)

    property_obj = get_object_or_404(Property, pk=property_id, is_active=True)
    comparison_list = request.session.get('comparison_list', [])
    comparison_list = [int(item) for item in comparison_list if str(item).isdigit()]

    if property_id in comparison_list:
        comparison_list.remove(property_id)
        action = 'removed'
    else:
        if len(comparison_list) >= 4:
            return JsonResponse({'success': False, 'message': 'You can compare up to 4 properties at a time.'})
        comparison_list.append(property_id)
        action = 'added'

    request.session['comparison_list'] = comparison_list
    return JsonResponse({'success': True, 'action': action, 'count': len(comparison_list), 'message': f'Property {action} to comparison list.'})


@login_required
@require_POST
def clear_comparison(request):
    request.session['comparison_list'] = []
    return JsonResponse({'success': True, 'message': 'Comparison list cleared.'})


# ============================================
# Chatbot Integration
# ============================================

@require_POST
def chatbot_response(request):
    """
    AI-powered chatbot endpoint (GPT-4o).

    Accepts JSON body: { "message": str, "use_memory": bool }
    Session key 'chatbot_state' persists conversation across requests.

    Returns JSON:
      response          – text reply to show the user
      intent            – detected intent label
      lead              – captured lead data dict
      qualification_stage – cold | warm | hot
      appointment       – appointment details dict
      requires_human    – bool; true when human agent should take over
      handoff_reason    – reason string if requires_human is true
    """
    from .chatbot_service import chatbot as luxe_chatbot

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    user_message = str(data.get('message', '')).strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required.'}, status=400)

    # Memory flag – defaults to True so conversations are stateful
    use_memory_raw = data.get('use_memory', True)
    if isinstance(use_memory_raw, bool):
        use_memory = use_memory_raw
    else:
        use_memory = str(use_memory_raw).strip().lower() in {'1', 'true', 'yes', 'on'}

    # Load persisted session state
    session_state = {}
    if use_memory:
        session_state = request.session.get('chatbot_state', {})
        if not isinstance(session_state, dict):
            session_state = {}

    # Build conversation_state from session
    conversation_state = {
        'chat_history': session_state.get('chat_history', []),
        'lead': session_state.get('lead', {}),
        'search_criteria': session_state.get('search_criteria', {}),
        'appointment': session_state.get('appointment', {}),
    }

    for source_key, target_key in [
        ('lead_name', 'name'),
        ('lead_contact', 'contact'),
        ('lead_budget', 'budget'),
        ('lead_city', 'city'),
        ('lead_property_type', 'property_type'),
        ('lead_bhk', 'bhk'),
    ]:
        value = data.get(source_key)
        if value and not conversation_state['lead'].get(target_key):
            conversation_state['lead'][target_key] = value

    try:
        result = luxe_chatbot.process_message(
            user_message,
            conversation_state=conversation_state,
        )
    except Exception as exc:
        logger.error('Chatbot process_message error: %s', exc)
        return JsonResponse({
            'response': (
                "I'm having a brief technical issue. "
                "Please try again or call us directly – we're here 24/7!"
            ),
            'intent': 'unknown',
            'requires_human': True,
            'handoff_reason': str(exc),
        }, status=500)

    # Persist updated state to session
    if use_memory:
        request.session['chatbot_state'] = {
            'chat_history': result.get('chat_history', []),
            'lead': result.get('lead', {}),
            'search_criteria': result.get('search_criteria', {}),
            'appointment': result.get('appointment', {}),
        }
        request.session.modified = True

    return JsonResponse({
        'response': result.get('message', ''),
        'intent': result.get('intent', 'unknown'),
        'lead': result.get('lead', {}),
        'qualification_stage': result.get('qualification_stage', 'cold'),
        'appointment': result.get('appointment', {}),
        'requires_human': result.get('requires_human', False),
        'handoff_reason': result.get('handoff_reason', ''),
    })
