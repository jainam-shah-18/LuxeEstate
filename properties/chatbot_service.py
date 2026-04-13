"""Fresh intelligent chatbot backend for LuxeEstate."""

import json
import logging
import os
import re
from statistics import mean
from typing import Any, Dict, List

from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_LEAD = {
    "name": "",
    "contact": "",
    "budget": "",
    "city": "",
    "property_type": "",
    "bhk": "",
}

DEFAULT_APPOINTMENT = {
    "requested": False,
    "property_hint": "",
    "preferred_datetime": "",
}

HUMAN_HANDOFF_TRIGGERS = {
    "speak to agent": "User requested a human agent.",
    "talk to agent": "User requested a human agent.",
    "human": "User requested human support.",
    "real person": "User requested a real person.",
    "urgent": "Urgent support needed.",
    "complaint": "Complaint requires agent follow-up.",
    "legal": "Legal query requires human support.",
}

APPOINTMENT_PATTERNS = [
    r"\bschedule\b",
    r"\bappointment\b",
    r"\bvisit\b",
    r"\bsite visit\b",
    r"\bbook\b",
    r"\bcall back\b",
    r"\bcallback\b",
]

MARKET_PRICE_PATTERNS = [
    r"\bprice\b",
    r"\bcost\b",
    r"\brate\b",
    r"\bmarket\b",
    r"\bas of now\b",
    r"\bcurrent(?:ly)?\b",
]

WEBSITE_REALTIME_PATTERNS = [
    r"\bhow many\b",
    r"\bcount\b",
    r"\bavailable\b",
    r"\blistings?\b",
    r"\bshow\b",
    r"\blatest\b",
    r"\bnew\b",
    r"\brecent(?:ly)?\b",
    r"\bposted\b",
    r"\btop\s*\d+\b",
    r"\bunder\b",
    r"\bwithin\b",
    r"\bnearby\b",
    r"\bnear\b",
    r"\bcities?\b",
    r"\blocations?\b",
    r"\bright now\b",
    r"\bmost recent(?:ly)?\b",
]

LOCALITY_NOISE_TERMS = {
    "india",
    "address",
    "road",
    "rd",
    "street",
    "st",
    "lane",
    "ln",
    "main road",
    "cross road",
    "apartment",
    "apartments",
    "apt",
    "building",
    "tower",
    "floor",
    "flat",
    "house",
    "plot",
    "block",
    "phase",
}

SYSTEM_PROMPT = """You are Luxe, the 24/7 intelligent assistant for LuxeEstate.
You must handle property inquiries, qualify leads, and schedule appointments.
Answer user questions directly first. Then ask at most one concise follow-up question only when needed.
Never repeat the same question/response in back-to-back turns.
Do not ask for details already captured in current lead state.
Ask concise follow-up questions to collect missing details from: name, contact, budget, city, property_type, bhk.
Escalate to human only for explicit requests, legal matters, or unresolved complaints.
Return JSON only with this exact shape:
{{
  "message": "string",
  "intent": "greeting|inquiry|buy|rent|invest|appointment|support|qualification|handoff|unknown",
  "lead": {{"name":"","contact":"","budget":"","city":"","property_type":"","bhk":""}},
  "appointment": {{"requested": false, "property_hint": "", "preferred_datetime": ""}},
  "requires_human": false,
  "handoff_reason": ""
}}
Property inventory snapshot: {property_context}
Conversation history: {history_context}
Current lead state: {lead_context}
"""


