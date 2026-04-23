<div align="center">

<br/>

```
██╗     ██╗   ██╗██╗  ██╗███████╗    ███████╗███████╗████████╗ █████╗ ████████╗███████╗
██║     ██║   ██║╚██╗██╔╝██╔════╝    ██╔════╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██╔════╝
██║     ██║   ██║ ╚███╔╝ █████╗      █████╗  ███████╗   ██║   ███████║   ██║   █████╗  
██║     ██║   ██║ ██╔██╗ ██╔══╝      ██╔══╝  ╚════██║   ██║   ██╔══██║   ██║   ██╔══╝  
███████╗╚██████╔╝██╔╝ ██╗███████╗    ███████╗███████║   ██║   ██║  ██║   ██║   ███████╗
╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚══════╝
```

### 🏡 *Discover. Compare. Own. Powered by AI.*

<p>
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-6.0.3-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Django_Channels-ASGI_WebSocket-E95420?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/NVIDIA_NIM-Llama_3.1_+_NeVA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" />
  <img src="https://img.shields.io/badge/Razorpay-Payments-02042B?style=for-the-badge&logo=razorpay&logoColor=white" />
  <img src="https://img.shields.io/badge/Google_OAuth-2.0-4285F4?style=for-the-badge&logo=google&logoColor=white" />
</p>

<p>
  <img src="https://img.shields.io/badge/License-MIT-gold?style=flat-square" />
  <img src="https://img.shields.io/badge/Made%20with-❤️-red?style=flat-square" />
  <img src="https://img.shields.io/badge/Ahmedabad-🇮🇳-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=flat-square" />
</p>

<br/>

> *"Real estate is the best investment in the world because it is the only thing they're not making anymore."*
> — Jainam Shah
>
> **LuxeEstate** doesn't just list properties — it understands them. Upload a photo, describe your dream home in plain English, or let our AI read your browsing history to surface exactly what you need next.

<br/>

---

</div>

## 🧠 What is LuxeEstate?

**LuxeEstate** is a full-stack, AI-augmented real estate platform that combines the engineering rigor of a Django 6 monolith with the intelligence of NVIDIA NIM (Llama 3.1 + NeVA-22B vision). It is far more than a property directory:

- 🔍 **Find homes by photo** — upload an image, extract visual features, match against every listing in the database with a weighted scoring algorithm
- 💬 **Ask in plain English** — our Llama-powered chatbot converts natural-language queries into structured filters and surfaces matching properties
- 📊 **Understand the market** — auto-generated comparable pricing and trend summaries per city and property type
- 🏆 **Promote listings** — Razorpay-backed premium packages push listings to featured slots for 7 to 90 days, with atomic transactions and auto-generated invoices
- 📡 **Chat in real time** — Django Channels WebSocket keeps buyers and agents connected without page refreshes
- 🔐 **Stay secure** — Google OAuth 2.0, OTP email verification, role-based access, and `select_for_update()` payment guards

---

## 🎬 Feature Gallery

<div align="center">

| 🖼️ Visual Image Search | 🤖 AI Chatbot | 📊 Market Intelligence | ⚖️ Property Comparison |
|:---:|:---:|:---:|:---:|
| Upload photo → weighted feature match | Llama 3.1 with guardrails + lead capture | Comparable pricing + trend signal | Side-by-side amenity + POI diff |

| 💬 Real-Time Chat | 💳 Premium Packages | 🗺️ Maps + 18 POI Types | 👤 Role System |
|:---:|:---:|:---:|:---:|
| WebSocket · Channels · Redis | Razorpay · 7/14/30/90 days | Google Maps + OpenStreetMap | buyer · owner · agent · admin |

</div>

---

## 🌊 System Architecture


