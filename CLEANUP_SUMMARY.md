# Project Cleanup Summary - January 8, 2026

## ✅ Final Clean State

This project has been thoroughly cleaned and prepared for Railway deployment at `www.ingredientiq.ai`.

### What Was Removed

**Mobile App Files (Surgical Removal):**
- Firebase push notification system (`firebase_service.py`, `notification_*.py`)
- Celery background tasks (`celery.py`, `tasks.py`)
- Barcode scanner optimization
- Mobile-specific API endpoints
- Service workers (`firebase-messaging-sw.js`, `sw.js`)

**AWS/Docker Infrastructure:**
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- `nginx/` folder
- `auto-deploy.sh` (AWS deployment script)
- `bitbucket-pipelines.yml` (CI/CD)

**Legacy/Duplicate Files:**
- `build/` folder (migrated to `frontend/website/`)
- `react_admin/` folder (migrated to `frontend/admin/`)
- `_archived/` folder (backup files)
- `scripts/` folder (one-time cleanup scripts)
- Old documentation (`README_OLD_AWS.md`, `BUILD_SERVING_GUIDE.md`, etc.)

**Security Risks:**
- Firebase Admin SDK JSON credentials
- Hardcoded secrets in settings.py
- Original .env with exposed credentials
- SQLite database

---

## 📁 Final Project Structure

```
website-ingredientiq-ai/
├── .gitignore              # Git ignore patterns
├── .env.example            # Environment template
├── .env                    # Local config (not committed)
├── manage.py               # Django CLI
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── CLEANUP_SUMMARY.md      # This file
│
├── railway.json            # Railway deployment config
├── Procfile                # Process definition
├── nixpacks.toml           # Nixpacks build config
│
├── foodanalysis/           # Django project config
│   ├── settings.py         # Main settings (secured)
│   ├── urls.py             # URL routing + health check
│   └── wsgi.py             # WSGI application
│
├── foodinfo/               # Core API (website/admin only)
│   ├── models.py           # Database models
│   ├── views.py            # API endpoints
│   ├── urls.py             # API routes
│   ├── serializers.py      # DRF serializers
│   ├── enhanced_ai_analysis.py
│   ├── confidence_engine.py
│   └── ...
│
├── panel/                  # Admin panel backend
│   ├── views.py
│   └── urls.py
│
├── Website/                # Public website backend
│   ├── views.py
│   └── urls.py
│
├── frontend/               # React builds
│   ├── website/            # Public website
│   │   ├── index.html
│   │   └── static/
│   └── admin/              # Admin panel
│       ├── index.html
│       └── static/
│
├── data/                   # API data files
│   └── food.json
│
├── static/                 # Shared static files
│   └── manifest.json
│
├── templates/              # Django templates
│
└── docs/                   # Documentation
    └── RAILWAY_DEPLOYMENT.md
```

---

## ⚠️ CRITICAL: Rotate These Credentials

The following were EXPOSED in the original repo and MUST be rotated before production:

| Service | What to Rotate |
|---------|---------------|
| **AWS** | Access Key ID, Secret Access Key |
| **Stripe** | Secret Key, Webhook Secret |
| **Google OAuth** | Client ID, Client Secret |
| **Apple OAuth** | All credentials |
| **Email** | Gmail app password |
| **USDA/Foursquare/Unsplash** | API keys |
| **Twilio** | Account SID, Auth Token |
| **Django** | Generate new SECRET_KEY |

---

## 🚀 Ready for Railway Deployment

1. Push to GitHub
2. Connect to Railway
3. Add PostgreSQL database
4. Set environment variables (see `.env.example`)
5. Configure custom domain: `www.ingredientiq.ai`

See [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md) for complete instructions.
