# Project Cleanup Summary - January 8, 2026 (Updated)

## ✅ Final Clean State

This project has been thoroughly cleaned and deployed to Railway at `www.ingredientiq.ai`.

**Mobile app discontinued.** Only the website and admin panel remain.

---

## Phase 1: Initial Cleanup (Secrets & Infrastructure)

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

**Security Risks Fixed:**
- Firebase Admin SDK JSON credentials removed
- Hardcoded secrets in settings.py removed
- Original .env with exposed credentials removed
- SQLite database excluded from git

---

## Phase 2: Deep Cleanup (Mobile App Code Removal)

**Lines Removed: ~27,294**

**Deleted Files:**
| File | Lines | Purpose |
|------|-------|---------|
| `foodinfo/views.py` | ~21,000 | Mobile API endpoints |
| `foodinfo/enhanced_ai_analysis.py` | ~1,200 | AI food analysis |
| `foodinfo/confidence_engine.py` | ~400 | Confidence scoring |
| `foodinfo/performance_optimization.py` | ~300 | Caching layer |
| `foodinfo/utils.py` | ~2,900 | FSA/medical APIs |
| `foodinfo/ssl_fix.py` | ~20 | SSL monkey-patch |
| `foodinfo/test.py` | - | Test file |
| `foodinfo/enhanced_methods.py` | - | Dead code |
| `foodinfo/forms.py` | - | Unused forms |
| `foodinfo/urls.py` | - | Mobile URL routes |
| `foodinfo/management/commands/sync_scan_counts.py` | - | Management command |

**Refactored Files:**
| File | Before | After | Change |
|------|--------|-------|--------|
| `foodinfo/serializers.py` | 395 lines | ~150 lines | Kept only admin panel serializers |
| `foodinfo/admin.py` | ~200 lines | ~40 lines | Only essential models |
| `foodinfo/utils.py` | ~2,900 lines | 5 lines | Emptied (not imported) |
| `requirements.txt` | 26 packages | 17 packages | Removed OCR/AI/CV |

**New Files:**
- `foodinfo/helpers.py` - Contains `safe_delete_user()` for admin panel

**Packages Removed from requirements.txt:**
- `easyocr` - OCR for mobile scanning
- `numpy` - Used by easyocr
- `open-clip-torch` - AI image analysis
- `opencv-python-headless` - Image processing
- `pytesseract` - OCR
- `azure-cognitiveservices-vision-computervision` - Azure AI
- `pytrends` - Google trends
- `geopy` - Geolocation

---

## 📁 Final Project Structure

```
website-ingredientiq-ai/
├── manage.py               # Django CLI
├── requirements.txt        # Python dependencies (trimmed)
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
├── foodinfo/               # Core models & serializers
│   ├── models.py           # User, FAQ, DownloadPDF, etc.
│   ├── serializers.py      # Admin panel serializers only
│   ├── admin.py            # Django admin registrations
│   ├── helpers.py          # safe_delete_user()
│   ├── permissions.py      # IsSuperAdmin permission
│   └── utils.py            # Empty (placeholder)
│
├── panel/                  # Admin panel backend
│   ├── views.py            # Admin API endpoints
│   ├── urls.py             # Admin routes
│   └── utils/              # Response helpers
│
├── Website/                # Public website backend
│   ├── views.py            # Website API endpoints
│   ├── urls.py             # Website routes
│   └── models.py           # Blog, RelatedPosts, etc.
│
├── frontend/               # React builds
│   ├── website/            # Public website
│   │   ├── index.html
│   │   └── static/
│   └── admin/              # Admin panel
│       ├── index.html
│       └── static/
│
├── static/                 # Shared static files
│   └── manifest.json
│
├── templates/              # Django templates
│
└── docs/                   # Documentation
    ├── RAILWAY_DEPLOYMENT.md
    ├── ADMIN_PANEL_AUDIT.md
    ├── ACCOUNT_DELETION.md
    └── HANDOVER.md
```

---

## Models Kept in foodinfo

| Model | Purpose |
|-------|---------|
| `User` | Custom user model (AUTH_USER_MODEL) |
| `UserSubscription` | Premium subscriptions |
| `AccountDeletionRequest` | GDPR deletion tracking |
| `FAQ` | FAQ content for website |
| `AboutUS` | About page content |
| `privacypolicy` | Privacy policy content |
| `Termandcondition` | Terms & conditions |
| `DownloadPDF` | PDF downloads |
| `DownloadRequest` | Download requests |
| `MonthlyScanUsage` | Usage tracking (may be removable) |
| `NotificationTemplate` | Email templates |

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
