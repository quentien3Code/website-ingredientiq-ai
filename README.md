# IngredientIQ Backend

A comprehensive **Food Safety & Nutrition Analysis Platform** built with Django REST Framework, featuring AI-powered ingredient analysis, personalized health insights, and a React-based admin panel.

## 🚀 Features

- **AI-Powered Analysis**: GPT-4 Turbo integration for personalized health insights
- **Ingredient Analysis**: OCR-based label scanning + barcode product lookup
- **Deterministic Risk Engine**: Three-tier priority system for allergen detection
- **Confidence Engine**: Geometric mean calculation for analysis accuracy
- **Admin Panel**: React-based dashboard for content management
- **Public Website**: Landing page and marketing content
- **Subscription System**: Stripe integration for premium features

## 🌐 Live Site

- **Website**: https://www.ingredientiq.ai
- **Admin Panel**: https://www.ingredientiq.ai/control-panel/

## 📁 Project Structure

```
website-ingredientiq-ai/
├── foodanalysis/          # Django project configuration
│   ├── settings.py        # Main settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI application
│
├── foodinfo/              # Core API application
│   ├── models.py          # Database models
│   ├── views.py           # API endpoints
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # API routes
│   ├── confidence_engine.py
│   └── enhanced_ai_analysis.py
│
├── panel/                 # Admin panel backend
│   ├── views.py           # Admin API endpoints
│   └── urls.py            # Admin routes
│
├── Website/               # Public website backend
│   ├── views.py           # Website API endpoints
│   └── urls.py            # Website routes
│
├── frontend/              # Consolidated frontend assets
│   ├── website/           # React public website (compiled)
│   │   ├── index.html
│   │   ├── static/
│   │   ├── images/
│   │   └── css/, js/
│   └── admin/             # React admin panel (compiled)
│       ├── index.html
│       └── static/
│
├── data/                  # API data files
│   └── food.json          # Food labels reference data
│
├── templates/             # Django templates
├── static/                # Shared static files (service workers)
├── nginx/                 # Nginx configuration
│
├── docs/                  # Documentation
├── scripts/               # Utility scripts
│
├── docker-compose.yml     # Docker orchestration
├── Dockerfile             # Backend container
├── requirements.txt       # Python dependencies
└── manage.py              # Django CLI
```

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 4.2.20, Django REST Framework |
| **AI/ML** | OpenAI GPT-4 Turbo, Custom Confidence Engine |
| **Database** | PostgreSQL (Railway) |
| **Frontend** | React (pre-built in `frontend/website/` and `frontend/admin/`) |
| **Auth** | JWT, OAuth2 (Google, Apple) |
| **Payments** | Stripe |
| **Hosting** | Railway.com |
| **Storage** | AWS S3 |
| **Domain** | www.ingredientiq.ai |

## 🚦 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (production) or SQLite (development)
- Docker & Docker Compose (optional)

## Production Required: `DJANGO_SECRET_KEY`

This service uses Django sessions + CSRF protection. The `SECRET_KEY` must be stable across restarts and across multiple Gunicorn workers/instances.

- In production (`DEBUG=False`), `DJANGO_SECRET_KEY` is required. If it is missing, the app will fail-fast at startup.
- In development (`DEBUG=True`), you can opt-in to an ephemeral key by setting `ALLOW_INSECURE_DEV_SECRET_KEY=1` (sessions will not survive restarts).

Generate a new key (do not hardcode it in the repo):

`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/quentien3Code/website-ingredientiq-ai.git
   cd website-ingredientiq-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d
```

## 🔗 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/foodapp/` | Core API (scanning, analysis, user profiles) |
| `/master/` | Admin panel API |
| `/web/` | Public website API (blogs, FAQs, etc.) |
| `/admin/` | Django admin interface |
| `/control-panel/` | React admin dashboard |
| `/launch` | Landing page |

## 📚 Documentation

- [Railway Deployment](docs/RAILWAY_DEPLOYMENT.md) - **Complete Railway deployment guide**
- [Project Handover](docs/HANDOVER.md) - Complete system documentation
- [Account Deletion](docs/ACCOUNT_DELETION.md) - User account lifecycle
- [Build & Serving](docs/BUILD_SERVING.md) - React build configuration
- [Cleanup Summary](CLEANUP_SUMMARY.md) - Project cleanup and mobile removal details

## 🔐 Security Notes

- Never commit `.env` files
- Never commit Firebase Admin SDK JSON files
- All API keys should be stored as environment variables
- See `.env.example` for required configuration

## 📝 License

Proprietary - All Rights Reserved

## 👥 Contact

For questions about this project, contact the development team.
