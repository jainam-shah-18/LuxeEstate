"""
AI-powered property image search service for LuxeEstate.

Uses OpenAI Vision (GPT-4o) to analyze uploaded query images, extract
detailed property features (pool, kitchen type, amenities, architecture
style, etc.), and rank active listings by visual similarity.
"""

import base64
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature taxonomy – what the AI is asked to detect
# ---------------------------------------------------------------------------

FEATURE_CATEGORIES = {
    "outdoor": [
        "swimming pool", "infinity pool", "rooftop terrace", "balcony",
        "garden", "lawn", "courtyard", "private driveway", "outdoor kitchen",
        "bbq area", "fire pit", "jacuzzi", "hot tub", "solar panels",
    ],
    "kitchen": [
        "modular kitchen", "open kitchen", "island kitchen", "closed kitchen",
        "chef kitchen", "breakfast bar", "pantry", "butler pantry",
    ],
    "living": [
        "double height ceiling", "open plan living", "fireplace",
        "exposed brick wall", "floor to ceiling windows", "skylight",
        "wooden flooring", "marble flooring", "chandeliers",
    ],
    "bedroom": [
        "walk in wardrobe", "en suite bathroom", "master suite",
        "built in storage",
    ],
    "bathroom": [
        "bathtub", "rain shower", "steam room", "sauna",
        "double vanity", "heated floor",
    ],
    "building": [
        "high rise", "low rise", "gated community", "standalone villa",
        "penthouse", "duplex", "sea view", "mountain view", "city skyline view",
        "heritage architecture", "modern architecture", "colonial architecture",
    ],
    "amenities": [
        "gym", "yoga studio", "co working space", "library",
        "home theatre", "game room", "wine cellar", "lift elevator",
        "concierge", "security cabin", "cctv", "parking garage",
        "ev charging", "servant quarters",
    ],
}

ALL_KNOWN_FEATURES: Set[str] = {f for cat in FEATURE_CATEGORIES.values() for f in cat}

