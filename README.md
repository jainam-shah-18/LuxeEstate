# LuxeEstate

A Django-based real estate platform with AI-assisted property discovery, user role dashboards, favorites, messaging, and payment workflows.

## Features

- Property listing, search, filters, and detail pages
- Role-based user flows (buyer, agent, admin)
- AI chatbot support for property discovery
- Favorites and property comparison
- Real-time style messaging module with Channels
- Razorpay integration for property promotion/payment flows
- Google OAuth login and Google Maps/Places integration
- Admin analytics dashboards

## Tech Stack

- Python
- Django
- Django Channels + Daphne
- Django Allauth
- Django REST Framework
- Razorpay
- OpenAI API
- SQLite (default local database)

## Project Structure

```
LuxeEstate_updated/
├── LuxeEstate/          # Django project settings, urls, asgi/wsgi
├── accounts/            # Auth, profiles, role-based user features
├── properties/          # Property models, views, AI/chatbot services
├── favorites/           # Favorite properties
├── messaging/           # Conversations and chat logic
├── payments/            # Payment and subscription logic
├── admin_dashboard/     # Admin analytics and dashboard views
├── templates/           # HTML templates
├── static/              # Source static assets
├── manage.py
├── requirements.txt
└── .env.example
```

## Setup and Run (Local)

### 1) Clone

```bash
git clone https://github.com/jainam-shah-18/LuxeEstate.git
cd LuxeEstate
```

### 2) Create virtual environment

```bash
python -m venv .venv
```

Activate:

- Windows PowerShell:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your own keys and credentials.

### 5) Apply migrations

```bash
python manage.py migrate
```

### 6) Run development server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000`

## Core Environment Variables

Set these in `.env`:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_PLACES_API_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `OPENAI_API_KEY`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

## Notes

- Never commit `.env` or any private keys.
- Runtime/generated directories (`media`, `staticfiles`, `logs`, `__pycache__`) are intentionally ignored.
- If you use Redis for Channels, configure `CHANNEL_LAYERS_HOST` and `CHANNEL_LAYERS_PORT`.

## License

This project is for educational and development use. Add a dedicated `LICENSE` file if you plan public/production distribution.
