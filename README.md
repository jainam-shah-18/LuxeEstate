# LuxeEstate

LuxeEstate is a full-stack Django real estate platform for listing discovery, user engagement, messaging, and payment-powered property promotion.

## Core Features

- Property listing, browsing, and detail pages
- Favorites and saved properties
- Built-in messaging between users
- Role-based admin dashboard
- AI-assisted chat and image search integrations
- Payment flows for subscriptions and promoted listings
- Google OAuth login support
- Realtime-ready architecture with Django Channels

## Tech Stack

- Python 3.10+
- Django 6
- Django REST Framework
- Django Allauth
- Django Channels + Daphne
- Razorpay integration
- Google APIs (OAuth, Maps, Places)
- SQLite by default (configurable)

## Project Structure

```text
LuxeEstate_updated/
├── LuxeEstate/          # Project settings, URLs, ASGI/WSGI
├── accounts/            # Authentication and user account logic
├── admin_dashboard/     # Admin-specific pages and tools
├── favorites/           # Favorites feature
├── messaging/           # User messaging flows
├── payments/            # Checkout, subscriptions, invoices, webhooks
├── properties/          # Property models, views, AI/image search logic
├── templates/           # HTML templates
├── static/              # Source static assets
├── requirements.txt
└── .env.example
```

## Local Setup

### 1) Clone and enter project

```bash
git clone <your-repo-url>
cd LuxeEstate_updated
```

### 2) Create and activate virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Copy the sample file:

```powershell
Copy-Item .env.example .env
```

Then update `.env` with the credentials and API keys required for your environment.

### 5) Run migrations

```bash
python manage.py migrate
```

### 6) (Optional) Create admin user

```bash
python manage.py createsuperuser
```

### 7) Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

## Environment Variables

Key variables used by this project include:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `DB_ENGINE`, `DB_NAME`
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_MAPS_API_KEY`, `GOOGLE_PLACES_API_KEY`
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`
- `NVIDIA_API_KEY`, `NIM_CHAT_MODEL`, `NVIDIA_VISION_MODEL`
- `CHANNEL_LAYERS_HOST`, `CHANNEL_LAYERS_PORT`

See `.env.example` for the full template and defaults.

## Payment Webhook Endpoint

For Razorpay webhook delivery, configure:

- `/payments/webhook/razorpay/`

Use the same webhook secret in Razorpay Dashboard and `.env`.

## Notes

- `.env`, `venv`, `db.sqlite3`, `logs`, `media`, and generated static artifacts are git-ignored.
- For production, set `DEBUG=False`, configure secure cookie/SSL settings, and use a production-grade database and ASGI deployment.
- If using realtime messaging at scale, configure Redis-backed Channels.

## License

This project is currently intended for educational and development use.
