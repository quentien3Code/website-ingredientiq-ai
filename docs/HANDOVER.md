# IngredientIQ Backend - Project Handover Documentation

**Project Name:** IngredientIQ Food Safety & Nutrition Analysis Platform  
**Version:** 2.3  
**Handover Date:** December 2024  
**Document Version:** 1.0

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Architecture & Technology Stack](#architecture--technology-stack)
4. [Core Features & Functionality](#core-features--functionality)
5. [API Documentation](#api-documentation)
6. [Database Schema](#database-schema)
7. [AI/ML Components](#aiml-components)
8. [Deployment & Infrastructure](#deployment--infrastructure)
9. [Configuration & Environment Variables](#configuration--environment-variables)
10. [Testing & Quality Assurance](#testing--quality-assurance)
11. [Maintenance & Support](#maintenance--support)
12. [Known Issues & Future Enhancements](#known-issues--future-enhancements)
13. [Contact & Support](#contact--support)

---

## 1. Executive Summary

### 1.1 Project Purpose

IngredientIQ is a comprehensive food safety and nutrition analysis platform that helps users make informed decisions about food products based on their personal health profiles, allergies, dietary preferences, and medical conditions. The platform uses AI-powered analysis, OCR technology, and regulatory databases to provide personalized health insights.

### 1.2 Key Achievements

- ✅ **AI-Powered Health Insights**: Implemented GPT-4 Turbo-based Insight Composer and Expert Advice Composer
- ✅ **Deterministic Risk Engine**: Three-tier priority system (Mandatory, Secondary, Preference)
- ✅ **Confidence Engine**: Geometric mean calculation with 0.72 defer threshold
- ✅ **Dual Scanning Methods**: OCR-based label scanning and barcode scanning
- ✅ **Real-time Analysis**: 2-3 second response time with parallel processing
- ✅ **Comprehensive API**: 50+ endpoints covering all platform features
- ✅ **Production-Ready**: Docker containerization, nginx reverse proxy, PostgreSQL database

### 1.3 Technology Highlights

- **Backend Framework**: Django 4.2.20 with Django REST Framework
- **AI/ML**: OpenAI GPT-4 Turbo, custom confidence engine, deterministic risk engine
- **Database**: PostgreSQL (production), SQLite (development)
- **Deployment**: Docker, Docker Compose, nginx, Gunicorn
- **Authentication**: JWT tokens, OAuth2 (Google, Apple)
- **Payment**: Stripe integration
- **Notifications**: Firebase Cloud Messaging (FCM)

---

## 2. Project Overview

### 2.1 System Architecture

The IngredientIQ backend is built as a **Django monolith** with the following logical components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                        │
│         (Mobile App, Web App, Admin Panel)                   │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ HTTPS/REST API
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                    Nginx Reverse Proxy                        │
│              (Port 80/443, SSL Termination)                    │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ HTTP
                         │
┌────────────────────────▼──────────────────────────────────────┐
│              Django Backend (Gunicorn)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Views      │  │   Models     │  │   Utils      │        │
│  │   (API)      │  │   (Data)     │  │   (Logic)    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   AI Engine  │  │   OCR        │  │   External   │        │
│  │   (GPT-4)    │  │   Processing │  │   APIs        │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────┬──────────────────────────────────────┘
                         │
         ┌────────────────┴────────────────┐
         │                                  │
┌────────▼────────┐              ┌─────────▼─────────┐
│   PostgreSQL    │              │   AWS S3 /        │
│   Database      │              │   Local Storage   │
└─────────────────┘              └───────────────────┘
```

### 2.2 Project Structure

```
foodapp_backend/
├── foodanalysis/              # Django project settings
│   ├── settings.py           # Main configuration
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py               # WSGI application
│   └── middleware.py        # Custom middleware
├── foodinfo/                  # Main application
│   ├── models.py             # Database models
│   ├── views.py              # API views (20,000+ lines)
│   ├── serializers.py        # Data serialization
│   ├── urls.py               # URL routing
│   ├── confidence_engine.py  # Confidence calculation
│   ├── enhanced_ai_analysis.py  # AI analysis
│   ├── utils.py              # Utility functions
│   └── management/           # Custom commands
├── panel/                     # Admin panel app
├── Website/                   # Website app
├── nginx/                     # Nginx configuration
│   ├── Dockerfile
│   └── default.conf
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Backend Docker image
├── requirements.txt          # Python dependencies
└── manage.py                # Django management
```

### 2.3 Key Components

1. **Food Safety Analysis Engine**
   - OCR-based label scanning
   - Barcode-based product lookup
   - Ingredient extraction and normalization
   - Nutrition data parsing

2. **Deterministic Risk Engine (DRE)**
   - Three-tier priority system
   - Allergen detection
   - Medical condition matching
   - Medication interaction checking

3. **AI Health Insights**
   - Insight Composer (3-section narrative)
   - Expert Advice Composer (2-section counseling)
   - GPT-4 Turbo integration
   - Word-budget enforcement

4. **Confidence Engine**
   - Geometric mean calculation
   - Multi-factor confidence scoring
   - Defer threshold (0.72)

5. **User Management**
   - Authentication & authorization
   - Profile management
   - Subscription management
   - Scan history

---

## 3. Architecture & Technology Stack

### 3.1 Technology Stack

#### Backend Framework
- **Django**: 4.2.20
- **Django REST Framework**: 3.15.2
- **Python**: 3.8.10

#### Database
- **PostgreSQL**: 15 (production)
- **SQLite**: 3 (development)

#### AI/ML
- **OpenAI GPT-4 Turbo**: Primary AI model
- **OpenAI GPT-3.5 Turbo**: Fallback (legacy)
- **Custom Confidence Engine**: Geometric mean calculation
- **Custom Deterministic Engine**: Rule-based risk assessment

#### OCR & Image Processing
- **EasyOCR**: 1.7.2
- **OpenCV**: 4.11.0.86
- **PIL/Pillow**: Image processing
- **AWS Textract**: Alternative OCR (optional)

#### External APIs
- **Open Food Facts**: Product database
- **FDA/OpenFDA**: Regulatory data
- **USDA FDC**: Nutrition database
- **EFSA/OpenFoodTox**: European safety data
- **PubMed/MedlinePlus**: Medical research
- **PubChem/TOXNET**: Toxicology data
- **SNOMED CT**: Medical terminology
- **ICD-10**: Disease classification

#### Authentication & Security
- **JWT**: djangorestframework-simplejwt 5.3.1
- **OAuth2**: django-allauth 65.5.0
- **CORS**: django-cors-headers 4.4.0

#### Payment Processing
- **Stripe**: 12.0.0

#### Notifications
- **Firebase Admin SDK**: 6.5.0
- **Twilio**: 9.5.2 (SMS)

#### Deployment
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **Nginx**: Reverse proxy
- **Gunicorn**: WSGI server

#### Storage
- **AWS S3**: boto3 1.37.13
- **Django Storages**: 1.14.5

### 3.2 Design Patterns

1. **MVC Pattern**: Django's Model-View-Controller architecture
2. **RESTful API**: REST principles for API design
3. **Service Layer**: Utility functions for business logic
4. **Repository Pattern**: Model abstraction layer
5. **Factory Pattern**: Object creation for complex models

### 3.3 Security Features

- **JWT Authentication**: Secure token-based auth
- **CORS Protection**: Cross-origin request handling
- **CSRF Protection**: Django's built-in CSRF middleware
- **SQL Injection Prevention**: Django ORM parameterized queries
- **XSS Protection**: Template auto-escaping
- **Rate Limiting**: Scan limits per user
- **Input Validation**: Serializer-based validation
- **SSL/TLS**: HTTPS enforcement (production)

---

## 4. Core Features & Functionality

### 4.1 Food Label Scanning (OCR)

**Endpoint**: `POST /foodapp/food-safety-check/`

**Functionality**:
- Accepts image file (JPG, PNG)
- Performs OCR using EasyOCR
- Extracts nutrition facts and ingredients
- Normalizes ingredient names
- Matches against user profile
- Generates AI health insights
- Returns comprehensive analysis

**Key Features**:
- Image preprocessing (enhancement, rotation)
- Multi-language OCR support
- Ingredient parsing and normalization
- Nutrition data extraction
- Safety status determination
- AI-powered insights

### 4.2 Barcode Scanning

**Endpoint**: `POST /foodapp/barcode/`

**Functionality**:
- Accepts barcode number or image
- Looks up product in Open Food Facts
- Fetches product data
- Performs same analysis as OCR scan
- Returns identical response structure

**Key Features**:
- Barcode validation
- Product database lookup
- Fallback to OCR if barcode fails
- Same AI analysis pipeline
- Consistent response format

### 4.3 Deterministic Risk Engine (DRE)

**Method**: `_apply_three_tier_priority()`

**Three-Tier System**:

1. **Tier 1 (Mandatory - No-Go)**:
   - Life-threatening allergens
   - Product recalls
   - Banned ingredients
   - Critical medication interactions

2. **Tier 2 (Secondary - Caution)**:
   - Condition-specific thresholds (diabetes, hypertension, etc.)
   - Sodium/sugar limits
   - FODMAP sensitivities
   - Moderate medication interactions

3. **Tier 3 (Preference - Go)**:
   - Dietary preferences (vegan, keto, etc.)
   - Health goals
   - Lifestyle choices

**Output**:
```json
{
  "status": "No-Go|Caution|Go",
  "tier1_hits": [...],
  "tier2_hits": [...],
  "tier3_hits": [...]
}
```

### 4.4 Confidence Engine

**File**: `foodinfo/confidence_engine.py`

**Functionality**:
- Calculates geometric mean of confidence factors
- Factors: OCR quality, barcode confidence, NER confidence, source reliability
- Threshold: 0.72 (if below, status = Defer)
- Returns confidence metadata for audit

**Formula**:
```
confidence = (ocr_quality × barcode_confidence × ner_confidence × source_reliability)^(1/4)
```

### 4.5 Insight Composer

**Method**: `get_insight_composer()`

**Functionality**:
- Generates 3-section narrative using GPT-4 Turbo
- Fixed system prompt (non-editable)
- Word-budget enforcement:
  - BLUF Insight: 30-80 words
  - Main Explanation: 50-100 words
  - Deeper Reference: 120-160 words
  - Total: ≤ 340 words
- Citation limit: ≤ 3 authorities
- Post-processing validation

**Output Structure**:
```json
{
  "bluf_insight": "...",
  "main_explanation": "...",
  "deeper_reference": "...",
  "disclaimer": "Informational, not diagnostic...",
  "word_counts": {
    "bluf_insight": 45,
    "main_explanation": 78,
    "deeper_reference": 142,
    "total": 265
  },
  "audit_log": {
    "model": "gpt-4-turbo",
    "prompt_hash": "...",
    "input_hash": "...",
    "timestamp": "..."
  }
}
```

### 4.6 Expert Advice Composer

**Method**: `get_expert_advice_composer()`

**Functionality**:
- Generates 2-section counseling using GPT-4 Turbo
- Fixed system prompt (non-editable)
- Word-budget enforcement:
  - Healthier Pathway: 120-150 words
  - Your Smarter Path: 120-150 words
  - Total: ≤ 270 words
- Citation limit: ≤ 2 authorities
- No product swaps or brand endorsements

**Output Structure**:
```json
{
  "healthier_pathway": "...",
  "your_smarter_path": "...",
  "word_counts": {
    "healthier_pathway": 135,
    "your_smarter_path": 142,
    "total": 277
  },
  "audit_log": {...}
}
```

### 4.7 User Management

**Features**:
- User registration and authentication
- Profile management (health conditions, allergies, preferences)
- Subscription management (Freemium, Premium plans)
- Scan history and favorites
- Settings (notifications, dark mode, language)
- Account deletion (GDPR compliant)

### 4.8 Subscription Management

**Features**:
- Stripe integration
- Multiple subscription tiers
- Scan limit enforcement
- Discount eligibility
- Subscription cancellation
- Webhook handling

### 4.9 Push Notifications

**Features**:
- Firebase Cloud Messaging (FCM)
- Lifecycle notifications (subscription expiry, scan limits)
- User preference management
- Device token management

---

## 5. API Documentation

### 5.1 Authentication Endpoints

#### Sign Up
```
POST /foodapp/signup/
Body: {
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securepassword"
}
Response: {
  "user": {...},
  "tokens": {
    "access": "...",
    "refresh": "..."
  }
}
```

#### Login
```
POST /foodapp/login/
Body: {
  "email": "user@example.com",
  "password": "securepassword"
}
Response: {
  "user": {...},
  "tokens": {...}
}
```

#### Google OAuth Login
```
POST /foodapp/login/google/
Body: {
  "access_token": "..."
}
Response: {
  "user": {...},
  "tokens": {...}
}
```

#### Apple Sign In
```
POST /foodapp/login/apple/
Body: {
  "identity_token": "...",
  "authorization_code": "..."
}
Response: {
  "user": {...},
  "tokens": {...}
}
```

#### Forgot Password
```
POST /foodapp/forgot-password/
Body: {
  "email": "user@example.com"
}
Response: {
  "message": "OTP sent to email"
}
```

#### Verify OTP
```
POST /foodapp/verifyotp/
Body: {
  "email": "user@example.com",
  "otp": "123456"
}
Response: {
  "message": "OTP verified",
  "reset_token": "..."
}
```

#### Change Password
```
POST /foodapp/change-password/
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "old_password": "...",
  "new_password": "..."
}
```

### 5.2 Food Analysis Endpoints

#### OCR Food Label Scan
```
POST /foodapp/food-safety-check/
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "image": <file>,
  "product_name": "Optional Product Name"
}
Response: {
  "scan_id": 123,
  "product_name": "...",
  "safety_status": "safe|caution|unsafe|unknown",
  "confidence_metadata": {...},
  "insight_composer": {...},
  "expert_advice": {...},
  "three_tier_priority": {...},
  "nutrition_data": {...},
  "ingredients": [...],
  "go_ingredients": [...],
  "caution_ingredients": [...],
  "no_go_ingredients": [...],
  "extracted_text": "...",
  "image_url": "..."
}
```

#### Update Scan Image (PUT)
```
PUT /foodapp/food-safety-check/
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "image": <file>,
  "scan_id": 123
}
Response: {
  "scan_id": 123,
  "image_url": "...",
  "updated_existing_scan": true,
  "message": "Image updated successfully"
}
```

#### Barcode Scan
```
POST /foodapp/barcode/
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "barcode": "1234567890123",
  "image": <optional_file>
}
Response: {
  // Same structure as OCR scan
}
```

### 5.3 User Profile Endpoints

#### Get User Profile
```
GET /foodapp/user-profile/
Headers: {
  "Authorization": "Bearer <token>"
}
Response: {
  "id": 1,
  "email": "...",
  "full_name": "...",
  "Health_conditions": "...",
  "Allergies": "...",
  "Dietary_preferences": "...",
  ...
}
```

#### Update User Profile
```
PATCH /foodapp/user-profile/
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "Health_conditions": "diabetes, hypertension",
  "Allergies": "peanuts, shellfish",
  "Dietary_preferences": "vegan, gluten-free"
}
```

### 5.4 Scan History

#### Get Scan History
```
GET /foodapp/scan-history/
Headers: {
  "Authorization": "Bearer <token>"
}
Query Params: {
  "page": 1,
  "page_size": 20
}
Response: {
  "count": 100,
  "results": [
    {
      "scan_id": 123,
      "product_name": "...",
      "safety_status": "...",
      "created_at": "...",
      "image_url": "..."
    },
    ...
  ]
}
```

### 5.5 Subscription Endpoints

#### Get Subscription Prices
```
GET /foodapp/subscription-prices/
Response: {
  "freemium": {
    "price": 0,
    "scans_per_month": 6
  },
  "premium": {
    "price": 9.99,
    "scans_per_month": -1  // unlimited
  }
}
```

#### Subscribe User
```
POST /foodapp/subscribe/
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "plan": "premium",
  "stripe_token": "..."
}
```

#### Subscription Management
```
GET /foodapp/subscription-management/
Headers: {
  "Authorization": "Bearer <token>"
}
Response: {
  "current_plan": "premium",
  "scans_used": 45,
  "scans_remaining": -1,
  "renewal_date": "..."
}
```

### 5.6 Ingredient Information

#### Get Ingredient Full Data
```
GET /foodapp/fulldata/
Query Params: {
  "ingredient": "sodium benzoate"
}
Response: {
  "ingredient": "...",
  "safety_data": {...},
  "regulatory_status": {...},
  "health_effects": {...}
}
```

#### Ingredient LLM Info
```
POST /foodapp/api/ingredient-info/
Body: {
  "ingredient": "sodium benzoate"
}
Response: {
  "summary": "...",
  "safety": "...",
  "uses": "..."
}
```

### 5.7 Other Endpoints

- `GET /foodapp/FAQ/` - Frequently Asked Questions
- `GET /foodapp/AboutUS/` - About Us content
- `GET /foodapp/privacy-policy/` - Privacy Policy
- `GET /foodapp/termsandcondition/` - Terms and Conditions
- `POST /foodapp/feedback/` - Submit feedback
- `POST /foodapp/contact-support/` - Contact support
- `POST /foodapp/toggle-favorite/` - Toggle favorite scan
- `GET /foodapp/trending-ingredients/` - Trending ingredients
- `GET /foodapp/news/trending/` - Trending news

---

## 6. Database Schema

### 6.1 Core Models

#### User Model
```python
class User(AbstractBaseUser, PermissionsMixin):
    id = BigAutoField(primary_key=True)
    email = EmailField(unique=True)
    full_name = CharField(max_length=255)
    phone_number = CharField(max_length=20, unique=True, null=True)
    otp = CharField(max_length=100, null=True)
    
    # Health Profile
    Dietary_preferences = TextField(blank=True)
    Health_conditions = TextField(blank=True)
    Allergies = TextField(blank=True)
    Medications = TextField(blank=True)
    Demographics = TextField(blank=True)
    Health_Goals = TextField(blank=True)
    Motivation = TextField(blank=True)
    Behavioral_patterns = TextField(blank=True)
    
    # Settings
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    notifications_enabled = BooleanField(default=True)
    dark_mode = BooleanField(default=False)
    language = CharField(max_length=20, default="English")
    subscription_plan = CharField(max_length=100, default="Freemium plan")
    
    # Timestamps
    date_joined = DateTimeField(default=timezone.now)
    created_at = DateTimeField(default=timezone.now)
```

#### FoodLabelScan Model
```python
class FoodLabelScan(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    product_name = CharField(max_length=255, null=True)
    product_image_url = URLField(null=True)
    image_url = URLField(null=True)
    extracted_text = TextField(blank=True)
    nutrition_data = JSONField(default=dict)
    safety_status = CharField(max_length=50, default="unknown")
    ingredients = JSONField(default=list)
    go_ingredients = JSONField(default=list)
    caution_ingredients = JSONField(default=list)
    no_go_ingredients = JSONField(default=list)
    is_favorite = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### UserSubscription Model
```python
class UserSubscription(models.Model):
    user = OneToOneField(User, on_delete=CASCADE)
    stripe_customer_id = CharField(max_length=255, null=True)
    stripe_subscription_id = CharField(max_length=255, null=True)
    plan = CharField(max_length=50, default="freemium")
    status = CharField(max_length=50, default="active")
    current_period_start = DateTimeField(null=True)
    current_period_end = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

#### MonthlyScanUsage Model
```python
class MonthlyScanUsage(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    month = IntegerField()  # 1-12
    year = IntegerField()
    scan_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
```

### 6.2 Relationships

- **User** → **FoodLabelScan** (One-to-Many)
- **User** → **UserSubscription** (One-to-One)
- **User** → **MonthlyScanUsage** (One-to-Many)
- **User** → **UserHealthPreference** (One-to-Many)

### 6.3 Indexes

- `User.email` (unique index)
- `User.phone_number` (unique index)
- `FoodLabelScan.user_id` (foreign key index)
- `FoodLabelScan.created_at` (for scan history queries)

---

## 7. AI/ML Components

### 7.1 Insight Composer

**Location**: `foodinfo/views.py` → `get_insight_composer()`

**System Prompt** (Fixed, Non-Editable):
```
You are IngredientIQ's AI Health Interpreter.

Always output exactly three sections, in this order and with these headings:

BLUF Insight (30–80 words) — clear summary of safety status (Go / Caution / No-Go) and the main trigger ingredient(s).

Main Explanation (50–100 words) — concise reasoning describing which ingredients caused the flag, how they relate to the user's profile, and how the decision engine weighted them.

Deeper Reference (Expandable, 120–160 words) — an evidence-based explanation citing up to 3 authoritative sources (FDA, EFSA, PubMed, USDA). Clarify severity level and rationale.

Write at an 8th-grade readability level, compassionate & clinical tone.

Do not add sections or commentary. Keep total ≤ 340 words.
```

**Input Schema (IHI - Insight Health Interpretation)**:
```json
{
  "status": "Go|Caution|No-Go|Defer",
  "jurisdiction": "US|EU|...",
  "product": {"name": "..."},
  "profile": {
    "region": "...",
    "medical": {...},
    "medications": [...],
    "allergies": [...],
    "sensitivities": [...],
    "preferences": {...},
    "insight_depth": "brief|simple|data|case_by_case"
  },
  "ingredients": [{"name": "..."}],
  "nutrients": {...},
  "evidence": [
    {
      "authority": "FDA|EFSA|PubMed|USDA",
      "ref": "...",
      "note": "..."
    }
  ],
  "weights": {
    "allergen": 1.0,
    "recall": 1.0,
    "med_interaction": 1.0,
    "safety_threshold": 0.7,
    "sensitivity": 0.5,
    "preference": 0.2
  },
  "risk_vectors": [
    {
      "type": "allergen|regulatory|sensitivity",
      "ingredient": "...",
      "tier": "mandatory|secondary|preference",
      "severity": 0.0-1.0
    }
  ],
  "per_container_math": {}
}
```

**Post-Processing Guards**:
1. Word count validation (strict ranges)
2. Citation limit (≤ 3)
3. Section existence check
4. Fallback generation if validation fails

### 7.2 Expert Advice Composer

**Location**: `foodinfo/views.py` → `get_expert_advice_composer()`

**System Prompt** (Fixed, Non-Editable):
```
You are IngredientIQ's Expert Nutrition Analyst.

Always output exactly two sections, with these headings and constraints:

Healthier Pathway (Prognosis, 120–150 words)

• Use the provided context only (ingredients, profile, jurisdiction, evidence).
• Explain likely health trajectory if current pattern continues; reflect mandatory vs. secondary risks.
• Cite at most 2 credible authorities present in the evidence (FDA, EFSA, PubMed, USDA).
• 8th-grade readability, compassionate clinical tone. No diagnosis or medical advice.

Your Smarter Path (Counseling, 120–150 words)

• Provide behavior- and process-oriented guidance consistent with the profile and risks.
• Be jurisdiction-aware and confidence-aware (if confidence is low, advise rescanning/verification).
• Cite at most 2 authorities from the evidence if needed for credibility.
• Do not recommend product swaps or alternatives. No brand endorsements.
• 8th-grade readability, supportive and clear.

Do not add extra headings or commentary. Keep the total ≤ 270 words.
```

**Input Schema (EAI - Expert Advice Input)**:
```json
{
  "status": "Go|Caution|No-Go|Defer",
  "jurisdiction": "US|EU|...",
  "product": {"name": "..."},
  "profile": {
    "region": "...",
    "medical": {...},
    "medications": [...],
    "allergies": [...],
    "sensitivities": [...],
    "preferences": {...},
    "demographics": {...},
    "motivation": "...",
    "behavioral_patterns": "...",
    "counseling_style": "Analyzer|Empath|Optimizer|Explorer|Minimalist",
    "insight_depth": "brief|simple|data|case_by_case"
  },
  "ingredients": [{"name": "..."}],
  "nutrients": {...},
  "evidence": [...],
  "weights": {...},
  "risk_vectors": [...],
  "per_container_math": {}
}
```

**Post-Processing Guards**:
1. Word count validation (120-150 per section, total ≤ 270)
2. Citation limit (≤ 2)
3. No product swaps/brand endorsements
4. Fallback generation if validation fails

### 7.3 Confidence Engine

**Location**: `foodinfo/confidence_engine.py`

**Class**: `ConfidenceEngine`

**Methods**:
- `calculate_confidence()`: Geometric mean calculation
- `should_defer()`: Threshold check (0.72)
- `extract_confidence_factors()`: Extract from scan data
- `get_confidence_metadata()`: Audit logging

**Confidence Factors**:
1. OCR Quality (0.0-1.0)
2. Barcode Confidence (0.0-1.0)
3. NER Confidence (0.0-1.0)
4. Source Reliability (0.0-1.0)
5. AI Consistency (optional, 0.0-1.0)
6. Regulatory Coverage (optional, 0.0-1.0)

**Formula**:
```python
confidence = (factor1 × factor2 × ... × factorN)^(1/N)
```

**Defer Logic**:
```python
if confidence < 0.72:
    status = "Defer"
```

### 7.4 Deterministic Risk Engine

**Location**: `foodinfo/views.py` → `_apply_three_tier_priority()`

**Tier 1 (Mandatory - No-Go)**:
- Allergen matches (exact or fuzzy)
- Product recalls (FDA/EFSA)
- Banned ingredients (jurisdiction-specific)
- Critical medication interactions

**Tier 2 (Secondary - Caution)**:
- Condition-specific thresholds:
  - Diabetes: Sugar > threshold
  - Hypertension: Sodium > threshold
  - Celiac: Gluten detected
  - IBS/FODMAP: High-FODMAP ingredients
- Moderate medication interactions

**Tier 3 (Preference - Go)**:
- Dietary preferences (vegan, keto, etc.)
- Health goals alignment
- Lifestyle choices

**Output**:
```python
{
    "status": "No-Go|Caution|Go",
    "tier1_hits": [
        {
            "ingredient": "...",
            "reason": "...",
            "severity": 1.0
        }
    ],
    "tier2_hits": [...],
    "tier3_hits": [...]
}
```

### 7.5 Model Configuration

**Primary Model**: `gpt-4-turbo`
- Temperature: 0.4 (Insight), 0.3 (Expert Advice)
- Top-p: 0.9
- Max tokens: 750 (Insight), 600 (Expert Advice)
- Frequency penalty: 0
- Presence penalty: 0

**Fallback Model**: `gpt-3.5-turbo` (legacy, not used in new implementation)

---

## 8. Deployment & Infrastructure

### 8.1 Docker Setup

**docker-compose.yml**:
```yaml
version: "3.8"

services:
  foodai-backend:
    build: .
    container_name: foodai-backend
    restart: always
    command: ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8018 foodanalysis.wsgi:application"]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    networks:
      - foodai_network
    depends_on:
      - foodai-db

  foodai-db:
    image: postgres:15
    container_name: foodai-db
    restart: always
    environment:
      POSTGRES_DB: foodai
      POSTGRES_USER: foodai_user
      POSTGRES_PASSWORD: pass098foodai1123
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - foodai_network

  foodai-nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: foodai-nginx
    restart: always
    ports:
      - "8018:80"
    networks:
      - foodai_network
    depends_on:
      - foodai-backend
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - /etc/letsencrypt:/etc/letsencrypt:ro

networks:
  foodai_network:
    driver: bridge

volumes:
  static_volume:
  media_volume:
  postgres-data:
```

### 8.2 Deployment Steps

1. **Build Docker Images**:
   ```bash
   docker-compose build
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d
   ```

3. **Run Migrations**:
   ```bash
   docker-compose exec foodai-backend python manage.py migrate
   ```

4. **Collect Static Files**:
   ```bash
   docker-compose exec foodai-backend python manage.py collectstatic --noinput
   ```

5. **Create Superuser**:
   ```bash
   docker-compose exec foodai-backend python manage.py createsuperuser
   ```

### 8.3 AWS ECR Deployment

**Build and Push Backend**:
```bash
# Authenticate
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 888722447205.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t foodai .

# Tag
docker tag foodai:latest 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai:latest

# Push
docker push 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai:latest
```

**Build and Push Nginx**:
```bash
# Build
docker build -t foodai-nginx ./nginx

# Tag
docker tag foodai-nginx:latest 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai-nginx:latest

# Push
docker push 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai-nginx:latest
```

### 8.4 Nginx Configuration

**Location**: `nginx/default.conf`

**Key Features**:
- Reverse proxy to Gunicorn (port 8018)
- Static file serving
- SSL termination (production)
- CORS headers
- Request size limits

### 8.5 Environment Variables

See [Configuration & Environment Variables](#9-configuration--environment-variables) section.

---

## 9. Configuration & Environment Variables

### 9.1 Required Environment Variables

All environment variables should be set in Railway dashboard, NOT in code files.

**Required variables for Railway deployment:**

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (generate with `secrets.token_urlsafe(50)`) |
| `DEBUG` | Set to `False` for production |
| `ALLOWED_HOSTS` | `ingredientiq.ai,www.ingredientiq.ai` |
| `DATABASE_URL` | Auto-set by Railway PostgreSQL |
| `EMAIL_HOST_USER` | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | Gmail app password |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name |
| `STRIPE_SECRET_KEY` | Stripe live secret key |
| `STRIPE_PUBLISHABLE_KEY` | Stripe live publishable key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |

**Note:** Firebase and Twilio are no longer needed (mobile app discontinued).

### 9.2 Django Settings

**Key Settings** (in `foodanalysis/settings.py`):

- `SECRET_KEY`: Django secret key (keep secure)
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: List of allowed hostnames
- `DATABASES`: Database configuration
- `STATIC_URL`: Static files URL
- `MEDIA_URL`: Media files URL
- `CORS_ALLOWED_ORIGINS`: CORS origins
- `JWT_AUTH`: JWT configuration

### 9.3 Security Settings

- `SECURE_SSL_REDIRECT`: Redirect HTTP to HTTPS
- `SESSION_COOKIE_SECURE`: Secure session cookies
- `CSRF_COOKIE_SECURE`: Secure CSRF cookies
- `SECURE_BROWSER_XSS_FILTER`: XSS protection
- `SECURE_CONTENT_TYPE_NOSNIFF`: Content type protection

---

## 10. Testing & Quality Assurance

### 10.1 Manual Testing Checklist

**Authentication**:
- [ ] User registration
- [ ] User login
- [ ] Google OAuth login
- [ ] Apple Sign In
- [ ] Forgot password flow
- [ ] OTP verification
- [ ] Password change

**Food Scanning**:
- [ ] OCR scan with valid image
- [ ] OCR scan with invalid image
- [ ] Barcode scan with valid barcode
- [ ] Barcode scan with invalid barcode
- [ ] Image update (PUT method)
- [ ] Scan history retrieval
- [ ] Favorite toggle

**AI Insights**:
- [ ] Insight Composer generation
- [ ] Expert Advice generation
- [ ] Word count validation
- [ ] Citation limits
- [ ] Fallback generation
- [ ] Confidence calculation
- [ ] Defer status handling

**User Profile**:
- [ ] Profile retrieval
- [ ] Profile update
- [ ] Health conditions update
- [ ] Allergies update
- [ ] Dietary preferences update

**Subscription**:
- [ ] Subscription prices retrieval
- [ ] Subscription creation
- [ ] Subscription management
- [ ] Scan limit enforcement
- [ ] Webhook handling

### 10.2 API Testing

**Tools**:
- Postman
- cURL
- Python requests library

**Example Test Script**:
```python
import requests

BASE_URL = "https://ingredientiq.ai/foodapp"

# Login
response = requests.post(f"{BASE_URL}/login/", json={
    "email": "test@example.com",
    "password": "password123"
})
token = response.json()["tokens"]["access"]

# Scan Food Label
headers = {"Authorization": f"Bearer {token}"}
files = {"image": open("test_image.jpg", "rb")}
response = requests.post(
    f"{BASE_URL}/food-safety-check/",
    headers=headers,
    files=files
)
print(response.json())
```

### 10.3 Performance Testing

**Key Metrics**:
- OCR processing time: < 2 seconds
- AI analysis time: < 3 seconds
- Total response time: < 5 seconds
- API response time: < 1 second (cached endpoints)

**Load Testing**:
- Use tools like Apache JMeter or Locust
- Test concurrent users: 10, 50, 100, 500
- Monitor response times and error rates

---

## 11. Maintenance & Support

### 11.1 Regular Maintenance Tasks

**Daily**:
- Monitor error logs
- Check API response times
- Verify external API availability
- Check database connection health

**Weekly**:
- Review scan usage statistics
- Check subscription statuses
- Review user feedback
- Monitor OpenAI API usage/costs

**Monthly**:
- Database backup verification
- Security updates
- Dependency updates (review)
- Performance optimization review

### 11.2 Logging

**Log Locations**:
- Application logs: Docker container logs
- Error logs: Django error logging
- Access logs: Nginx access logs

**View Logs**:
```bash
# Backend logs
docker-compose logs -f foodai-backend

# Nginx logs
docker-compose logs -f foodai-nginx

# Database logs
docker-compose logs -f foodai-db
```

### 11.3 Database Maintenance

**Backup**:
```bash
docker-compose exec foodai-db pg_dump -U foodai_user foodai > backup.sql
```

**Restore**:
```bash
docker-compose exec -T foodai-db psql -U foodai_user foodai < backup.sql
```

**Migrations**:
```bash
# Create migration
docker-compose exec foodai-backend python manage.py makemigrations

# Apply migration
docker-compose exec foodai-backend python manage.py migrate
```

### 11.4 Common Issues & Solutions

**Issue**: OpenAI API timeout
- **Solution**: Check API key, increase timeout, implement retry logic

**Issue**: Database connection errors
- **Solution**: Verify database container is running, check credentials

**Issue**: Static files not loading
- **Solution**: Run `collectstatic`, check nginx configuration

**Issue**: CORS errors
- **Solution**: Update `CORS_ALLOWED_ORIGINS` in settings

**Issue**: Scan limit not enforced
- **Solution**: Check `MonthlyScanUsage` model, verify subscription status

---

## 12. Known Issues & Future Enhancements

### 12.1 Known Issues

1. **Word Count Validation**: Occasionally, GPT-4 may generate responses slightly outside word count ranges. Fallback mechanism handles this.

2. **OCR Accuracy**: OCR quality depends on image quality. Users are advised to use clear, well-lit images.

3. **External API Dependencies**: Some features depend on external APIs (Open Food Facts, FDA, etc.). Network issues may cause delays.

4. **Barcode Database Coverage**: Not all products are available in Open Food Facts database. OCR fallback is used.

### 12.2 Future Enhancements

1. **Microservices Architecture**: Migrate from monolith to microservices for better scalability

2. **Caching Layer**: Implement Redis caching for frequently accessed data

3. **Real-time Notifications**: WebSocket support for real-time updates

4. **Multi-language Support**: Expand beyond English for OCR and AI responses

5. **Advanced Analytics**: User behavior analytics, product trend analysis

6. **Machine Learning Models**: Train custom models for ingredient recognition

7. **Batch Processing**: Support for batch scan processing

8. **API Rate Limiting**: Implement rate limiting per user/IP

---

## 13. Contact & Support

### 13.1 Technical Support

For technical issues or questions:
- Review this documentation
- Check error logs
- Review API response structure
- Consult code comments

### 13.2 Key Files Reference

- **Main Views**: `foodapp_backend/foodinfo/views.py`
- **Models**: `foodapp_backend/foodinfo/models.py`
- **URLs**: `foodapp_backend/foodinfo/urls.py`
- **Settings**: `foodapp_backend/foodanalysis/settings.py`
- **Confidence Engine**: `foodapp_backend/foodinfo/confidence_engine.py`
- **Docker Config**: `foodapp_backend/docker-compose.yml`

### 13.3 Important Notes

1. **API Keys**: Never commit API keys to version control. Use environment variables.

2. **Database**: Always backup before migrations or major changes.

3. **OpenAI Costs**: Monitor OpenAI API usage to control costs.

4. **Security**: Keep dependencies updated, especially security-related packages.

5. **Testing**: Always test in staging environment before production deployment.

---

## Appendix A: API Response Examples

### A.1 Successful OCR Scan Response

```json
{
  "scan_id": 123,
  "product_name": "Chocolate Chip Cookies",
  "safety_status": "caution",
  "confidence_metadata": {
    "combined_confidence": 0.85,
    "threshold": 0.72,
    "should_defer": false,
    "factors": {
      "ocr_quality": 0.9,
      "barcode_confidence": 0.0,
      "ner_confidence": 0.85,
      "source_reliability": 0.8
    },
    "calculation_method": "geometric_mean"
  },
  "insight_composer": {
    "bluf_insight": "This product contains high sugar content that may not align with your diabetes management goals. The 15g of added sugar per serving exceeds recommended daily limits for individuals managing blood glucose levels.",
    "main_explanation": "The decision engine flagged this product due to its sugar content (15g per serving) which exceeds the threshold for diabetes management. Sugar can cause rapid blood glucose spikes, making it challenging to maintain stable levels. The system weighted this as a secondary concern, indicating caution rather than complete avoidance.",
    "deeper_reference": "According to FDA guidelines, products with more than 10g of added sugar per serving should be consumed in moderation by individuals with diabetes. Research published in PubMed demonstrates that consistent consumption of high-sugar foods can lead to poor glycemic control. The American Diabetes Association recommends limiting added sugars to less than 10% of daily caloric intake, which for most adults translates to approximately 50g per day. This product's sugar content represents 30% of that daily limit in a single serving.",
    "disclaimer": "Informational, not diagnostic. Consult healthcare providers for medical advice.",
    "word_counts": {
      "bluf_insight": 45,
      "main_explanation": 78,
      "deeper_reference": 142,
      "total": 265
    },
    "audit_log": {
      "model": "gpt-4-turbo",
      "prompt_hash": "a1b2c3d4e5f6",
      "input_hash": "f6e5d4c3b2a1",
      "timestamp": "2024-12-15T10:30:00Z"
    }
  },
  "expert_advice": {
    "healthier_pathway": "If you continue consuming products with high sugar content like this, you may experience more frequent blood glucose fluctuations. Over time, this pattern can make diabetes management more challenging and potentially increase the risk of complications. The FDA recommends monitoring sugar intake carefully, and research from PubMed shows that consistent high-sugar consumption can negatively impact long-term glycemic control.",
    "your_smarter_path": "Consider reading nutrition labels more carefully before purchasing, focusing on the 'Added Sugars' line. When you do choose to enjoy a treat, plan for it by adjusting other meals that day to stay within your daily sugar budget. Keep a food diary to track patterns and identify which products work best for your management goals. Consult with your healthcare provider or a registered dietitian to develop a personalized meal plan that accommodates occasional treats while maintaining stable blood glucose levels.",
    "word_counts": {
      "healthier_pathway": 135,
      "your_smarter_path": 142,
      "total": 277
    },
    "audit_log": {
      "model": "gpt-4-turbo",
      "prompt_hash": "x1y2z3w4v5",
      "input_hash": "v5w4z3y2x1",
      "timestamp": "2024-12-15T10:30:05Z"
    }
  },
  "three_tier_priority": {
    "status": "Caution",
    "tier1_hits": [],
    "tier2_hits": [
      {
        "ingredient": "Sugar",
        "reason": "Exceeds diabetes threshold (15g > 10g)",
        "severity": 0.7
      }
    ],
    "tier3_hits": []
  },
  "nutrition_data": {
    "serving_size": "1 cookie (30g)",
    "calories": 150,
    "total_fat": 7,
    "saturated_fat": 3,
    "sugar": 15,
    "sodium": 120
  },
  "ingredients": ["flour", "sugar", "chocolate chips", "butter", "eggs"],
  "go_ingredients": ["flour", "eggs"],
  "caution_ingredients": ["sugar"],
  "no_go_ingredients": [],
  "extracted_text": "Nutrition Facts\nServing Size: 1 cookie (30g)\nCalories: 150\n...",
  "image_url": "https://storage.com/food_labels/abc123.jpg"
}
```

### A.2 Defer Status Response

```json
{
  "scan_id": 124,
  "product_name": "Unknown Product",
  "safety_status": "unknown",
  "confidence_metadata": {
    "combined_confidence": 0.65,
    "threshold": 0.72,
    "should_defer": true,
    "factors": {
      "ocr_quality": 0.6,
      "barcode_confidence": 0.0,
      "ner_confidence": 0.7,
      "source_reliability": 0.65
    }
  },
  "insight_composer": {
    "bluf_insight": "We couldn't verify this product with high enough confidence. Please rescan with a clearer image and ensure the full nutrition label is visible.",
    "main_explanation": "Confidence in the scan quality was insufficient to provide a complete safety assessment. For accurate analysis, we need clear visibility of all ingredients and nutrition facts.",
    "deeper_reference": "According to FDA and EFSA guidelines, complete nutritional information is essential for accurate health assessments. When scan quality is low, our system cannot reliably extract all necessary data points.",
    "disclaimer": "Informational, not diagnostic. Consult healthcare providers for medical advice.",
    "word_counts": {...},
    "audit_log": {...}
  },
  "expert_advice": null,
  "three_tier_priority": {
    "status": "Defer",
    "tier1_hits": [],
    "tier2_hits": [],
    "tier3_hits": []
  }
}
```

---

## Appendix B: Error Codes

### B.1 HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### B.2 Custom Error Responses

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-12-15T10:30:00Z"
}
```

---

## Document End

**Last Updated**: December 2024  
**Version**: 1.0  
**Status**: Complete

For questions or clarifications, please refer to the codebase or contact the development team.

