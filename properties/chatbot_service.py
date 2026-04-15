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
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import Avg, Max, Min, QuerySet
from django.utils import timezone

from .models import Property, Lead, Appointment

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
    r"time|date|day|today|tomorrow|yesterday|"
    r"jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
    r"aug|august|sep|sept|september|oct|october|nov|november|dec|december|"
    r"\d{1,2}\s*(?:/|-)\s*\d{1,2}(?:\s*(?:/|-)\s*\d{2,4})?"
    r")\b",
    re.IGNORECASE,
)

PROPERTY_TYPES = {"apartment", "house", "villa", "plot", "commercial", "office", "shop", "farmland"}
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

    def _now_context(self) -> Tuple[str, str, str, str]:
        now = timezone.localtime(timezone.now())
        tz_name = now.strftime("%Z") or "IST"
        return (
            f"{now.strftime('%A, %d %B %Y, %I:%M %p')} {tz_name}",
            now.strftime("%A"),
            now.strftime("%d %B %Y"),
            now.strftime("%I:%M %p"),
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
            city = city_match.group(1).strip().title()
            # Handle abbreviations
            abbreviations = {
                "Blr": "Bangalore",
                "Mumbai": "Mumbai",
                "Delhi": "Delhi",
                "Pune": "Pune",
                "Chennai": "Chennai",
                "Kolkata": "Kolkata",
                "Hyderabad": "Hyderabad",
                "Noida": "Noida",
                "Gurgaon": "Gurgaon",
                "Ahmedabad": "Ahmedabad",
                "Whitefield": "Whitefield",
                "Manyata": "Manyata",
            }
            out["location"] = abbreviations.get(city, city)
        elif re.match(r"^\s*[A-Za-z][A-Za-z\s]{2,30}\s*$", text) and " " not in text.strip() and not GREETING_RE.match(text) and not GOODBYE_RE.match(text):
            city = text.strip().title()
            abbreviations = {
                "Blr": "Bangalore",
                "Mumbai": "Mumbai",
                "Delhi": "Delhi",
                "Pune": "Pune",
                "Chennai": "Chennai",
                "Kolkata": "Kolkata",
                "Hyderabad": "Hyderabad",
                "Noida": "Noida",
                "Gurgaon": "Gurgaon",
                "Ahmedabad": "Ahmedabad",
            }
            out["location"] = abbreviations.get(city, city)

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
        """Handle common FAQs automatically"""
        text = (message or "").strip().lower()
        
        faqs = {
            "how to buy": "To buy a property on LuxeEstate: 1) Search for properties, 2) Contact the agent, 3) Schedule site visits, 4) Make an offer, 5) Complete legal paperwork. I can help with steps 1-3!",
            "how to sell": "To sell your property: 1) Create a listing with photos and details, 2) Set competitive pricing, 3) Respond to inquiries, 4) Show the property, 5) Negotiate and close. Contact our team for professional assistance.",
            "pricing": "Property prices vary by location, type, and condition. I can show you current market rates and help find properties within your budget.",
            "loan": "For home loans, I recommend consulting licensed banks or NBFCs. They offer various schemes for different buyer types. I can help you find properties that fit common loan amounts.",
            "legal": "All LuxeEstate transactions involve proper legal documentation. We ensure clear titles and transparent processes. For specific legal advice, consult a qualified lawyer.",
            "commission": "Agent commissions vary but typically range from 1-2% of the property value. LuxeEstate ensures transparent fee structures.",
            "verification": "We verify all property documents and agent credentials. Every listing goes through our quality check process.",
            "support": "I'm here 24/7 to help with property searches, lead qualification, and appointment scheduling. For complex issues, I can connect you with human experts.",            # Legal & Verification
            "rera": "RERA registration ensures project transparency. Check the RERA website or ask the developer for the registration number. All LuxeEstate projects are RERA compliant.",
            "documents": "Key documents to verify: Sale deed, title deed, encumbrance certificate, property tax receipts, and NOC from society/builder.",
            "oc/cc": "OC (Occupation Certificate) allows legal occupation. CC (Completion Certificate) confirms construction completion. Always verify these before booking.",
            "freehold": "Freehold means you own the land and building. Leasehold means ownership for a fixed period. Freehold is generally preferred for long-term investment.",
            "encumbrance": "An encumbrance-free property has no legal claims, liens, or disputes. Always get an encumbrance certificate from the sub-registrar.",
            "sale agreement": "Sale agreement is a contract outlining terms. Sale deed is the final transfer document registered with the government.",
            "home loan pre-approval": "Pre-approval gives you a clear budget and strengthens your offer. It shows sellers you're a serious buyer.",
            "taxes": "Stamp duty and registration charges vary by state (typically 5-8%). Property tax is annual, based on property value.",
            # Location & Lifestyle
            "best areas": "I can help identify family-friendly areas based on schools, hospitals, and connectivity. Share your city and preferences for specific recommendations.",
            "metro": "Properties near metro stations offer excellent connectivity. I can show listings within 1-2 km of metro lines in major cities.",
            "schools": "I can find properties near top-rated schools. Popular areas include [city-specific recommendations].",
            "hospitals": "Medical facilities are crucial. I can locate properties near reputed hospitals and healthcare centers.",
            "traffic": "Low-traffic areas typically have good infrastructure. I can suggest localities with efficient public transport and road networks.",
            "it parks": "Tech hubs offer convenience for working professionals. I can show properties near major IT parks and business districts.",
            "long-term living": "Consider factors like infrastructure, amenities, future development, and community. I can provide insights on specific localities.",
            "amenities": "Nearby amenities include schools, hospitals, malls, parks, and transport. I can check proximity for specific properties.",
            "safe neighborhoods": "Safety is paramount. I can recommend areas with good security, lighting, and community watch programs.",
            "lifestyle comparison": "I can compare localities based on cost of living, connectivity, amenities, and growth potential.",
            # Investment
            "good investment": "Look for properties in growing areas with good rental demand. I can analyze potential ROI based on location and type.",
            "rental yield": "Rental yield varies by location (typically 3-6%). I can estimate based on current market rates.",
            "appreciation": "Areas with infrastructure development show higher appreciation. I can share historical trends for specific localities.",
            "buy now or wait": "Market timing depends on economic conditions. Generally, buying in a stable market is advisable. I can provide current market insights.",
            "roi comparison": "2BHK vs 3BHK ROI depends on rental rates and capital appreciation. I can compare based on current data.",
            "maintenance costs": "Budget 0.5-1% of property value annually for maintenance, depending on property age and type.",        }
        
        for keyword, response in faqs.items():
            if keyword in text:
                return response
        
        # Handle budget queries
        budget_response = self._handle_budget_queries(message)
        if budget_response:
            return budget_response
        
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

    def _save_lead(self, lead: Dict[str, str], session_id: Optional[str] = None):
        """Stub method for saving leads - not implemented"""
        return None

    def _save_appointment(self, lead, appointment: Dict[str, Any]):
        """Stub method for saving appointments - not implemented"""
        return None

    def _assign_agent_to_hot_lead(self, lead):
        """Stub method for assigning agents - not implemented"""
        pass

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
        if intent == "greeting":
            return "Hello! I am Luxe AI Concierge. Are you looking to buy, rent, or invest today?", "", asked_fields
        
        if intent == "goodbye":
            return "Thanks for chatting with LuxeEstate. I am here whenever you need property help.", "", asked_fields
        
        if intent == "appointment" or appointment.get("requested"):
            return self._deterministic_reply(raw, intent, lead, criteria, appointment), "", asked_fields

        if intent == "intent_change":
            return f"I understand you've changed your mind. Let's focus on {lead.get('intent', 'your property needs')}. What specific requirements do you have?", "", asked_fields
        
        if intent == "preference":
            return f"Noted! I'll remember your preferences for future recommendations. {self._listing_snapshot(lead, criteria)[0]}", "", asked_fields
        
        if intent == "explanation":
            return "I recommend properties based on your specified criteria (location, budget, type, etc.) and current market availability. All listings are live and verified.", "", asked_fields
        
        if intent == "data_freshness":
            now_text, day_name, date_text, time_text = self._now_context()
            return f"All property data is current as of {date_text} at {time_text}. Listings are updated in real-time from our database.", "", asked_fields

        if intent == "unknown":
            # Check for common FAQs
            faq_response = self._handle_faq(raw)
            if faq_response:
                return faq_response
            return self.handle_fallback(intent, raw), "", asked_fields

        try:
            message, model = self._nim_reply(raw, history, lead, criteria)
        except Exception as exc:
            logger.info("NVIDIA NIM unavailable, using deterministic fallback: %s", exc)
            message = self._deterministic_reply(raw, intent, lead, criteria, appointment)
            model = ""

        if next_question and intent in {"unknown", "inquiry", "buy", "rent", "invest"}:
            prompts = {
                "intent": "Are you looking to buy, rent, or invest in a property?",
                "location": "Which city or locality do you prefer?",
                "property_type": "Which property type should I look for (apartment, villa, plot, office, etc.)?",
                "budget": "What budget range should I target?",
                "name": "May I have your name so our LuxeEstate team can follow up?",
                "contact": "Please share your phone number or email for follow-up.",
            }
            if next_question not in asked_fields:
                followup = prompts.get(next_question, "")
                if followup:
                    message = f"{message} {followup}".strip()
                    asked_fields.add(next_question)
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
        """Send automated follow-ups for leads and appointments (to be called by management command)"""
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
        
        # Follow up on cold leads after 7 days
        cold_leads = Lead.objects.filter(
            qualification_stage='cold',
            created_at__lte=now - timezone.timedelta(days=7),
            status='new'
        )
        
        for lead in cold_leads:
            # TODO: Send follow-up message via email/SMS
            logger.info(f"Follow-up needed for cold lead {lead.id}")
        
        # Escalate hot leads without appointments after 24 hours
        hot_leads_no_appointment = Lead.objects.filter(
            qualification_stage='hot',
            created_at__lte=now - timezone.timedelta(hours=24),
            status='qualified'
        ).exclude(appointments__isnull=False)
        
        for lead in hot_leads_no_appointment:
            # TODO: Escalate to human agent or send urgent follow-up
            logger.info(f"Hot lead {lead.id} needs urgent follow-up")

    def _query_from_lead(self, lead: Dict[str, str], criteria: Dict[str, Any]) -> QuerySet:
        qs = Property.objects.filter(is_active=True, status="available")
        location = (criteria.get("location") or criteria.get("city") or lead.get("location") or "").strip()
        if location:
            qs = qs.filter(city__icontains=location)
        ptype = (criteria.get("property_type") or lead.get("property_type") or "").strip().lower()
        normalized_type = self._normalize_property_type(ptype)
        if normalized_type:
            qs = qs.filter(property_type=normalized_type)
        bhk_text = (criteria.get("bhk") or lead.get("bhk") or "").strip().lower()
        bhk_num = re.search(r"(\d+)", bhk_text)
        if bhk_num:
            qs = qs.filter(bedrooms=int(bhk_num.group(1)))

        budget_rupees = self._budget_to_rupees(criteria.get("budget") or lead.get("budget") or "")
        if budget_rupees:
            qs = qs.filter(price__lte=budget_rupees)

        # Additional filters
        if lead.get("ready_to_move") == "yes":
            qs = qs.filter(possession_status="ready")
        if lead.get("furnished"):
            qs = qs.filter(furnishing__icontains=lead["furnished"])
        if lead.get("facing"):
            qs = qs.filter(facing__icontains=lead["facing"].split()[0])  # e.g., east from east-facing
        if lead.get("amenities"):
            amenities_list = [a.strip() for a in lead["amenities"].split(",")]
            for amenity in amenities_list:
                qs = qs.filter(amenities__icontains=amenity)
        if lead.get("posted_within_days"):
            days = int(lead["posted_within_days"])
            qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))
        if lead.get("min_area_sqft"):
            sqft = int(lead["min_area_sqft"])
            qs = qs.filter(area__gte=sqft)

        return qs

    def _calculate_emi(self, principal: Decimal, interest_rate: Decimal, tenure_years: int) -> Decimal:
        """Calculate monthly EMI using standard formula"""
        monthly_rate = interest_rate / 12 / 100
        months = tenure_years * 12
        if monthly_rate == 0:
            return principal / months
        emi = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
        return emi.quantize(Decimal('0.01'))

    def _estimate_rental_yield(self, property_price: Decimal, monthly_rent: Decimal) -> Decimal:
        """Estimate annual rental yield"""
        if property_price == 0:
            return Decimal('0')
        return (monthly_rent * 12 / property_price * 100).quantize(Decimal('0.01'))

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
        
        # Rental yield
        yield_match = re.search(r"rental yield in ([A-Za-z\s]+)", text, re.IGNORECASE)
        if yield_match:
            locality = yield_match.group(1).strip()
            # Mock data - in real implementation, fetch from database
            avg_yield = Decimal('4.5')  # Example
            return f"Average rental yield in {locality.title()} is around {avg_yield}%. This can vary based on property type and condition."
        
        # Price trends
        trend_match = re.search(r"price trend in ([A-Za-z\s]+)", text, re.IGNORECASE)
        if trend_match:
            locality = trend_match.group(1).strip()
            # Mock data
            trend = "increased by 8-12% in the last year"
            return f"Property prices in {locality.title()} have {trend}. For the most accurate data, I recommend checking recent transactions."
        
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
        if GREETING_RE.match(user_message):
            return "Hello! I am Luxe AI Concierge. Are you looking to buy, rent, or invest today?"
        if GOODBYE_RE.match(user_message):
            return "Thanks for chatting with LuxeEstate. I am here whenever you need property help."
        if appointment.get("requested"):
            has_when = bool((appointment.get("preferred_datetime") or "").strip())
            has_contact = bool((lead.get("contact") or "").strip())
            if has_when and has_contact:
                return (
                    f"Perfect! Your site-visit appointment is scheduled for {appointment.get('preferred_datetime')}. "
                    f"Our LuxeEstate team will contact you at {lead.get('contact')} to confirm the details. "
                    f"You'll receive a confirmation message shortly."
                )
            if not has_when and not has_contact:
                return "Great, I can help schedule a site visit. Please share your preferred date/time and contact number."
            if not has_when:
                return "Please share your preferred date and time for the site visit."
            return "Please share your contact number or email so we can confirm the site visit."
        if DATETIME_HINT_RE.search(user_message):
            relative_reply = self._relative_date_reply(user_message)
            if relative_reply:
                return relative_reply
            now_text, day_name, date_text, time_text = self._now_context()
            return f"Current time is {time_text} on {day_name}, {date_text}. ({now_text})"

        listing_text, info = self._listing_snapshot(lead, criteria)
        if info.get("count", 0) == 0:
            return "I could not find active listings for these filters. Share city, budget, or property type and I will broaden the search."
        if intent in {"buy", "rent", "invest", "inquiry"}:
            if info.get("count", 0) == 0:
                return (
                    "I couldn't find active listings matching your exact criteria. "
                    "Would you like me to:\n"
                    "• Broaden your search (remove some filters)\n"
                    "• Show similar properties in nearby areas\n"
                    "• Connect you with a property specialist\n"
                    "Just let me know how you'd like to proceed!"
                )
            else:
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
        api_key = (getattr(settings, "NVIDIA_API_KEY", None) or "").strip()
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY is not configured")
        try:
            import requests
            client = requests.Session()
            base_url = "https://integrate.api.nvidia.com/v1"
        except ImportError as exc:
            raise RuntimeError("Requests library is not installed. Run: pip install requests") from exc

        model = getattr(settings, "NIM_CHAT_MODEL", "gpt-4o-mini").strip()
        listing_text, _ = self._listing_snapshot(lead, criteria)
        now_text, day_name, date_text, time_text = self._now_context()

        system = (
            "You are LuxeEstate's real estate chatbot assistant. "
            "Respond only with property-related guidance, lead qualification, appointment scheduling, "
            "and search recommendations for LuxeEstate. "
            "Do not provide general knowledge, do not discuss unrelated topics, "
            "and do not fabricate property details.\n"
            f"Current date: {date_text}\n"
            f"Current day: {day_name}\n"
            f"Current time: {time_text}\n"
            f"Live listing snapshot:\n{listing_text}\n"
            f"Lead data: {lead}\n"
            "Handle advanced queries: EMI calculations, investment analysis, legal questions, location insights.\n"
            "Support abbreviations (Blr=Bangalore, 2BHK=2 BHK), handle preference changes, remember user preferences.\n"
            "For edge cases: If user changes mind (e.g., 'actually I want to buy'), acknowledge and adjust search.\n"
            "If user asks 'why this listing', explain based on criteria match.\n"
            "If user says 'connect to human', escalate politely.\n"
            "If user asks about data freshness, confirm current date and that listings are live.\n"
            "If the user asks off-topic or abusive questions, politely redirect to LuxeEstate real estate support."
        )

        messages = [{"role": "system", "content": system}]
        for turn in history[-self.MAX_HISTORY_MESSAGES :]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        try:
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 300,
                "n": 1,
            }
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise Exception(f"NVIDIA API error: {resp.text}")
            data = resp.json()
        except Exception as exc:
            raise RuntimeError("NVIDIA chat completion failed") from exc

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("NVIDIA returned no completion")
        text = (choices[0].get("message", {}).get("content") or "").strip()
        if not text:
            raise RuntimeError("empty completion")
        return text, model

    def detect_intent(self, message: str) -> str:
        text = (message or "").strip()
        lower = text.lower()
        if not text:
            return "unknown"
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

        if SECURITY_RE.search(raw):
            message = "I can only help with safe LuxeEstate property assistance and cannot process sensitive or unsafe requests."
            intent = "security"
            security_flagged = True
        elif HUMAN_RE.search(raw):
            message = "I am routing this to a LuxeEstate human agent. Please share contact details and our team will reach out."
            intent = "handoff"
            requires_human = True
            handoff_reason = "User requested human escalation"
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
        
        if lead and any(lead.values()):  # Only save if lead has some data
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
            "model": model if "model" in locals() else "",
            "chat_history": history,
            "search_criteria": criteria,
            "current_datetime": now_text,
            "current_day": day_name,
            "current_date": date_text,
            "current_time": time_text,
            "guidelines": [
                "Only discuss LuxeEstate property-related topics.",
                "Use live listing context and avoid fabricated availability.",
                "Collect lead details progressively and politely.",
                "Escalate sensitive/legal/complaint requests to a human agent.",
            ],
            "out_of_scope": intent == "unknown",
            "security_flagged": security_flagged,
            "handoff": requires_human,
            "qualified_lead": len(missing_fields) == 0,
            "just_qualified": previous_missing > 0 and len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "next_question_field": next_question,
            "asked_fields": sorted(list(asked_fields)),
            "last_question_field": next_question if next_question else "",
        })
        return result


chatbot = LuxeChatbot()

