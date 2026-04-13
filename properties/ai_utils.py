"""
AI utilities for property image analysis, visual search, and lightweight suggestions.
"""
import json
import logging
import os
import re
from typing import Dict, List, Set

from django.conf import settings
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

CANONICAL_VISUAL_FEATURES = {
    'swimming pool',
    'kitchen',
    'modular kitchen',
    'open kitchen',
    'closed kitchen',
    'garden',
    'parking space',
    'bedroom',
    'bathroom',
    'living room',
    'balcony',
    'terrace',
    'gym',
}

VISUAL_FEATURE_SYNONYMS = {
    'pool': 'swimming pool',
    'swimming': 'swimming pool',
    'swimming_pool': 'swimming pool',
    'modular': 'modular kitchen',
    'open kitchen': 'open kitchen',
    'closed kitchen': 'closed kitchen',
    'kitchen': 'kitchen',
    'garden': 'garden',
    'lawn': 'garden',
    'parking': 'parking space',
    'garage': 'parking space',
    'bedroom': 'bedroom',
    'bathroom': 'bathroom',
    'living': 'living room',
    'living room': 'living room',
    'hall': 'living room',
    'balcony': 'balcony',
    'terrace': 'terrace',
    'gym': 'gym',
    'fitness': 'gym',
}

PRIMARY_VISUAL_AMENITIES = frozenset(
    {
        'swimming pool',
        'garden',
        'gym',
        'parking space',
        'kitchen',
        'bedroom',
        'bathroom',
        'living room',
    }
)

FEATURE_COMPATIBILITY_GROUPS = {
    'kitchen': {'kitchen', 'modular kitchen', 'open kitchen', 'closed kitchen'},
    'modular kitchen': {'modular kitchen'},
    'open kitchen': {'open kitchen', 'kitchen'},
    'closed kitchen': {'closed kitchen', 'kitchen'},
}


def normalize_visual_feature(value):
    token = str(value or '').strip().lower()
    if not token:
        return None

    normalized = token.replace('-', ' ').replace('_', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)

    if normalized in VISUAL_FEATURE_SYNONYMS:
        return VISUAL_FEATURE_SYNONYMS[normalized]

    for key, canonical in VISUAL_FEATURE_SYNONYMS.items():
        if key in normalized:
            return canonical

    if normalized in CANONICAL_VISUAL_FEATURES:
        return normalized
    return None


def normalize_feature_set(values):
    normalized = set()
    if not values:
        return normalized

    if isinstance(values, str):
        values = [item.strip() for item in values.split(',') if item.strip()]

    for item in values:
        feature = normalize_visual_feature(item)
        if feature:
            normalized.add(feature)
    return normalized


def focus_visual_query_features(query_features):
    features = set(query_features or [])
    kitchen_variants = {'kitchen', 'modular kitchen', 'open kitchen', 'closed kitchen'}
    if features.intersection(kitchen_variants):
        for variant in ['modular kitchen', 'open kitchen', 'closed kitchen']:
            if variant in features:
                return [variant]
        return ['kitchen']

    primary = features.intersection(PRIMARY_VISUAL_AMENITIES)
    if primary:
        return sorted(primary)
    return sorted(features)