class LuxeChatbot:
    DEFAULT_MODEL = "gpt-4o-mini"
    TEMPERATURE = 0.2
    MAX_HISTORY = 20

    def __init__(self):
        self.model = getattr(settings, "OPENAI_MODEL", self.DEFAULT_MODEL)
        self._api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        self._client = None

    @staticmethod
    def _is_plain_greeting(message: str) -> bool:
        lowered = (message or "").strip().lower()
        if not lowered:
            return False
        return bool(re.fullmatch(r"(hi|hello|hey|hii|hola|good morning|good evening|good afternoon)[!. ]*", lowered))

    @staticmethod
    def _normalize(value: Any) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _base_result() -> Dict[str, Any]:
        return {
            "message": "",
            "intent": "unknown",
            "lead": {**DEFAULT_LEAD},
            "qualification_stage": "cold",
            "appointment": {**DEFAULT_APPOINTMENT},
            "requires_human": False,
            "handoff_reason": "",
        }

    @staticmethod
    def _safe_json_parse(raw_text: str) -> Dict[str, Any]:
        if not raw_text:
            return {}
        text = raw_text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {}
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}

    @staticmethod
    def _merge_lead(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, str]:
        merged = {**DEFAULT_LEAD, **(base or {})}
        for key in DEFAULT_LEAD:
            value = (incoming or {}).get(key)
            if value:
                merged[key] = str(value).strip()
        return merged

    @staticmethod
    def _merge_appointment(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        merged = {**DEFAULT_APPOINTMENT, **(base or {})}
        if (incoming or {}).get("requested"):
            merged["requested"] = True
        for field in ("property_hint", "preferred_datetime"):
            value = (incoming or {}).get(field)
            if value:
                merged[field] = str(value).strip()
        return merged

    @staticmethod
    def _qualification_stage(lead: Dict[str, Any]) -> str:
        score = sum(bool(lead.get(k)) for k in DEFAULT_LEAD)
        if score >= 4:
            return "hot"
        if score >= 2:
            return "warm"
        return "cold"

    @staticmethod
    def _extract_message_fields(message: str) -> Dict[str, str]:
        text = message.lower()
        out: Dict[str, str] = {}

        email = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", message)
        if email:
            out["contact"] = email.group(0)

        phone = re.search(r"(?:\+91|0)?\s*([6-9]\d{9})", re.sub(r"[^\d+]", "", message))
        if phone and not out.get("contact"):
            out["contact"] = phone.group(1)

        name = re.search(r"\b(my name is|i am|i'm)\s+([A-Za-z ]{2,40})", message, re.IGNORECASE)
        if name:
            out["name"] = name.group(2).strip().title()

        budget = re.search(
            r"((?:rs\.?|inr|₹)?\s*\d+(?:[\.,]\d+)?\s*(?:lakh|lac|crore|cr|k|million|m)?)",
            text,
        )
        if budget:
            out["budget"] = budget.group(1).strip()

        city = re.search(
            r"\b(?:in|at|near)\s+([A-Za-z ]{2,30}?)(?:\s+(?:with|for|under|budget|price)\b|[.,]|$)",
            message,
            re.IGNORECASE,
        )
        if city:
            out["city"] = city.group(1).strip().title()

        bhk = re.search(r"(\d+)\s*(?:bhk|bedroom|bedrooms|beds?)\b", text)
        if bhk:
            out["bhk"] = f"{bhk.group(1)} BHK"

        ptype = re.search(r"\b(apartment|villa|plot|flat|house|studio|penthouse)\b", text)
        if ptype:
            out["property_type"] = ptype.group(1)

        return out

    @staticmethod
    def _detect_appointment(message: str) -> bool:
        normalized = message.lower()
        return any(re.search(pattern, normalized) for pattern in APPOINTMENT_PATTERNS)

    @staticmethod
    def _extract_datetime_hint(message: str) -> str:
        explicit = re.search(
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*(?:at)?\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            message,
            re.IGNORECASE,
        )
        if explicit:
            return explicit.group(1).strip()
        match = re.search(
            r"(\b(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+)(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?)",
            message,
            re.IGNORECASE,
        )
        return match.group(1) if match else ""

    @staticmethod
    def _is_property_query(message: str) -> bool:
        lowered = message.lower()
        property_terms = (
            "property",
            "apartment",
            "flat",
            "villa",
            "plot",
            "house",
            "home",
            "bhk",
            "buy",
            "rent",
            "lease",
            "invest",
            "price",
            "locality",
            "location",
        )
        return any(term in lowered for term in property_terms)

    @staticmethod
    def _is_information_question(message: str) -> bool:
        lowered = message.strip().lower()
        if "?" in lowered:
            return True
        return bool(
            re.search(
                r"^(what|which|where|when|why|how|can|could|is|are|do|does|should)\b",
                lowered,
            )
        )

    @staticmethod
    def _is_market_price_query(message: str) -> bool:
        lowered = message.lower()
        has_price_keyword = any(re.search(pattern, lowered) for pattern in MARKET_PRICE_PATTERNS)
        has_property_reference = bool(
            re.search(r"\b(apartment|flat|villa|plot|house|property|bhk|home)\b", lowered)
        )
        return has_price_keyword and has_property_reference

    @staticmethod
    def _is_website_realtime_query(message: str) -> bool:
        lowered = message.lower()
        return any(re.search(pattern, lowered) for pattern in WEBSITE_REALTIME_PATTERNS)

    @staticmethod
    def _next_missing_field(lead: Dict[str, str]) -> str:
        priority = ["city", "bhk", "budget", "property_type", "name", "contact"]
        for field in priority:
            if not lead.get(field):
                return field
        return ""

    @staticmethod
    def _label_for_field(field: str) -> str:
        labels = {
            "city": "preferred city",
            "bhk": "required BHK",
            "budget": "budget range",
            "property_type": "property type",
            "name": "name",
            "contact": "contact number or email",
        }
        return labels.get(field, field.replace("_", " "))

    @staticmethod
    def _detect_handoff(message: str) -> str:
        lowered = message.lower()
        for trigger, reason in HUMAN_HANDOFF_TRIGGERS.items():
            if trigger in lowered:
                return reason
        return ""

    @staticmethod
    def _history_text(history: List[Dict[str, str]]) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for item in history[-LuxeChatbot.MAX_HISTORY:]:
            role = item.get("role", "user")
            content = item.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _lead_text(lead: Dict[str, str]) -> str:
        parts = [f"{k}={v}" for k, v in (lead or {}).items() if v]
        return ", ".join(parts) if parts else "No lead details yet."

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            return None
        try:
            import openai
        except ImportError:
            return None
        if hasattr(openai, "OpenAI"):
            self._client = openai.OpenAI(api_key=self._api_key)
        else:
            openai.api_key = self._api_key
            self._client = openai
        return self._client

    def _extract_llm_text(self, response: Any) -> str:
        if not response:
            return ""
        if hasattr(response, "output_text") and response.output_text:
            return self._normalize(response.output_text)
        if hasattr(response, "choices") and response.choices:
            msg = getattr(response.choices[0], "message", None)
            if isinstance(msg, dict):
                return self._normalize(msg.get("content", ""))
            return self._normalize(getattr(msg, "content", ""))
        return ""

    def _build_property_context(self, search_criteria: Dict[str, Any]) -> str:
        try:
            from properties.models import Property

            query = Property.objects.filter(is_active=True)
            if search_criteria.get("city"):
                query = query.filter(city__icontains=search_criteria["city"])
            if search_criteria.get("property_type"):
                query = query.filter(property_type__icontains=search_criteria["property_type"])

            records = []
            for prop in query.order_by("-created_at")[:8]:
                records.append(
                    {
                        "id": prop.id,
                        "title": getattr(prop, "title", ""),
                        "city": getattr(prop, "city", ""),
                        "price": str(getattr(prop, "price", "")),
                        "listing_type": getattr(prop, "listing_type", ""),
                        "property_type": getattr(prop, "property_type", ""),
                        "bedrooms": str(getattr(prop, "bedrooms", "")),
                    }
                )
            return json.dumps(records)
        except Exception as exc:
            logger.warning("Property context unavailable: %s", exc)
            return "[]"

    def _call_llm(self, user_message: str, history: List[Dict[str, str]], lead: Dict[str, str], search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        client = self._get_client()
        if client is None:
            return {}

        system = SYSTEM_PROMPT.format(
            property_context=self._build_property_context(search_criteria),
            history_context=self._history_text(history),
            lead_context=self._lead_text(lead),
        )

        try:
            if hasattr(client, "responses"):
                response = client.responses.create(
                    model=self.model,
                    temperature=self.TEMPERATURE,
                    input=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                )
            elif hasattr(client, "chat") and hasattr(client.chat, "completions"):
                response = client.chat.completions.create(
                    model=self.model,
                    temperature=self.TEMPERATURE,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                )
            else:
                response = client.ChatCompletion.create(
                    model=self.model,
                    temperature=self.TEMPERATURE,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                )
        except Exception as exc:
            logger.warning("LLM request failed, using fallback: %s", exc)
            return {}

        return self._safe_json_parse(self._extract_llm_text(response))

    @staticmethod
    def _format_price(value: float) -> str:
        if value >= 1e7:
            return f"Rs {value / 1e7:.2f} Cr"
        if value >= 1e5:
            return f"Rs {value / 1e5:.1f} Lakh"
        return f"Rs {value:,.0f}"

    @staticmethod
    def _parse_budget_to_value(raw_budget: str) -> float:
        if not raw_budget:
            return 0.0
        text = str(raw_budget).strip().lower().replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|k|thousand|million|m)?", text)
        if not match:
            return 0.0
        value = float(match.group(1))
        unit = (match.group(2) or "").strip()
        multipliers = {
            "crore": 1e7,
            "cr": 1e7,
            "lakh": 1e5,
            "lac": 1e5,
            "k": 1e3,
            "thousand": 1e3,
            "million": 1e6,
            "m": 1e6,
        }
        return value * multipliers.get(unit, 1.0)

    @staticmethod
    def _extract_locality_names(addresses: List[str], limit: int = 8) -> List[str]:
        def _clean_part(part: str) -> str:
            token = re.sub(r"\(.*?\)", "", part or "").strip(" -:.")
            token = re.sub(r"\s+", " ", token).strip()
            token = re.sub(
                r"^(near|opp|opp\.|opposite|behind|beside|adjacent to)\s+",
                "",
                token,
                flags=re.IGNORECASE,
            ).strip()
            return token

        scored: Dict[str, int] = {}
        for address in addresses:
            for part in str(address).split(","):
                token = _clean_part(part)
                if not token or len(token) < 3:
                    continue

                lowered = token.lower()
                if lowered in LOCALITY_NOISE_TERMS:
                    continue
                if re.fullmatch(r"\d{4,}", lowered):
                    continue
                if re.search(r"\b(?:pin|pincode|zip)\b", lowered):
                    continue

                score = 1
                if not any(ch.isdigit() for ch in token):
                    score += 2
                if " " in token:
                    score += 1
                if len(token) > 4:
                    score += 1

                current = scored.get(token, -1)
                if score > current:
                    scored[token] = score

        ranked = sorted(scored.items(), key=lambda item: (-item[1], item[0].lower()))
        return [name for name, _ in ranked[:limit]]

    def _market_price_message(self, lead: Dict[str, str], search_criteria: Dict[str, Any]) -> str:
        try:
            from properties.models import Property

            query = Property.objects.filter(is_active=True)
            city = (lead.get("city") or search_criteria.get("city") or "").strip()
            if city:
                query = query.filter(city__icontains=city)

            property_type = (lead.get("property_type") or search_criteria.get("property_type") or "").strip()
            if property_type:
                query = query.filter(property_type__icontains=property_type)

            bhk_val = (lead.get("bhk") or "").strip().lower()
            bhk_match = re.search(r"(\d+)", bhk_val)
            if bhk_match:
                query = query.filter(bedrooms=int(bhk_match.group(1)))

            count = query.count()
            if not count:
                if city:
                    return (
                        f"I do not see active listings for {city} right now. "
                        "Share your budget and BHK preference, and I will suggest nearby options."
                    )
                return "I need your preferred city to share current apartment prices."

            prices = [float(p.price) for p in query.exclude(price__isnull=True).exclude(price=0).only("price")[:100]]
            if not prices:
                return "Live price data is limited for this filter right now. I can still suggest matching properties."
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            city_label = city or "your selected area"
            return (
                f"Current apartment prices in {city_label} are around {self._format_price(avg_price)} on average, "
                f"with active listings from {self._format_price(min_price)} to {self._format_price(max_price)} "
                f"based on {count} live listings."
            )
        except Exception as exc:
            logger.warning("Market price lookup failed: %s", exc)
            return "I am unable to fetch live prices right now. Please try again in a moment."

    def _website_realtime_message(
        self,
        user_message: str,
        lead: Dict[str, str],
        search_criteria: Dict[str, Any],
    ) -> str:
        try:
            from properties.models import Property

            lowered = user_message.lower()
            base_query = Property.objects.filter(is_active=True)
            city = (lead.get("city") or search_criteria.get("city") or "").strip()
            property_type = (lead.get("property_type") or search_criteria.get("property_type") or "").strip()

            filtered = base_query
            if city:
                filtered = filtered.filter(city__icontains=city)
            if property_type:
                filtered = filtered.filter(property_type__icontains=property_type)

            budget_cap = self._parse_budget_to_value(lead.get("budget") or "")
            message_budget_match = re.search(
                r"\b(?:under|within|upto|up to|max(?:imum)?|budget(?:\s+is)?(?:\s+only)?)\s*((?:rs\.?|inr|₹)?\s*\d+(?:[\.,]\d+)?\s*(?:lakh|lac|crore|cr|k|million|m)?)",
                lowered,
                re.IGNORECASE,
            )
            if message_budget_match:
                message_budget_cap = self._parse_budget_to_value(message_budget_match.group(1))
                if message_budget_cap > 0:
                    budget_cap = message_budget_cap
            budget_mentioned = bool(re.search(r"\b(budget|under|within|max(?:imum)?|upto|up to)\b", lowered))
            if budget_cap > 0:
                filtered = filtered.filter(price__lte=budget_cap)

            top_count_match = re.search(r"\btop\s*(\d+)\b", lowered)
            top_limit = int(top_count_match.group(1)) if top_count_match else 3
            top_limit = min(max(top_limit, 1), 10)

            asks_locations = bool(re.search(r"\b(which|what)\s+(locations|cities|areas)\b", lowered))
            if asks_locations:
                location_query = base_query
                if property_type:
                    location_query = location_query.filter(property_type__icontains=property_type)
                if budget_cap > 0:
                    location_query = location_query.filter(price__lte=budget_cap)
                city_counts = (
                    location_query.exclude(city__isnull=True)
                    .exclude(city="")
                    .values("city")
                    .order_by("city")
                )
                summary: Dict[str, int] = {}
                for row in city_counts:
                    c = row.get("city")
                    if c:
                        summary[c] = summary.get(c, 0) + 1
                if not summary:
                    return "I do not see active LuxeEstate locations for that filter right now."
                top_locations = sorted(summary.items(), key=lambda item: (-item[1], item[0]))[:8]
                suffix = f" under {self._format_price(budget_cap)}" if budget_cap > 0 else ""
                labels = [f"{name} ({count})" for name, count in top_locations]
                return f"Active LuxeEstate locations{suffix}: " + ", ".join(labels) + "."

            if (
                "latest" in lowered
                or "new" in lowered
                or "recent" in lowered
                or "posted" in lowered
                or top_count_match
                or budget_mentioned
            ):
                latest = list(filtered.order_by("-created_at").values("title", "city", "price")[:top_limit])
                if not latest:
                    return "No recent active listings found for this filter right now."
                latest_lines = []
                for item in latest:
                    latest_lines.append(
                        f"{item.get('title', 'Property')} ({item.get('city', 'Unknown city')}) - {self._format_price(float(item.get('price') or 0))}"
                    )
                scope = f" in {city}" if city else ""
                budget_note = f" under {self._format_price(budget_cap)}" if budget_cap > 0 else ""
                return f"Latest active listings{scope}{budget_note}: " + "; ".join(latest_lines)

            if "nearby" in lowered or "near by" in lowered or "near area" in lowered or "nearby area" in lowered:
                nearby_samples = list(
                    filtered.exclude(address__isnull=True)
                    .exclude(address="")
                    .values_list("address", flat=True)[:8]
                )
                if not nearby_samples:
                    # Fall back to a broader set (without strict budget filtering) for locality hints.
                    fallback_query = base_query
                    if city:
                        fallback_query = fallback_query.filter(city__icontains=city)
                    if property_type:
                        fallback_query = fallback_query.filter(property_type__icontains=property_type)
                    nearby_samples = list(
                        fallback_query.exclude(address__isnull=True)
                        .exclude(address="")
                        .values_list("address", flat=True)[:8]
                    )
                    if not nearby_samples:
                        nearby_samples = list(
                            base_query.exclude(address__isnull=True)
                            .exclude(address="")
                            .values_list("address", flat=True)[:8]
                        )
                    if not nearby_samples:
                        return (
                            "I could not find nearby locality details right now. "
                            "Try sharing city or landmark to get better locality suggestions."
                        )
                area_list = self._extract_locality_names(nearby_samples, limit=8)
                if not area_list:
                    return "Nearby locality details are limited in current listings, but I can still suggest matching properties."
                return "Nearby areas from current active listings: " + ", ".join(area_list[:8]) + "."

            if "cities" in lowered:
                cities = list(
                    base_query.exclude(city__isnull=True).exclude(city="")
                    .values_list("city", flat=True).distinct()[:15]
                )
                if not cities:
                    return "I do not see active city data right now."
                return "Active listing cities on LuxeEstate: " + ", ".join(cities) + "."

            if "how many" in lowered or "count" in lowered or "available" in lowered or "listing" in lowered:
                total = filtered.count()
                scope_parts = []
                if city:
                    scope_parts.append(f"in {city}")
                if property_type:
                    scope_parts.append(f"for {property_type}")
                scope = " ".join(scope_parts).strip()
                if scope:
                    return f"There are currently {total} active listings {scope} on LuxeEstate."
                return f"There are currently {total} active listings on LuxeEstate."

            if self._is_market_price_query(user_message):
                return self._market_price_message(lead, search_criteria)

            priced_values = [float(p.price) for p in filtered.exclude(price__isnull=True).exclude(price=0).only("price")[:120]]
            if priced_values:
                avg_price = mean(priced_values)
                return (
                    f"Based on live LuxeEstate listings, average price is {self._format_price(avg_price)} "
                    f"with a range of {self._format_price(min(priced_values))} to {self._format_price(max(priced_values))}."
                )
            return "I can answer LuxeEstate listing questions in real time. Ask about counts, latest listings, cities, or price ranges."
        except Exception as exc:
            logger.warning("Website realtime lookup failed: %s", exc)
            return "I am unable to fetch live LuxeEstate data right now. Please try again shortly."

    def _rule_based_reply(
        self,
        user_message: str,
        intent: str,
        lead: Dict[str, str],
        appointment: Dict[str, Any],
        search_criteria: Dict[str, Any],
    ) -> str:
        lowered = user_message.lower()
        if self._is_website_realtime_query(lowered):
            return self._website_realtime_message(user_message, lead, search_criteria)
        if lead.get("budget") and (
            re.search(r"\b(my|the)\s+budget\b", lowered)
            or re.search(r"\bonly\b", lowered)
            or re.search(r"\bunder\b", lowered)
            or re.search(r"\bwithin\b", lowered)
        ):
            return self._website_realtime_message(user_message, lead, search_criteria)
        if self._is_market_price_query(lowered):
            return self._market_price_message(lead, search_criteria)
        if intent == "appointment" and appointment.get("preferred_datetime"):
            date_time = appointment.get("preferred_datetime")
            return (
                f"Perfect, I noted your site visit request for {date_time}. "
                "Please share your contact number so our agent can confirm the booking."
            )
        if intent in {"buy", "rent", "invest", "inquiry"} and self._is_information_question(user_message):
            city = lead.get("city")
            if city:
                return f"Sure, I can help with options in {city}. Share your budget range and preferred BHK to shortlist quickly."
            if not self._is_property_query(user_message):
                return "I answer only from LuxeEstate live listing data. Ask me about listings, cities, prices, recent posts, or nearby areas."
            return "Sure, I can help. Tell me your preferred city and budget, and I will suggest matching options."
        if re.search(r"\b(my name is|i am|i'm)\b", lowered) and lead.get("name"):
            return f"Thanks {lead.get('name')}. Please share your city and budget so I can suggest relevant properties."
        return self._fallback_message(intent, lead, appointment)

    @staticmethod
    def _fallback_message(intent: str, lead: Dict[str, str], appointment: Dict[str, Any]) -> str:
        if appointment.get("requested"):
            return (
                "I can help schedule your appointment. Please share your preferred date/time and contact number, "
                "and an agent will confirm shortly."
            )
        next_field = LuxeChatbot._next_missing_field(lead)
        if not next_field:
            return "Thanks, your requirements are captured. Would you like me to suggest matching properties now?"
        if intent in {"buy", "rent", "invest", "inquiry"}:
            label = LuxeChatbot._label_for_field(next_field)
            return f"Great, I can help with that. Could you share your {label} so I can recommend the best options?"
        return "Hi! I can help you find properties, qualify your requirements, and schedule visits anytime."

    @staticmethod
    def _make_non_repetitive_message(message: str, history: List[Dict[str, str]], intent: str, lead: Dict[str, str]) -> str:
        if not history:
            return message
        def _normalized_cmp(text: str) -> str:
            lowered = LuxeChatbot._normalize(text).lower()
            return re.sub(r"[\W_]+", " ", lowered).strip()

        last_assistant_message = ""
        for item in reversed(history):
            if item.get("role") == "assistant":
                last_assistant_message = LuxeChatbot._normalize(item.get("content", ""))
                break
        if not last_assistant_message or _normalized_cmp(message) != _normalized_cmp(last_assistant_message):
            return message

        next_field = LuxeChatbot._next_missing_field(lead)
        candidate_messages: List[str] = []
        if next_field and intent in {"buy", "rent", "invest", "inquiry"}:
            label = LuxeChatbot._label_for_field(next_field)
            candidate_messages = [
                f"To narrow options better, please share your {label}.",
                f"Please tell me your {label}, and I will shortlist matching listings.",
                f"Once I have your {label}, I can give precise options right away.",
            ]
        else:
            candidate_messages = [
                "Happy to help further. Tell me your exact requirement and I will answer directly.",
                "I can help instantly if you share a specific city, budget, or property type.",
                "Share one clear requirement and I will give a direct answer.",
            ]

        last_normalized = _normalized_cmp(last_assistant_message)
        for candidate in candidate_messages:
            if _normalized_cmp(candidate) != last_normalized:
                return candidate
        return candidate_messages[0]

    def process_message(self, user_message: str, conversation_state: Dict[str, Any] = None) -> Dict[str, Any]:
        state = conversation_state or {}
        history = state.get("chat_history", []) or []
        lead = self._merge_lead(DEFAULT_LEAD, state.get("lead", {}))
        appointment = self._merge_appointment(DEFAULT_APPOINTMENT, state.get("appointment", {}))
        search_criteria = dict(state.get("search_criteria", {}) or {})

        extracted = self._extract_message_fields(user_message)
        lead = self._merge_lead(lead, extracted)

        lowered = user_message.lower()
        intent = "unknown"
        if self._is_plain_greeting(user_message):
            intent = "greeting"
        if any(word in lowered for word in ("buy", "purchase")):
            intent = "buy"
        elif any(word in lowered for word in ("rent", "lease")):
            intent = "rent"
        elif "invest" in lowered:
            intent = "invest"
        elif any(word in lowered for word in ("support", "help", "issue")):
            intent = "support"
        elif self._is_property_query(user_message):
            intent = "inquiry"
        elif self._is_information_question(user_message):
            intent = "inquiry"

        has_context = bool(state.get("chat_history")) or bool(lead.get("city")) or bool(lead.get("budget"))
        if intent == "unknown" and has_context:
            intent = "inquiry"

        if self._detect_appointment(user_message):
            appointment["requested"] = True
            appointment["preferred_datetime"] = appointment.get("preferred_datetime") or self._extract_datetime_hint(user_message)
            appointment["property_hint"] = appointment.get("property_hint") or lead.get("property_type", "")
            intent = "appointment"

        handoff_reason = self._detect_handoff(user_message)
        requires_human = bool(handoff_reason)
        if requires_human:
            intent = "handoff"

        if lead.get("city"):
            search_criteria["city"] = lead["city"]
        if lead.get("property_type"):
            search_criteria["property_type"] = lead["property_type"]

        force_realtime = self._is_website_realtime_query(user_message) or (
            bool(lead.get("budget"))
            and bool(re.search(r"\b(my|the)\s+budget\b|\bonly\b|\bunder\b|\bwithin\b", lowered))
        )
        llm_payload = {} if force_realtime else self._call_llm(user_message, history, lead, search_criteria)

        result = self._base_result()
        result["intent"] = llm_payload.get("intent") or intent
        result["lead"] = self._merge_lead(lead, llm_payload.get("lead", {}))
        result["appointment"] = self._merge_appointment(appointment, llm_payload.get("appointment", {}))
        result["requires_human"] = bool(llm_payload.get("requires_human", False)) or requires_human
        result["handoff_reason"] = llm_payload.get("handoff_reason", "") or handoff_reason
        result["qualification_stage"] = self._qualification_stage(result["lead"])

        message = self._normalize(llm_payload.get("message", ""))
        if force_realtime:
            message = self._website_realtime_message(user_message, result["lead"], search_criteria)
        elif not message:
            message = self._rule_based_reply(
                user_message=user_message,
                intent=result["intent"],
                lead=result["lead"],
                appointment=result["appointment"],
                search_criteria=search_criteria,
            )
        message = self._make_non_repetitive_message(message, history, result["intent"], result["lead"])
        result["message"] = message

        updated_history = list(history)
        updated_history.append({"role": "user", "content": user_message})
        updated_history.append({"role": "assistant", "content": message})
        result["chat_history"] = updated_history[-self.MAX_HISTORY:]
        result["search_criteria"] = search_criteria
        return result


chatbot = LuxeChatbot()
LuxeEstateChatbot = LuxeChatbot