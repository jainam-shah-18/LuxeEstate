"""
LuxeEstate chatbot backend (rewritten from scratch).

Design goals:
- deterministic and fast first response path
- live listing snapshot from Property table on every request
- session-friendly state shape compatible with existing view layer
- optional NIM generation with graceful fallback
"""

from __future__ import annotations

import logging
import re
import requests
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import Avg, Max, Min, QuerySet
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Property, Lead, Appointment
from .chatbot_system_prompt import CHATBOT_SYSTEM_PROMPT, is_out_of_scope, get_scope_redirect

logger = logging.getLogger(__name__)

DEFAULT_LEAD = {
    "name": "",
    "contact": "",
    "intent": "",
    "budget": "",
    "location": "",
    "property_type": "",
    "bhk": "",
}

DEFAULT_APPOINTMENT = {
    "requested": False,
    "property_hint": "",
    "preferred_datetime": "",
    "confirmed": False,
}

LEAD_ORDER = ["intent", "location", "property_type", "budget", "name", "contact"]

GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|hii|namaste|good morning|good afternoon|good evening)\s*[!.,\s]*$",
    re.IGNORECASE,
)
GOODBYE_RE = re.compile(r"^\s*(bye|goodbye|exit|quit|stop|see you)\s*[!.,\s]*$", re.IGNORECASE)
DATETIME_HINT_RE = re.compile(
    r"\b("
    r"time|date|day|today|tomorrow|yesterday|current|now|"
    r"what\s+(?:is|'s|time)|current\s+time|what\s+time|what\s+date|"
    r"jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
    r"aug|august|sep|sept|september|oct|october|nov|november|dec|december|"
    r"\d{1,2}\s*(?:/|-)\s*\d{1,2}(?:\s*(?:/|-)\s*\d{2,4})?"
    r")\b",
    re.IGNORECASE,
)

PROPERTY_TYPES = {"apartment", "house", "villa", "plot", "commercial", "office", "shop", "farmland"}

# Comprehensive city abbreviations and alias mappings
CITY_ABBREVIATIONS = {
    # Major cities
    "blr": "Bangalore",
    "bangalore": "Bangalore",
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "ncr": "Delhi",
    "pune": "Pune",
    "delhi": "Delhi",
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "ahmedabad": "Ahmedabad",
    "ahmd": "Ahmedabad",
    "surat": "Surat",
    "vadodara": "Vadodara",
    "jaipur": "Jaipur",
    "lucknow": "Lucknow",
    "kanpur": "Kanpur",
    "nagpur": "Nagpur",
    "indore": "Indore",
    "thane": "Thane",
    "bhopal": "Bhopal",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "noida": "Noida",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "goa": "North Goa",  # Map "Goa" to "North Goa"
    "north goa": "North Goa",
    "south goa": "South Goa",
    # Popular localities
    "whitefield": "Whitefield",
    "manyata": "Manyata",
    "indiranagar": "Indiranagar",
    "koramangala": "Koramangala",
    "banjara hills": "Banjara Hills",
}

INTENT_PATTERNS = {
    "rent": re.compile(r"\b(rent|rental|lease|on rent)\b", re.IGNORECASE),
    "invest": re.compile(r"\b(invest|investment|roi|yield|appreciation)\b", re.IGNORECASE),
    "buy": re.compile(r"\b(buy|purchase|looking|need|want|search|find|show)\b", re.IGNORECASE),
}
APPOINTMENT_RE = re.compile(r"\b(site visit|visit|schedule|appointment|callback|call back|meeting)\b", re.IGNORECASE)
HUMAN_RE = re.compile(r"\b(human|agent|manager|complaint|fraud|legal|dispute|urgent)\b", re.IGNORECASE)
SECURITY_RE = re.compile(
    r"\b(otp|pin|cvv|card number|password|passcode|secret key|ignore instructions|jailbreak|system prompt)\b",
    re.IGNORECASE,
)

# Additional patterns for advanced queries
READY_TO_MOVE_RE = re.compile(r"\b(ready.?to.?move|ready.?possession|immediate|available now)\b", re.IGNORECASE)
FURNISHED_RE = re.compile(r"\b(furnished|unfurnished|semi.furnished)\b", re.IGNORECASE)
FACING_RE = re.compile(r"\b(east.facing|west.facing|north.facing|south.facing)\b", re.IGNORECASE)
AMENITIES_RE = re.compile(r"\b(parking|lift|elevator|garden|pool|gym|security|gated|community)\b", re.IGNORECASE)
RECENT_POST_RE = re.compile(r"\b(last \d+ days?|recent|newly launched|posted in)\b", re.IGNORECASE)
AREA_SQFT_RE = re.compile(r"\b(at least (\d+) sq ft|minimum (\d+) sqft|over (\d+) square feet)\b", re.IGNORECASE)


