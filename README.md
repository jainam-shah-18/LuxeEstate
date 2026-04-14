# LuxeEstate V2 ✨

> Premium AI-powered real estate experience built with Django - crafted for discovery, trust, and high-conversion property journeys.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-Framework-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/API-Django_REST_Framework-red)
![Channels](https://img.shields.io/badge/Realtime-Django_Channels-purple)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-Educational-blue)

---

## Table of Contents

- [Vision](#vision-)
- [Feature Badges by Category](#feature-badges-by-category-)
- [Signature Highlights](#signature-highlights-)
- [Product Preview](#product-preview-)
- [Tech Stack](#tech-stack-)
- [Project Structure](#project-structure-)
- [Quick Start](#quick-start-)
- [Required Environment Variables](#required-environment-variables-)
- [Development Notes](#development-notes-)
- [License](#license-)

---

## Vision

LuxeEstate brings modern property discovery and transaction workflows into one polished platform:
- 🔍 Smart browsing with rich filters and listing comparison
- 🤖 AI-assisted recommendations via conversational search
- 👥 Role-based journeys for buyers, agents, and admins
- 💬 Built-in communication for faster conversion
- 💳 Secure monetization and payment-ready flows

---

## Feature Badges by Category

### Discovery & Experience
![Smart Search](https://img.shields.io/badge/Discovery-Smart_Search-1f6feb)
![Property Filters](https://img.shields.io/badge/Discovery-Advanced_Filters-1f6feb)
![Comparison](https://img.shields.io/badge/Discovery-Listing_Comparison-1f6feb)

### AI & Automation
![OpenAI Chatbot](https://img.shields.io/badge/AI-OpenAI_Assistant-7a3cff)
![Contextual Recommendations](https://img.shields.io/badge/AI-Contextual_Recommendations-7a3cff)

### Engagement & Communication
![Messaging](https://img.shields.io/badge/Engagement-Real--Time_Messaging-ff6b35)
![Favorites](https://img.shields.io/badge/Engagement-Favorites-ff6b35)
![Dashboards](https://img.shields.io/badge/Engagement-Role_Based_Dashboards-ff6b35)

### Payments & Growth
![Razorpay](https://img.shields.io/badge/Payments-Razorpay_Integrated-00a86b)
![Promotions](https://img.shields.io/badge/Growth-Promotions_Ready-00a86b)

### Security & Identity
![Google OAuth](https://img.shields.io/badge/Auth-Google_OAuth-4285F4)
![Role Access](https://img.shields.io/badge/Security-Role_Based_Access-4285F4)

### Location Intelligence
![Google Maps](https://img.shields.io/badge/Maps-Google_Maps-fbbc05)
![Places API](https://img.shields.io/badge/Maps-Places_API-fbbc05)

---

## Signature Highlights

- **Premium discovery flow:** elegant listing exploration with useful filter depth.
- **AI concierge feel:** natural language search support for instant recommendations.
- **Role-first architecture:** tailored user experiences for buyer, agent, and admin personas.
- **Integrated conversion loop:** favorites, messaging, and payments in one stack.
- **Scalable Django base:** production-friendly structure with REST and Channels.

---

## Product Preview

> Keep screenshots in `docs/screenshots/` (update paths if filenames change).

| Home Page | Property Listing |
| --- | --- |
| [![LuxeEstate Home](docs/screenshots/home-page.png)](docs/screenshots/home-page.png) | [![Property Listing](docs/screenshots/property-listing.png)](docs/screenshots/property-listing.png) |
| Property Details | User Dashboard |
| [![Property Details](docs/screenshots/property-details.png)](docs/screenshots/property-details.png) | [![User Dashboard](docs/screenshots/user-dashboard.png)](docs/screenshots/user-dashboard.png) |
| Chatbot / Messaging | |
| [![Chatbot and Messaging](docs/screenshots/chatbot-messaging.png)](docs/screenshots/chatbot-messaging.png) | |

---

## Tech Stack

### Backend
- Python
- Django
- Django REST Framework
- Django Channels + Daphne
- Django Allauth

### Services & Integrations
- OpenAI API
- Razorpay
- Google OAuth
- Google Maps / Places APIs

### Data
- SQLite (default local database)

---

## Project Structure

```text
LuxeEstate_updated/
├── LuxeEstate/          # Django project settings, urls, asgi/wsgi
├── accounts/            # Authentication, profiles, role-based features
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

---

## Quick Start

### 1) Clone repository
```bash
git clone https://github.com/jainam-shah-18/LuxeEstate.git
cd LuxeEstate
```

### 2) Create and activate virtual environment
```bash
python -m venv .venv
```

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

### 4) Configure environment
macOS/Linux:
```bash
cp .env.example .env
```

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

Update `.env` with your credentials and API keys.

### 5) Run migrations
```bash
python manage.py migrate
```

### 6) Start local server
```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000`

---

## Required Environment Variables

Set these values in `.env`:
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

---

## Development Notes

- Do not commit `.env` files or private credentials.
- Runtime/generated directories (`media`, `staticfiles`, `logs`, `__pycache__`) are intentionally ignored.
- For Redis-backed Channels, configure `CHANNEL_LAYERS_HOST` and `CHANNEL_LAYERS_PORT`.
- Recent updates include improvements to property search, image-driven lookup flow, and listing comparison UX.

---

## License

This repository is currently intended for educational and development use.  
Add a dedicated `LICENSE` file for production or public distribution.