class ImageFeatureDetector:
    """Analyze property images and detect searchable visual features."""

    def __init__(self):
        self.hist_bins = 6

    def _extract_filename_features(self, image_path: str) -> Set[str]:
        filename = os.path.basename(image_path or '').lower()
        tokens = set(
            token.strip()
            for token in re.split(r'[\W_]+', filename)
            if token.strip()
        )

        detected = set()
        keyword_map = {
            'swimming': 'swimming pool',
            'pool': 'swimming pool',
            'kitchen': 'kitchen',
            'modular': 'modular kitchen',
            'open': 'open kitchen',
            'closed': 'closed kitchen',
            'garden': 'garden',
            'lawn': 'garden',
            'yard': 'garden',
            'balcony': 'balcony',
            'terrace': 'terrace',
            'gym': 'gym',
            'parking': 'parking space',
            'garage': 'parking space',
            'bedroom': 'bedroom',
            'bathroom': 'bathroom',
            'living': 'living room',
            'hall': 'living room',
        }

        for token in tokens:
            mapped = keyword_map.get(token)
            if mapped:
                detected.add(mapped)

        prioritized = [
            'swimming pool',
            'garden',
            'gym',
            'parking space',
            'modular kitchen',
            'open kitchen',
            'closed kitchen',
            'kitchen',
        ]
        for feature in prioritized:
            if feature in detected:
                return {feature}
        return detected

    def _extract_visual_signature(self, rgb_image: Image.Image) -> Dict:
        small = rgb_image.resize((8, 8), resample=Image.LANCZOS)
        grayscale = small.convert('L')
        pixels = list(grayscale.getdata())
        avg = sum(pixels) / max(len(pixels), 1)
        avg_hash = ''.join('1' if pixel >= avg else '0' for pixel in pixels)

        histogram = rgb_image.histogram()
        red = histogram[0:256]
        green = histogram[256:512]
        blue = histogram[512:768]
        hist = red[:self.hist_bins] + green[:self.hist_bins] + blue[:self.hist_bins]
        total = float(sum(hist)) or 1.0
        color_hist = [round(value / total, 5) for value in hist]

        gray = rgb_image.convert('L')
        pixels = list(gray.getdata())
        brightness = round(sum(pixels) / (len(pixels) * 255.0), 5)

        width, height = rgb_image.size
        saturation = 0.0
        try:
            hsv = rgb_image.convert('HSV')
            sat_values = [pixel[1] for pixel in list(hsv.getdata())]
            saturation = round(sum(sat_values) / (len(sat_values) * 255.0), 5)
        except Exception:
            saturation = 0.0

        edge_image = rgb_image.convert('L').filter(ImageFilter.FIND_EDGES)
        edges = list(edge_image.getdata())
        edge_density = round(sum(1 for p in edges if p > 32) / max(len(edges), 1), 5)

        return {
            'avg_hash': avg_hash,
            'color_hist': color_hist,
            'brightness': brightness,
            'saturation': saturation,
            'edge_density': edge_density,
            'aspect_ratio': round(width / max(height, 1), 3),
        }

    def _detect_visual_features(self, rgb_image: Image.Image) -> Set[str]:
        width, height = rgb_image.size
        pixels = list(rgb_image.getdata())
        red_sum = green_sum = blue_sum = 0
        for r, g, b in pixels:
            red_sum += r
            green_sum += g
            blue_sum += b

        total = float(len(pixels)) or 1.0
        red_ratio = red_sum / (total * 255.0)
        green_ratio = green_sum / (total * 255.0)
        blue_ratio = blue_sum / (total * 255.0)
        saturation_floor = 0.18
        aspect = width / max(height, 1)

        features = set()
        if blue_ratio > 0.30 and saturation_floor < 0.65 and aspect > 1.2:
            features.add('swimming pool')
        if green_ratio > 0.28 and blue_ratio < 0.40 and aspect < 1.8:
            features.add('garden')
        if saturation_floor < 0.35 and 0.45 < red_ratio < 0.7 and aspect > 1.0:
            features.add('living room')
        if width > height and 0.25 < saturation_floor < 0.7 and aspect > 1.1:
            features.add('kitchen')
        if aspect < 0.85 and min(width, height) > 300:
            features.add('bathroom')
        return {feature for feature in features if feature in CANONICAL_VISUAL_FEATURES}

    def analyze_image(self, image_path: str, original_filename: str = None) -> Dict:
        detected_features = set()
        if original_filename:
            detected_features.update(self._extract_filename_features(original_filename))
        else:
            detected_features.update(self._extract_filename_features(image_path))

        signature = {}
        try:
            with Image.open(image_path) as image:
                rgb_image = image.convert('RGB')
                signature = self._extract_visual_signature(rgb_image)
                detected_features.update(self._detect_visual_features(rgb_image))
        except Exception as exc:
            logger.warning('Unable to analyze image %s: %s', image_path, exc)

        detected_features = sorted({feature for feature in detected_features if feature in CANONICAL_VISUAL_FEATURES})
        description = 'Detected features: ' + (', '.join(detected_features) if detected_features else 'interior details')

        return {
            'detected_features': detected_features,
            'description': description,
            'visual_signature': signature,
        }


class VisualPropertySearchEngine:
    """Search properties by extracted visual features."""

    def __init__(self, detector: ImageFeatureDetector):
        self.detector = detector

    def extract_query_features(self, image_path: str, original_filename: str = None):
        analysis = self.detector.analyze_image(image_path, original_filename)
        return analysis, sorted(normalize_feature_set(analysis.get('detected_features') or []))

    def extract_property_features(self, property_obj):
        features = set()
        for image_obj in property_obj.images.all():
            features.update(normalize_feature_set(image_obj.ai_detected_features))
        return features

    def rank_matches(self, query_features: List[str], properties):
        query_features = focus_visual_query_features(query_features)
        query_set = set(query_features)
        ranked = []
        if not query_set:
            return ranked

        for property_obj in properties:
            prop_features = self.extract_property_features(property_obj)
            if not prop_features:
                continue

            matched = []
            total_weight = 0.0
            score = 0.0
            for feature in query_features:
                weight = 1.0
                if feature in {'swimming pool', 'garden', 'gym'}:
                    weight = 1.5
                if feature in prop_features:
                    score += weight
                    matched.append(feature)
                elif feature in FEATURE_COMPATIBILITY_GROUPS and FEATURE_COMPATIBILITY_GROUPS[feature].intersection(prop_features):
                    score += weight * 0.75
                    matched.append(feature)
                total_weight += weight

            if matched and score > 0 and len(matched) == len(query_features):
                ranked.append(
                    {
                        'property_id': property_obj.id,
                        'score': round(score / max(total_weight, 1.0), 4),
                        'matched_features': sorted(matched),
                    }
                )

        ranked.sort(key=lambda item: item['score'], reverse=True)
        return ranked


class SearchSuggestionEngine:
    """Provide autocomplete suggestions from property text and tags."""

    def get_suggestions(self, query: str, limit: int = 12) -> List[str]:
        if not query:
            return []

        try:
            from django.db.models import Q
            from properties.models import Property

            query = query.strip()
            suggestions = []
            seen = set()
            properties = Property.objects.filter(is_active=True).filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(city__icontains=query)
                | Q(ai_tags__icontains=query)
            ).order_by('-views_count')[: limit * 2]

            for prop in properties:
                for candidate in [prop.title, prop.city]:
                    if candidate and query.lower() in candidate.lower() and candidate not in seen:
                        suggestions.append(candidate)
                        seen.add(candidate)
                for tag in prop.ai_tags or []:
                    if tag and query.lower() in tag.lower() and tag not in seen:
                        suggestions.append(tag)
                        seen.add(tag)
                if len(suggestions) >= limit:
                    break

            return suggestions[:limit]
        except Exception as exc:
            logger.warning('Search suggestions failed: %s', exc)
            return []


