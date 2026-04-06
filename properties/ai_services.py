"""
AI helpers: lead chatbot, recommendations, description/SEO, image feature hints.
Uses OpenAI / Google Vision when API keys are set; sensible fallbacks otherwise.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings

# Import the new SEO service
from .seo_service import (
    generate_seo_optimized_description,
    generate_seo_meta_description,
    generate_seo_optimized_title,
    extract_property_keywords,
    calculate_seo_score,
)


def chatbot_reply(user_message: str, property_title: str | None = None) -> str:
    """Rule-based + optional OpenAI for property chat widget."""
    try:
        text = (user_message or "").strip().lower()
        if not text:
            return "Hi! Ask me about this listing, pricing, or scheduling a visit."

        if any(k in text for k in ("price", "cost", "how much")):
            return (
                "For exact pricing and negotiations, the listing agent can help. "
                "Use Contact Agent or open live chat with the owner."
            )
        if any(k in text for k in ("visit", "schedule", "appointment", "meeting")):
            return (
                "I can note your interest in a site visit. Reply with your preferred date range; "
                "the agent will confirm shortly."
            )
        if any(k in text for k in ("loan", "emi", "mortgage")):
            return (
                "EMI depends on bank rates and tenure. I recommend checking with your bank "
                "or our payment partner flow for indicative numbers."
            )

        key = getattr(settings, "OPENAI_API_KEY", "") or ""
        if key:
            try:
                r = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a concise real-estate assistant for LuxeEstate. "
                                    "Answer in under 80 words. Property context: "
                                    + (property_title or "general inquiry")
                                ),
                            },
                            {"role": "user", "content": user_message[:2000]},
                        ],
                        "max_tokens": 200,
                    },
                    timeout=25,
                )
                r.raise_for_status()
                data = r.json()
                return (
                    data["choices"][0]["message"]["content"].strip()
                    or "Thanks for your message — an agent will respond shortly."
                )
            except Exception as api_error:
                print(f"OpenAI API error in chatbot_reply: {api_error}")
                # Fall through to default response

        return (
            "Thanks for your message. For detailed answers about this property, "
            "please use Contact Agent or continue in live chat with the listing owner."
        )
    except Exception as e:
        print(f"Unexpected error in chatbot_reply: {e}")
        return (
            "Thanks for your message. An agent will respond shortly."
        )


def recommend_for_user(user, limit: int = 8, exclude_pk: int | None = None):
    """ML-enhanced recommendations using collaborative filtering and user behavior."""
    try:
        from .ml_recommendations import recommend_properties_ml
        return recommend_properties_ml(user, limit, exclude_pk)
    except Exception as e:
        print(f"ML recommendation failed: {e}")
        # Fallback to basic recommendations
        from properties.models import Property
        from favorites.models import Favorite

        if not user.is_authenticated:
            qs = Property.objects.order_by("-views_count", "-created_at")
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            return qs[:limit]

        favs = Favorite.objects.filter(user=user).select_related("property")
        cities = {f.property.city for f in favs}
        types = {f.property.property_type for f in favs}
        qs = Property.objects.all()
        if cities:
            qs = qs.filter(city__in=cities)
        elif types:
            qs = qs.filter(property_type__in=types)
        else:
            qs = Property.objects.order_by("-views_count", "-created_at")
        qs = qs.exclude(agent=user)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs.order_by("-views_count", "-created_at").distinct()[:limit]


def generate_property_description(payload: dict[str, Any]) -> str:
    """SEO-friendly description from structured fields; uses AI enhancement."""
    # Use the new SEO-optimized description generator
    return generate_seo_optimized_description(payload)


def seo_snippet(description: str, max_len: int = 155) -> str:
    """Generate SEO-optimized meta description."""
    city = ""  # These params are optional for the new function
    property_type = ""
    return generate_seo_meta_description(description, city, property_type, max_length=max_len)


def analyze_property_image(image_field) -> dict[str, Any]:
    """
    Returns labels/features for search. Uses Google Vision label detection if key set;
    otherwise returns empty tags (UI can still allow manual tags).
    """
    key = getattr(settings, "GOOGLE_VISION_API_KEY", "") or ""
    if not key or not image_field:
        return {"labels": [], "features": []}

    try:
        from base64 import b64encode

        image_field.open("rb")
        content = image_field.read()
        image_field.close()
        b64 = b64encode(content).decode("ascii")
        r = requests.post(
            f"https://vision.googleapis.com/v1/images:annotate?key={key}",
            json={
                "requests": [
                    {
                        "image": {"content": b64},
                        "features": [{"type": "LABEL_DETECTION", "maxResults": 15}],
                    }
                ]
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        responses = data.get("responses", [{}])[0]
        labels = responses.get("labelAnnotations", [])
        names = [l.get("description", "") for l in labels if l.get("description")]
        poolish = any(
            re.search(r"swimming|pool", n, re.I) for n in names
        )
        kitchenish = any(re.search(r"kitchen", n, re.I) for n in names)
        feats = []
        if poolish:
            feats.append("swimming_pool")
        if kitchenish:
            feats.append("kitchen_visible")
        return {"labels": names[:12], "features": feats}
    except Exception:
        return {"labels": [], "features": []}


def detect_property_features_advanced(image_field) -> dict[str, Any]:
    """
    Advanced image analysis to detect property features.
    Uses Google Vision API and OpenAI Vision for detailed feature detection.
    Returns structured feature data with confidence scores and categories.
    """
    if not image_field:
        return {
            "success": False,
            "features": [],
            "categories": {},
            "confidence": 0,
            "raw_labels": [],
            "message": "No image provided"
        }
    
    # Read image data once
    try:
        image_field.seek(0)
        image_data = image_field.read()
        image_field.seek(0)
        if not image_data:
            return {
                "success": False,
                "features": [],
                "categories": {},
                "confidence": 0,
                "raw_labels": [],
                "message": "Image is empty"
            }
    except Exception as e:
        print(f"Error reading image: {e}")
        return {
            "success": False,
            "features": [],
            "categories": {},
            "confidence": 0,
            "raw_labels": [],
            "message": f"Error reading image: {str(e)}"
        }
    
    # Feature mapping categories
    FEATURE_MAPPING = {
        "swimming_pool": {
            "keywords": ["swimming", "pool", "water feature", "aquatic"],
            "category": "Water Features",
            "icon": "🏊",
            "search_term": "pool"
        },
        "kitchen": {
            "keywords": ["kitchen", "cooking", "appliances", "stove", "counter"],
            "category": "Interior",
            "icon": "👨‍🍳",
            "search_term": "kitchen"
        },
        "garden": {
            "keywords": ["garden", "landscape", "plants", "grass", "outdoor space"],
            "category": "Outdoor",
            "icon": "🌳",
            "search_term": "garden"
        },
        "balcony": {
            "keywords": ["balcony", "terrace", "patio", "deck", "veranda"],
            "category": "Outdoor",
            "icon": "🏢",
            "search_term": "balcony"
        },
        "parking": {
            "keywords": ["parking", "garage", "carport", "driveway"],
            "category": "Amenities",
            "icon": "🚗",
            "search_term": "parking"
        },
        "living_room": {
            "keywords": ["living room", "lounge", "sitting", "furniture"],
            "category": "Interior",
            "icon": "🛋️",
            "search_term": "living room"
        },
        "bedroom": {
            "keywords": ["bedroom", "bed", "dormitory"],
            "category": "Interior",
            "icon": "🛏️",
            "search_term": "bedroom"
        },
        "bathroom": {
            "keywords": ["bathroom", "toilet", "washroom", "bath"],
            "category": "Interior",
            "icon": "🚿",
            "search_term": "bathroom"
        },
        "modern": {
            "keywords": ["modern", "contemporary", "minimal", "sleek"],
            "category": "Style",
            "icon": "✨",
            "search_term": "modern"
        },
        "luxury": {
            "keywords": ["luxury", "premium", "high-end", "elegant"],
            "category": "Style",
            "icon": "👑",
            "search_term": "luxury"
        },
        "natural_light": {
            "keywords": ["window", "sunlight", "bright", "light", "window panes"],
            "category": "Features",
            "icon": "☀️",
            "search_term": "natural light"
        },
        "hardwood_flooring": {
            "keywords": ["hardwood", "wooden floor", "flooring", "parquet"],
            "category": "Features",
            "icon": "🪵",
            "search_term": "hardwood floor"
        },
        "marble": {
            "keywords": ["marble", "granite", "stone"],
            "category": "Features",
            "icon": "🪨",
            "search_term": "marble"
        },
        "gym": {
            "keywords": ["gym", "fitness", "exercise", "workout"],
            "category": "Amenities",
            "icon": "💪",
            "search_term": "gym"
        },
        "security": {
            "keywords": ["security", "gate", "fence", "camera"],
            "category": "Security",
            "icon": "🔒",
            "search_term": "security"
        }
    }
    
    labels = []
    confidence = 0
    
    # Try Google Vision API first
    google_key = getattr(settings, "GOOGLE_VISION_API_KEY", "") or ""
    if google_key:
        try:
            from base64 import b64encode
            b64 = b64encode(image_data).decode("ascii")
            
            r = requests.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={google_key}",
                json={
                    "requests": [
                        {
                            "image": {"content": b64},
                            "features": [
                                {"type": "LABEL_DETECTION", "maxResults": 25},
                                {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                                {"type": "SAFE_SEARCH_DETECTION"}
                            ],
                        }
                    ]
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            responses = data.get("responses", [{}])[0]
            
            # Extract labels
            label_annotations = responses.get("labelAnnotations", [])
            labels = [
                {
                    "text": l.get("description", "").lower(),
                    "confidence": l.get("score", 0)
                }
                for l in label_annotations if l.get("description")
            ]
            
            if labels:
                confidence = max(round(l["confidence"] * 100) for l in labels)
        except Exception as e:
            print(f"Google Vision API error: {e}")
    
    # Try OpenAI Vision API for detailed analysis if key available
    try:
        openai_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        if openai_key and labels:
            from base64 import b64encode
            b64 = b64encode(image_data).decode("utf-8")
            
            prompt = """You are a real estate property feature detector. 
            Analyze this property image and identify specific features and amenities visible.
            Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
            {
                "features": ["feature1", "feature2"],
                "style": ["modern", "luxury", etc],
                "quality": "high/medium/low",
                "room_types": ["kitchen", "bedroom", etc],
                "outdoor": ["pool", "garden", etc],
                "materials": ["marble", "hardwood", etc]
            }
            Be specific about what you actually see in the image."""
            
            try:
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                }
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{b64}",
                                            "detail": "high"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 500,
                    },
                    timeout=30,
                )
                
                if response.status_code == 200:
                    ai_response = response.json()
                    try:
                        content = ai_response["choices"][0]["message"]["content"]
                        # Clean up JSON response (remove markdown code blocks if present)
                        content = content.strip()
                        if content.startswith("```"):
                            content = content.split("```")[1]
                            if content.startswith("json"):
                                content = content[4:]
                        if content.endswith("```"):
                            content = content[:-3]
                        # Parse JSON from response
                        import json as json_lib
                        analysis = json_lib.loads(content.strip())
                        if "features" in analysis:
                            # Merge AI-detected features with labels
                            for feature in analysis.get("features", []):
                                if isinstance(feature, str) and feature not in [l["text"] for l in labels]:
                                    labels.append({"text": feature.lower(), "confidence": 0.75})
                    except Exception as parse_error:
                        print(f"Failed to parse AI response: {parse_error}")
            except Exception as ai_error:
                print(f"AI Vision analysis error: {ai_error}")
    except Exception as e:
        print(f"Claude/AI analysis setup error: {e}")
    
    # Match labels to features with confidence scoring
    detected_features = []
    categories_found = {}
    
    for label in labels:
        label_text = label.get("text", "").lower()
        label_confidence = label.get("confidence", 0)
        
        for feature_key, feature_config in FEATURE_MAPPING.items():
            keywords = feature_config["keywords"]
            if any(keyword in label_text for keyword in keywords):
                # Check if this feature is already detected
                existing = next((f for f in detected_features if f["id"] == feature_key), None)
                if existing:
                    existing["confidence"] = max(existing["confidence"], int(label_confidence * 100))
                else:
                    detected_features.append({
                        "id": feature_key,
                        "name": feature_key.replace("_", " ").title(),
                        "icon": feature_config["icon"],
                        "category": feature_config["category"],
                        "search_term": feature_config["search_term"],
                        "confidence": int(label_confidence * 100)
                    })
                
                # Track category
                category = feature_config["category"]
                if category not in categories_found:
                    categories_found[category] = []
                categories_found[category].append(feature_key)
    
    # Sort by confidence
    detected_features.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "success": len(detected_features) > 0,
        "features": detected_features[:15],  # Top 15 features
        "categories": categories_found,
        "confidence": confidence if confidence > 0 else (
            int((sum(f["confidence"] for f in detected_features) / len(detected_features)) / 100 * 100) 
            if detected_features else 0
        ),
        "raw_labels": [l["text"] for l in labels[:10]],
        "feature_count": len(detected_features),
        "message": f"Detected {len(detected_features)} features" if detected_features else "No features detected"
    }


def search_properties_by_features(detected_features: list[dict], limit: int = 24) -> list:
    """
    Search for properties matching the detected image features.
    Uses feature matching and relevance scoring.
    """
    from properties.models import Property
    
    if not detected_features:
        return list(Property.objects.prefetch_related('images').order_by('-is_featured', '-views_count')[:limit])
    
    # Build search queries based on top features
    search_terms = []
    for feature in detected_features[:5]:  # Top 5 features
        search_term = feature.get("search_term", "")
        if search_term:
            search_terms.append(search_term)
    
    # Create complex Q objects for OR search
    from django.db.models import Q, F
    
    query = Q()
    for term in search_terms:
        query |= Q(description__icontains=term)
        query |= Q(title__icontains=term)
        query |= Q(ai_generated_description__icontains=term)
        query |= Q(image_features_json__icontains=term)
    
    if query:
        results = Property.objects.filter(query).distinct().prefetch_related('images').order_by('-is_featured', '-views_count')
    else:
        results = Property.objects.prefetch_related('images').order_by('-is_featured', '-views_count')
    
    return list(results[:limit])


def merge_image_features(property_instance, new_features: list[str]):
    from properties.models import Property

    obj = Property.objects.get(pk=property_instance.pk)
    current = obj.image_features_json or {}
    tags = set(current.get("tags", []))
    tags.update(new_features)
    merged = {**current, "tags": sorted(tags)}
    Property.objects.filter(pk=property_instance.pk).update(image_features_json=merged)


def generate_comprehensive_seo_data(property_obj) -> dict[str, Any]:
    """
    Generate all SEO data for a property in one operation.
    Returns a dictionary with all SEO-related fields ready to save.
    Handles API failures gracefully with sensible fallbacks.
    """
    try:
        from properties.models import Property
        
        # Prepare payload with all available property data
        nearby_locations = [
            nl.name for nl in property_obj.nearby_locations.all()
        ] if hasattr(property_obj, 'nearby_locations') else []
        
        payload = {
            "title": property_obj.title or "",
            "city": property_obj.city or "",
            "property_type": property_obj.get_property_type_display() or "",
            "price": str(property_obj.price) if property_obj.price else "",
            "address": property_obj.address or "",
            "nearby_locations": nearby_locations[:5],
        }
        
        # Generate SEO-optimized description
        description = generate_property_description(payload)
        
        # Generate meta description
        meta_description = seo_snippet(description, max_len=155)
        
        # Extract and structure keywords
        keywords_data = extract_property_keywords(
            title=property_obj.title or "",
            city=property_obj.city or "",
            property_type=property_obj.get_property_type_display() or "",
            description=description,
            address=property_obj.address or "",
            nearby_locations=nearby_locations,
        )
        
        # Calculate SEO score
        seo_score_data = calculate_seo_score(
            title=property_obj.title or "",
            description=description,
            meta_description=meta_description,
            keywords=keywords_data.get('primary', []),
        )
        
        return {
            "ai_generated_description": description,
            "seo_meta_description": meta_description,
            "seo_keywords": keywords_data,
            "seo_score": seo_score_data["score"],
        }
    
    except Exception as e:
        print(f"Error generating comprehensive SEO data: {e}")
        # Return minimal valid data on failure
        return {
            "ai_generated_description": property_obj.description or "",
            "seo_meta_description": (property_obj.title or "")[:155],
            "seo_keywords": {},
            "seo_score": 0,
        }