class LuxeChatbot:
    MAX_HISTORY = 24
    MAX_HISTORY_MESSAGES = 12

    def __init__(self):
        """Initialize chatbot with persistent requests session for API calls"""
        self.http_client = requests.Session()
        # Configure session for better connection handling
        self.http_client.headers.update({
            'User-Agent': 'LuxeEstate-Chatbot/1.0'
        })

    def _now_context(self) -> Tuple[str, str, str, str]:
        now = timezone.localtime(timezone.now())
        tz_name = now.strftime("%Z") or "IST"
        return (
            f"{now.strftime('%A, %d %B %Y, %I:%M %p')} {tz_name}",
            now.strftime("%A"),
            now.strftime("%d %B %Y"),
            now.strftime("%I:%M %p"),
        )

    def _tomorrow_context(self) -> Tuple[str, str]:
        """Get tomorrow's date and day name"""
        tomorrow = timezone.localtime(timezone.now()) + timedelta(days=1)
        return (
            tomorrow.strftime("%d %B %Y"),
            tomorrow.strftime("%A"),
        )

    def _relative_date_reply(self, user_message: str) -> Optional[str]:
        now = timezone.localtime(timezone.now())
        if re.search(r"\bday after tomorrow\b", user_message, re.IGNORECASE):
            target = now + timedelta(days=2)
            return f"The day after tomorrow is {target.strftime('%A, %d %B %Y')}."
        if re.search(r"\btomorrow\b", user_message, re.IGNORECASE):
            target = now + timedelta(days=1)
            return f"Tomorrow is {target.strftime('%A, %d %B %Y')}."
        if re.search(r"\byesterday\b", user_message, re.IGNORECASE):
            target = now - timedelta(days=1)
            return f"Yesterday was {target.strftime('%A, %d %B %Y')}."
        return None

    def _normalize_property_type(self, token: str) -> str:
        t = (token or "").strip().lower()
        synonyms = {
            "flat": "apartment",
            "apartment": "apartment",
            "villa": "villa",
            "plot": "plot",
            "house": "house",
            "home": "house",
            "office": "office",
            "shop": "shop",
            "commercial": "commercial",
            "farmland": "farmland",
        }
        return synonyms.get(t, t if t in PROPERTY_TYPES else "")

    def _extract_budget_text(self, message: str) -> str:
        if not message:
            return ""
        m = re.search(
            r"(?:under|upto|up to|below|within|budget|around)?\s*(?:rs\.?|inr|₹)?\s*"
            r"(\d+(?:[\.,]\d+)?)\s*(lakh|lac|l|crore|cr|k|thousand|million|m)?",
            message,
            re.IGNORECASE,
        )
        if not m:
            return ""
        
        value = m.group(1).replace(",", "")
        unit = (m.group(2) or "").lower()
        
        # If no unit is found, check if the number is large enough to be a raw value
        # or if it's likely a partial match we should ignore
        if not unit and len(value) < 4:
            return ""
            
        return f"{value} {unit}".strip()

    def _budget_to_rupees(self, budget_text: str) -> Optional[Decimal]:
        if not budget_text:
            return None
        m = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|l|crore|cr|k|thousand|million|m)?", budget_text, re.IGNORECASE)
        if not m:
            return None
        try:
            value = Decimal(m.group(1))
        except (InvalidOperation, TypeError):
            return None
        unit = (m.group(2) or "").lower()
        multiplier = Decimal("1")
        if unit in {"k", "thousand"}:
            multiplier = Decimal("1000")
        elif unit in {"lakh", "lac", "l"}:
            multiplier = Decimal("100000")
        elif unit in {"crore", "cr"}:
            multiplier = Decimal("10000000")
        elif unit in {"million", "m"}:
            multiplier = Decimal("1000000")
        return value * multiplier

    def _extract_lead_fields(self, message: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        text = (message or "").strip()
        lower = text.lower()

        name_match = re.search(r"\b(?:my name is|i am|i'm)\s+([A-Za-z][A-Za-z ]{1,40})\b", text, re.IGNORECASE)
        if name_match:
            out["name"] = name_match.group(1).strip().title()

        email_match = re.search(r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
        phone_match = re.search(r"(?:\+91|0)?\s*([1-9]\d{9})\b", text)
        if email_match:
            out["contact"] = email_match.group(0).strip()
        elif phone_match:
            out["contact"] = phone_match.group(1).strip()

        for intent, pattern in INTENT_PATTERNS.items():
            if pattern.search(lower):
                out["intent"] = intent
                break

        city_match = re.search(
            r"\b(?:in|at|near)\s+([A-Za-z][A-Za-z\s]{1,30}?)(?:\s+(?:for|under|budget|price|with)\b|[.,]|$)",
            text,
            re.IGNORECASE,
        )
        if city_match:
            city = city_match.group(1).strip()
            # Normalize and map city name using comprehensive abbreviations
            city_normalized = CITY_ABBREVIATIONS.get(city.lower(), city)
            out["location"] = city_normalized
        elif re.match(r"^\s*[A-Za-z][A-Za-z\s]{2,30}\s*$", text) and " " not in text.strip() and not GREETING_RE.match(text) and not GOODBYE_RE.match(text):
            city = text.strip()
            # Normalize and map city name using comprehensive abbreviations
            city_normalized = CITY_ABBREVIATIONS.get(city.lower(), city)
            out["location"] = city_normalized

        ptype = re.search(r"\b(flat|apartment|villa|plot|house|home|office|shop|commercial|farmland)\b", lower)
        if ptype:
            normalized = self._normalize_property_type(ptype.group(1))
            if normalized:
                out["property_type"] = normalized

        bhk_match = re.search(r"\b(\d{1,2})\s*(?:bhk|bed|bedroom|bedrooms)\b", lower)
        if bhk_match:
            out["bhk"] = f"{bhk_match.group(1)} BHK"
        elif re.search(r"\b(\d{1,2})bhk\b", lower):  # Handle 2BHK without space
            num_match = re.search(r"\b(\d{1,2})bhk\b", lower)
            if num_match:
                out["bhk"] = f"{num_match.group(1)} BHK"

        budget_text = self._extract_budget_text(text)
        if budget_text:
            out["budget"] = budget_text

        # Additional extractions
        if READY_TO_MOVE_RE.search(lower):
            out["ready_to_move"] = "yes"
        if FURNISHED_RE.search(lower):
            furnished_match = FURNISHED_RE.search(lower)
            out["furnished"] = furnished_match.group(0).lower()
        if FACING_RE.search(lower):
            facing_match = FACING_RE.search(lower)
            out["facing"] = facing_match.group(0).lower()
        if AMENITIES_RE.search(lower):
            amenities = AMENITIES_RE.findall(lower)
            out["amenities"] = ", ".join(set(amenities))
        if RECENT_POST_RE.search(lower):
            days_match = re.search(r"last (\d+) days?", lower)
            if days_match:
                out["posted_within_days"] = days_match.group(1)
        if AREA_SQFT_RE.search(lower):
            sqft_match = AREA_SQFT_RE.search(lower)
            if sqft_match:
                out["min_area_sqft"] = sqft_match.group(1) or sqft_match.group(2) or sqft_match.group(3)

        return out

    def _extract_appointment_datetime(self, message: str) -> str:
        text = (message or "").strip()
        if not text:
            return ""
        date_pattern = re.compile(
            r"\b("
            r"today|tomorrow|day after tomorrow|"
            r"\d{1,2}\s*(?:/|-)\s*\d{1,2}(?:\s*(?:/|-)\s*\d{2,4})?|"
            r"\d{1,2}(?:st|nd|rd|th)?\s+"
            r"(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
            r"aug|august|sep|sept|september|oct|october|nov|november|dec|december)"
            r")\b",
            re.IGNORECASE,
        )
        date_matches = list(date_pattern.finditer(text))
        time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)|\d{1,2}\s*o'?clock)\b", text, re.IGNORECASE)

        # Ignore listing metadata dates like "Posted on: 5 April".
        candidate_dates = []
        for match in date_matches:
            context_before = text[max(0, match.start() - 20):match.start()].lower()
            if re.search(r"(posted|listed)\s+on\s*:?\s*$", context_before):
                continue
            candidate_dates.append(match.group(1).strip())

        chosen_date = candidate_dates[-1] if candidate_dates else ""
        if chosen_date and time_match:
            return f"{chosen_date} {time_match.group(1)}".strip()
        if chosen_date:
            return chosen_date
        if time_match:
            return time_match.group(1).strip()
        return ""

    def extract_entities(self, message: str) -> Dict[str, Any]:
        lead_fields = self._extract_lead_fields(message)
        return {
            "lead": lead_fields,
            "appointment_datetime": self._extract_appointment_datetime(message),
        }

    def _handle_faq(self, message: str) -> Optional[str]:
        """
        DEPRECATED: All FAQ handling moved to NVIDIA NIM for real-time, AI-generated responses.
        This method is kept for backward compatibility but always returns None.
        """
        # EMI calculations are the ONLY exception - these are mathematical, not content
        emi_response = self._handle_budget_queries(message)
        if emi_response:
            return emi_response
        
        # All other queries must go through NVIDIA NIM
        return None

    def handle_fallback(self, intent: str, user_message: str) -> str:
        """Handle unknown intents with a generic fallback response"""
        return "I can help with property search, pricing, and site visits on LuxeEstate. What would you like to explore?"

    def _qualification_stage(self, lead: Dict[str, str]) -> str:
        """Determine lead qualification stage"""
        missing = len(self._missing_fields(lead))
        if missing == 0:
            return "hot"
        elif missing <= 2:
            return "warm"
        else:
            return "cold"

    def _save_lead(self, lead_data: Dict[str, str], session_id: Optional[str] = None):
        """Save lead to database"""
        try:
            lead, created = Lead.objects.update_or_create(
                session_id=session_id,
                defaults={
                    "name": lead_data.get("name"),
                    "contact": lead_data.get("contact"),
                    "intent": lead_data.get("intent"),
                    "budget": lead_data.get("budget"),
                    "location": lead_data.get("location"),
                    "property_type": lead_data.get("property_type"),
                    "bhk": lead_data.get("bhk"),
                }
            )
            lead.update_qualification()
            return lead
        except Exception as e:
            logger.error(f"Error saving lead: {e}")
            return None

    def _save_appointment(self, lead, appointment_data: Dict[str, Any]):
        """Save appointment to database"""
        try:
            # Simple date parsing for the stub
            # In a real app, use a more robust parser like dateutil
            dt_str = appointment_data.get("preferred_datetime", "")
            # Mocking a datetime for now as parsing arbitrary strings is complex
            # In production, use a proper parser
            scheduled_dt = timezone.now() + timedelta(days=1) 
            
            appointment = Appointment.objects.create(
                lead=lead,
                scheduled_datetime=scheduled_dt,
                notes=f"Requested via chatbot: {appointment_data.get('property_hint')}"
            )
            return appointment
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
            return None

    def _assign_agent_to_hot_lead(self, lead):
        """Assign an available agent to a hot lead"""
        if lead.qualification_stage == 'hot' and not lead.assigned_agent:
            agent = User.objects.filter(is_staff=True).first()
            if agent:
                lead.assigned_agent = agent
                lead.save(update_fields=['assigned_agent'])

    def manage_conversation_state(self, conversation_state: Optional[dict], user_message: str) -> Dict[str, Any]:
        raw = (user_message or "").strip()[:1000]
        state = conversation_state or {}
        history = list(state.get("chat_history", []) or [])
        extracted = self.extract_entities(raw)
        lead = self._merge(state.get("lead", {}), extracted.get("lead", {}), DEFAULT_LEAD)
        criteria = dict(state.get("search_criteria", {}) or {})
        for key in ("location", "property_type", "budget", "bhk"):
            if lead.get(key):
                criteria[key] = lead[key]
        appointment = self._merge(state.get("appointment", {}), {}, DEFAULT_APPOINTMENT)
        if extracted.get("appointment_datetime"):
            appointment["preferred_datetime"] = extracted.get("appointment_datetime")
        intent = self.detect_intent(raw)
        if intent == "appointment":
            appointment["requested"] = True
            appointment["property_hint"] = (raw[:160]).strip()
        if appointment.get("requested") and intent == "datetime":
            intent = "appointment"
        if appointment.get("requested") and appointment.get("preferred_datetime") and lead.get("contact"):
            appointment["confirmed"] = True
        
        # Handle intent changes
        if intent == "intent_change":
            # Reset intent based on new message
            for new_intent, pattern in INTENT_PATTERNS.items():
                if pattern.search(raw.lower()):
                    lead["intent"] = new_intent
                    break
        
        # Handle preferences
        if intent == "preference":
            # Extract and store preferences
            if "west-facing" in raw.lower():
                lead["preferred_facing"] = "west-facing"
            elif "east-facing" in raw.lower():
                lead["preferred_facing"] = "east-facing"
            if "balcony" in raw.lower():
                lead["preferred_features"] = (lead.get("preferred_features", "") + " balcony").strip()
        
        asked_fields = set(state.get("asked_fields", []) or [])
        previous_missing = len(self._missing_fields(state.get("lead", {})))
        missing_fields = self._missing_fields(lead)
        next_question = next((f for f in missing_fields if f not in asked_fields), missing_fields[0] if missing_fields else "")
        return {
            "raw": raw,
            "history": history,
            "lead": lead,
            "criteria": criteria,
            "appointment": appointment,
            "asked_fields": asked_fields,
            "previous_missing": previous_missing,
            "missing_fields": missing_fields,
            "next_question": next_question,
            "intent": intent,
        }

    def generate_response(
        self,
        raw: str,
        intent: str,
        history: List[Dict[str, str]],
        lead: Dict[str, str],
        criteria: Dict[str, Any],
        appointment: Dict[str, Any],
        missing_fields: List[str],
        next_question: str,
        asked_fields: set,
    ) -> Tuple[str, str, set]:
        """Generate response using NVIDIA NIM ONLY - all responses from real-time AI, no hardcoded fallbacks"""
        
        message = ""
        model = ""
        try:
            message, model = self._nim_reply(raw, history, lead, criteria)
            logger.info(f"Successfully generated response using NVIDIA NIM model: {model}")
            return message, model, asked_fields
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"NVIDIA NIM failed - no hardcoded fallback will be used: {error_msg}")
            # Return error to user indicating AI service issue - NO hardcoded fallback allowed
            message = (
                f"⚠️ AI service temporarily unavailable ({error_msg}). "
                "Please check NVIDIA_API_KEY and NIM configuration in .env file."
            )
            model = "error"
        
        return message, model, asked_fields

    def _merge(self, base: Dict[str, Any], update: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        merged = {**defaults, **(base or {})}
        for key, value in (update or {}).items():
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue
            merged[key] = value
        return merged

    def _missing_fields(self, lead: Dict[str, str]) -> List[str]:
        return [f for f in LEAD_ORDER if not (lead or {}).get(f)]

    def send_automated_followups(self):
        """Send automated follow-ups for leads and appointments"""
        now = timezone.now()
        
        # Send reminders for upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            scheduled_datetime__gte=now,
            scheduled_datetime__lte=now + timezone.timedelta(hours=24),
            status='scheduled',
            reminder_sent=False
        )
        
        for appointment in upcoming_appointments:
            try:
                appointment.send_reminder()
                logger.info(f"Sent reminder for appointment {appointment.id}")
            except Exception as e:
                logger.error(f"Failed to send reminder for appointment {appointment.id}: {e}")

    def _query_from_lead(self, lead: Dict[str, str], criteria: Dict[str, Any]) -> QuerySet:
        qs = Property.objects.filter(is_active=True)
        
        # Normalize and filter by location/city
        location = (criteria.get("location") or criteria.get("city") or lead.get("location") or "").strip()
        if location:
            # Normalize location using CITY_ABBREVIATIONS mapping
            normalized_location = CITY_ABBREVIATIONS.get(location.lower(), location)
            # Use case-insensitive match to handle any casing variations
            qs = qs.filter(city__iexact=normalized_location)
        
        # Filter by property type
        ptype = (criteria.get("property_type") or lead.get("property_type") or "").strip().lower()
        normalized_type = self._normalize_property_type(ptype)
        if normalized_type:
            qs = qs.filter(property_type=normalized_type)
        
        # Filter by BHK/bedrooms
        bhk_text = (criteria.get("bhk") or lead.get("bhk") or "").strip().lower()
        bhk_num = re.search(r"(\d+)", bhk_text)
        if bhk_num:
            qs = qs.filter(bedrooms=int(bhk_num.group(1)))

        # Filter by budget
        budget_rupees = self._budget_to_rupees(criteria.get("budget") or lead.get("budget") or "")
        if budget_rupees:
            qs = qs.filter(price__lte=budget_rupees)

        # Filter by furnishing
        if lead.get("furnished"):
            qs = qs.filter(furnishing__icontains=lead["furnished"])
        
        # Filter by minimum area
        if lead.get("min_area_sqft"):
            try:
                sqft = int(lead["min_area_sqft"])
                qs = qs.filter(area_sqft__gte=sqft)
            except (ValueError, TypeError):
                pass

        return qs

    def _calculate_emi(self, principal: Decimal, interest_rate: Decimal, tenure_years: int) -> Decimal:
        """Calculate monthly EMI using standard formula"""
        monthly_rate = interest_rate / 12 / 100
        months = tenure_years * 12
        if monthly_rate == 0:
            return principal / months
        emi = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
        return emi.quantize(Decimal('0.01'))

    def _handle_budget_queries(self, message: str) -> Optional[str]:
        """Handle EMI, investment, and budget-related queries"""
        text = (message or "").strip().lower()
        
        # EMI calculation
        emi_match = re.search(r"emi for (?:rs\.?|inr|₹)?(\d+(?:[\.,]\d+)?)\s*(lakh|lac|l|crore|cr|k)?\s*(?:loan)?\s*,?\s*(\d+(?:\.\d+)?)%?\s*(?:interest)?\s*,?\s*(\d+)\s*years?", text, re.IGNORECASE)
        if emi_match:
            value = emi_match.group(1).replace(",", "")
            unit = (emi_match.group(2) or "").lower()
            rate = Decimal(emi_match.group(3))
            years = int(emi_match.group(4))
            
            principal = self._budget_to_rupees(f"{value} {unit}")
            if principal:
                emi = self._calculate_emi(principal, rate, years)
                return f"For a loan of ₹{principal:,.0f} at {rate}% interest for {years} years, your monthly EMI would be approximately ₹{emi:,.0f}."
        
        return None

    def _listing_snapshot(self, lead: Dict[str, str], criteria: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        qs = self._query_from_lead(lead, criteria)
        total = qs.count()
        if total == 0:
            return "No active listings match the current filters.", {"count": 0}

        aggr = qs.aggregate(min_price=Min("price"), max_price=Max("price"), avg_price=Avg("price"))
        top = list(qs.order_by("-is_featured", "-created_at")[:3])
        lines = []
        for item in top:
            bhk = f"{item.bedrooms} BHK" if item.bedrooms else "N/A BHK"
            lines.append(f"- {item.title} ({item.city}) | {bhk} | ₹{item.price:,.0f}")
        snapshot = (
            f"Active listings: {total}\n"
            f"Price range: ₹{aggr['min_price']:,.0f} - ₹{aggr['max_price']:,.0f}\n"
            f"Average price: ₹{aggr['avg_price']:,.0f}\n"
            "Top matches:\n" + "\n".join(lines)
        )
        return snapshot, {"count": total, "top": [p.id for p in top]}

    def _deterministic_reply(
        self,
        user_message: str,
        intent: str,
        lead: Dict[str, str],
        criteria: Dict[str, Any],
        appointment: Dict[str, Any],
    ) -> str:
        now_text, day_name, date_text, time_text = self._now_context()
        tomorrow_date, tomorrow_day = self._tomorrow_context()
        
        if GREETING_RE.match(user_message):
            return "Hello! I am Luxe AI Concierge. Are you looking to buy, rent, or invest today?"
        if GOODBYE_RE.match(user_message):
            return "Thanks for chatting with LuxeEstate. I am here whenever you need property help."
        if appointment.get("requested"):
            has_when = bool((appointment.get("preferred_datetime") or "").strip())
            has_contact = bool((lead.get("contact") or "").strip())
            if has_when and has_contact:
                # Format appointment confirmation with proper date context
                apt_datetime = appointment.get('preferred_datetime', '')
                if 'tomorrow' in apt_datetime.lower():
                    apt_datetime = apt_datetime.replace('tomorrow', f'{tomorrow_day}, {tomorrow_date}')
                elif 'today' in apt_datetime.lower():
                    apt_datetime = apt_datetime.replace('today', f'{day_name}, {date_text}')
                
                return (
                    f"Perfect! Your site-visit appointment is scheduled for {apt_datetime}. "
                    f"Our LuxeEstate team will contact you at {lead.get('contact')} to confirm the details. "
                    f"You'll receive a confirmation message shortly."
                )
            if not has_when and not has_contact:
                return "Great, I can help schedule a site visit. Please share your preferred date/time and contact number."
            if not has_when:
                return f"Please share your preferred date and time for the site visit. (Today is {day_name}, {date_text}. Tomorrow is {tomorrow_day}, {tomorrow_date})"
            return "Please share your contact number or email so we can confirm the site visit."
        if DATETIME_HINT_RE.search(user_message):
            relative_reply = self._relative_date_reply(user_message)
            if relative_reply:
                return relative_reply
            return f"Current time is {time_text} on {day_name}, {date_text}. ({now_text}) Tomorrow is {tomorrow_day}, {tomorrow_date}."

        listing_text, info = self._listing_snapshot(lead, criteria)
        if info.get("count", 0) == 0:
            return "I could not find active listings for these filters. Share city, budget, or property type and I will broaden the search."
        if intent in {"buy", "rent", "invest", "inquiry"}:
            return (
                "Here is the live LuxeEstate snapshot:\n"
                f"{listing_text}\n"
                "Tell me more about what you're looking for."
            )
        return "I can help with property search, pricing, and site visits on LuxeEstate. What would you like to explore?"

    def _nim_reply(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        lead: Dict[str, str],
        criteria: Dict[str, Any],
    ) -> Tuple[str, str]:
        """
        Generate response using NVIDIA NIM API.
        Supports both NVIDIA Cloud API and self-hosted NIM endpoints.
        """
        # Get API configuration from settings
        api_key = (getattr(settings, "NVIDIA_API_KEY", None) or "").strip()
        if not api_key:
            logger.warning("NVIDIA_API_KEY is not configured. Set NVIDIA_API_KEY in .env file for AI enhancements.")
            raise RuntimeError("NVIDIA_API_KEY not configured. Chatbot will use deterministic fallback responses.")
        
        # Get NIM endpoint configuration (support both cloud and self-hosted)
        nim_endpoint = getattr(settings, "NVIDIA_NIM_ENDPOINT", "https://integrate.api.nvidia.com/v1").strip()
        model = getattr(settings, "NIM_CHAT_MODEL", "meta/llama-3.1-8b-instruct").strip()
        
        logger.debug(f"NIM Configuration - Model: {model}, Endpoint: {nim_endpoint}, API Key present: {bool(api_key)}")
        
        # Validate configuration
        if not model:
            raise RuntimeError("NIM_CHAT_MODEL is not configured")
        
        # Use persistent HTTP client for better connection pooling
        if not self.http_client:
            self.http_client = requests.Session()

        listing_text, _ = self._listing_snapshot(lead, criteria)
        now_text, day_name, date_text, time_text = self._now_context()
        tomorrow_date, tomorrow_day = self._tomorrow_context()

        # Get available cities from database
        available_cities = sorted(set(Property.objects.filter(
            is_active=True, status="available"
        ).values_list('city', flat=True)))
        cities_context = f"Available cities: {', '.join(available_cities)}" if available_cities else "No cities available yet"

        # Build comprehensive system prompt with actual context
        system = CHATBOT_SYSTEM_PROMPT.replace(
            "{context_will_be_injected_here}",
            f"CURRENT DATE & TIME CONTEXT:\n"
            f"- Today: {date_text} ({day_name})\n"
            f"- Current Time: {time_text}\n"
            f"- Tomorrow: {tomorrow_date} ({tomorrow_day})\n"
            f"- Full Context: {now_text}\n\n"
            f"{cities_context}\n"
            f"Live listing snapshot:\n{listing_text}\n"
            f"Lead profile: {lead}"
        )

        # Build message history
        messages = [{"role": "system", "content": system}]
        for turn in history[-self.MAX_HISTORY_MESSAGES:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        # Call NVIDIA NIM API with proper error handling
        try:
            url = f"{nim_endpoint.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 500,
                "top_p": 0.9,
            }
            
            logger.debug(f"Calling NVIDIA NIM at {url} with model {model}")
            resp = self.http_client.post(url, headers=headers, json=payload, timeout=30)
            
            if resp.status_code != 200:
                error_detail = resp.text
                logger.error(f"NVIDIA NIM API error (status {resp.status_code}): {error_detail}")
                if resp.status_code == 401:
                    raise Exception("NVIDIA NIM API authentication failed. Verify NVIDIA_API_KEY in .env is correct and not expired.")
                elif resp.status_code == 404:
                    raise Exception("NVIDIA NIM model not found. Verify NIM_CHAT_MODEL in .env (e.g., 'meta/llama-3.1-8b-instruct').")
                elif resp.status_code == 429:
                    raise Exception("NVIDIA NIM API rate limited. Too many requests. Please wait and retry.")
                else:
                    raise Exception(f"NVIDIA NIM API returned {resp.status_code}: {error_detail[:200]}")
            
            data = resp.json()
        except requests.exceptions.Timeout:
            logger.error("NVIDIA NIM API request timed out (30s) - endpoint may be slow, unreachable, or experiencing high load")
            raise RuntimeError("NVIDIA NIM API request timed out (30s). Endpoint unreachable or experiencing delays.")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to NVIDIA NIM at {nim_endpoint}: {e}")
            raise RuntimeError(f"Failed to connect to NVIDIA NIM endpoint ({nim_endpoint}): {e}")
        except Exception as exc:
            logger.error(f"NVIDIA NIM call failed: {exc}")
            raise RuntimeError(f"NVIDIA NIM chat completion failed: {exc}") from exc

        # Extract and validate response
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("NVIDIA NIM returned no completion choices")
        
        text = (choices[0].get("message", {}).get("content") or "").strip()
        if not text:
            raise RuntimeError("NVIDIA NIM returned empty completion")
        
        logger.info(f"NVIDIA NIM response generated ({len(text)} chars)")
        return text, model

    def detect_intent(self, message: str) -> str:
        text = (message or "").strip()
        lower = text.lower()
        if not text:
            return "unknown"
        
        # Check for out-of-scope topics first (CRITICAL - must be before property intents)
        if is_out_of_scope(message):
            return "out_of_scope"
        
        if GREETING_RE.match(text):
            return "greeting"
        if GOODBYE_RE.match(text):
            return "goodbye"
        if APPOINTMENT_RE.search(lower):
            return "appointment"
        if DATETIME_HINT_RE.search(text):
            return "datetime"
        
        # Handle intent changes
        if re.search(r"\bactually|but|instead|changed my mind|now i want\b", lower):
            return "intent_change"
        
        # Handle preferences
        if re.search(r"\bprefer|like|always|remember\b", lower):
            return "preference"
        
        # Handle questions about recommendations
        if re.search(r"\bwhy|how come|explain\b", lower):
            return "explanation"
        
        # Handle data freshness
        if re.search(r"\bupdated|current|today|fresh|latest\b", lower):
            return "data_freshness"
        
        for intent, pattern in INTENT_PATTERNS.items():
            if pattern.search(lower):
                return intent
        if any(k in lower for k in ("property", "listing", "price", "bhk", "apartment", "villa", "plot", "budget", "emi", "investment", "legal", "rera", "documents", "location", "area", "locality", "amenities", "schools", "hospitals", "metro", "traffic", "safe", "gated", "furnished", "facing", "parking", "lift", "ready", "newly launched", "posted")):
            return "inquiry"
        return "unknown"

    def process_message(self, user_message: str, conversation_state: Optional[dict] = None) -> dict:
        raw = (user_message or "").strip()[:1000]
        now_text, day_name, date_text, time_text = self._now_context()
        tomorrow_date, tomorrow_day = self._tomorrow_context()
        state = conversation_state or {}

        state_data = self.manage_conversation_state(state, raw)
        history = state_data["history"]
        lead = state_data["lead"]
        criteria = state_data["criteria"]
        appointment = state_data["appointment"]
        asked_fields = state_data["asked_fields"]
        previous_missing = state_data["previous_missing"]
        missing_fields = state_data["missing_fields"]
        next_question = state_data["next_question"]
        intent = state_data["intent"]

        requires_human = False
        handoff_reason = ""
        security_flagged = False
        out_of_scope_flagged = False

        if SECURITY_RE.search(raw):
            message = "I can only help with safe LuxeEstate property assistance and cannot process sensitive or unsafe requests."
            intent = "security"
            security_flagged = True
            model = ""
        elif HUMAN_RE.search(raw):
            message = "I am routing this to a LuxeEstate human agent. Please share contact details and our team will reach out."
            intent = "handoff"
            requires_human = True
            handoff_reason = "User requested human escalation"
            model = ""
        elif intent == "out_of_scope":
            message = get_scope_redirect(raw)
            out_of_scope_flagged = True
            model = ""
        else:
            message, model, asked_fields = self.generate_response(
                raw,
                intent,
                history,
                lead,
                criteria,
                appointment,
                missing_fields,
                next_question,
                asked_fields,
            )

        history.append({"role": "user", "content": raw})
        history.append({"role": "assistant", "content": message})
        history = history[-self.MAX_HISTORY :]

        # Persist lead and appointment data
        saved_lead = None
        saved_appointment = None
        session_id = state.get("session_id")
        
        result = {
            "lead_id": None,
            "qualification_stage": self._qualification_stage(lead),
            "agent_assigned": None,
            "appointment_id": None,
            "appointment_status": None,
        }
        
        if lead and any(lead.values()):
            try:
                saved_lead = self._save_lead(lead, session_id)
                if saved_lead:
                    result["lead_id"] = saved_lead.id
                    result["qualification_stage"] = saved_lead.qualification_stage
                    
                    # Auto-assign agent to hot leads
                    if saved_lead.qualification_stage == 'hot':
                        self._assign_agent_to_hot_lead(saved_lead)
                        result["agent_assigned"] = saved_lead.assigned_agent.username if saved_lead.assigned_agent else None
            except Exception as e:
                logger.error(f"Failed to save lead: {e}")
        
        if appointment.get("confirmed") and saved_lead:
            try:
                saved_appointment = self._save_appointment(saved_lead, appointment)
                if saved_appointment:
                    result["appointment_id"] = saved_appointment.id
                    result["appointment_status"] = saved_appointment.status
            except Exception as e:
                logger.error(f"Failed to save appointment: {e}")

        result.update({
            "message": message,
            "intent": intent,
            "lead": lead,
            "appointment": appointment,
            "requires_human": requires_human,
            "handoff_reason": handoff_reason,
            "model": model,
            "chat_history": history,
            "search_criteria": criteria,
            "current_datetime": now_text,
            "current_day": day_name,
            "current_date": date_text,
            "current_time": time_text,
            "tomorrow_date": tomorrow_date,
            "tomorrow_day": tomorrow_day,
            "guidelines": [
                "Only discuss LuxeEstate property-related topics.",
                "Use live listing context and avoid fabricated availability.",
                "Collect lead details progressively and politely.",
                "Escalate sensitive/legal/complaint requests to a human agent.",
            ],
            "out_of_scope": out_of_scope_flagged,
            "security_flagged": security_flagged,
            "handoff": requires_human,
            "qualified_lead": len(missing_fields) == 0,
            "just_qualified": previous_missing > 0 and len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "next_question_field": next_question,
            "asked_fields": list(asked_fields),
            "last_question_field": next_question if next_question else "",
        })
        return result


chatbot = LuxeChatbot()
