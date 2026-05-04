# LuxeEstate - Premium Real Estate Platform

Professional real estate platform built with Django for property discovery, user engagement, AI-assisted search, and payment-enabled listing promotion.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/API-Django_REST_Framework-red)
![Channels](https://img.shields.io/badge/Realtime-Django_Channels-6f42c1)
![Razorpay](https://img.shields.io/badge/Payments-Razorpay-0C2451)
![NVIDIA_NIM](https://img.shields.io/badge/AI-NVIDIA_NIM-76B900)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## Table of Contents

- [Overview](#overview)
- [🌟 Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [📋 Project Structure](#-project-structure)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration](#️-configuration)
- [🤖 AI & Chatbot Integration](#-ai--chatbot-integration)
- [💳 Payments and Billing](#-payments-and-billing)
- [🔐 Security Features](#-security-features)
- [📚 Documentation](#-documentation)
- [🧪 Testing](#-testing)
- [📦 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📝 License](#-license)
- [Troubleshooting](#troubleshooting)

---

## Overview

LuxeEstate unifies listing management, customer communication, and revenue workflows in one application. The platform is designed for three core groups:

- **Buyers/Tenants**: discover, compare, save, and inquire about properties.
- **Agents/Owners**: publish and manage listings, respond to leads, and promote properties.
- **Administrators**: track platform growth, engagement, and revenue metrics.

It includes built-in support for authentication, OTP verification, favorites, messaging, payments, AI tooling, and analytics dashboards.

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

## 📚 Documentation

Comprehensive documentation guides are available:

- [CHATBOT_INTEGRATION.md](CHATBOT_INTEGRATION.md) - Chatbot setup, configuration, and API details
- [CHATBOT_GUIDE.md](CHATBOT_GUIDE.md) - End-user chatbot guide and workflows
- [NVIDIA_NIM_SETUP.md](NVIDIA_NIM_SETUP.md) - AI model integration and NVIDIA NIM setup
- [QUICK_START.md](QUICK_START.md) - Quick start guide for new developers
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Detailed implementation overview
- [VERIFICATION.md](VERIFICATION.md) - Testing checklist and verification procedures
- [.env.example](.env.example) - Environment configuration template

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
- Image-based property search
- Admin dashboard analytics
- Email delivery verification

See [VERIFICATION.md](VERIFICATION.md) for comprehensive testing checklist.

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

### Docker Deployment (Optional)

Create `Dockerfile` and `docker-compose.yml` for containerized deployment.

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
- **Documentation**: See docs/ folder for detailed guides

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

Triggers chatbot-driven automated follow-up handling for leads and appointments.

### Setup Payment Packages

```bash
python manage.py setup_payment_packages
```

Helper command for payment package initialization and management.

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
| Frontend | Django Templates, JavaScript, CSS |
| Data | SQLite (default), configurable DB backend |
| Static Delivery | WhiteNoise |

---

## 📋 Project Structure

```
LuxeEstate/
├── accounts/              # User authentication, OTP, profile management
├── properties/            # Property listings, search, AI features, chatbot
├── messaging/            # Real-time WebSocket messaging system
├── payments/             # Payment processing, subscriptions, webhooks
├── favorites/            # Favorite properties tracking
├── admin_dashboard/      # Administrator analytics interface
├── LuxeEstate/           # Main project settings, ASGI/WSGI config
├── static/               # CSS, JavaScript assets
├── staticfiles/          # Collected static files for production
├── templates/            # HTML templates
├── media/               # User-uploaded property images
├── logs/                # Application log files
├── docs/                # Documentation and guides
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not committed)
└── README.md           # This file
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
NIM_CHAT_MODEL=meta/llama-2-7b-chat-q8_0
NVIDIA_VISION_MODEL=nvidia/neva-22b
AI_CHATBOT_GUIDELINES=Professional property assistance guidelines
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

For complete list, see [.env.example](.env.example)

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

### Payment Packages

The platform supports multiple subscription tiers:
- Basic, Premium, Elite packages
- Property listing promotions
- Featured property placements
- Custom package creation via admin

---

## 🤖 AI & Chatbot Integration

### NVIDIA NIM Integration

LuxeEstate leverages NVIDIA's NIM (NVIDIA Inference Microservice) for advanced AI capabilities:

**Features:**
- **Meta Llama 2 7B Chat**: Conversational property assistance
- **NVIDIA NEVA 22B**: Advanced image understanding for property images
- **Configurable System Prompts**: Flexible chatbot behavior via `AI_CHATBOT_GUIDELINES`
- **Real-time Inference**: Low-latency AI responses

**Setup:**
1. Obtain NVIDIA API Key from [api.nvidia.com](https://api.nvidia.com)
2. Configure in `.env`:
   ```
   NVIDIA_API_KEY=nvapi-xxxxx...
   NIM_CHAT_MODEL=meta/llama-2-7b-chat-q8_0
   NVIDIA_VISION_MODEL=nvidia/neva-22b
   ```
3. Refer to [NVIDIA_NIM_SETUP.md](NVIDIA_NIM_SETUP.md) for detailed setup

### Chatbot Features

- **Property Inquiries**: Answer questions about listings
- **Smart Recommendations**: AI-powered property suggestions
- **Lead Qualification**: Automated lead assessment
- **Follow-up Automation**: Scheduled follow-up messages
- **Multi-turn Conversations**: Context-aware dialogues
- **Configurable Behavior**: System prompt customization

### AI Capabilities

1. **Description Generation**: Auto-generate property descriptions from metadata
2. **Image Search**: Visual similarity matching across listings
3. **Chatbot Support**: Conversational AI for customer support
4. **Smart Matching**: AI-powered property-to-buyer matching

For detailed guides:
- [CHATBOT_INTEGRATION.md](CHATBOT_INTEGRATION.md) - Setup & configuration
- [CHATBOT_GUIDE.md](CHATBOT_GUIDE.md) - User guide
- [NVIDIA_NIM_SETUP.md](NVIDIA_NIM_SETUP.md) - AI model setup

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

## Troubleshooting

### OTP/Email Issues

**Problem**: Emails not being sent
- **Solution**: Verify SMTP credentials in `.env`
- Check Gmail app-specific password (if using Gmail)
- Enable "Less secure apps" if using older email providers
- Review app logs for TLS/certificate errors
- Test with debug email backend locally

**Command to test email:**
```bash
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Payment Issues

**Problem**: Webhook not processing
- Re-check Razorpay keys and webhook secret in `.env`
- Confirm webhook URL is reachable from internet (test with ngrok)
- Check payment webhook logs in database
- Verify signature calculation matches Razorpay format

**Problem**: Payment verification failing
- Ensure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are correct
- Check payment status in Razorpay dashboard
- Review database payment records for status

### AI/Chatbot Issues

**Problem**: Chatbot not responding
- Verify `NVIDIA_API_KEY` is correct and active
- Check NVIDIA NIM API status
- Review chatbot logs for API errors
- Ensure `NIM_CHAT_MODEL` is valid
- Test API key: `curl -H "Authorization: Bearer $NVIDIA_API_KEY" https://integrate.api.nvidia.com/v1/models`

**Problem**: Image search not working
- Verify `NVIDIA_VISION_MODEL` is configured
- Check image file size and format (JPEG, PNG recommended)
- Review image processing logs
- Ensure vision model API key is active

### Static/Media Files Issues

**Problem**: Static files not loading in production
- Re-run `python manage.py collectstatic --noinput`
- Verify static files directory permissions
- Check WhiteNoise configuration
- Review web server static file serving config (nginx, Apache)

**Problem**: Media uploads not working
- Check media directory permissions
- Verify `MEDIA_URL` and `MEDIA_ROOT` settings
- Ensure disk space available
- Check file upload size limits in settings

### Database Issues

**Problem**: Migration failures
```bash
# Check migration status
python manage.py showmigrations

# Migrate specific app
python manage.py migrate accounts

# View specific migration
python manage.py sqlmigrate accounts 0001_initial
```

**Problem**: Foreign key constraint errors
- Ensure related objects exist before creation
- Check data integrity in admin interface
- Review recent model changes

### WebSocket/Messaging Issues

**Problem**: Real-time messaging not working
- Verify Django Channels is installed: `pip list | grep channels`
- Check `CHANNEL_LAYERS` configuration in settings
- Ensure Redis is running (if using Redis backend)
- Test WebSocket connection: Check browser console for connection errors
- Review Daphne/ASGI server logs

### General Debugging

Enable verbose logging:
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

Check application logs:
```bash
tail -f logs/django.log
python manage.py runserver --verbosity 2
```

---

**Last Updated**: May 4, 2026

For more information and latest updates, visit the [GitHub repository](https://github.com/jainam-shah-18/LuxeEstate)