# Features grouped for fuzzy matching (alias → canonical)
FEATURE_ALIASES: Dict[str, str] = {
    "pool": "swimming pool",
    "infinity": "infinity pool",
    "terrace": "rooftop terrace",
    "balcony terrace": "balcony",
    "yard": "garden",
    "backyard": "garden",
    "outdoor bbq": "bbq area",
    "jacuzzi": "jacuzzi",
    "hot tub": "hot tub",
    "kitchen island": "island kitchen",
    "open plan kitchen": "open kitchen",
    "walk-in wardrobe": "walk in wardrobe",
    "walk-in closet": "walk in wardrobe",
    "ensuite": "en suite bathroom",
    "bathtub": "bathtub",
    "rain shower": "rain shower",
    "steam shower": "steam room",
    "high ceiling": "double height ceiling",
    "tall ceiling": "double height ceiling",
    "skyline view": "city skyline view",
    "ocean view": "sea view",
    "sea facing": "sea view",
    "parking": "parking garage",
    "gym": "gym",
    "elevator": "lift elevator",
    "lift": "lift elevator",
    "cctv camera": "cctv",
    "water feature": "swimming pool",
    "pool area": "swimming pool",
    "poolside": "swimming pool",
    "outdoor area": "garden",
    "patio": "garden",
    "bright space": "open plan living",
    "indoor space": "open plan living",
    "room interior": "open plan living",
    "interior room": "open plan living",
    "bright interior": "open plan living",
    "open space": "open plan living",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ImageAnalysisResult:
    detected_features: List[str] = field(default_factory=list)
    property_type_hint: str = ""
    style_description: str = ""
    confidence: float = 0.0
    raw_response: str = ""
    error: Optional[str] = None


@dataclass
class PropertyMatch:
    property_id: int
    title: str
    score: float
    matched_features: List[str]
    total_property_features: int


# ---------------------------------------------------------------------------
# Core service
# ---------------------------------------------------------------------------

class AIImageSearchService:
    """
    Analyse a user-uploaded property image with GPT-4o Vision and return
    a ranked list of property IDs that share the most features.
    """

    VISION_MODEL = "gpt-4o"

    _SYSTEM_PROMPT = (
        "You are an expert real estate image analyst. "
        "Your job is to identify EVERY architectural feature, furniture piece, "
        "interior design element, outdoor amenity, and structural characteristic visible in the image. "
        "Be thorough and inclusive - err on the side of detecting MORE features, not fewer. "
        "Even uncertain features should be included (confidence will be lower). "
        "Be specific – distinguish between 'modular kitchen' and 'open kitchen', "
        "'swimming pool' and 'infinity pool', etc. "
        "Respond ONLY with valid JSON – no markdown, no explanation."
    )

    _USER_PROMPT = (
        "Analyze this real-estate image and extract EVERY visible property feature you can identify. "
        "Be inclusive and thorough - include even minor or uncertain features. "
        "Return JSON with exactly these keys:\n"
        "  detected_features: list[str]  – EVERY feature you can identify, including uncertain ones "
        "(use lowercase, from the known taxonomy when possible)\n"
        "  property_type_hint: str       – best guess: apartment|villa|house|penthouse|commercial|plot|unknown\n"
        "  style_description: str        – one-sentence description of the visual style\n"
        "  confidence: float             – your overall confidence 0.0-1.0\n\n"
        f"Known feature taxonomy (use these labels when applicable):\n"
        f"{json.dumps(FEATURE_CATEGORIES, indent=2)}\n\n"
        "Include features from the taxonomy AND any other features you observe. "
        "If unsure, still include the feature but it will have lower confidence. "
        "Return ONLY the JSON object."
    )

    def __init__(self):
        self._client = None
        self._api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        # Log missing API key only once during init
        if not self._api_key:
            logger.warning(
                "OPENAI_API_KEY is not configured. Image search will fail. "
                "Please set OPENAI_API_KEY in your .env file or Django settings."
            )

    # ------------------------------------------------------------------
    # Client initialisation (lazy)
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                error_msg = (
                    "OPENAI_API_KEY is not configured. Please:\n"
                    "1. Sign up at https://platform.openai.com\n"
                    "2. Create an API key\n"
                    "3. Add it to your .env file: OPENAI_API_KEY=sk-...\n"
                    "4. Restart the Django server"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("openai package is not installed. Run: pip install openai")
            except Exception as exc:
                logger.error("Failed to initialize OpenAI client: %s", exc)
                raise
        return self._client

    # ------------------------------------------------------------------
    # Image encoding
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_image(image_path: str) -> Tuple[str, str]:
        """Return (base64_data, mime_type)."""
        ext = os.path.splitext(image_path)[-1].lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/jpeg")
        with open(image_path, "rb") as fh:
            data = base64.b64encode(fh.read()).decode("utf-8")
        return data, mime

    # ------------------------------------------------------------------
    # Feature normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        return text.strip().lower()

    def _resolve_feature(self, raw: str) -> str:
        """Map raw AI output to canonical feature label."""
        norm = self._normalise(raw)
        # Exact match in known set
        if norm in ALL_KNOWN_FEATURES:
            return norm
        # Check aliases
        if norm in FEATURE_ALIASES:
            return FEATURE_ALIASES[norm]
        # Partial match – if one known feature is a substring of the raw value
        for known in ALL_KNOWN_FEATURES:
            if known in norm or norm in known:
                return known
        # Return as-is (novel feature – still useful for display)
        return norm

    def _resolve_features(self, raw_list: List[str]) -> List[str]:
        seen: Set[str] = set()
        out: List[str] = []
        for raw in raw_list:
            resolved = self._resolve_feature(str(raw))
            if resolved and resolved not in seen:
                seen.add(resolved)
                out.append(resolved)
        return out

    def _tokenize_text(self, text: str) -> Set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", text.lower())}

    def _property_text_signature(self, property_obj) -> Set[str]:
        signature = set()
        for feature in self._get_property_features(property_obj):
            signature.update(self._tokenize_text(feature))

        description = getattr(property_obj, 'description', '') or ''
        signature.update(self._tokenize_text(description))

        ai_tags = getattr(property_obj, 'ai_tags', []) or []
        if isinstance(ai_tags, str):
            try:
                ai_tags = json.loads(ai_tags)
            except (json.JSONDecodeError, ValueError):
                ai_tags = [tag.strip() for tag in ai_tags.split(',') if tag.strip()]

        for tag in ai_tags:
            signature.update(self._tokenize_text(str(tag)))

        return signature

    def _partial_match_score(self, query_features: Set[str], prop_obj) -> float:
        query_tokens = set()
        for feature in query_features:
            query_tokens.update(self._tokenize_text(feature))
        if not query_tokens:
            return 0.0

        prop_tokens = self._property_text_signature(prop_obj)
        overlap = query_tokens & prop_tokens
        if not overlap:
            return 0.0

        union = query_tokens | prop_tokens
        return round(len(overlap) / len(union), 4)

    # ------------------------------------------------------------------
    # Fallback feature detection (when AI fails or returns nothing)
    # ------------------------------------------------------------------

    def _detect_fallback_features(self, image_path: str) -> List[str]:
        """
        Fallback feature detection using basic image analysis.
        Uses PIL/Pillow to detect basic visual characteristics.
        Returns list of generic property features detected.
        """
        fallback_features = []
        try:
            from PIL import Image, ImageOps, ImageStat
            
            img = Image.open(image_path)
            img = img.convert('RGB')
            width, height = img.size
            
            # Basic size checks
            if width < 100 or height < 100:
                logger.warning("Image too small for meaningful analysis")
                fallback_features.append("property image")
                return fallback_features
            
            # Detect color distribution using simple sampling
            # Sample pixels from different regions
            pixels = []
            try:
                # Get pixels from center and corners
                for x in [width // 4, width // 2, 3 * width // 4]:
                    for y in [height // 4, height // 2, 3 * height // 4]:
                        pixel = img.getpixel((x, y))
                        if isinstance(pixel, tuple) and len(pixel) >= 3:
                            pixels.append(pixel[:3])
            except:
                pass
            
            if not pixels:
                fallback_features.append("property image")
                return fallback_features
            
            # Analyze color characteristics
            r_avg = sum(p[0] for p in pixels) / len(pixels)
            g_avg = sum(p[1] for p in pixels) / len(pixels)
            b_avg = sum(p[2] for p in pixels) / len(pixels)
            brightness = (r_avg + g_avg + b_avg) / 3
            
            # Green channel > red and blue = likely outdoor/garden
            green_dominant = g_avg > r_avg and g_avg > b_avg and g_avg > 100
            # Blue channel > others = likely water/pool
            blue_dominant = b_avg > r_avg and b_avg > g_avg and b_avg > 100
            # High brightness = outdoor/well-lit
            bright = brightness > 180
            # Low brightness = indoor
            dark = brightness < 100
            
            # Aspect ratio heuristics
            aspect_ratio = width / height if height > 0 else 1
            wide_format = aspect_ratio > 1.4  # Landscape
            tall_format = aspect_ratio < 0.7  # Portrait
            
            # Feature inference
            if green_dominant:
                fallback_features.extend(["garden"])

            if blue_dominant:
                fallback_features.extend(["swimming pool"])

            if bright and not green_dominant and not blue_dominant:
                fallback_features.append("open plan living")

            if dark:
                fallback_features.append("open plan living")
                if tall_format:
                    fallback_features.append("open plan living")

            if wide_format and bright and not blue_dominant and not green_dominant:
                fallback_features.append("open plan living")

            if tall_format and dark:
                fallback_features.append("open plan living")
                fallback_features.append("open plan living")
            
            # Always add baseline features
            if not fallback_features:
                fallback_features.append("property")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_fallback = []
            for f in fallback_features:
                if f not in seen:
                    seen.add(f)
                    unique_fallback.append(f)
            
            logger.info(
                f"Fallback detection: RGB=({r_avg:.0f},{g_avg:.0f},{b_avg:.0f}), "
                f"brightness={brightness:.0f}, aspect={aspect_ratio:.2f}, "
                f"green_dominant={green_dominant}, blue_dominant={blue_dominant}, "
                f"features={unique_fallback}"
            )
            
            return unique_fallback
            
        except ImportError:
            logger.warning("PIL/Pillow not available for fallback detection - installing may help")
            # If PIL is not available, return a minimal set
            return ["property image"]
        except Exception as exc:
            logger.warning(f"Fallback feature detection failed: {exc}")
            return ["property image"]

    # ------------------------------------------------------------------
    # Vision call
    # ------------------------------------------------------------------

    def analyse_image(self, image_path: str) -> ImageAnalysisResult:
        """
        Send image to GPT-4o Vision and parse the structured response.
        Falls back to basic image analysis if AI returns no features.
        Always returns an ImageAnalysisResult (uses fallback on error).
        """
        try:
            b64, mime = self._encode_image(image_path)
            client = self._get_client()

            response = client.chat.completions.create(
                model=self.VISION_MODEL,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": self._SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{b64}",
                                    "detail": "high",
                                },
                            },
                            {"type": "text", "text": self._USER_PROMPT},
                        ],
                    },
                ],
            )

            raw_text = response.choices[0].message.content or ""
            result = self._parse_vision_response(raw_text)
            
            # If AI returned no features, try fallback detection
            if not result.detected_features and not result.error:
                logger.info("AI returned no features; attempting fallback detection")
                fallback_features = self._detect_fallback_features(image_path)
                if fallback_features:
                    result.detected_features = self._resolve_features(fallback_features)
                    result.confidence = 0.3  # Mark as low confidence
            
            return result

        except Exception as exc:
            logger.error("GPT-4o vision analysis failed: %s", exc)
            # Try fallback detection even on API errors
            logger.info("Vision API failed; attempting fallback image analysis")
            fallback_features = self._detect_fallback_features(image_path)
            if fallback_features:
                return ImageAnalysisResult(
                    detected_features=self._resolve_features(fallback_features),
                    confidence=0.2,
                    raw_response=str(exc),
                )
            return ImageAnalysisResult(error=str(exc))

    def _parse_vision_response(self, raw_text: str) -> ImageAnalysisResult:
        """Parse the JSON from GPT-4o; tolerant of markdown fences."""
        text = raw_text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            ).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Last resort – try to extract JSON object
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.warning("Could not parse vision JSON: %s", text[:200])
                    return ImageAnalysisResult(raw_response=raw_text, error="JSON parse failed")
            else:
                return ImageAnalysisResult(raw_response=raw_text, error="No JSON found in response")

        raw_features = data.get("detected_features", [])
        if not isinstance(raw_features, list):
            raw_features = []

        return ImageAnalysisResult(
            detected_features=self._resolve_features(raw_features),
            property_type_hint=str(data.get("property_type_hint", "unknown")).lower(),
            style_description=str(data.get("style_description", "")),
            confidence=float(data.get("confidence", 0.5)),
            raw_response=raw_text,
        )

    # ------------------------------------------------------------------
    # Property feature extraction
    # ------------------------------------------------------------------

    def _get_property_features(self, property_obj) -> Set[str]:
        """
        Collect all text-based features from a property model instance.
        Checks: amenities JSON, ai_tags, description keywords, furnishing.
        """
        features: Set[str] = set()

        def add_feature(raw_feature: str):
            if not raw_feature:
                return
            resolved = self._resolve_feature(str(raw_feature))
            if resolved:
                features.add(resolved)

        # amenities field (stored as JSON list or comma string)
        amenities = getattr(property_obj, "amenities", None)
        if amenities:
            if isinstance(amenities, list):
                for a in amenities:
                    add_feature(a)
            elif isinstance(amenities, str):
                try:
                    parsed = json.loads(amenities)
                    if isinstance(parsed, list):
                        for a in parsed:
                            add_feature(a)
                except (json.JSONDecodeError, ValueError):
                    for a in amenities.split(","):
                        add_feature(a)

        # ai_tags
        ai_tags = getattr(property_obj, "ai_tags", None)
        if ai_tags:
            if isinstance(ai_tags, list):
                for t in ai_tags:
                    add_feature(t)
            elif isinstance(ai_tags, str):
                try:
                    tags = json.loads(ai_tags)
                    if isinstance(tags, list):
                        for t in tags:
                            add_feature(t)
                except (json.JSONDecodeError, ValueError):
                    for t in ai_tags.split(","):
                        add_feature(t)

        # description keyword matching
        description = getattr(property_obj, "description", "") or ""
        desc_lower = description.lower()
        for feature in ALL_KNOWN_FEATURES:
            if feature in desc_lower:
                add_feature(feature)

        # furnishing as a rough feature
        furnishing = getattr(property_obj, "furnishing", "") or ""
        if furnishing:
            add_feature(furnishing.strip().lower())

        # property type
        ptype = getattr(property_obj, "property_type", "") or ""
        if ptype:
            add_feature(ptype.strip().lower())

        # image-level ai analysis if stored on PropertyImage
        try:
            for img in property_obj.images.all():
                image_features = getattr(img, "ai_detected_features", None)
                if image_features:
                    if isinstance(image_features, list):
                        for feat in image_features:
                            add_feature(feat)
                    elif isinstance(image_features, str):
                        try:
                            parsed = json.loads(image_features)
                            if isinstance(parsed, list):
                                for feat in parsed:
                                    add_feature(feat)
                        except (json.JSONDecodeError, ValueError):
                            for feat in image_features.split(","):
                                add_feature(feat)

                sig = getattr(img, "ai_visual_signature", None)
                if sig:
                    if isinstance(sig, str):
                        try:
                            sig = json.loads(sig)
                        except (json.JSONDecodeError, ValueError):
                            sig = {}
                    if isinstance(sig, dict):
                        for feat in sig.get("detected_features", []):
                            add_feature(feat)
        except Exception:
            pass

        return features

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def rank_properties(
        self,
        query_features: List[str],
        properties,
        min_score: float = 0.01,
    ) -> List[PropertyMatch]:
        """
        Score each property by Jaccard-style feature overlap with query.
        Returns list sorted by score descending; only above min_score.
        
        Scoring formula: (Jaccard + Recall) / 2
        - Jaccard: intersection / union (0-1)
        - Recall: matched / query_features (0-1)
        - min_score of 0.01 means at least very minimal overlap
        """
        query_set = set(self._resolve_features(query_features))
        if not query_set:
            return []

        results: List[PropertyMatch] = []
        for prop in properties:
            prop_features = self._get_property_features(prop)
            if not prop_features:
                continue

            matched = query_set & prop_features
            if matched:
                union = query_set | prop_features
                jaccard = len(matched) / len(union)
                recall = len(matched) / len(query_set)
                score = round((jaccard + recall) / 2, 4)

                if score >= min_score:
                    results.append(
                        PropertyMatch(
                            property_id=prop.id,
                            title=prop.title or f"Property #{prop.id}",
                            score=score,
                            matched_features=sorted(matched),
                            total_property_features=len(prop_features),
                        )
                    )
                continue

            # No exact feature overlap: attempt a lightweight partial text-based match.
            fallback_score = self._partial_match_score(query_set, prop)
            if fallback_score >= min_score:
                results.append(
                    PropertyMatch(
                        property_id=prop.id,
                        title=prop.title or f"Property #{prop.id}",
                        score=round(fallback_score * 0.5, 4),
                        matched_features=[],
                        total_property_features=len(prop_features),
                    )
                )

        results.sort(key=lambda m: m.score, reverse=True)
        return results

    # ------------------------------------------------------------------
    # High-level entry point
    # ------------------------------------------------------------------

    def search(
        self,
        image_path: str,
        properties,
    ) -> Dict:
        """
        Full pipeline: analyse image → extract features → rank properties.

        Returns a dict with:
          success: bool
          detected_features: list[str]
          property_type_hint: str
          style_description: str
          matches: list[dict]  – [{property_id, title, score, matched_features}]
          error: str | None
        """
        analysis = self.analyse_image(image_path)

        if analysis.error and not analysis.detected_features:
            return {
                "success": False,
                "detected_features": [],
                "property_type_hint": "",
                "style_description": "",
                "matches": [],
                "error": analysis.error,
            }

        # Use adaptive min_score based on confidence
        # Lower threshold when using fallback detection (confidence < 0.5)
        min_score = 0.001 if analysis.confidence < 0.5 else 0.01
        matches = self.rank_properties(analysis.detected_features, properties, min_score=min_score)

        return {
            "success": True,
            "detected_features": analysis.detected_features,
            "property_type_hint": analysis.property_type_hint,
            "style_description": analysis.style_description,
            "confidence": analysis.confidence,
            "matches": [
                {
                    "property_id": m.property_id,
                    "title": m.title,
                    "score": m.score,
                    "matched_features": m.matched_features,
                }
                for m in matches
            ],
            "error": None,
        }


# Module-level singleton
image_search_service = AIImageSearchService()