class MarketAnalysisEngine:
    """Lightweight market insights based on local comparables."""

    def get_market_insights(self, property_obj, count: int = 6):
        try:
            from properties.models import Property

            comparables = (
                Property.objects.filter(
                    city=property_obj.city,
                    property_type=property_obj.property_type,
                    is_active=True,
                )
                .exclude(id=property_obj.id)
                .order_by('price')[:count]
            )

            if not comparables:
                return {
                    'summary': 'Insufficient local comparable listings to generate market insights.',
                    'trend': 'No trend available.',
                }

            price_values = [float(item.price) for item in comparables if item.price is not None]
            average_price = sum(price_values) / max(len(price_values), 1)
            estimate = average_price
            if property_obj.area_sqft and average_price > 0:
                estimate = average_price

            trend = 'This home is priced in line with comparable listings.'
            if property_obj.price and float(property_obj.price) > average_price * 1.05:
                trend = 'This property is valued above recent local comparables.'
            elif property_obj.price and float(property_obj.price) < average_price * 0.95:
                trend = 'This property is priced below local comparables and may represent strong value.'

            return {
                'summary': (
                    f'The average price of similar properties in {property_obj.city} is ' 
                    f'₹{average_price:,.0f}. This property compares well to the local market.'
                ),
                'trend': trend,
                'average_price': f'₹{average_price:,.0f}',
                'estimated_price': f'₹{estimate:,.0f}',
            }
        except Exception as exc:
            logger.warning('Market analysis failed: %s', exc)
            return {
                'summary': 'Unable to calculate market insights at this time.',
                'trend': '',
            }


class PropertyComparisonEngine:
    """Generate concise AI-assisted comparison direction."""

    def get_comparison_summary(self, properties):
        if not properties:
            return {'headline': 'No properties selected for comparison.', 'highlights': []}

        best_value = min(properties, key=lambda p: float(p.price or 0) / max(p.area_sqft or 1, 1))
        highest_rating = max(properties, key=lambda p: p.rating or 0)
        highlights = [
            f'{best_value.title} offers the strongest price-to-size value.',
            f'{highest_rating.title} has the highest rating ({highest_rating.rating or 0}/5).',
        ]
        return {'headline': 'AI-assisted comparison summary', 'highlights': highlights}


image_analyzer = ImageFeatureDetector()
visual_search_engine = VisualPropertySearchEngine(image_analyzer)
search_suggestion_engine = SearchSuggestionEngine()
market_analysis_engine = MarketAnalysisEngine()
comparison_engine = PropertyComparisonEngine()
"""
AI utilities for property recommendations, descriptions, and image analysis
"""
import os
import json
import logging
import re
from datetime import datetime
from typing import List, Dict
import numpy as np
from PIL import Image
from django.db.models import Q, Avg
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

CANONICAL_VISUAL_FEATURES = {
    'swimming pool',
    'kitchen',
    'modular kitchen',
    'open kitchen',
    'closed kitchen',
    'garden',
    'parking space',
    'bedroom',
    'bathroom',
    'living room',
    'balcony',
    'terrace',
    'gym',
}

# Amenities users search for by photo; when any of these are detected, drop weaker
# tags (e.g. bedroom/kitchen) so listings are not matched on partial scores.
PRIMARY_VISUAL_AMENITIES = frozenset(
    {
        'swimming pool',
        'garden',
        'gym',
        'parking space',
        'kitchen',
        'bedroom',
        'bathroom',
        'living room',
    }
)

KITCHEN_FEATURES = frozenset(
    {
        'kitchen',
        'modular kitchen',
        'open kitchen',
        'closed kitchen',
    }
)

SPECIFIC_KITCHEN_FEATURES = frozenset(
    {
        'modular kitchen',
        'open kitchen',
        'closed kitchen',
    }
)


def _focus_kitchen_query_features(kitchen_features):
    """Return the tightest kitchen query features.

    If a specific kitchen subtype is present, prefer that subtype instead of
    returning the generic 'kitchen' tag too.
    """
    specific = kitchen_features.intersection(SPECIFIC_KITCHEN_FEATURES)
    if specific:
        return sorted(specific)
    return ['kitchen']


def focus_visual_query_features(query_features):
    """
    Return the most relevant visual features from the query.
    If the image contains any kitchen-related features, focus strictly on kitchen variants
    so kitchen image searches do not match unrelated rooms.
    """
    features = set(query_features or [])
    kitchen_in_query = features.intersection(KITCHEN_FEATURES)
    if kitchen_in_query:
        return _focus_kitchen_query_features(kitchen_in_query)

    primary_in_query = features.intersection(PRIMARY_VISUAL_AMENITIES)
    if primary_in_query:
        return sorted(primary_in_query)
    return sorted(features)

VISUAL_FEATURE_SYNONYMS = {
    'pool': 'swimming pool',
    'swim': 'swimming pool',
    'spool': 'swimming pool',
    'swimming': 'swimming pool',
    'swimming_pool': 'swimming pool',
    'kitchen': 'kitchen',
    'kit': 'kitchen',
    'modular': 'modular kitchen',
    'modular kitchen': 'modular kitchen',
    'open kitchen': 'open kitchen',
    'closed kitchen': 'closed kitchen',
    'garden': 'garden',
    'gar': 'garden',
    'lawn': 'garden',
    'yard': 'garden',
    'parking': 'parking space',
    'park': 'parking space',
    'garage': 'parking space',
    'bedroom': 'bedroom',
    'bed': 'bedroom',
    'bathroom': 'bathroom',
    'bath': 'bathroom',
    'living': 'living room',
    'liv': 'living room',
    'living room': 'living room',
    'hall': 'living room',
    'balcony': 'balcony',
    'bal': 'balcony',
    'terrace': 'terrace',
    'ter': 'terrace',
    'gym': 'gym',
    'fitness': 'gym',
}

