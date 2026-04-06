import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, LabelEncoder
from django.db.models import Count, Avg
from .models import Property, UserSearch, UserView, UserProfile
import numpy as np


def build_user_property_matrix():
    """
    Build a user-property interaction matrix based on views, searches, and favorites.
    """
    # Get all users who have interactions
    users = set()
    for model in [UserView, UserSearch]:
        users.update(model.objects.values_list('user_id', flat=True))

    users = list(users)
    if not users:
        return pd.DataFrame(), []

    # Get all properties
    properties = list(Property.objects.values_list('id', flat=True))

    # Initialize matrix
    matrix = pd.DataFrame(0, index=users, columns=properties)

    # Add views (weight 3)
    views = UserView.objects.values('user_id', 'property_id')
    for view in views:
        matrix.at[view['user_id'], view['property_id']] += 3

    # Add searches (weight 1) - if search matches property
    searches = UserSearch.objects.all()
    for search in searches:
        matching_props = Property.objects.filter(
            city__icontains=search.city or '',
            property_type=search.property_type or '',
            price__gte=search.min_price or 0,
            price__lte=search.max_price or 999999999
        ).values_list('id', flat=True)
        for prop_id in matching_props:
            if prop_id in properties:
                matrix.at[search.user_id, prop_id] += 1

    # Add favorites (weight 5) - assuming favorites app exists
    try:
        from favorites.models import Favorite
        favs = Favorite.objects.values('user_id', 'property_id')
        for fav in favs:
            matrix.at[fav['user_id'], fav['property_id']] += 5
    except ImportError:
        pass

    return matrix, properties


def get_user_features(user):
    """
    Get user feature vector from profile and history.
    """
    try:
        profile = UserProfile.objects.get(user=user)
        budget_min = float(profile.budget_min or 0)
        budget_max = float(profile.budget_max or 10000000)
        cities = profile.preferred_cities
        types = profile.preferred_property_types
    except UserProfile.DoesNotExist:
        budget_min = 0
        budget_max = 10000000
        cities = []
        types = []

    # Recent searches
    recent_searches = UserSearch.objects.filter(user=user).order_by('-timestamp')[:10]
    search_cities = [s.city for s in recent_searches if s.city]
    search_types = [s.property_type for s in recent_searches if s.property_type]
    search_prices = [float(s.min_price or 0) + float(s.max_price or 10000000) for s in recent_searches]
    avg_search_price = np.mean(search_prices) if search_prices else 500000

    # Viewed properties features
    viewed_props = UserView.objects.filter(user=user).select_related('property')
    viewed_prices = [float(p.property.price) for p in viewed_props]
    viewed_cities = [p.property.city for p in viewed_props]
    viewed_types = [p.property.property_type for p in viewed_props]

    avg_viewed_price = np.mean(viewed_prices) if viewed_prices else avg_search_price

    # Combine cities and types
    all_cities = list(set(cities + search_cities + viewed_cities))
    all_types = list(set(types + search_types + viewed_types))

    return {
        'budget_min': budget_min,
        'budget_max': budget_max,
        'avg_price': avg_viewed_price,
        'cities': all_cities,
        'types': all_types,
    }


def get_property_features(property):
    """
    Get property feature vector.
    """
    return {
        'price': float(property.price),
        'city': property.city,
        'type': property.property_type,
        'latitude': float(property.latitude or 0),
        'longitude': float(property.longitude or 0),
        'views': property.views_count,
    }


def recommend_properties_ml(user, limit=8, exclude_pk=None):
    """
    ML-based recommendations using collaborative filtering and content-based features.
    """
    if not user.is_authenticated:
        return Property.objects.order_by('-views_count')[:limit]

    # Build interaction matrix
    matrix, prop_ids = build_user_property_matrix()
    if matrix.empty:
        # Fallback to basic recommendations
        from .ai_services import recommend_for_user
        return recommend_for_user(user, limit, exclude_pk)

    # Compute user similarities
    if matrix.shape[0] > 1:
        user_sim = cosine_similarity(matrix)
        user_sim_df = pd.DataFrame(user_sim, index=matrix.index, columns=matrix.index)

        # Find similar users
        user_idx = matrix.index.get_loc(user.id)
        similar_users = user_sim_df.iloc[user_idx].sort_values(ascending=False)[1:6]  # top 5 similar

        # Aggregate ratings from similar users
        recommendations = {}
        for sim_user_id, sim_score in similar_users.items():
            user_ratings = matrix.loc[sim_user_id]
            for prop_id, rating in user_ratings.items():
                if rating > 0:
                    recommendations[prop_id] = recommendations.get(prop_id, 0) + rating * sim_score

        # Sort by score
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        rec_prop_ids = [pid for pid, score in sorted_recs if pid != exclude_pk][:limit]
    else:
        rec_prop_ids = []

    # If not enough, add content-based recommendations
    if len(rec_prop_ids) < limit:
        user_features = get_user_features(user)
        all_props = Property.objects.exclude(pk=exclude_pk).exclude(id__in=rec_prop_ids)

        prop_scores = []
        for prop in all_props:
            prop_features = get_property_features(prop)
            score = 0

            # Price match
            if user_features['budget_min'] <= prop_features['price'] <= user_features['budget_max']:
                score += 2
            elif abs(prop_features['price'] - user_features['avg_price']) / user_features['avg_price'] < 0.5:
                score += 1

            # City match
            if prop_features['city'] in user_features['cities']:
                score += 3

            # Type match
            if prop_features['type'] in user_features['types']:
                score += 2

            # Popularity
            score += min(prop_features['views'] / 100, 1)

            prop_scores.append((prop.id, score))

        prop_scores.sort(key=lambda x: x[1], reverse=True)
        additional_ids = [pid for pid, score in prop_scores[:limit - len(rec_prop_ids)]]
        rec_prop_ids.extend(additional_ids)

    # Return Property objects
    if rec_prop_ids:
        return Property.objects.filter(id__in=rec_prop_ids).order_by('-views_count')
    else:
        return Property.objects.order_by('-views_count')[:limit]