<div align="center">
  <h1>🏰 LuxeEstate Platform Architecture</h1>
  <p><i>A high-end, AI-powered real estate solution built with Django, NVIDIA NIM, and Google APIs.</i></p>

  <!-- Replace 'YOUR_IMAGE_URL' with the link to the final image I generated for you -->
  <img src="https://lens.usercontent.google.com/banana?agsi=CmdnbG9iYWw6OjAwMDA1NWNmZWM3MDAyNmQ6MDAwMDAwZWI6MToxOWVjZDE1MjM0MWFjOWJjOjAwMDA1NWNmZWM3MDAyNmQ6MDAwMDAxODdhNjIwMzM2ODowMDA2NTAxY2I3YTI5NTJmEAIYAQ==" alt="LuxeEstate Architecture Diagram" width="900px">
</div>

---

## 🛠️ Technical Architecture

LuxeEstate is built on a modern, asynchronous architecture designed for real-time engagement and high-performance AI processing.

### **Frontend & Client**
- **Framework:** Responsive UI built with [Bootstrap 5](https://getbootstrap.com).
- **Dynamic Inputs:** Styled with [Django Crispy Forms](https://readthedocs.io).
- **Maps Integration:** [Google Maps JS SDK](https://google.com) & [Places API](https://google.com) for 18-category POI discovery.

### **Backend Core**
- **Server:** [Daphne ASGI](https://github.com) for production-grade HTTP and WebSocket handling.
- **Framework:** [Django](https://djangoproject.com) with 6 dedicated app namespaces (Accounts, Properties, Messaging, etc.).
- **Real-time:** [Django Channels](https://readthedocs.io) with a Redis channel layer for instant messaging.

### **Data & Intelligence**
- **Persistence:** [PostgreSQL](https://postgresql.org) (Production) and SQLite (Development).
- **AI Stack:** Integration with [NVIDIA NIM](https://nvidia.com) for Llama 3.1 LLM and NeVA-22B visual matching.
- **Payments:** Secure transaction processing via [Razorpay SDK](https://razorpay.com) with webhook validation.




## ✨ Key Features

### 🏠 Property Listings — Every Type, Every Detail

| Property Types | Status Options | Furnishing |
|---|---|---|
| Apartment · House · Villa · Plot | Available / Sold / Rented | Unfurnished / Semi-Furnished / Furnished |
| Commercial · Office · Shop · Farmland | — | — |

Each listing stores bedrooms, bathrooms, area (sqft), price, lat/lng, pincode, amenities (JSONField), and a full **18-category nearby POI catalogue** — hospitals, schools, metro stations, banks, ATMs, pharmacies, gyms, parks, restaurants, and more — sourced via Google Places API.

---

### 🤖 AI & Intelligence Layer

LuxeEstate ships **five production AI engines**, all backed by NVIDIA NIM — no local GPU required.

```
AI Engine Inventory:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. LuxeChatbot                → Llama 3.1 8B · scoped guardrails · lead capture
  2. ImageFeatureDetector       → avg-hash · edge-density · colour histogram
  3. VisualPropertySearchEngine → Feature-weighted cosine match (premium: 1.5×)
  4. PropertyRecommendationEngine → TF-IDF + view history + budget signal scoring
  5. MarketAnalysisEngine       → Comparable pricing + above/below market signal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### Visual Feature Detection — Amenity Weights

| Feature | Search Weight | Category |
|---|---|---|
| Swimming Pool | **1.5×** | Premium |
| Garden | **1.5×** | Premium |
| Gym | **1.5×** | Premium |
| Modular / Open / Closed Kitchen | 1.0× | Standard |
| Bedroom · Bathroom · Living Room | 1.0× | Standard |
| Balcony · Terrace · Parking Space | 1.0× | Standard |

> Partial credit (0.75×) is awarded for semantically compatible variants — e.g. "open kitchen" satisfies a "kitchen" query via `FEATURE_COMPATIBILITY_GROUPS`.

#### TF-IDF Recommendation Signals

```
Signals consumed by PropertyRecommendationEngine.get_recommendations():
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  UserPropertyView (last 35 views)   → location + type affinity
  Profile.favorite_cities             → city boost score
  Profile.preferred_property_type     → type match boost
  Median viewed price ± 35% spread    → budget window + distance score
  TF-IDF on title + description       → content similarity vector
  + city + property_type + ai_tags
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 🔐 Authentication & Security

| Mechanism | Implementation |
|---|---|
| Email / Password | `allauth` — email as auth identifier, no separate username field |
| Google OAuth 2.0 | `allauth.socialaccount.providers.google` + custom `SocialAccountAdapter` |
| OTP Email Verification | 6-digit OTP on `Profile`, configurable max attempts / cooldown / expiry |
| Role-Based Access | `buyer` · `owner` · `agent` · `admin` enforced at view layer |
| HMAC Payment Verification | Razorpay HMAC-SHA256 signature verified server-side before fulfilment |
| Atomic Transactions | `select_for_update()` on payment rows — prevents double-credit |
| CORS | `corsheaders` middleware with `CORS_ALLOWED_ORIGINS` whitelist |
| SMTP Hardening | Custom backend uses Certifi CA bundle; insecure-skip-verify gated to dev |
| IP Tracking | `last_login_ip` persisted on `Profile` for audit trails |
| Zero Hardcoded Secrets | All credentials via `python-decouple` + `.env` |

---

### 💳 Payments — Razorpay Integration

```
User picks a package (7 / 14 / 30 / 90 days)
      │
      ▼
Django creates Razorpay order (server-side SDK, amount in paise)
      │
      ▼
Razorpay JS Checkout (UPI / Card / Netbanking / Wallet)
      │
      ▼
Browser posts { payment_id · order_id · signature } → verify endpoint
      │
      ▼
Django HMAC-SHA256 verification via RAZORPAY_WEBHOOK_SECRET
      │
      ├─ ✅ SUCCESS
      │     → select_for_update() payment row (atomic)
      │     → Payment.mark_completed()
      │     → Invoice auto-generated  (INV-YYYYMMDD-{id})
      │     → Property.is_featured = True, featured_until = now + N days
      │     → PaymentAuditLog entry written
      │
      └─ ❌ FAILURE → status = 'failed' · audit log · user redirected
            │
      ▼
Razorpay Webhook (server-to-server) → idempotent secondary confirmation
```

| Package | Duration | Outcome |
|---|---|---|
| Starter | 7 days | Featured badge on listing card |
| Standard | 14 days | Featured badge + priority in search results |
| Premium | 30 days | Featured + priority + homepage slot |
| Elite | 90 days | All Premium benefits for three months |

---

### 📡 Real-Time Messaging (Django Channels)

```
Buyer opens property detail page
    │
    ▼
Conversation model created — unique_together (property, initiator, recipient)
    │
    ▼
WebSocket connection → Channels routing → InMemoryChannelLayer / Redis
    │
    ▼
Messages persisted to Message model (text · image · document)
    │
    ▼
is_read + read_at fields → unread badge counts
    │
    ▼
Full history available on reconnect (DB-backed, not ephemeral)
```

---

## 🛠️ Tech Stack

<div align="center">

### Backend & Framework
![Python](https://img.shields.io/badge/Python_3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django_6.0.3-092E20?style=for-the-badge&logo=django&logoColor=white)
![Daphne](https://img.shields.io/badge/Daphne-ASGI-E95420?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-red?style=for-the-badge&logo=django)
![Channels](https://img.shields.io/badge/Django_Channels-WebSocket-092E20?style=for-the-badge&logo=django)

### AI & Vision
![NVIDIA](https://img.shields.io/badge/NVIDIA_NIM-Llama_3.1_8B-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![NeVA](https://img.shields.io/badge/NVIDIA_NeVA--22B-Vision_AI-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![sklearn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-Image_Processing-3776AB?style=for-the-badge&logo=python&logoColor=white)

### Auth & Payments
![allauth](https://img.shields.io/badge/django--allauth-OAuth_+_OTP-092E20?style=for-the-badge&logo=django)
![Google](https://img.shields.io/badge/Google_OAuth_2.0-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Razorpay](https://img.shields.io/badge/Razorpay-02042B?style=for-the-badge&logo=razorpay&logoColor=white)

### Frontend & Static
![Bootstrap](https://img.shields.io/badge/Bootstrap_5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Google Maps](https://img.shields.io/badge/Google_Maps_JS-4285F4?style=for-the-badge&logo=googlemaps&logoColor=white)
![WhiteNoise](https://img.shields.io/badge/WhiteNoise-Static_Files-lightgrey?style=for-the-badge)

### Infrastructure
![Redis](https://img.shields.io/badge/Redis-Channel_Layer-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-Media_Storage-FF9900?style=for-the-badge&logo=amazons3&logoColor=white)

</div>

---

## 📁 Project Structure

```
LuxeEstate_updated/
│
├── 🔧 LuxeEstate/                     # Django project package
│   ├── settings.py                    # Centralised settings via python-decouple
│   ├── urls.py                        # Root URL dispatcher (8 app namespaces)
│   ├── asgi.py                        # ASGI entry — Daphne + Channels routing
│   ├── routing.py                     # WebSocket URL patterns
│   └── smtp_backend.py                # Hardened SMTP (Certifi CA bundle)
│
├── 👤 accounts/                       # Auth · profiles · OTP · roles
│   ├── models.py                      # Profile · UserPropertyView · SavedSearch
│   ├── views.py                       # Register · login · OTP verify · agent list
│   ├── forms.py                       # Registration + profile edit forms
│   ├── adapters.py                    # Custom allauth SocialAccountAdapter
│   ├── utils.py                       # OTP generation + throttle helpers
│   └── templatetags/social_helpers.py
│
├── 🏠 properties/                     # Core listing domain
│   ├── models.py                      # Property · PropertyImage · PropertyReview
│   ├── views.py                       # CRUD · search · compare · visual search
│   ├── ai_utils.py                    # 🧠 Five AI engines (58 KB)
│   │   ├── ImageFeatureDetector       #   avg-hash · edge-density · colour histogram
│   │   ├── VisualPropertySearchEngine #   weighted feature match + partial credit
│   │   ├── PropertyRecommendationEngine #  TF-IDF + view history + budget scoring
│   │   ├── MarketAnalysisEngine       #   comparable pricing + trend direction
│   │   ├── PropertyComparisonEngine   #   structured side-by-side diff
│   │   └── SearchSuggestionEngine     #   autocomplete from titles + ai_tags
│   ├── chatbot_service.py             # 🤖 LuxeChatbot — Llama 3.1 (46 KB)
│   │   ├── Guardrail system           #   scoped to listing data; refuses OTP/CVV asks
│   │   ├── Lead extraction            #   name · email · phone · budget · intent regex
│   │   └── Budget parser              #   "50 lakh" / "2 crore" → Decimal in ₹
│   ├── image_search_service.py        # 🖼️ NeVA-22B visual search (41 KB)
│   ├── location_utils.py              # OpenStreetMap / Nominatim geocoding wrapper
│   ├── payment_utils.py               # Promotion package application helpers
│   └── management/commands/
│       ├── analyze_images.py          # Seed ai_analysis on all PropertyImage rows
│       ├── geocode_properties.py      # Backfill lat/lng via Nominatim
│       └── send_followups.py          # Email follow-up sequences
│
├── ⭐ favorites/                      # Save / unsave (unique per user + property)
├── 💬 messaging/                      # Channels WebSocket + DB message persistence
├── 💳 payments/                       # Razorpay · packages · invoices · audit log
│   └── models.py                      # PaymentPackage · Payment · Subscription
│                                      # Invoice · PaymentAuditLog · PaymentWebhookEvent
├── 📊 admin_dashboard/                # Analytics: users · listings · revenue · roles
│
├── 📄 templates/                      # App-scoped Django HTML templates
├── 🎨 static/                         # CSS, JS, images
├── 📷 media/                          # User-uploaded files (dev local)
├── 📝 logs/django.log
│
├── 📐 docs/figures/
│   ├── fig_1_1_use_case_auth_listing.png
│   ├── fig_1_2_activity_property_search.png
│   ├── fig_1_3_use_case_chatbot_leads.png
│   ├── fig_1_4_activity_payment_messaging.png
│   └── fig_1_5_use_case_admin_analytics.png
│
├── manage.py
├── .env.example
└── .env                               # Local secrets — never committed
```

---

## 💻 Code Walkthrough

### 🖼️ Visual Property Search Engine

```python
# properties/ai_utils.py

class VisualPropertySearchEngine:
    """Match properties by visual amenity features extracted from a query image."""

    PREMIUM_FEATURES = {'swimming pool', 'garden', 'gym'}   # weight = 1.5×

    def rank_matches(self, query_features: list[str], properties) -> list[dict]:
        query_features = focus_visual_query_features(query_features)
        ranked = []

        for prop in properties:
            prop_features = self.extract_property_features(prop)   # from ai_analysis JSONField
            score, total_weight, matched = 0.0, 0.0, []

            for feature in query_features:
                weight = 1.5 if feature in self.PREMIUM_FEATURES else 1.0

                if feature in prop_features:
                    score += weight
                    matched.append(feature)
                elif FEATURE_COMPATIBILITY_GROUPS.get(feature, set()) & prop_features:
                    score += weight * 0.75          # partial credit for semantic relatives
                    matched.append(feature)

                total_weight += weight

            # Only rank if ALL query features are at least partially satisfied
            if matched and len(matched) == len(query_features):
                ranked.append({
                    'property_id': prop.id,
                    'score': round(score / max(total_weight, 1.0), 4),
                    'matched_features': sorted(matched),
                })

        return sorted(ranked, key=lambda x: x['score'], reverse=True)
```

---

### 🤖 AI Chatbot — Lead Extraction & Budget Parser

```python
# properties/chatbot_service.py

class LuxeChatbot:
    """Llama 3.1-powered assistant scoped strictly to LuxeEstate listing data."""

    def _budget_to_rupees(self, budget_text: str) -> Decimal | None:
        """Convert '50 lakh', '2 crore', '500k' → exact Decimal in ₹."""
        m = re.search(
            r"(\d+(?:\.\d+)?)\s*(lakh|lac|l|crore|cr|k|thousand|million|m)?",
            budget_text, re.IGNORECASE
        )
        if not m:
            return None
        value = Decimal(m.group(1))
        multipliers = {
            'k': 1_000,      'thousand': 1_000,
            'lakh': 100_000, 'lac': 100_000,   'l': 100_000,
            'crore': 10_000_000, 'cr': 10_000_000,
            'million': 1_000_000, 'm': 1_000_000,
        }
        return value * Decimal(str(multipliers.get((m.group(2) or '').lower(), 1)))

    def _extract_lead_fields(self, message: str) -> dict:
        """Extract name, contact, budget, and purchase intent from one message."""
        out = {}
        if name := re.search(
            r"\b(?:my name is|i am|i'm)\s+([A-Za-z][A-Za-z ]{1,40})\b",
            message, re.IGNORECASE
        ):
            out['name'] = name.group(1).strip().title()

        if email := re.search(r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}", message):
            out['contact'] = email.group(0)
        elif phone := re.search(r"(?:\+91|0)?\s*([1-9]\d{9})\b", message):
            out['contact'] = phone.group(1)

        if budget_text := self._extract_budget_text(message):
            out['budget'] = str(self._budget_to_rupees(budget_text))

        return out
```

---

### 💳 Razorpay — Atomic Payment Completion

```python
# payments/views.py

def _complete_payment_transaction(payment, *, razorpay_payment_id=None, razorpay_signature=None):
    """
    Atomically mark a payment completed and auto-generate the invoice.
    select_for_update() prevents double-credit in concurrent webhook + browser callbacks.
    """
    with transaction.atomic():
        locked = (
            Payment.objects
            .select_for_update()
            .select_related('package', 'property')
            .get(pk=payment.pk)
        )

        if razorpay_payment_id:
            locked.razorpay_payment_id = razorpay_payment_id
        if razorpay_signature:
            locked.razorpay_signature = razorpay_signature
        locked.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'updated_at'])

        if locked.status != 'completed':
            locked.mark_completed()         # sets is_featured=True + featured_until on Property
            locked.refresh_from_db()

        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{locked.id}"
        invoice, created = Invoice.objects.get_or_create(
            payment=locked,
            defaults={
                'invoice_number': invoice_number,
                'due_date': timezone.now() + timedelta(days=30),
                'subtotal': locked.amount,
                'total': locked.amount,
                'is_paid': True,
                'paid_at': timezone.now(),
            },
        )
        return locked, invoice, created
```

---

### 📈 TF-IDF Recommendation Engine

```python
# properties/ai_utils.py

class PropertyRecommendationEngine:
    """Personalised recommendations from view history + profile preferences."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')

    def get_user_preferences(self, user) -> dict:
        views = UserPropertyView.objects.filter(user=user).select_related('property')[:35]
        viewed_prices = [float(v.property.price) for v in views if v.property.price]
        location_history = [v.property.city.lower().strip() for v in views if v.property.city]

        if viewed_prices:
            median_price = float(np.median(np.array(viewed_prices)))
            spread = max(median_price * 0.35, 1_000_000)
        else:
            median_price, spread = None, 0

        return {
            'favorite_cities': user.profile.favorite_cities.split(',') if
                               user.profile.favorite_cities else [],
            'preferred_type':  user.profile.preferred_property_type,
            'location_history': location_history,
            'median_viewed_price': median_price,
            'price_range': {
                'min': max(0.0, median_price - spread),
                'max': median_price + spread,
            } if median_price else {'min': 0, 'max': float('inf')},
        }

    def _budget_score(self, pref_price: float, prop_price: float) -> float:
        """Return 0.0–1.0 based on distance from user's median viewed price."""
        if not pref_price or not prop_price:
            return 0.4
        return max(1.0 - min(abs(prop_price - pref_price) / max(pref_price, 1), 1.0), 0.0)
```

---

## 🗃️ Data Models

```
accounts_profile
  ├── user (OneToOne → auth.User)
  ├── role [buyer | owner | agent | admin]
  ├── otp_code · otp_created_at · email_verified
  ├── google_id · is_google_account
  ├── favorite_cities (comma-separated) · preferred_property_type
  ├── rating (0–5) · total_reviews
  └── last_login_ip · created_at · updated_at

properties_property
  ├── title · description · price · property_type · status · furnishing
  ├── city · state · address · pincode · latitude · longitude
  ├── bedrooms · bathrooms · area_sqft
  ├── amenities (JSONField)
  ├── nearby_* × 18 POI categories (each a JSONField list)
  ├── views_count (db_index) · rating · total_reviews
  ├── is_featured · featured_until · promotion_package (FK)
  └── agent (FK → auth.User)

properties_propertyimage
  ├── property (FK) · image · is_primary
  └── ai_analysis (JSONField)         ← populated by manage.py analyze_images

messaging_conversation
  ├── property (FK) · initiator (FK) · recipient (FK)
  └── unique_together: (property, initiator, recipient)

messaging_message
  ├── conversation (FK) · sender · recipient · message
  ├── is_read · read_at
  └── message_type [text | image | document]

payments_payment
  ├── user · package (FK) · property (FK)
  ├── amount · razorpay_order_id (unique) · razorpay_payment_id (unique)
  ├── razorpay_signature · status [pending | completed | failed | cancelled | refunded]
  └── related: PaymentAuditLog · Invoice · Subscription · PaymentWebhookEvent
```

---

## 📱 Interface Walkthrough

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/3ceb1bde-94da-42ff-bf22-3d8692f883b9" />

---


---
PROPERTY DETAIL PAGE
---


<img width="1920" height="1080" alt="Screenshot (296)" src="https://github.com/user-attachments/assets/7453c7b9-0503-4a5f-91f8-bc8ff2405e70" />

---
<img width="1920" height="1080" alt="Screenshot (297)" src="https://github.com/user-attachments/assets/45967df2-77ce-4f4c-a911-ee94f0e44fbc" />


```

## 🗺️ Roadmap

| Feature | Status |
|---|---|
| Core listing CRUD with multi-image upload | ✅ Complete |
| Google OAuth 2.0 + OTP email verification | ✅ Complete |
| AI chatbot — Llama 3.1 via NVIDIA NIM | ✅ Complete |
| Visual image-to-listing search via NeVA-22B | ✅ Complete |
| TF-IDF property recommendations | ✅ Complete |
| Market comparable analysis | ✅ Complete |
| Razorpay premium packages + invoicing | ✅ Complete |
| Django Channels real-time WebSocket messaging | ✅ Complete |
| Side-by-side property comparison | ✅ Complete |
| 18-category nearby POI via Google Places | ✅ Complete |
| Admin analytics dashboard | ✅ Complete |
| UML documentation (5 diagrams) | ✅ Complete |
| PostgreSQL + Redis production configuration | ✅ Ready |
| AWS S3 media storage configuration | ✅ Ready |
| Celery async task queue | 🚧 In Progress |
| Property price prediction ML model | 📋 Planned |
| Mobile app (React Native) | 📋 Planned |
| Saved search email alert digests | 📋 Planned |
| Multi-city geo-clustering recommendations | 📋 Planned |

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version |
|---|---|
| Python | ≥ 3.11 |
| pip | ≥ 23.x |
| Redis | Only needed for multi-worker WebSocket in production |

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-org/LuxeEstate.git
cd LuxeEstate/LuxeEstate_updated
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment

```bash
cp .env.example .env
# Fill in the values from the Environment Reference table below
```

> **Minimum required:** only `SECRET_KEY`. All external services degrade gracefully — AI returns empty results, payments use test mode, emails print to console.

### 5️⃣ Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6️⃣ Register Google Social App (Optional)

```bash
python create_social_app.py
# Reads GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET from .env
```

### 7️⃣ Seed AI Image Analysis (Optional)

```bash
python manage.py analyze_images
# Runs NVIDIA NeVA-22B against all PropertyImage rows → stores ai_analysis JSONField
```

### 8️⃣ Backfill Geocoordinates (Optional)

```bash
python manage.py geocode_properties
# Nominatim lookup for any Property missing latitude/longitude
```

### 9️⃣ Run the Development Server

```bash
python manage.py runserver
```

> 🌐 Open `http://localhost:8000`

---

## ⚙️ Environment Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Django secret key |
| `DEBUG` | | `True` | Set `False` in production |
| `ALLOWED_HOSTS` | | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DB_ENGINE` | | `sqlite3` | `django.db.backends.postgresql` for Postgres |
| `DB_NAME` | | `db.sqlite3` | Database name or file path |
| `EMAIL_HOST_USER` | | `""` | SMTP sender — blank → OTPs print to console |
| `EMAIL_HOST_PASSWORD` | | `""` | SMTP app password |
| `GOOGLE_OAUTH_CLIENT_ID` | | `""` | Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | | `""` | Google OAuth client secret |
| `GOOGLE_MAPS_API_KEY` | | `""` | Google Maps JS API (map embeds) |
| `GOOGLE_PLACES_API_KEY` | | `""` | Google Places API (nearby POI) |
| `RAZORPAY_KEY_ID` | | `""` | Razorpay publishable key |
| `RAZORPAY_KEY_SECRET` | | `""` | Razorpay secret key |
| `RAZORPAY_WEBHOOK_SECRET` | | `""` | HMAC webhook verification secret |
| `NIM_API_KEY` | | `""` | NVIDIA NIM API key (all AI features) |
| `NVIDIA_MODEL` | | `meta/llama-3.1-8b-instruct` | NIM chat model |
| `NVIDIA_VISION_MODEL` | | `nvidia/neva-22b` | NIM vision model |
| `CHANNEL_LAYERS_HOST` | | `""` | Redis host — blank → InMemoryChannelLayer |
| `CHANNEL_LAYERS_PORT` | | `6379` | Redis port |
| `SITE_URL` | | `http://localhost:8000` | Base URL for email links |
| `SECURE_SSL_REDIRECT` | | `False` | `True` behind HTTPS in production |
| `OTP_VERIFY_MAX_ATTEMPTS` | | `5` | Max OTP attempts per window |
| `OTP_VERIFY_WINDOW_SECONDS` | | `600` | OTP validity window in seconds |
| `OTP_RESEND_COOLDOWN_SECONDS` | | `60` | Min gap between OTP resend requests |
| `LOG_LEVEL` | | `INFO` | Python logging level |

---

## 🚢 Deployment

### Production Checklist

```
[ ] DEBUG=False
[ ] SECRET_KEY — long, random, unique string
[ ] ALLOWED_HOSTS — only your domain(s)
[ ] SECURE_SSL_REDIRECT=True           (behind HTTPS terminator)
[ ] SESSION_COOKIE_SECURE=True
[ ] CSRF_COOKIE_SECURE=True
[ ] SECURE_HSTS_SECONDS=31536000       (after confirming HTTPS is stable)
[ ] DB_ENGINE=django.db.backends.postgresql  (dedicated credentials)
[ ] CHANNEL_LAYERS_HOST=<redis-host>   (multi-worker WebSocket)
[ ] AWS_* vars configured              (media storage offloaded to S3)
[ ] python manage.py collectstatic --no-input
[ ] python manage.py migrate
[ ] Razorpay webhook URL registered in Razorpay dashboard
[ ] CORS_ALLOWED_ORIGINS locked to production frontend origins
```

### Recommended Production Stack

```
Nginx (TLS termination · static file serving via WhiteNoise / S3)
    └─► Daphne (ASGI — HTTP + WebSocket on a single port)
            └─► Django (6 app modules)
    ◄──────────► PostgreSQL    (primary database)
    ◄──────────► Redis         (channel layer + optional cache)
    ◄──────────► AWS S3        (media storage)
    ◄──────────► NVIDIA NIM    (AI inference — external REST API)
    ◄──────────► Razorpay      (payments — external REST API)
    ◄──────────► Google APIs   (OAuth 2.0 · Maps · Places)
```

---

## 🤝 Contributing

```bash
# Fork, then:
git checkout -b feature/your-feature
git commit -m 'feat: describe your change clearly'
git push origin feature/your-feature
# Open a Pull Request against main
```

- Follow Django conventions and PEP 8
- Add or update tests for any changed behaviour
- Never commit `.env` or credentials of any kind
- Report security vulnerabilities privately via email, not a public issue

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for full terms.

---

## 👨‍💻 Author

<div align="center">

**Built from Ahmedabad, India 🇮🇳**

[![GitHub](https://img.shields.io/badge/GitHub-Connect-181717?style=for-the-badge&logo=github)](https://github.com/jainam-shah-18)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/jainamshah41)


</div>

---

<div align="center">

**⭐ Star this repo if LuxeEstate impressed you! ⭐**

*Because every home deserves an intelligent search engine. 🏡*

*Built with Django 6 · Powered by NVIDIA NIM · Payments via Razorpay*

</div>