FEATURE_COMPATIBILITY_GROUPS = {
    'kitchen': {'kitchen', 'modular kitchen', 'open kitchen', 'closed kitchen'},
    'modular kitchen': {'modular kitchen'},
    'open kitchen': {'open kitchen'},
    'closed kitchen': {'closed kitchen'},
}


def normalize_visual_feature(value):
    token = str(value or '').strip().lower()
    if not token:
        return None

    compact = token.replace('-', ' ').replace('_', ' ')
    compact = ' '.join(compact.split())
    if compact in VISUAL_FEATURE_SYNONYMS:
        return VISUAL_FEATURE_SYNONYMS[compact]

    for keyword, canonical in VISUAL_FEATURE_SYNONYMS.items():
        if keyword in compact:
            return canonical
    return None


def normalize_feature_set(values):
    normalized = set()
    if not values:
        return normalized
    if isinstance(values, str):
        values = [item.strip() for item in values.split(',') if item.strip()]
    for item in values:
        token = normalize_visual_feature(item)
        if token:
            normalized.add(token)
    return normalized


def calculate_visual_similarity(sig1, sig2):
    """
    Compute a similarity score (0.0 to 1.0) between two visual signatures.
    Signatures contain color_hist, brightness, saturation, edge_density, avg_hash.
    """
    if not sig1 or not sig2:
        return 0.0

    score = 0.0

    # 1. Perceptual Hash (avg_hash is 64-char binary string)
    hash1 = sig1.get('avg_hash', '')
    hash2 = sig2.get('avg_hash', '')
    if hash1 and hash2 and len(hash1) == len(hash2):
        matches = sum(1 for a, b in zip(hash1, hash2) if a == b)
        hash_sim = matches / max(len(hash1), 1)
        # Weight this highly because structure defines the object heavily
        score += hash_sim * 0.4
    else:
        # Penalty for missing hash
        score += 0.2

    # 2. Color Histogram (Bhattacharyya or intersection)
    hist1 = sig1.get('color_hist', [])
    hist2 = sig2.get('color_hist', [])
    if hist1 and hist2 and len(hist1) == len(hist2):
        # hist is a concatenation of 3 normalized histograms, so it sums to 3.0
        intersection = sum(min(a, b) for a, b in zip(hist1, hist2)) / 3.0
        score += intersection * 0.4
    else:
        score += 0.2

    # 3. Physical Features (20%)
    def diff_sim(k):
        v1, v2 = sig1.get(k, 0), sig2.get(k, 0)
        return max(1.0 - abs(v1 - v2), 0.0)

    b_sim = diff_sim('brightness')
    s_sim = diff_sim('saturation')
    e_sim = diff_sim('edge_density')

    physical_sim = (b_sim + s_sim + e_sim) / 3.0
    score += physical_sim * 0.2

    return score


