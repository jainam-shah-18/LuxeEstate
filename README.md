# LuxeEstate - Premium Real Estate Platform

Professional real estate platform built with Django for property discovery, user engagement, AI-assisted search, payment-enabled listing promotion, and Telegram chatbot integration.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/API-Django_REST_Framework-red)
![Channels](https://img.shields.io/badge/Realtime-Django_Channels-6f42c1)
![Razorpay](https://img.shields.io/badge/Payments-Razorpay-0C2451)
![NVIDIA_NIM](https://img.shields.io/badge/AI-NVIDIA_NIM-76B900)
![Telegram](https://img.shields.io/badge/Bot-Telegram-2CA5E0?logo=telegram&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## Table of Contents

- [Overview](#overview)
- [Features](#-features)
- [Telegram Chatbot](#-telegram-chatbot)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#️-configuration)
- [AI & Chatbot Integration](#-ai--chatbot-integration)
- [Payments and Billing](#-payments-and-billing)
- [Security Features](#-security-features)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)
- [Troubleshooting](#troubleshooting)

---

## Overview

LuxeEstate unifies listing management, customer communication, and revenue workflows in one application. The platform is designed for three core groups:

- **Buyers/Tenants**: discover, compare, save, and inquire about properties.
- **Agents/Owners**: publish and manage listings, respond to leads, and promote properties.
- **Administrators**: track platform growth, engagement, and revenue metrics.

It includes built-in support for authentication, OTP verification, favorites, messaging, payments, AI tooling, Telegram chatbot, and analytics dashboards.

---

## 🌟 Features

### Core Platform
- **Property Management**: Browse, search, and manage premium real estate listings
- **Advanced Filtering**: Filter properties by location, price, amenities, and more
- **Favorites System**: Save and manage favorite properties
- **User Profiles**: Comprehensive user profiles with authentication and customization
- **Admin Dashboard**: Full administrative control and analytics
- **Home and listing pages** with pagination
- **Rich property detail pages**
- **Add, edit, and delete** listing workflow
- **My Properties view** for owners/agents
- **Geocoding retry support** and nearby places integration

### AI & Chatbot Integration
- **NVIDIA NIM Integration**: Advanced AI model integration for intelligent property recommendations
- **Intelligent Chatbot**: AI-powered conversational chatbot for property inquiries and customer support
- **Smart Property Search**: AI-enhanced property discovery and matching
- **Image Search**: Advanced image-based property search capabilities
- **Configurable AI behavior** through environment variables
- **Chatbot system prompt management** for flexible behavior control

### Telegram Chatbot
- **Full Telegram Bot Integration**: Real-time property assistance via Telegram
- **City-based Property Search**: Find properties by city name
- **Amenities Info**: Ask about amenities for any property
- **Nearby Places**: Get nearby hospitals, schools, malls, metro, etc.
- **Distance & Travel Times**: Distance in km with travel time by Walking, Cycling, Bus, Driving, Train, and Flight
- **Price Queries**: Get property prices in Lakhs/Crores
- **Area/Sqft Info**: Property size details
- **BHK/Bedroom Details**: Room configuration info
- **Furnishing Status**: Furnished/unfurnished details
- **Payment Methods**: Full payment options info
- **Appointment Scheduling**: Book site visits with date/time
- **Contact Number Handling**: Save contact for appointment confirmation
- **Date & Time Queries**: Current date, time, tomorrow's date, yesterday
- **Small Talk Handling**: Greetings, farewells, thank you responses
- **Stale State Reset**: Automatically resets filters when switching cities
- **Pasted Property Title Support**: Ask questions about a specific property by pasting its title

### Communication & Messaging
- **Real-time Messaging**: WebSocket-based instant messaging between users
- **Conversation Management**: Organized conversation threads
- **Message History**: Full message tracking and archiving
- **User Notifications**: Real-time notification system
- **Agent contact and lead** conversations

### Payments & Subscriptions
- **Payment Integration**: Secure payment processing with Razorpay
- **Subscription Packages**: Multiple tier packages for different user levels
- **Payment History**: Transaction tracking and management
- **Invoice Generation**: Automated invoice creation
- **Package-based promotion** purchase flow
- **Subscription detail and cancellation** flow
- **Webhook processing** with event persistence

### Search & Discovery
- **Keyword and filter-based** property search
- **AJAX filter and city** endpoints
- **Search suggestions** endpoint
- **Property comparison** add/list/clear workflows
- **Search by image** with visual feature extraction

### Authentication & Accounts
- Email/password registration and login
- OTP verification and resend support
- Google OAuth sign-in (Allauth provider integration)
- Profile completion and management
- Password change flow
- Social authentication options

### Additional Features
- **SEO Optimization**: Sitemap, robots.txt, and SEO-friendly URLs
- **Privacy & Security**: GDPR-compliant privacy policy, terms of service, cookie management
- **Mobile Responsive**: Fully responsive design for all devices
- **Email Notifications**: Automated email system for user updates
- **Central admin dashboard** with analytics
- **User, Property, Revenue, and Engagement analytics**

---

## 🤖 Telegram Chatbot

### What You Can Ask

| Question Type | Example |
|---|---|
| Property search | "show me properties in Mumbai" |
| Amenities | "what amenities are available in Pune" |
| Nearby places | "nearby places in Ahmedabad" |
| Distance & travel | "distance to hospital in Hyderabad" |
| Travel by mode | "distance by bus train walking in Kochi" |
| Price | "what is the price of properties in Mumbai" |
| Area/Sqft | "how many square feet in Kochi property" |
| BHK/Bedrooms | "how many bedrooms in Kolkata" |
| Furnishing | "furnished properties in Pune" |
| Payment methods | "what are the payment methods" |
| Appointment | "schedule appointment on 6th May at 5pm for this property: ..." |
| Contact | "my contact number is 9876543210" |
| Date/Time | "today is which day?" / "what is the current time?" |
| Tomorrow | "tomorrow is which date?" |
| Greetings | "hi", "hello", "bye", "thank you", "ok bye" |

### Travel Modes Supported
For every nearby place with a known distance, the bot shows:
- **Walking** (5 km/h)
- **Cycling** (15 km/h)
- **Bus** (25 km/h)
- **Driving** (40 km/h)
- **Train** (60 km/h)
- **Flight** (800 km/h + 90 min airport overhead, for 150+ km)

### Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your-bot-token
   SITE_URL=https://yourdomain.com
   ```
3. Set webhook:
   ```bash
   python manage.py setup_telegram_webhook
   ```
4. Webhook endpoint: `/telegram/webhook/`

---

## 🔐 Security Features

- **CSRF Protection**: All forms protected against Cross-Site Request Forgery
- **XSS Prevention**: Template escaping against Cross-Site Scripting
- **SQL Injection Prevention**: Django ORM parameterized queries
- **Secure Password Hashing**: PBKDF2 algorithm with salt
- **HTTPS Ready**: Production HTTPS configuration
- **Environment Variable Isolation**: Secrets stored in `.env` (not committed)
- **Rate Limiting**: API endpoint rate limiting
- **Secure Session Management**: Secure cookie settings
- **OAuth Integration**: Google OAuth for secure authentication
- **Webhook Validation**: Signature verification for Razorpay webhooks

---

## 🧪 Testing

### Run Tests

```bash
python manage.py test
```

### Pre-Release Checks

```bash
python manage.py check
python manage.py test accounts
python manage.py test properties
python manage.py test messaging
python manage.py test payments
python manage.py test favorites
```

### Manual Testing Recommendations

- Authentication and OTP flows
- Property create/edit/delete operations
- Search, filtering, and comparison features
- Messaging and real-time notifications
- Payment success/failure and webhook processing
- AI chatbot functionality
- Telegram chatbot all question types
- Image-based property search
- Admin dashboard analytics
- Email delivery verification

---

## 📦 Deployment

### Development Server

```bash
python manage.py runserver
```

### Production Deployment Checklist

- Set `DEBUG=False` in `.env`
- Configure production `ALLOWED_HOSTS`
- Use secure production `SECRET_KEY` (generate new one)
- Enable HTTPS and secure cookie settings
  ```python
  CSRF_COOKIE_SECURE = True
  SESSION_COOKIE_SECURE = True
  ```
- Use PostgreSQL or MySQL instead of SQLite
- Configure persistent media/static file storage (S3 recommended)
- Run `python manage.py collectstatic --noinput`
- Configure background job strategy for periodic tasks
- Add monitoring, alerting, and backup policies
- Set up proper logging and error tracking
- Configure email service for production
- Enable HSTS headers
- Set up rate limiting and DDoS protection

### Using Gunicorn (Recommended)

```bash
pip install gunicorn
gunicorn LuxeEstate.wsgi:application --bind 0.0.0.0:8000
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes following code style guidelines
4. Write/update tests for new functionality
5. Commit changes (`git commit -m 'Add AmazingFeature'`)
6. Push to branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request with detailed description

---

## 📝 License

This repository is intended for educational, development, and commercial use.
Refer to LICENSE file for specific terms.

---

## 📞 Support & Community

- **Issues**: Report bugs via [GitHub Issues](https://github.com/jainam-shah-18/LuxeEstate/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/jainam-shah-18/LuxeEstate/discussions)

---

## 👥 Authors

- **Jainam Shah** - Project Lead & Architecture
- Contributors and community members

---

## 📈 Roadmap

**In Development:**
- [ ] Advanced analytics dashboard enhancements
- [ ] Mobile app (iOS/Android)
- [ ] Machine learning property recommendations
- [ ] Virtual property tours with 360°
- [ ] Multi-language chatbot support
- [ ] Mobile push notifications

**Planned Features:**
- [ ] Video walkthrough system
- [ ] Blockchain property verification
- [ ] Advanced reporting suite
- [ ] CRM integration
- [ ] API marketplace

---

## Management Commands

### Send Follow-up Messages

```bash
python manage.py send_followups
```

### Setup Payment Packages

```bash
python manage.py setup_payment_packages
```

### Setup Telegram Webhook

```bash
python manage.py setup_telegram_webhook
```

---

## Route Map

| Route Prefix | Module | Purpose |
|---|---|---|
| `/` | Properties | Home, listings, details, search, comparison |
| `/auth/` | Accounts | Registration, login, OTP, profile |
| `/accounts/` | Django Allauth | Social authentication, account management |
| `/favorites/` | Favorites | Save/manage favorite properties |
| `/messaging/` | Messaging | Conversations, real-time messaging |
| `/payments/` | Payments | Pricing, checkout, subscriptions, webhooks |
| `/dashboard/` | Admin Dashboard | Analytics and metrics |
| `/admin/` | Django Admin | Administrative interface |
| `/api/` | REST API | API endpoints for mobile/external apps |
| `/telegram/` | Telegram Bot | Webhook endpoint for Telegram bot |

**Static Info Pages:**
- `/about/` - About LuxeEstate
- `/terms/` - Terms of Service
- `/privacy/` - Privacy Policy
- `/cookies/` - Cookie Policy
- `/sitemap/` - XML sitemap for SEO

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 6.x
- **Database**: SQLite (Development) / PostgreSQL (Production Ready)
- **API**: Django REST Framework
- **Real-time**: Django Channels with WebSocket support
- **Authentication**: Django Allauth with social OAuth
- **AI Integration**: NVIDIA NIM API
- **Telegram Bot**: python-telegram-bot / Telegram Webhook API

### Frontend
- **Template Engine**: Django Templates
- **Styling**: CSS3, Bootstrap
- **JavaScript**: AJAX, WebSockets
- **Image Processing**: Pillow

### Infrastructure & Services
- **Email**: SMTP configuration with fallback
- **Media Storage**: Local file system (scalable to S3)
- **Logging**: Python logging with file rotation
- **Static Files**: WhiteNoise for production serving
- **Payments**: Razorpay integration with webhooks
- **Maps/Geocoding**: Google Maps & Places API

| Layer | Tools |
|---|---|
| Backend | Python, Django 6.x |
| API | Django REST Framework |
| Auth | Django Allauth, Google OAuth |
| Realtime | Django Channels, Daphne |
| Payments | Razorpay SDK + webhook handlers |
| AI | NVIDIA NIM integrations |
| Telegram | Telegram Bot API (webhook) |
| Frontend | Django Templates, JavaScript, CSS |
| Data | SQLite (default), configurable DB backend |
| Static Delivery | WhiteNoise |

---

## 📋 Project Structure

```
LuxeEstate/
├── accounts/                        # User authentication, OTP, profile management
├── properties/                      # Property listings, search, AI features, chatbot
│   ├── chatbot_service.py           # Core chatbot logic with all question handlers
│   ├── chatbot_system_prompt.py     # AI system prompt and scope rules
│   ├── telegram_bot.py              # Telegram update/callback handler
│   ├── telegram_integration.py      # Telegram session management
│   ├── telegram_views.py            # Telegram webhook view
│   ├── telegram_urls.py             # Telegram URL routing
│   └── management/commands/
│       └── setup_telegram_webhook.py
├── messaging/                       # Real-time WebSocket messaging system
├── payments/                        # Payment processing, subscriptions, webhooks
├── favorites/                       # Favorite properties tracking
├── admin_dashboard/                 # Administrator analytics interface
├── LuxeEstate/                      # Main project settings, ASGI/WSGI config
├── static/                          # CSS, JavaScript assets
├── templates/                       # HTML templates
├── media/                           # User-uploaded property images
├── logs/                            # Application log files
├── manage.py                        # Django management script
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (not committed)
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip or conda package manager
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jainam-shah-18/LuxeEstate.git
   cd LuxeEstate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: `http://localhost:8000`
   - Admin dashboard: `http://localhost:8000/admin`

---

## ⚙️ Configuration

### Environment Variables (.env)

Core Settings:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

Database:
```
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Email Configuration:
```
EMAIL_BACKEND=smtp_backend.CustomEmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@luxeestate.com
```

NVIDIA NIM Configuration:
```
NVIDIA_API_KEY=your-nvidia-api-key
NIM_CHAT_MODEL=meta/llama-3.1-8b-instruct
NVIDIA_VISION_MODEL=nvidia/neva-22b
AI_CHATBOT_GUIDELINES=Professional property assistance guidelines
```

Telegram Bot:
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
SITE_URL=https://yourdomain.com
```

Social Authentication:
```
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GOOGLE_MAPS_API_KEY=your-google-maps-key
GOOGLE_PLACES_API_KEY=your-google-places-key
```

Payment Configuration:
```
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret
PAYMENT_TEST_MODE=True
```

Realtime Communication:
```
CHANNEL_LAYERS_HOST=localhost
CHANNEL_LAYERS_PORT=6379
```

---

## 💳 Payments and Billing

### Implemented Payment Features

- **Package Pricing**: Tiered subscription and promotion packages
- **Payment Processing**: Secure Razorpay integration
- **Payment Verification**: Real-time payment status confirmation
- **Success/Failure Flows**: Comprehensive payment result pages
- **Subscription Management**: Detail views and cancellation workflows
- **Invoice Management**: Automated invoice generation and viewing
- **Webhook Processing**: Razorpay webhook ingestion and processing
- **Payment Auditing**: Complete payment lifecycle tracking
- **Event Persistence**: Webhook event storage for audit trails

### Razorpay Webhook Setup

Configure one of these endpoints in Razorpay dashboard:

- `/payments/webhook/razorpay/`
- `/payments/webhook/payment-gateway/` (alias)

Ensure `RAZORPAY_WEBHOOK_SECRET` in `.env` exactly matches dashboard configuration.

---

## 🤖 AI & Chatbot Integration

### NVIDIA NIM Integration

LuxeEstate leverages NVIDIA's NIM (NVIDIA Inference Microservice) for advanced AI capabilities:

**Features:**
- **Meta Llama 3.1 8B Instruct**: Conversational property assistance
- **NVIDIA NEVA 22B**: Advanced image understanding for property images
- **Configurable System Prompts**: Flexible chatbot behavior via `AI_CHATBOT_GUIDELINES`
- **Real-time Inference**: Low-latency AI responses

**Setup:**
1. Obtain NVIDIA API Key from [api.nvidia.com](https://api.nvidia.com)
2. Configure in `.env`:
   ```
   NVIDIA_API_KEY=nvapi-xxxxx...
   NIM_CHAT_MODEL=meta/llama-3.1-8b-instruct
   NVIDIA_VISION_MODEL=nvidia/neva-22b
   ```

---

## Troubleshooting

### Telegram Bot Issues

**Problem**: Bot not responding
- Verify `TELEGRAM_BOT_TOKEN` is correct in `.env`
- Check webhook is set: `python manage.py setup_telegram_webhook`
- Ensure server is publicly accessible (use ngrok for local dev)
- Check `telegram_debug.log` for errors

**Problem**: "No listings found" on every message
- Clear stale conversation state:
  ```bash
  python manage.py shell -c "from properties.models import TelegramUser; TelegramUser.objects.all().update(conversation_state={})"
  ```
- Restart the Django server to reload updated code

### OTP/Email Issues

**Problem**: Emails not being sent
- Verify SMTP credentials in `.env`
- Check Gmail app-specific password (if using Gmail)
- Test with debug email backend locally

### Payment Issues

**Problem**: Webhook not processing
- Re-check Razorpay keys and webhook secret in `.env`
- Confirm webhook URL is reachable from internet (test with ngrok)
- Check payment webhook logs in database

### AI/Chatbot Issues

**Problem**: Chatbot not responding
- Verify `NVIDIA_API_KEY` is correct and active
- Check NVIDIA NIM API status
- Ensure `NIM_CHAT_MODEL` is valid

### Database Issues

**Problem**: Migration failures
```bash
python manage.py showmigrations
python manage.py migrate properties
```

### WebSocket/Messaging Issues

**Problem**: Real-time messaging not working
- Verify Django Channels is installed: `pip list | grep channels`
- Check `CHANNEL_LAYERS` configuration in settings
- Ensure Redis is running (if using Redis backend)

---

**Last Updated**: May 5, 2026

For more information and latest updates, visit the [GitHub repository](https://github.com/jainam-shah-18/LuxeEstate)
