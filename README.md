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

### *Redefining Real Estate Discovery — Intelligent. Immersive. Indispensable.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0.3-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Django Channels](https://img.shields.io/badge/Channels-WebSocket-E95420?style=for-the-badge&logo=django&logoColor=white)](https://channels.readthedocs.io)
[![Redis](https://img.shields.io/badge/Redis-Channel_Layer-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payments-02042B?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-AI_Engine-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![License](https://img.shields.io/badge/License-MIT-gold?style=for-the-badge)](LICENSE)

</div>

---

## What is LuxeEstate?

LuxeEstate is a **full-stack, AI-augmented real estate platform** built on Django 6 and served over ASGI with Django Channels. It goes far beyond a property listing board: buyers find homes through natural-language AI search, visual image matching, and a Llama-powered chatbot; sellers and agents promote listings via Razorpay-backed premium packages; and administrators govern the ecosystem through a purpose-built analytics dashboard. Every feature — from OTP-gated email verification to real-time WebSocket messaging — is wired together in a single, cohesive monolith with clean app separation.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Feature Matrix](#feature-matrix)
- [Tech Stack](#tech-stack)
- [Data Models](#data-models)
- [AI & Intelligence Layer](#ai--intelligence-layer)
- [Authentication & Security](#authentication--security)
- [Payments](#payments)
- [Real-Time Messaging](#real-time-messaging)
- [Getting Started](#getting-started)
- [Environment Reference](#environment-reference)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                             │
│          Bootstrap 5 · Crispy Forms · Google Maps JS SDK            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  HTTP / WebSocket
┌───────────────────────────────▼─────────────────────────────────────┐
│                     ASGI SERVER  (Daphne)                           │
│                                                                     │
│  ┌──────────────────────┐     ┌─────────────────────────────────┐  │
│  │  Django HTTP Router  │     │  Django Channels WebSocket      │  │
│  │  (6 apps + allauth)  │     │  (InMemory / Redis layer)       │  │
│  └──────────┬───────────┘     └────────────────┬────────────────┘  │
│             │                                  │                   │
│  ┌──────────▼───────────────────────────────────▼────────────────┐ │
│  │                    Django Application Core                    │ │
│  │  accounts · properties · favorites · messaging · payments     │ │
│  │  admin_dashboard                                              │ │
│  └──────────┬───────────────────────────────────────────────────┘ │
│             │                                                      │
│  ┌──────────▼──────────┐  ┌──────────────────┐  ┌─────────────┐  │
│  │   SQLite / Postgres  │  │   NVIDIA NIM API  │  │  Razorpay   │  │
│  │   (ORM via Django)   │  │  Llama 3.1 · NeVA │  │  Webhooks   │  │
│  └─────────────────────┘  └──────────────────┘  └─────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Google APIs: OAuth 2.0 · Maps JS · Places (Nearby POI)     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

The application is structured as six focused Django apps sharing a single database. The ASGI entry point (Daphne) handles both standard HTTP requests and persistent WebSocket connections for real-time chat.

---

## Feature Matrix

| Domain | Capability |
|---|---|
| **Discovery** | Full-text search · advanced multi-filter panel · AI semantic search · visual/image-based property matching |
| **AI Chatbot** | Llama 3.1 (NVIDIA NIM) powered assistant with LuxeEstate-scoped guardrails and lead capture |
| **Recommendations** | Personalised property suggestions based on user view history and preference profile |
| **Market Intelligence** | AI-generated market analysis per city/type with comparable pricing signals |
| **Property Comparison** | Side-by-side multi-property comparison with amenity diff and nearby POI counts |
| **Maps & POI** | Google Maps embed + OpenStreetMap geocoding + 18-category nearby place data per listing |
| **Listings** | CRUD for all property types (Apartment, House, Villa, Plot, Commercial, Office, Shop, Farmland) |
| **Media** | Multi-image upload per property with AI image analysis (NVIDIA NeVA vision model) |
| **Authentication** | Email/password + Google OAuth 2.0 via django-allauth · OTP email verification · role-based access |
| **Favourites** | Save/unsave properties with timestamped favourites list |
| **Messaging** | Real-time WebSocket chat between buyer and agent/owner per property conversation thread |
| **Payments** | Razorpay-powered premium listing packages (7/14/30/90 days) with webhook verification |
| **Notifications** | Email follow-up sequences via management command · Django messages framework |
| **Admin Dashboard** | Analytics: user growth, listing counts, payment revenue, role distribution |
| **Saved Searches** | Persist search filter sets as named queries per user |
| **Property Reviews** | Star rating + text review system per property |

---

## Tech Stack

### Backend
| Layer | Technology | Purpose |
|---|---|---|
| Language | **Python 3.14** | Core runtime |
| Framework | **Django 6.0.3** | HTTP, ORM, admin, templating |
| ASGI Server | **Daphne + Django Channels** | WebSocket support for real-time messaging |
| Channel Layer | **InMemoryChannelLayer** (dev) / **channels_redis** (prod) | WebSocket message routing |
| Auth | **django-allauth** | Email auth + Google OAuth 2.0 + OTP flow |
| API Layer | **Django REST Framework** | JSON endpoints with session auth, pagination, search/ordering |
| Static Files | **WhiteNoise** (CompressedManifest) | Zero-config static serving |
| Forms | **crispy-forms** + **crispy-bootstrap5** | Styled form rendering |
| Config | **python-decouple** + **python-dotenv** | 12-factor env var management |

### AI & External Services
| Service | SDK / Integration | Feature |
|---|---|---|
| **NVIDIA NIM** (Llama 3.1 8B Instruct) | REST API via `requests` | AI chatbot, semantic search, recommendations, market analysis |
| **NVIDIA NeVA-22B** | REST API via `requests` | Visual image analysis + image-to-property search |
| **Google OAuth 2.0** | `allauth.socialaccount.providers.google` | Social login |
| **Google Maps JS API** | Browser SDK | Interactive property maps |
| **Google Places API** | Server-side + browser | Nearby POI discovery (18 categories) |
| **OpenStreetMap / Nominatim** | `location_utils.OpenStreetMapAPI` | Geocoding fallback |
| **Razorpay** | `razorpay` Python SDK + JS checkout | Payment processing + webhook verification |

### Frontend
| Tool | Role |
|---|---|
| Bootstrap 5 | Responsive grid and component library |
| crispy-forms | Django form rendering with Bootstrap 5 pack |
| Google Maps JS SDK | Map embeds on property detail and route pages |
| Django template engine | Server-side HTML rendering |

### Database & Storage
| Component | Default (Dev) | Production |
|---|---|---|
| Database | **SQLite 3** | **PostgreSQL** |
| Media storage | Local filesystem (`/media/`) | AWS S3 (config ready) |
| Cache | `LocMemCache` | Redis |
| Channel layer | `InMemoryChannelLayer` | `channels_redis` |

---

## Data Models

### `accounts` App

```python
class Profile(models.Model):
    # One-to-one extension of Django's built-in User
    user                    = OneToOneField(User)
    role                    = CharField(choices=['buyer','owner','agent','admin'])
    phone                   = CharField(max_length=15)
    bio                     = TextField()
    profile_picture         = ImageField(upload_to='profile_pictures/')

    # OTP / email verification
    email_verified          = BooleanField(default=False)
    otp_code                = CharField(max_length=6)
    otp_created_at          = DateTimeField()

    # Social auth
    google_id               = CharField(max_length=100, unique=True)
    is_google_account       = BooleanField()

    # Preferences
    favorite_cities         = TextField()          # comma-separated
    preferred_property_type = CharField(max_length=50)

    # Agent-specific
    rating                  = FloatField(validators=[0–5])
    total_reviews           = PositiveIntegerField()

    # Metadata
    last_login_ip           = GenericIPAddressField()
    created_at / updated_at = DateTimeField()

class UserPropertyView(models.Model):
    # Tracks which users viewed which properties (unique per user+property pair)
    user       = ForeignKey(User)
    property   = ForeignKey(Property)
    viewed_at  = DateTimeField(auto_now_add=True)

class SavedSearch(models.Model):
    # Persisted search filter sets
    user       = ForeignKey(User)
    name       = CharField(max_length=100)
    query      = JSONField()               # arbitrary filter dict
    created_at = DateTimeField()
```

### `properties` App

```python
class Property(models.Model):
    # Identity
    title           = CharField(max_length=200, db_index=True)
    description     = TextField()
    price           = DecimalField(max_digits=15)
    property_type   = CharField(choices=['apartment','house','villa','plot',
                                         'commercial','office','shop','farmland'])
    status          = CharField(choices=['available','sold','rented'])

    # Location
    city, state, address, pincode = CharField / TextField
    latitude, longitude           = FloatField          # for Maps
    
    # Specs
    bedrooms, bathrooms = PositiveIntegerField()
    area_sqft           = PositiveIntegerField()
    furnishing          = CharField(choices=['unfurnished','semi-furnished','furnished'])
    amenities           = JSONField()                   # flexible feature list

    # Relations
    agent           = ForeignKey(User)                  # listing owner

    # Metrics
    views_count     = PositiveIntegerField(db_index=True)
    rating          = FloatField(validators=[0–5])
    total_reviews   = PositiveIntegerField()

    # AI-enriched nearby POI (18 categories, each a JSONField list)
    nearby_hospital, nearby_school, nearby_metro, nearby_bank ...

    # Promotion
    is_featured           = BooleanField()
    featured_until        = DateTimeField()
    promotion_package     = ForeignKey(PaymentPackage)

class PropertyImage(models.Model):
    property    = ForeignKey(Property, related_name='images')
    image       = ImageField()
    is_primary  = BooleanField()
    ai_analysis = JSONField()     # NVIDIA NeVA analysis result

class PropertyReview(models.Model):
    property   = ForeignKey(Property)
    reviewer   = ForeignKey(User)
    rating     = IntegerField(validators=[1–5])
    comment    = TextField()
    created_at = DateTimeField()
```

### `messaging` App

```python
class Conversation(models.Model):
    # Property-scoped 1-to-1 conversation thread
    property   = ForeignKey(Property)
    initiator  = ForeignKey(User, related_name='initiated_conversations')
    recipient  = ForeignKey(User, related_name='received_conversations')
    is_active  = BooleanField(default=True)
    # unique_together: (property, initiator, recipient)

class Message(models.Model):
    conversation = ForeignKey(Conversation)
    sender       = ForeignKey(User)
    recipient    = ForeignKey(User)
    message      = TextField()
    is_read      = BooleanField(default=False)
    read_at      = DateTimeField()
    image        = ImageField(upload_to='message_attachments/%Y/%m/%d/')
    message_type = CharField(choices=['text','image','document'])
```

### `payments` App

```python
class PaymentPackage(models.Model):
    name          = CharField(max_length=100)
    description   = TextField()
    price         = DecimalField()
    duration_days = IntegerField(choices=[7, 14, 30, 90])
    features      = JSONField()         # feature bullet list
    is_active     = BooleanField()

class Payment(models.Model):
    user                 = ForeignKey(User)
    package              = ForeignKey(PaymentPackage)
    property             = ForeignKey(Property)
    amount               = DecimalField()
    razorpay_order_id    = CharField(unique=True)
    razorpay_payment_id  = CharField(unique=True)
    razorpay_signature   = CharField(max_length=256)
    status               = CharField(choices=['pending','completed','failed',
                                              'cancelled','refunded'])
    payment_method       = CharField(default='razorpay')
```

### `favorites` App

```python
class Favorite(models.Model):
    user       = ForeignKey(User)
    property   = ForeignKey(Property)
    created_at = DateTimeField(auto_now_add=True)
    # unique_together: (user, property)
```

---

## AI & Intelligence Layer

All AI features live in `properties/ai_utils.py` (58 KB), `properties/chatbot_service.py` (46 KB), and `properties/image_search_service.py` (41 KB). They call NVIDIA NIM REST endpoints — no locally-hosted models required.

### AI Chatbot (`chatbot_service.py`)
- Powered by **Llama 3.1 8B Instruct** via NVIDIA NIM
- Scoped strictly to LuxeEstate listing data via configurable `AI_CHATBOT_GUIDELINES` (pipe-separated rules injected as a system prompt)
- Built-in guardrails: refuses to fabricate prices, legal status, payment confirmations, or ask for OTP/CVV
- Lead capture: extracts buyer intent signals from conversation and surfaces relevant listings
- Configured via `NIM_CHAT_MODEL` and `NVIDIA_API_KEY` env vars

### Semantic Property Search (`ai_utils.py → search_suggestion_engine`)
- Converts natural-language queries into structured filter sets using Llama
- Normalises feature vocabulary (e.g. "open kitchen" → kitchen feature group) via `FEATURE_COMPATIBILITY_GROUPS`

### Visual Image Search (`image_search_service.py`)
- Upload a reference photo to find visually similar properties
- Uses **NVIDIA NeVA-22B** vision model to extract a feature vector from uploaded images
- Matches against the `ai_analysis` JSONField stored per `PropertyImage` at upload time
- Seeded by `manage.py analyze_images` management command

### Recommendation Engine (`ai_utils.py → recommendation_engine`)
- Reads `UserPropertyView` history for the current user
- Feeds view history + profile preferences to Llama for a ranked recommendation list

### Market Analysis Engine (`ai_utils.py → market_analysis_engine`)
- Generates a city/property-type market summary (demand signals, price benchmarks, investment outlook) via Llama
- Cached per city+type to avoid repeated inference calls

### Property Comparison Engine (`ai_utils.py → comparison_engine`)
- Structured side-by-side diff of two or more properties
- AI narrative summary highlighting the key trade-offs

---

## Authentication & Security

LuxeEstate uses **django-allauth** for the complete auth lifecycle with several hardened extensions:

| Mechanism | Implementation |
|---|---|
| Email/password login | allauth `ACCOUNT_AUTHENTICATION_METHOD = 'email'` |
| Google OAuth 2.0 | `allauth.socialaccount.providers.google` with custom `SocialAccountAdapter` |
| OTP email verification | 6-digit OTP generated on `Profile`, verified server-side with configurable attempt limits and cooldown (`OTP_VERIFY_MAX_ATTEMPTS`, `OTP_VERIFY_WINDOW_SECONDS`, `OTP_RESEND_COOLDOWN_SECONDS`) |
| Role-based access | `Profile.role` (`buyer`, `owner`, `agent`, `admin`) enforced at view layer |
| Session security | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` toggled via env vars |
| HTTPS enforcement | `SECURE_SSL_REDIRECT` + `SECURE_HSTS_SECONDS` configurable for production |
| CORS | `corsheaders.middleware.CorsMiddleware` with `CORS_ALLOWED_ORIGINS` whitelist |
| Static security headers | Django's `SecurityMiddleware` |
| IP tracking | `last_login_ip` persisted on `Profile` for audit trails |
| SMTP resilience | Custom `smtp_backend.EmailBackend` wraps Django's SMTP backend with Certifi CA bundle and optional insecure-skip-verify escape hatch (dev only) |
| Secrets management | All secrets in `.env` via `python-decouple`; zero hardcoded credentials in source |

---

## Payments

Premium listing promotion is powered by **Razorpay**.

**Flow:**

```
User selects package
    → Django creates Razorpay order (server-side, razorpay-python SDK)
    → Razorpay JS Checkout renders in browser
    → User completes payment (UPI / card / netbanking)
    → Browser posts payment_id + signature to Django verify endpoint
    → Django verifies HMAC-SHA256 signature using RAZORPAY_WEBHOOK_SECRET
    → On success: Payment record → 'completed', Property → is_featured=True, featured_until set
    → Razorpay webhook endpoint provides secondary server-to-server confirmation
```

**Packages** (seeded via admin or fixtures):

| Tier | Duration | Outcome |
|---|---|---|
| Starter | 7 days | Featured badge on listing card |
| Standard | 14 days | Featured badge + priority search rank |
| Premium | 30 days | Featured badge + priority rank + homepage slot |
| Elite | 90 days | All Premium benefits for three months |

---

## Real-Time Messaging

Buyer ↔ Agent/Owner conversations use **Django Channels** over WebSocket:

- Each property spawns at most one `Conversation` per buyer/agent pair (`unique_together` constraint)
- Messages are persisted to the `Message` model for full history
- The channel layer defaults to `InMemoryChannelLayer` in development; swap to `channels_redis` for multi-process production deployments by setting `CHANNEL_LAYERS_HOST` + `CHANNEL_LAYERS_PORT`
- Supports text, image attachments, and a `message_type` enum for future document sharing
- Unread tracking via `is_read` / `read_at` fields

---

## Getting Started

### Prerequisites

- Python 3.11+
- `git`
- (Optional) Redis — only needed for multi-worker WebSocket in production

### 1. Clone & enter

```bash
git clone https://github.com/your-org/LuxeEstate.git
cd LuxeEstate/LuxeEstate_updated
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Open .env and fill in the required values (see Environment Reference below)
```

At minimum you need `SECRET_KEY`. All other services degrade gracefully in development (AI features return empty results; payments use Razorpay test keys; emails print to console).

### 5. Database setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. (Optional) Seed Google social app

```bash
python create_social_app.py
```

This registers a `SocialApp` for Google OAuth using `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` from your `.env`.

### 7. (Optional) Analyse existing property images

```bash
python manage.py analyze_images
```

Runs NVIDIA NeVA against all uploaded `PropertyImage` records and stores the vision analysis in `ai_analysis` for visual search.

### 8. Collect static files (production only)

```bash
python manage.py collectstatic --no-input
```

### 9. Run the development server

```bash
python manage.py runserver
```

The application is served at `http://localhost:8000`.

---

## Environment Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Django secret key |
| `DEBUG` | | `True` | Set `False` in production |
| `ALLOWED_HOSTS` | | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DB_ENGINE` | | `sqlite3` | `django.db.backends.postgresql` for Postgres |
| `DB_NAME` | | `db.sqlite3` | Database name or file path |
| `EMAIL_HOST_USER` | | `""` | SMTP sender — if empty, OTPs print to console |
| `EMAIL_HOST_PASSWORD` | | `""` | SMTP app password |
| `GOOGLE_OAUTH_CLIENT_ID` | | `""` | Google OAuth app client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | | `""` | Google OAuth app client secret |
| `GOOGLE_MAPS_API_KEY` | | `""` | Google Maps JS API key (map embeds) |
| `GOOGLE_PLACES_API_KEY` | | `""` | Google Places API key (nearby POI) |
| `RAZORPAY_KEY_ID` | | `""` | Razorpay publishable key |
| `RAZORPAY_KEY_SECRET` | | `""` | Razorpay secret key |
| `RAZORPAY_WEBHOOK_SECRET` | | `""` | Webhook HMAC secret |
| `NIM_API_KEY` | | `""` | NVIDIA NIM API key (all AI features) |
| `NVIDIA_MODEL` | | `meta/llama-3.1-8b-instruct` | NIM chat model ID |
| `NVIDIA_VISION_MODEL` | | `nvidia/neva-22b` | NIM vision model ID |
| `CHANNEL_LAYERS_HOST` | | `""` | Redis host for WebSocket (blank = InMemory) |
| `CHANNEL_LAYERS_PORT` | | `6379` | Redis port |
| `SITE_URL` | | `http://localhost:8000` | Base URL (used in email links) |
| `SECURE_SSL_REDIRECT` | | `False` | Set `True` behind HTTPS in production |
| `OTP_VERIFY_MAX_ATTEMPTS` | | `5` | Max OTP verification attempts per window |
| `OTP_VERIFY_WINDOW_SECONDS` | | `600` | OTP validity window (seconds) |
| `OTP_RESEND_COOLDOWN_SECONDS` | | `60` | Minimum gap between OTP resend requests |
| `LOG_LEVEL` | | `INFO` | Python logging level |

---

## Project Structure

```
LuxeEstate_updated/
│
├── LuxeEstate/                  # Django project package
│   ├── settings.py              # Centralised settings with decouple
│   ├── urls.py                  # Root URL dispatcher
│   ├── asgi.py                  # ASGI entry point (Daphne + Channels)
│   ├── wsgi.py                  # WSGI entry point (gunicorn fallback)
│   ├── routing.py               # Django Channels WebSocket routing
│   └── smtp_backend.py          # Hardened SMTP backend (Certifi CA)
│
├── accounts/                    # Auth, profiles, roles, OTP
│   ├── models.py                # Profile, UserPropertyView, SavedSearch
│   ├── views.py                 # Register, login, OTP, profile, agent list
│   ├── forms.py                 # Registration and profile forms
│   ├── adapters.py              # Custom allauth SocialAccountAdapter
│   ├── utils.py                 # OTP generation helpers
│   └── templatetags/            # social_helpers tag library
│
├── properties/                  # Core listing domain
│   ├── models.py                # Property, PropertyImage, PropertyReview
│   ├── views.py                 # CRUD, search, compare, visual search, AI endpoints
│   ├── ai_utils.py              # Semantic search, recommendations, market analysis
│   ├── chatbot_service.py       # Llama-powered chatbot service
│   ├── image_search_service.py  # NeVA-based visual property search
│   ├── location_utils.py        # OpenStreetMap geocoding wrapper
│   ├── payment_utils.py         # Promotion package application helpers
│   └── management/commands/     # analyze_images, geocode_properties, send_followups
│
├── favorites/                   # Save/unsave properties
├── messaging/                   # WebSocket conversations + message persistence
├── payments/                    # Razorpay integration + package management
├── admin_dashboard/             # Admin analytics views
│
├── templates/                   # Django HTML templates (app-scoped)
├── static/                      # CSS, JS, images
├── media/                       # User-uploaded files (dev)
├── logs/                        # django.log
│
├── docs/
│   └── figures/                 # UML diagrams (use-case, activity, sequence)
│       ├── fig_1_1_use_case_auth_listing.png
│       ├── fig_1_2_activity_property_search.png
│       ├── fig_1_3_use_case_chatbot_leads.png
│       ├── fig_1_4_activity_payment_messaging.png
│       └── fig_1_5_use_case_admin_analytics.png
│
├── manage.py
├── .env.example
└── .env                         # Local secrets — never committed
```

---

## Deployment

### Production Checklist

Before going live, ensure every item below is addressed:

```
[ ] DEBUG=False in .env
[ ] SECRET_KEY is a long, random, unique value
[ ] ALLOWED_HOSTS includes your domain(s)
[ ] SECURE_SSL_REDIRECT=True (behind HTTPS terminator)
[ ] SESSION_COOKIE_SECURE=True
[ ] CSRF_COOKIE_SECURE=True
[ ] SECURE_HSTS_SECONDS=31536000 (after confirming HTTPS is stable)
[ ] DB_ENGINE=django.db.backends.postgresql with dedicated DB credentials
[ ] CHANNEL_LAYERS_HOST=<redis-host> (for multi-worker WebSocket)
[ ] Media files offloaded to AWS S3 (AWS_* vars configured)
[ ] python manage.py collectstatic --no-input
[ ] python manage.py migrate --run-syncdb
[ ] Razorpay webhook URL registered and RAZORPAY_WEBHOOK_SECRET set
[ ] CORS_ALLOWED_ORIGINS locked to your actual frontend origins
```

### Recommended Stack

```
Nginx (TLS termination + static serving)
    → Daphne (ASGI, all HTTP + WebSocket)
        → Django application
    ← PostgreSQL (primary DB)
    ← Redis (channel layer + optional cache)
    ← AWS S3 (media storage)
```

### Docker (one-liner dev environment)

```bash
docker compose up --build
```

A `docker-compose.yml` with Django + Redis services is a natural addition — contributions welcome.

---

## UML Diagrams

System behaviour is documented in `docs/figures/`:

| Diagram | Description |
|---|---|
| `fig_1_1_use_case_auth_listing.png` | Use case: authentication and property listing flows |
| `fig_1_2_activity_property_search.png` | Activity: property search (filters + AI semantic) |
| `fig_1_3_use_case_chatbot_leads.png` | Use case: AI chatbot and lead capture |
| `fig_1_4_activity_payment_messaging.png` | Activity: Razorpay payment and real-time messaging |
| `fig_1_5_use_case_admin_analytics.png` | Use case: admin dashboard and analytics |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Follow existing code style — Django conventions, PEP 8, descriptive commit messages
4. Add or update tests for any changed behaviour
5. Open a pull request against `main` with a clear description of the change

Please report security vulnerabilities privately via email rather than opening a public issue.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for full terms.

---

<div align="center">

*Built with Django 6 · Powered by NVIDIA NIM · Payments via Razorpay*

</div>
