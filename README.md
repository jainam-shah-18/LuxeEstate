# LuxeEstate

Professional real estate platform built with Django for property discovery, user engagement, AI-assisted search, and payment-enabled listing promotion.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/API-Django_REST_Framework-red)
![Channels](https://img.shields.io/badge/Realtime-Django_Channels-6f42c1)
![Razorpay](https://img.shields.io/badge/Payments-Razorpay-0C2451)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Business Use Cases](#business-use-cases)
- [User Flows](#user-flows)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Payments and Billing](#payments-and-billing)
- [AI Capabilities](#ai-capabilities)
- [Management Commands](#management-commands)
- [Route Map](#route-map)
- [Testing and Quality](#testing-and-quality)
- [Deployment Checklist](#deployment-checklist)
- [Troubleshooting](#troubleshooting)
- [Security Guidelines](#security-guidelines)
- [License](#license)

---

## Overview

LuxeEstate unifies listing management, customer communication, and revenue workflows in one application. The platform is designed for three core groups:

- **Buyers/Tenants**: discover, compare, save, and inquire about properties.
- **Agents/Owners**: publish and manage listings, respond to leads, and promote properties.
- **Administrators**: track platform growth, engagement, and revenue metrics.

It includes built-in support for authentication, OTP verification, favorites, messaging, payments, AI tooling, and analytics dashboards.

---

## Key Features

### Authentication and Accounts

- Email/password registration and login
- OTP verification and resend support
- Google OAuth sign-in (Allauth provider integration)
- Profile completion and profile management
- Password change flow

### Property Management

- Home and listing pages with pagination
- Rich property detail pages
- Add, edit, and delete listing workflow
- My Properties view for owners/agents
- Geocoding retry support and nearby places integration

### Search and Discovery

- Keyword and filter-based property search
- AJAX filter and city endpoints
- Search suggestions endpoint
- Property comparison add/list/clear workflows

### Engagement Features

- Favorites add/remove/toggle/list
- Agent contact and lead conversations
- Messaging inbox with conversation detail
- Notification retrieval and read acknowledgements

### Payments and Monetization

- Package-based promotion/purchase flow
- Payment creation and verification
- Success/failure result pages
- Subscription detail and cancellation flow
- Invoice views and payment history
- Razorpay webhook processing with event persistence
- Payment audit logs for lifecycle traceability

### AI Features

- AI-assisted property description generation
- Conversational chatbot endpoint for property support
- Search-by-image with visual feature extraction and ranking
- Configurable AI behavior through environment variables

### Admin Analytics

- Central admin dashboard
- User analytics
- Property analytics
- Revenue analytics
- Engagement analytics

---

## Business Use Cases

- **Brokerage Website**: operate a full listing and inquiry portal.
- **Agency CRM Layer**: centralize lead conversations and property actions.
- **Monetized Listing Platform**: sell subscription or promotional plans.
- **AI-Enhanced Search Portal**: improve discovery with chatbot and image-based matching.

---

## User Flows

### Buyer/Tenant Journey

1. Register/login (email+OTP or Google OAuth).
2. Search and filter listings.
3. Open details and compare shortlisted properties.
4. Save favorites and contact agents.
5. Continue discussions in messaging conversations.

### Agent/Owner Journey

1. Login and complete profile.
2. Create and manage listings.
3. Receive and respond to inquiries.
4. Promote properties using payment packages.
5. Monitor payment history and invoices.

### Admin Journey

1. Open admin dashboard.
2. Review user/property/revenue/engagement insights.
3. Track platform performance and growth.

---

## Architecture

```text
LuxeEstate_updated/
├── LuxeEstate/                # Core settings, URL config, ASGI/WSGI
├── accounts/                  # Authentication, OTP, profile logic
├── properties/                # Listings, search, comparison, AI features
├── favorites/                 # Saved properties module
├── messaging/                 # Conversations, messages, notifications
├── payments/                  # Packages, checkout, subscriptions, webhooks
├── admin_dashboard/           # Admin analytics dashboards
├── templates/                 # Frontend templates
├── static/                    # Static source assets (CSS/JS/images)
├── media/                     # User uploads (runtime generated)
├── requirements.txt
└── .env.example
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | Python, Django |
| API | Django REST Framework |
| Auth | Django Allauth, Google OAuth |
| Realtime | Django Channels, Daphne |
| Payments | Razorpay SDK + webhook handlers |
| AI | Nvidia NIM integrations |
| Frontend | Django Templates, JavaScript, CSS |
| Data | SQLite (default), configurable DB backend |
| Static Delivery | WhiteNoise |

---

## Getting Started

### 1) Clone repository

```bash
git clone https://github.com/jainam-shah-18/LuxeEstate.git
cd LuxeEstate
```

If your local project folder is `LuxeEstate_updated`, run commands there.

### 2) Create virtual environment

```bash
python -m venv .venv
```

### 3) Activate environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

### 5) Configure environment file

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Update values in `.env` before running the app.

### 6) Run database migrations

```bash
python manage.py migrate
```

### 7) Create superuser (recommended)

```bash
python manage.py createsuperuser
```

### 8) Start development server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000`

---

## Configuration

The project uses environment-driven configuration (`.env`). Important variables:

### Core

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_ENGINE`
- `DB_NAME`

### Email and OTP

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

Optional local debugging controls:

- `EMAIL_SMTP_INSECURE_SKIP_VERIFY`
- `EMAIL_SMTP_CA_BUNDLE`

### Integrations

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_PLACES_API_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `PAYMENT_TEST_MODE`
- `NVIDIA_API_KEY`
- `NIM_CHAT_MODEL`
- `NVIDIA_VISION_MODEL`
- `AI_CHATBOT_GUIDELINES`

### Realtime (Channels)

- `CHANNEL_LAYERS_HOST`
- `CHANNEL_LAYERS_PORT`

Refer to `.env.example` for all defaults and examples.

---

## Payments and Billing

### Implemented Payment Features

- Package pricing and purchase initiation
- Payment verify endpoint and callback verification
- Payment success/failure flows
- Subscription detail and cancellation
- Invoice detail and payment history
- Webhook ingestion and processing
- Payment event auditing and webhook event storage

### Razorpay Webhook Setup

Configure one of these endpoints in Razorpay dashboard:

- `/payments/webhook/razorpay/`
- `/payments/webhook/payment-gateway/` (alias)

Ensure `RAZORPAY_WEBHOOK_SECRET` in `.env` exactly matches dashboard configuration.

---

## AI Capabilities

### 1) AI Description Generation

Generates listing descriptions from available property metadata.

### 2) AI Chatbot

Handles property-related guidance with configurable model and policy guardrails.

### 3) Search by Image

Uploads property images, extracts visual features, and ranks listings by similarity.

For setup and troubleshooting specifics, see `IMAGE_SEARCH_SETUP.md`.

---

## Management Commands

### Send follow-up actions

```bash
python manage.py send_followups
```

Triggers chatbot-driven automated follow-up handling for leads and appointments.

### Setup payment packages helper

```bash
python manage.py setup_payment_packages
```

Current implementation deactivates active payment packages globally.

---

## Route Map

| Route Prefix | Module |
|---|---|
| `/` | Properties (home, list, detail, search, compare) |
| `/auth/` | Accounts (register/login/profile/OTP) |
| `/accounts/` | Django Allauth |
| `/favorites/` | Favorite actions and list |
| `/messaging/` | Conversations and notifications |
| `/payments/` | Pricing, payment flow, subscriptions, webhooks |
| `/dashboard/` | Admin analytics |
| `/admin/` | Django admin |

Static info pages:

- `/about/`
- `/terms/`
- `/privacy/`
- `/cookies/`
- `/sitemap/`

---

## Testing and Quality

Recommended pre-release checks:

```bash
python manage.py check
python manage.py test
```

Also validate manually:

- Auth and OTP flows
- Property create/edit/delete
- Search and comparison behavior
- Messaging and notifications
- Payment success/failure and webhook processing
- AI chatbot and image search availability

---

## Deployment Checklist

- Set `DEBUG=False`
- Configure production `ALLOWED_HOSTS`
- Use secure production `SECRET_KEY`
- Enable HTTPS and secure cookie settings
- Use production database (PostgreSQL recommended)
- Configure persistent media/static strategy
- Run `python manage.py collectstatic`
- Configure background job strategy for periodic commands
- Add monitoring, alerting, and backup policies

---

## Troubleshooting

### OTP/Email issues

- Verify SMTP credentials in `.env`
- Check fallback email backend behavior in debug mode
- Review app logs for TLS/certificate-related messages

### Payment issues

- Re-check Razorpay keys and webhook secret
- Confirm webhook URL is reachable from internet
- Review payment/invoice/audit/webhook records in database

### AI feature issues

- Verify `NVIDIA_API_KEY` and model variables
- Restart server after changing `.env`
- Use clear, high-quality images for image-based search

### Static/media issues in production

- Re-run `collectstatic`
- Confirm WhiteNoise/static serving config
- Verify media storage permissions and paths

---

## Security Guidelines

- Never commit `.env`, secrets, or private credentials
- Keep dependencies patched and updated
- Protect webhook secrets and API keys from frontend exposure
- Validate uploads and enforce reasonable file limits
- Review generated AI output before business-critical usage

---

## License

This repository is currently intended for educational and development use.