class PropertyRecommendationEngine:
    """
    Machine Learning-based property recommendation system
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    
    def _clean_city(self, city_value):
        return (city_value or "").strip().lower()
    
    def _safe_price(self, value):
        try:
            return float(value)
        except Exception:
            return 0.0
    
    def get_user_preferences(self, user):
        """Extract user preferences from their profile and search history"""
        preferences = {
            'favorite_cities': [],
            'preferred_type': None,
            'price_range': {'min': 0, 'max': float('inf')},
            'viewed_properties': [],
            'keywords': [],
            'location_history': [],
            'median_viewed_price': None,
        }
        
        try:
            if hasattr(user, 'profile'):
                if user.profile.favorite_cities:
                    preferences['favorite_cities'] = user.profile.favorite_cities.split(',')
                preferences['preferred_type'] = user.profile.preferred_property_type
            
            # Get viewed properties
            from accounts.models import UserPropertyView
            views = UserPropertyView.objects.filter(user=user).select_related('property')
            preferences['viewed_properties'] = [view.property.id for view in views[:10]]
            location_history = []
            viewed_prices = []
            keywords = []
            for view in views[:35]:
                prop = view.property
                city_clean = self._clean_city(getattr(prop, 'city', ''))
                if city_clean:
                    location_history.append(city_clean)
                if getattr(prop, 'price', None) is not None:
                    viewed_prices.append(float(prop.price))
                keywords.extend([
                    getattr(prop, 'property_type', '') or '',
                    getattr(prop, 'city', '') or '',
                    getattr(prop, 'description', '') or '',
                ])
            preferences['location_history'] = location_history
            preferences['keywords'] = [kw for kw in keywords if kw]
            if viewed_prices:
                median_price = float(np.median(np.array(viewed_prices)))
                spread = max(median_price * 0.35, 1000000)
                preferences['median_viewed_price'] = median_price
                preferences['price_range'] = {
                    'min': max(0.0, median_price - spread),
                    'max': median_price + spread,
                }
            
        except Exception as e:
            logger.error(f"Error extracting user preferences: {str(e)}")
        
        return preferences
    
    def _build_property_text(self, prop):
        return " ".join(
            [
                getattr(prop, 'title', '') or '',
                getattr(prop, 'description', '') or '',
                getattr(prop, 'city', '') or '',
                getattr(prop, 'property_type', '') or '',
                " ".join(getattr(prop, 'ai_tags', []) or []),
            ]
        ).strip()
    
    def _budget_score(self, pref_price, prop_price):
        if not pref_price or not prop_price:
            return 0.4
        distance_ratio = abs(prop_price - pref_price) / max(pref_price, 1)
        score = 1.0 - min(distance_ratio, 1.0)
        return max(score, 0.0)
    
    def get_recommendations(self, user, count=10):
        """
        Get personalized property recommendations for a user
        """
        try:
            from properties.models import Property
            
            preferences = self.get_user_preferences(user)
            properties_qs = Property.objects.filter(is_active=True).exclude(
                id__in=preferences['viewed_properties']
            )
            properties = list(properties_qs[:220])
            if not properties:
                return []
            
            favorite_cities = {
                self._clean_city(city)
                for city in (preferences.get('favorite_cities') or [])
                if city
            }
            location_history = preferences.get('location_history') or []
            location_weight_map = {}
            for city in location_history:
                location_weight_map[city] = location_weight_map.get(city, 0) + 1
            max_location_hits = max(location_weight_map.values()) if location_weight_map else 1
            
            preferred_type = preferences.get('preferred_type')
            preferred_price = preferences.get('median_viewed_price')
            viewed_keywords = " ".join(preferences.get('keywords') or [])
            corpus = [viewed_keywords or "real estate home"] + [self._build_property_text(prop) for prop in properties]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            scored = []
            for idx, prop in enumerate(properties):
                city_clean = self._clean_city(getattr(prop, 'city', ''))
                city_score = 1.0 if city_clean in favorite_cities else 0.0
                if city_clean in location_weight_map:
                    city_score = max(city_score, location_weight_map[city_clean] / max_location_hits)
                type_score = 1.0 if preferred_type and prop.property_type == preferred_type else 0.0
                budget_score = self._budget_score(preferred_price, self._safe_price(prop.price))
                popularity_score = min((float(prop.views_count or 0) / 250.0), 1.0)
                rating_score = min((float(prop.rating or 0) / 5.0), 1.0)
                semantic_score = float(similarities[idx]) if idx < len(similarities) else 0.0
                final_score = (
                    0.34 * semantic_score
                    + 0.22 * budget_score
                    + 0.16 * city_score
                    + 0.10 * type_score
                    + 0.10 * popularity_score
                    + 0.08 * rating_score
                )
                prop.recommendation_score = round(final_score, 4)
                scored.append((final_score, prop))
            
            scored.sort(key=lambda item: item[0], reverse=True)
            return [item[1] for item in scored[:count]]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def get_similar_properties(self, property_obj, count=5):
        """
        Find similar properties based on description, type, price, etc
        """
        try:
            from properties.models import Property
            
            similar = Property.objects.filter(
                property_type=property_obj.property_type,
                city=property_obj.city,
                is_active=True
            ).exclude(
                id=property_obj.id
            ).order_by('-rating', '-views_count')[:count]
            
            return list(similar)
            
        except Exception as e:
            logger.error(f"Error getting similar properties: {str(e)}")
            return []


class AIDescriptionGenerator:
    """
    Use OpenAI or other AI services to generate property descriptions
    """
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client if API key is available"""
        try:
            api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            api_key = api_key.strip() if isinstance(api_key, str) else None
            if api_key and (not hasattr(self, '_api_key') or self._api_key != api_key):
                os.environ['OPENAI_API_KEY'] = api_key
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self._api_key = api_key
        except Exception as e:
            logger.warning(f"OpenAI client not initialized: {str(e)}")
    
    def generate_description(self, property_data: Dict) -> str:
        """
        Generate AI-powered property description
        """
        self._init_client()
        if not self.client:
            return self._generate_template_description(property_data)
        
        try:
            prompt = f"""
            Generate a compelling and concise real estate property description based on the following details:
            
            Property Type: {property_data.get('property_type', 'Property')}
            Location: {property_data.get('city', '')}, {property_data.get('state', '')}
            Address: {property_data.get('address', '')}
            Price: ₹{property_data.get('price', 0):,.0f}
            Bedrooms: {property_data.get('bedrooms', 'N/A')}
            Bathrooms: {property_data.get('bathrooms', 'N/A')}
            Area: {property_data.get('area_sqft', 'N/A')} sq ft
            Furnishing: {property_data.get('furnishing', 'Unfurnished')}
            Nearby Locations: {property_data.get('nearby_summary', '')}
            
            Please create a property description that is engaging, highlights key features, 
            and appeals to potential buyers. Keep it between 150-250 words.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional real estate copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI description: {str(e)}")
            return self._generate_template_description(property_data)
    
    def _format_price_label(self, raw_price):
        try:
            price = float(raw_price)
            if price >= 1_00_00_000:
                return f"INR {price / 1_00_00_000:.2f} Cr"
            if price >= 1_00_000:
                return f"INR {price / 1_00_000:.1f} Lakh"
            return f"INR {price:,.0f}"
        except Exception:
            return "INR on request"
    
    def _generate_template_description(self, property_data: Dict) -> str:
        """
        Generate description using template when AI is not available
        """
        prop_type = property_data.get('property_type', 'Property')
        city = property_data.get('city', '')
        bedrooms = property_data.get('bedrooms', '')
        bathrooms = property_data.get('bathrooms', '')
        area = property_data.get('area_sqft', '')
        
        price_label = self._format_price_label(property_data.get('price'))
        nearby = property_data.get('nearby_summary') or "schools, hospitals, transit links, and daily essentials"
        furnishing = (property_data.get('furnishing') or 'unfurnished').replace('-', ' ')
        description = f"""
        Discover a future-ready {prop_type} in {city}, built for comfort, accessibility, and long-term value.
        This listing offers {bedrooms or 'well-planned'} bedrooms, {bathrooms or 'modern'} bathrooms, and around {area or 'spacious'} sq ft of usable area.
        Priced at {price_label}, it is ideal for homebuyers and investors searching for high-potential real estate in {city}.

        The home features {furnishing} interiors and convenient access to {nearby}.
        With strong neighborhood livability and lifestyle convenience, this property is designed for families, professionals, and premium rental demand.

        Schedule a visit today to explore this opportunity and compare it with similar listings in the market.
        """
        return description.strip()
    
    def generate_seo_payload(self, property_data: Dict) -> Dict:
        tags = self.generate_seo_tags(property_data)
        property_type = (property_data.get('property_type') or 'property').replace('-', ' ').title()
        city = property_data.get('city') or 'India'
        bedrooms = property_data.get('bedrooms')
        bedroom_label = f"{bedrooms} BHK " if bedrooms else ""
        title = f"{bedroom_label}{property_type} for Sale in {city} | LuxeEstate"
        meta_description = (
            f"Explore {bedroom_label.lower() if bedrooms else ''}{property_type.lower()} listings in {city}. "
            "Get AI-personalized recommendations, market insights, and instant site-visit booking on LuxeEstate."
        )[:160]
        return {
            'seo_title': title,
            'meta_description': meta_description,
            'keywords': tags,
        }
    
    def generate_seo_tags(self, property_data: Dict) -> List[str]:
        """
        Generate SEO tags for property
        """
        tags = [
            f"buy-{property_data.get('property_type', 'property')}",
            f"{property_data.get('city', '').lower()}-property",
            f"real-estate-{property_data.get('city', '').lower()}",
        ]
        
        if property_data.get('bedrooms'):
            tags.append(f"{property_data['bedrooms']}-bedroom-property")
        
        if property_data.get('price'):
            try:
                price = float(property_data['price'])
                if price < 50_00_000:
                    tags.append("budget-property")
                elif price < 1_00_00_000:
                    tags.append("mid-range-property")
                else:
                    tags.append("luxury-property")
            except (ValueError, TypeError):
                pass
        
        return tags


class ImageFeatureDetector:
    """
    Analyze property images to detect features
    """
    
    def __init__(self):
        self.hist_bins = 8
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            api_key = api_key.strip() if isinstance(api_key, str) else None
            if api_key and (not hasattr(self, '_api_key') or self._api_key != api_key):
                os.environ['OPENAI_API_KEY'] = api_key
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self._api_key = api_key
        except Exception as e:
            logger.warning(f"OpenAI client not initialized for Vision: {str(e)}")

    def _normalize_hist(self, values):
        vector = np.array(values, dtype=np.float32)
        total = float(vector.sum())
        if total <= 0:
            return [0.0 for _ in values]
        return (vector / total).round(6).tolist()

    def _extract_filename_features(self, image_path: str):
        filename = os.path.basename(image_path).lower()
        tokens = {
            token.strip()
            for token in (
                filename.replace('-', ' ')
                .replace('_', ' ')
                .replace('.', ' ')
                .split()
            )
            if token.strip()
        }
        detected = set()
        keyword_map = {
            'swimming pool': 'swimming pool',
            'swimming': 'swimming pool',
            'kitchen': 'kitchen',
            'garden': 'garden',
            'gym': 'gym',
            'balcony': 'balcony',
            'terrace': 'terrace',
            'bedroom': 'bedroom',
            'bathroom': 'bathroom',
            'living': 'living room',
            'parking': 'parking space',
        }
        
        # Prioritize core features. If a specific structural feature is in filename,
        # we return it as the exclusive detection for better search accuracy.
        PRIORITY_FEATURES = [
            'swimming pool',
            'garden',
            'gym',
            'parking space',
            'kitchen',
            'terrace',
            'balcony',
        ]
        
        detected_all = set()
        for token, feature in keyword_map.items():
            if token in tokens:
                detected_all.add(feature)
                
        # Return only the highest priority feature found in the filename
        for pf in PRIORITY_FEATURES:
            if pf in detected_all:
                return {pf}
                
        return detected_all

    def _extract_visual_signature(self, rgb_image):
        resized = rgb_image.resize((256, 256))
        arr = np.array(resized, dtype=np.float32)
        if arr.size == 0:
            return {}

        red = arr[:, :, 0]
        green = arr[:, :, 1]
        blue = arr[:, :, 2]
        gray = (0.299 * red) + (0.587 * green) + (0.114 * blue)

        # Simple edge estimate to distinguish structured interiors.
        grad_x = np.abs(np.diff(gray, axis=1))
        grad_y = np.abs(np.diff(gray, axis=0))
        edge_density = float(((grad_x > 18).sum() + (grad_y > 18).sum()) / (gray.size * 2.0))

        brightness = float(np.mean(gray) / 255.0)
        channel_max = np.maximum.reduce([red, green, blue])
        channel_min = np.minimum.reduce([red, green, blue])
        saturation = float(np.mean((channel_max - channel_min) / np.maximum(channel_max, 1.0)))

        hist_r = self._normalize_hist(np.histogram(red, bins=self.hist_bins, range=(0, 255))[0])
        hist_g = self._normalize_hist(np.histogram(green, bins=self.hist_bins, range=(0, 255))[0])
        hist_b = self._normalize_hist(np.histogram(blue, bins=self.hist_bins, range=(0, 255))[0])
        color_hist = hist_r + hist_g + hist_b

        avg_hash_input = np.array(rgb_image.convert('L').resize((8, 8)), dtype=np.float32)
        avg_hash_threshold = float(avg_hash_input.mean())
        avg_hash = ''.join('1' if pixel >= avg_hash_threshold else '0' for pixel in avg_hash_input.flatten())

        return {
            'color_hist': color_hist,
            'brightness': round(brightness, 5),
            'saturation': round(saturation, 5),
            'edge_density': round(edge_density, 5),
            'avg_hash': avg_hash,
        }

    def _analyze_with_openai_vision(self, image_path: str) -> set:
        """Call OpenAI Vision API to detect exact features."""
        self._init_client()
        if not self.client:
            return set()
            
        import base64
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            prompt = (
                "You are a real estate visual feature detector. Look at the image carefully and identify which of the following features are clearly visible. "
                "If the image shows a kitchen, determine whether it is a modular kitchen, an open kitchen, or a closed kitchen. "
                "If the kitchen is visible but the subtype cannot be confidently identified, return 'kitchen'. "
                "Only return features from this exact list: [swimming pool, kitchen, modular kitchen, open kitchen, closed kitchen, garden, parking space, bedroom, bathroom, living room, balcony, terrace, gym]. "
                "Return the detected features as a JSON array of strings (e.g., [\"swimming pool\", \"garden\"]). If none are visible, return []."
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=150,
            )
            content = response.choices[0].message.content.strip()
            
            # Extract JSON array
            import json
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                detected_list = json.loads(match.group(0))
                return {str(item).lower() for item in detected_list if str(item).lower() in CANONICAL_VISUAL_FEATURES}
                
        except Exception as e:
            logger.warning("OpenAI Vision failed: %s", e)
            
        return set()

    def analyze_image(self, image_path: str, original_filename: str = None) -> Dict:
        """Analyze property image and output searchable feature metadata."""
        try:
            detected_features = set()
            file_name_source = original_filename if original_filename else image_path
            detected_features.update(self._extract_filename_features(file_name_source))

            with Image.open(image_path) as img:
                rgb = img.convert('RGB')
                width, height = rgb.size
                signature = self._extract_visual_signature(rgb)

                # Fetch AI features
                inferred = self._analyze_with_openai_vision(image_path)
                
                # If API quota/fail occurs, it relies gracefully on filename features.
                if inferred:
                    detected_features.update(inferred)

                if width >= 1400 or height >= 1400:
                    detected_features.add('high-resolution')
                if width > height:
                    detected_features.add('wide layout')

            ordered_features = sorted(detected_features)
            feature_phrase = ', '.join(ordered_features[:6]) if ordered_features else 'interior details'
            description = f"AI detected visual features: {feature_phrase}."
            result = {
                'detected_features': ordered_features,
                'description': description,
                'tags': ['property', 'real-estate'] + ordered_features[:5],
                'quality_score': 0.9 if ordered_features else 0.55,
                'visual_signature': signature,
            }
            logger.info(f"Image analysis completed for {image_path}")
            return result
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                'detected_features': [],
                'description': 'Property image',
                'tags': [],
                'quality_score': 0.5,
                'visual_signature': {},
            }


class VisualPropertySearchEngine:
    """Fresh backend for feature-based image search over property listings."""

    def __init__(self, detector: ImageFeatureDetector):
        self.detector = detector

    def extract_query_features(self, image_path: str, original_filename: str = None):
        analysis = self.detector.analyze_image(image_path, original_filename)
        detected = normalize_feature_set(analysis.get('detected_features') or [])
        query_features = sorted(feature for feature in detected if feature in CANONICAL_VISUAL_FEATURES)
        return analysis, query_features

    def extract_property_features(self, property_obj):
        image_features = set()
        for image_obj in property_obj.images.all():
            image_features.update(normalize_feature_set(image_obj.ai_detected_features))
            
        return image_features.intersection(CANONICAL_VISUAL_FEATURES)

    def rank_matches(self, query_features, properties):
        if not query_features:
            return []

        effective = focus_visual_query_features(query_features)
        query_set = set(effective)
        feature_weights = {
            'swimming pool': 1.6,
            'modular kitchen': 1.4,
            'open kitchen': 1.4,
            'closed kitchen': 1.4,
            'kitchen': 1.2,
            'garden': 1.2,
            'parking space': 1.1,
            'gym': 1.3,
        }
        ranked = []
        for prop in properties:
            prop_features = self.extract_property_features(prop)
            if not prop_features:
                continue
            matched_features = []
            weighted_score = 0.0
            weighted_max = 0.0
            ok = True

            for query_feature in query_set:
                weight = feature_weights.get(query_feature, 1.0)
                weighted_max += weight
                if query_feature in prop_features:
                    matched_features.append(query_feature)
                    weighted_score += weight
                else:
                    compatible = FEATURE_COMPATIBILITY_GROUPS.get(query_feature, set())
                    if compatible and compatible.intersection(prop_features):
                        matched_features.append(query_feature)
                        weighted_score += weight * 0.7
                    else:
                        ok = False
                        break

            if not ok or not matched_features:
                continue

            score = weighted_score / max(weighted_max, 1.0)
            ranked.append(
                {
                    'property_id': prop.id,
                    'score': round(score, 4),
                    'matched_features': sorted(set(matched_features)),
                }
            )
        ranked.sort(key=lambda item: item['score'], reverse=True)
        return ranked

    def search_from_image(self, image_path: str, properties, original_filename: str = None):
        analysis, query_features = self.extract_query_features(image_path, original_filename)
        if not query_features:
            return {
                'success': False,
                'message': 'Could not detect enough property features from the image.',
                'detected_features': sorted(normalize_feature_set(analysis.get('detected_features') or [])),
                'query_features': [],
                'matches': [],
            }
        focused = focus_visual_query_features(query_features)
        ranked_matches = self.rank_matches(focused, properties)
        if not ranked_matches:
            return {
                'success': False,
                'message': 'No listings matched the visual features from this image.',
                'detected_features': sorted(normalize_feature_set(analysis.get('detected_features') or [])),
                'query_features': focused,
                'matches': [],
            }

        # Keep high-relevance matches while allowing compatible subtypes
        # (for example, open kitchen <-> kitchen).
        filtered = [
            item for item in ranked_matches
            if item['score'] >= 0.7
            and len(item.get('matched_features') or []) == len(focused)
        ]
        
        if not filtered:
            return {
                'success': False,
                'message': 'No listings matched the required visual features with enough confidence.',
                'detected_features': sorted(normalize_feature_set(analysis.get('detected_features') or [])),
                'query_features': focused,
                'matches': [],
            }
        return {
            'success': True,
            'message': f'Found {len(filtered)} visually similar properties.',
            'detected_features': sorted(normalize_feature_set(analysis.get('detected_features') or [])),
            'query_features': focused,
            'matches': filtered[:30],
        }


class SearchSuggestionEngine:
    """AI-powered search suggestions and auto-complete"""

    def get_suggestions(self, query: str, limit: int = 12) -> List[str]:
        if not query:
            return []

        from properties.models import Property

        query = query.strip()
        suggestions = []
        seen = set()

        properties = Property.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(amenities__icontains=query) |
            Q(ai_tags__icontains=query)
        ).order_by('-views_count')[:limit * 2]

        for prop in properties:
            for candidate in [prop.title, prop.city]:
                if candidate and query.lower() in candidate.lower() and candidate not in seen:
                    suggestions.append(candidate)
                    seen.add(candidate)

            amenities = prop.amenities or []
            if isinstance(amenities, str):
                try:
                    amenities = json.loads(amenities)
                except Exception:
                    amenities = []

            for amenity in amenities:
                if amenity and query.lower() in amenity.lower() and amenity not in seen:
                    suggestions.append(amenity)
                    seen.add(amenity)

            for tag in prop.ai_tags or []:
                if tag and query.lower() in tag.lower() and tag not in seen:
                    suggestions.append(tag)
                    seen.add(tag)

            if len(suggestions) >= limit:
                break

        return suggestions[:limit]


class MarketAnalysisEngine:
    """Generate market insights and pricing suggestions"""

    def get_market_insights(self, property_obj, count: int = 10) -> Dict:
        try:
            from properties.models import Property

            comparables = Property.objects.filter(
                city=property_obj.city,
                property_type=property_obj.property_type,
                is_active=True
            ).exclude(id=property_obj.id)[:count]

            if not comparables:
                return {
                    'estimated_price': property_obj.formatted_price,
                    'average_price': property_obj.formatted_price,
                    'summary': 'Not enough comparable listings to generate a market estimate yet.',
                    'trend': 'No reliable trend available.'
                }

            total_price = 0.0
            total_area = 0.0
            comparable_prices = []
            price_per_sqft_values = []

            for comparable in comparables:
                comparable_prices.append(float(comparable.price))
                if comparable.area_sqft and comparable.area_sqft > 0:
                    price_per_sqft_values.append(float(comparable.price) / comparable.area_sqft)
                total_price += float(comparable.price)
                if comparable.area_sqft:
                    total_area += comparable.area_sqft

            average_price = total_price / max(len(comparable_prices), 1)
            avg_price_per_sqft = (
                sum(price_per_sqft_values) / len(price_per_sqft_values)
                if price_per_sqft_values else 0
            )

            if property_obj.area_sqft and avg_price_per_sqft > 0:
                estimated_price = avg_price_per_sqft * property_obj.area_sqft
            else:
                estimated_price = float(property_obj.price)

            price_gap = float(property_obj.price) - estimated_price
            gap_pct = (price_gap / estimated_price * 100) if estimated_price else 0

            if gap_pct > 5:
                trend = 'This listing is priced above local comparable listings.'
            elif gap_pct < -5:
                trend = 'This listing is priced below local comparable listings and may represent a strong value.'
            else:
                trend = 'This listing is priced in line with current local market trends.'

            summary = (
                f'Based on {len(comparables)} similar properties in {property_obj.city}, the average price is ' \
                f'₹{average_price:,.0f}. The estimated market price for this property is ' \
                f'₹{estimated_price:,.0f}.'
            )

            return {
                'estimated_price': f'₹{estimated_price:,.0f}',
                'average_price': f'₹{average_price:,.0f}',
                'summary': summary,
                'trend': trend,
                'comparable_count': len(comparables)
            }

        except Exception as e:
            logger.error(f"Error generating market insights: {str(e)}")
            return {
                'estimated_price': property_obj.formatted_price,
                'average_price': property_obj.formatted_price,
                'summary': 'Unable to generate market insights at this time.',
                'trend': ''
            }


class PropertyComparisonEngine:
    """AI-assisted comparison summaries for property comparisons"""

    def get_comparison_summary(self, properties):
        if not properties:
            return {
                'headline': 'No properties selected for comparison.',
                'highlights': []
            }

        values = []
        for prop in properties:
            price_per_sqft = None
            if prop.area_sqft and prop.area_sqft > 0:
                price_per_sqft = float(prop.price) / prop.area_sqft
            values.append({
                'property': prop,
                'price_per_sqft': price_per_sqft or float(prop.price),
            })

        best_value = min(values, key=lambda x: x['price_per_sqft'])['property']
        highest_rating = max(properties, key=lambda x: x.rating or 0)

        highlights = [
            f"{best_value.title} offers the best value with the lowest price per sq ft.",
            f"{highest_rating.title} has the highest customer rating ({highest_rating.rating}/5)."
        ]

        return {
            'headline': 'AI-assisted comparison summary',
            'highlights': highlights
        }


# Initialize singletons
recommendation_engine = PropertyRecommendationEngine()
description_generator = AIDescriptionGenerator()
image_analyzer = ImageFeatureDetector()
search_suggestion_engine = SearchSuggestionEngine()
market_analysis_engine = MarketAnalysisEngine()
comparison_engine = PropertyComparisonEngine()
visual_search_engine = VisualPropertySearchEngine(image_analyzer)
