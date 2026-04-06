"""
Advanced SEO service for property listings.
Handles keyword extraction, SEO-optimized descriptions, and metadata generation.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import requests
from django.conf import settings


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract SEO-relevant keywords from text.
    Filters for real estate and property-specific terms.
    """
    if not text:
        return []
    
    # Real estate keyword patterns
    patterns = {
        'property_type': r'\b(apartment|villa|house|bungalow|cottage|flat|studio|penthouse|plot|land|commercial|office|retail|warehouse)\b',
        'amenities': r'\b(swimming\s+pool|gym|garden|balcony|parking|elevator|lift|security|ac|furnished|semi-furnished|unfurnished|maid\s+room|shared\s+pool|community\s+center|open\s+parking|covered\s+parking)\b',
        'features': r'\b(bhk|bedroom|living\s+room|kitchen|dining|study|terrace|patio|courtyard|lawn|modular\s+kitchen|attached\s+bathroom|common\s+area)\b',
        'location': r'\b(near|close\s+to|adjacent\s+to|opposite|facing|overlooking|neighborhood|locality|area|zone|district|residential|commercial|gated|community)\b',
        'quality': r'\b(luxury|premium|modern|spacious|bright|well-maintained|newly\s+constructed|under\s+construction|resale|ready\s+to\s+move|freehold|leasehold)\b',
    }
    
    text_lower = text.lower()
    found_keywords = set()
    
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Normalize whitespace
            keyword = re.sub(r'\s+', ' ', match.lower().strip())
            if keyword and len(keyword) > 2:
                found_keywords.add(keyword)
    
    return sorted(list(found_keywords))[:max_keywords]


def extract_property_keywords(
    title: str,
    city: str,
    property_type: str,
    description: str,
    address: str = "",
    nearby_locations: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Extract all relevant keywords for a property from various fields.
    Returns structured keyword data for SEO.
    """
    nearby_locations = nearby_locations or []
    
    # Combine all text for keyword extraction
    combined_text = f"{title} {city} {property_type} {description} {address} {' '.join(nearby_locations)}"
    
    # Extract keywords by category
    all_keywords = extract_keywords(combined_text)
    
    # Always include location and property type as primary keywords
    primary_keywords = {city.lower(), property_type.lower()}
    primary_keywords.update(all_keywords[:5])
    
    return {
        'all': all_keywords,
        'primary': sorted(list(primary_keywords)),
        'location_keywords': [city.lower()],
        'property_keywords': [property_type.lower()],
        'amenity_keywords': [kw for kw in all_keywords if any(x in kw for x in ['pool', 'gym', 'parking', 'security'])],
    }


def generate_seo_optimized_description(payload: Dict[str, Any]) -> str:
    """
    Generate SEO-optimized property description using AI.
    Incorporates keywords naturally and follows best practices.
    """
    title = payload.get("title", "Property")
    city = payload.get("city", "")
    ptype = payload.get("property_type", "")
    price = payload.get("price", "")
    addr = payload.get("address", "")
    size = payload.get("size", "")
    bedrooms = payload.get("bedrooms", "")
    amenities = payload.get("amenities", [])
    nearby = payload.get("nearby_locations", [])
    
    # Build comprehensive context for AI
    amenities_text = ", ".join(amenities) if amenities else "premium amenities"
    nearby_text = ", ".join(nearby[:3]) if nearby else ""
    
    # Fallback description with natural keyword integration
    base_description = (
        f"{title} is a premium {ptype} located in {city}. "
        f"Situated at {addr[:100]}, this {ptype} offers exceptional value at {price}. "
    )
    
    if size:
        base_description += f"The property features {size} of prime living space. "
    if bedrooms:
        base_description += f"With {bedrooms} spacious bedrooms, this {ptype} is ideal for families. "
    
    base_description += (
        f"Key amenities include {amenities_text}. "
        f"Located conveniently near {nearby_text if nearby_text else 'major city amenities'}, "
        f"this {ptype} in {city} ensures excellent connectivity and lifestyle conveniences. "
        f"Perfect for discerning buyers seeking premium living in {city}."
    )
    
    key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if key:
        try:
            system_prompt = (
                "You are an expert real estate copywriter. Write a compelling, "
                "SEO-optimized property description (120-180 words). "
                "Include the location, property type, and key features naturally. "
                "Use keywords that buyers search for. Be persuasive but accurate. No markdown."
            )
            
            user_message = (
                f"Create an SEO description for: {json.dumps({k: v for k, v in payload.items() if k not in ['lat', 'lng']}, default=str)[:2000]}"
            )
            
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 400,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            ai_description = data["choices"][0]["message"]["content"].strip()
            if ai_description:
                return ai_description
        except Exception as e:
            print(f"SEO description generation error: {e}")
    
    return base_description


def generate_seo_meta_description(
    description: str,
    city: str,
    property_type: str,
    price: str = "",
    max_length: int = 155,
) -> str:
    """
    Generate an optimized meta description for search engines.
    Includes key information and primary keywords.
    """
    # Clean up the description
    plain_text = re.sub(r'\s+', ' ', (description or "").strip())
    
    # Create keyword-rich meta description
    if price:
        meta = f"{property_type} in {city} {price}. {plain_text[:100]}"
    else:
        meta = f"{property_type} in {city}. {plain_text[:100]}"
    
    # Trim to max length while preserving word boundaries
    if len(meta) <= max_length:
        return meta
    
    # Find the last space before max_length
    trimmed = meta[:max_length - 1]
    last_space = trimmed.rfind(" ")
    if last_space > 50:  # Ensure minimum content
        return trimmed[:last_space] + "…"
    
    return meta[:max_length - 1] + "…"


def generate_seo_optimized_title(
    original_title: str,
    city: str,
    property_type: str,
    bedrooms: str = "",
) -> str:
    """
    Generate an SEO-optimized title that includes target keywords.
    Format: [PropertyType] [Bedrooms] in [City] - [Original]
    """
    # Limit title to ~60 characters for ideal SERP display
    parts = []
    
    if bedrooms:
        parts.append(bedrooms)
    parts.append(property_type)
    parts.append("in")
    parts.append(city)
    
    seo_title = " ".join(parts)
    
    # If original title has unique value, append it
    if original_title and original_title.lower() not in seo_title.lower():
        remaining = 60 - len(seo_title) - 5  # 5 for " - " and buffer
        if remaining > 10:
            truncated = original_title[:remaining].rsplit(' ', 1)[0]
            seo_title = f"{seo_title} - {truncated}"
    
    return seo_title[:60]


def generate_schema_markup(
    property_obj: Dict[str, Any],
    base_url: str = "https://luxeestate.com",
) -> str:
    """
    Generate JSON-LD schema markup for property listings.
    Helps search engines understand property details.
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "name": "LuxeEstate",
        "url": base_url,
    }
    
    # Property-specific schema
    property_schema = {
        "@context": "https://schema.org",
        "@type": "Residence",
        "name": property_obj.get("title", "Property"),
        "description": property_obj.get("description", ""),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": property_obj.get("address", ""),
            "addressLocality": property_obj.get("city", ""),
            "addressCountry": "IN",
        },
        "priceCurrency": "INR",
        "price": str(property_obj.get("price", "")),
    }
    
    # Add optional fields
    if property_obj.get("latitude") and property_obj.get("longitude"):
        property_schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(property_obj.get("latitude")),
            "longitude": float(property_obj.get("longitude")),
        }
    
    return json.dumps(property_schema, indent=2)


