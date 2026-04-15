# LuxeEstate

LuxeEstate is a Django-based real estate platform built for property discovery, agent-buyer communication, AI-assisted search, and payment-enabled listing promotion.

It combines listing management, user authentication, favorites, chat, analytics, and payment workflows in a single project.

## Table of Contents

- [Why This Project Exists](#why-this-project-exists)
- [What Is Implemented](#what-is-implemented)
- [How the Platform Is Used](#how-the-platform-is-used)
- [Project Architecture](#project-architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Local Setup (Step-by-Step)](#local-setup-step-by-step)
- [Environment Variables](#environment-variables)
- [Payments and Webhooks](#payments-and-webhooks)
- [AI Features](#ai-features)
- [Management Commands](#management-commands)
- [Main URL Map](#main-url-map)
- [Troubleshooting](#troubleshooting)
- [Production Notes](#production-notes)
- [Security Notes](#security-notes)
- [License](#license)

## Why This Project Exists

Traditional property platforms often separate discovery, communication, and monetization. LuxeEstate brings these together:

- Buyers can discover and compare properties quickly.
- Agents can manage listings and engage interested users.
- Admins can monitor activity, growth, and revenue.
- Platform owners can monetize promotions/subscriptions through integrated payments.

## What Is Implemented

### 1) Authentication and User Accounts

- Email-based registration/login/logout flows
- OTP verification and OTP resend flow
- Profile creation and profile edit screens
- Password change support
- Google OAuth support via Django Allauth
- User role handling through profile data

### 2) Property Discovery and Listing Management

- Home page and paginated property listing pages
- Search with filtering utilities and search suggestions
- Property detail pages with media and metadata
- Add, edit, and delete property flows for owners/agents
- "My Properties" dashboard for listing owners
- City APIs, geocode retry helpers, and nearby-place utilities

### 3) AI-Enhanced Property Experience

- AI description generation endpoint for properties
- AI chatbot endpoint for user Q&A
- Search-by-image flow with feature extraction
- Image-based property ranking using visual/amenity signals
- Chatbot service with configurable guardrails via environment variables

### 4) Favorites and Comparison

- Add/remove/toggle favorites
- Favorites list view for signed-in users
- Property comparison add/list/clear features
- Comparison table and chart-friendly comparison data builders

### 5) Messaging and Notifications

- Conversation list and conversation detail views
- Contact-agent flow from property context
- Send message flow tied to properties
- Notification retrieval and mark-as-read support
- Legacy compatibility routes preserved for older links

### 6) Payments, Subscriptions, and Invoicing

- Pricing pages and package-driven purchase flow
- Payment creation and verification endpoints
- Callback-based verification support
- Success and failure views for payment outcomes
- Payment history and invoice detail pages
- Subscription start/detail/cancel flows
- Razorpay webhook endpoint (plus alias endpoint)
- Payment audit logging and webhook event persistence models

### 7) Admin Dashboard and Analytics

- Central admin dashboard
- User analytics
- Property analytics
- Revenue analytics
- Engagement analytics

## How the Platform Is Used

### Buyer/User Journey

1. Register/login (OTP and OAuth available).
2. Browse listings and use filters/search.
3. Open details, compare properties, save favorites.
4. Contact an agent from the listing.
5. Continue conversation in messaging area.

### Agent/Owner Journey

1. Login and complete profile.
2. Add and manage properties.
3. Receive user inquiries in messaging.
4. Promote a property via payment packages.
5. Track payment status/invoices.

### Admin Journey

1. Access admin dashboard.
2. Monitor users/properties/revenue/engagement.
3. Review platform trends and activity.

## Project Architecture

```text
LuxeEstate_updated/
├── LuxeEstate/          # Project config, URL routing, ASGI/WSGI, settings
├── accounts/            # Auth, OTP, profile and user-related flows
├── properties/          # Listings, search, detail, AI/chatbot, comparison
├── favorites/           # Saved property functionality
├── messaging/           # Conversations, messages, notifications
├── payments/            # Packages, checkout, subscriptions, invoices, webhooks
├── admin_dashboard/     # Dashboard and analytics views
├── templates/           # HTML templates
├── static/              # Source static files
├── media/               # User-uploaded files (runtime)
├── requirements.txt
└── .env.example
```

## Tech Stack

- Python 3.10+
- Django 6
- Django REST Framework
- Django Allauth
- Django Channels + Daphne
- Razorpay Python SDK
- Nvidia NIM API integration
- Google OAuth + Maps/Places integration
- WhiteNoise for static assets
- SQLite default database (configurable via env)

## Prerequisites

- Python 3.10 or newer
- pip
- Git
- (Optional for realtime scale) Redis
- API credentials if using external integrations (Google, Razorpay, Nvidia)

## Local Setup (Step-by-Step)

### 1) Clone repository

```bash
git clone https://github.com/jainam-shah-18/LuxeEstate.git
cd LuxeEstate
```

If your folder name is `LuxeEstate_updated`, run commands in that folder.

### 2) Create virtual environment

```bash
python -m venv .venv
```

### 3) Activate virtual environment

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

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Fill in `.env` values for your setup.

### 6) Apply migrations

```bash
python manage.py migrate
```

### 7) Create admin user (optional but recommended)

```bash
python manage.py createsuperuser
```

### 8) Run server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

## Environment Variables

Below are the most important variables (see `.env.example` for full list and defaults):

### Core Django

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_ENGINE`
- `DB_NAME`

### Email/OTP

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_SMTP_INSECURE_SKIP_VERIFY` (local debugging only)
- `EMAIL_SMTP_CA_BUNDLE` (optional custom CA path)

### Auth and Site

- `SITE_URL`
- `SITE_NAME`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

### Maps and Search Enhancements

- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_PLACES_API_KEY`

### Payments

- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `PAYMENT_TEST_MODE`

### AI

- `NVIDIA_API_KEY`
- `NIM_CHAT_MODEL`
- `NVIDIA_VISION_MODEL`
- `AI_CHATBOT_GUIDELINES`

### Channels/Realtime

- `CHANNEL_LAYERS_HOST`
- `CHANNEL_LAYERS_PORT`

## Payments and Webhooks

### Payment Flow

1. User selects a package/property promotion option.
2. App creates payment request/order.
3. Payment is verified through callback/API verification.
4. Status updates are reflected in payment history/invoice screens.
5. Audit entries are recorded for critical payment events.

### Razorpay Webhook Setup

Configure your Razorpay dashboard to send events to:

- `/payments/webhook/razorpay/`

Alias endpoint also exists:

- `/payments/webhook/payment-gateway/`

Use the same secret value in dashboard and `.env` for `RAZORPAY_WEBHOOK_SECRET`.

## AI Features

### Chatbot

- Endpoint: property chatbot API
- Uses configured Nvidia model and safety guidelines
- Designed for property-context assistance

### AI Description Generation

- Endpoint to generate property descriptions
- Uses listing metadata as context

### Search by Image

- Upload an image
- Extract visual/property features
- Rank properties by visual and amenity similarity

If image search is not working, verify `NVIDIA_API_KEY` and restart the server.

## Management Commands

### Send Follow-up Messages

```bash
python manage.py send_followups
```

Runs automated follow-up actions via chatbot service for leads/appointments.

### Payment Package Setup Utility

```bash
python manage.py setup_payment_packages
```

Current command implementation deactivates active promotion packages.

## Main URL Map

Top-level routes:

- `/` -> properties module (home/search/listing/details)
- `/auth/` -> accounts module
- `/accounts/` -> allauth routes
- `/favorites/` -> favorites module
- `/messaging/` -> messaging module
- `/payments/` -> payment/subscription/webhook module
- `/dashboard/` -> admin analytics module
- `/admin/` -> Django admin

Static informational pages:

- `/about/`, `/terms/`, `/privacy/`, `/cookies/`, `/sitemap/`

## Troubleshooting

### OTP email not arriving

- Check email settings in `.env`.
- In debug mode, OTP may print to console when SMTP is not configured.

### Payment verification issues

- Verify Razorpay keys and webhook secret.
- Confirm webhook target URL is public/reachable.
- Check payment and webhook logs in admin/database.

### AI features unavailable

- Ensure `NVIDIA_API_KEY` is valid.
- Verify model env vars are set correctly.
- Restart server after env changes.

### Static files missing in production

- Run `python manage.py collectstatic`.
- Ensure static serving is configured properly.

## Production Notes

- Set `DEBUG=False`.
- Use strong `SECRET_KEY`.
- Configure `ALLOWED_HOSTS`.
- Enable HTTPS and secure cookie settings.
- Use production DB (PostgreSQL recommended) instead of SQLite.
- Use Redis-backed channel layer for scaled realtime workloads.
- Configure logging/monitoring and periodic backups.

## Security Notes

- Never commit `.env` or secrets.
- Do not expose webhook secrets or API keys in frontend code.
- Keep dependencies updated.
- Validate uploads and enforce size/type limits.
- Review AI outputs before using them in sensitive decisions.

## License

This repository is currently intended for educational and development use.