def calculate_seo_score(
    title: str,
    description: str,
    meta_description: str,
    keywords: List[str],
) -> Dict[str, Any]:
    """
    Calculate an SEO score for a property listing (0-100).
    Provides feedback on what needs improvement.
    """
    score = 50  # Base score
    feedback = []
    
    # Title evaluation
    if title and len(title) >= 30 and len(title) <= 60:
        score += 10
    else:
        feedback.append(f"Title length: {len(title) if title else 0}. Ideal: 30-60 characters.")
    
    # Description evaluation
    if description and len(description) >= 120:
        score += 15
        if len(description) <= 500:
            score += 5
    else:
        feedback.append(f"Description length: {len(description) if description else 0}. Ideal: 120-500 words.")
    
    # Meta description evaluation
    if meta_description and len(meta_description) >= 120 and len(meta_description) <= 160:
        score += 10
    else:
        feedback.append(f"Meta description length: {len(meta_description) if meta_description else 0}. Ideal: 120-160 characters.")
    
    # Keyword evaluation
    if keywords and len(keywords) >= 3:
        score += 10
    else:
        feedback.append(f"Keywords: {len(keywords) if keywords else 0}. Need at least 3 primary keywords.")
    
    # Keyword presence in content
    keywords_in_desc = sum(1 for kw in keywords if kw.lower() in description.lower())
    if keywords_in_desc >= len(keywords) * 0.5:
        score += 10
    else:
        feedback.append(f"Keywords in description: {keywords_in_desc}/{len(keywords)}. Improve keyword integration.")
    
    return {
        "score": min(score, 100),
        "feedback": feedback,
        "level": "Good" if score >= 70 else "Fair" if score >= 50 else "Needs Work",
    }
