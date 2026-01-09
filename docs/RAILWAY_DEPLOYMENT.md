# Railway Deployment Guide for IngredientIQ

## Overview

This guide covers deploying the IngredientIQ backend to [Railway.com](https://railway.app) with the custom domain `www.ingredientiq.ai`.

## Prerequisites

1. A Railway account (sign up at railway.app)
2. A GitHub repository with this code pushed
3. Access to your domain registrar for `ingredientiq.ai`

## Deployment Steps

### 1. Create New Project on Railway

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
3. Connect your GitHub account and select the `website-ingredientiq-ai` repository
5. Railway will automatically detect the Django app

### 2. Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically sets the `DATABASE_URL` environment variable

### 3. Configure Environment Variables

In your Railway project settings, add these environment variables:

```bash
# Required - Set these in Railway dashboard, NOT in code
DJANGO_SECRET_KEY=<set-in-railway-dashboard>
DEBUG=False
ALLOWED_HOSTS=ingredientiq.ai,www.ingredientiq.ai

# Email - Configure in Railway dashboard
EMAIL_HOST_USER=<set-in-railway-dashboard>
EMAIL_HOST_PASSWORD=<set-in-railway-dashboard>

# AWS S3 (for file storage) - Configure in Railway dashboard
AWS_ACCESS_KEY_ID=<set-in-railway-dashboard>
AWS_SECRET_ACCESS_KEY=<set-in-railway-dashboard>
AWS_STORAGE_BUCKET_NAME=<set-in-railway-dashboard>
AWS_S3_REGION_NAME=us-east-2

# Stripe (payments) - Configure in Railway dashboard
STRIPE_SECRET_KEY=<set-in-railway-dashboard>
STRIPE_PUBLISHABLE_KEY=<set-in-railway-dashboard>
STRIPE_WEBHOOK_SECRET=<set-in-railway-dashboard>
STRIPE_MONTHLY_PRICE_ID=<set-in-railway-dashboard>
STRIPE_YEARLY_PRICE_ID=<set-in-railway-dashboard>

# OAuth - Configure in Railway dashboard
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=<set-in-railway-dashboard>
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=<set-in-railway-dashboard>
```

### 4. Generate a New Django Secret Key

Run this in Python to generate a secure key:

```python
import secrets
print(secrets.token_urlsafe(50))
```

### 5. Configure Custom Domain

1. In Railway project, go to **Settings** → **Domains**
2. Click **"+ Custom Domain"**
3. Enter `www.ingredientiq.ai`
4. Railway will provide DNS records to add

### 6. Configure DNS at Your Registrar

Add the following DNS records at your domain registrar:

| Type  | Name | Value |
|-------|------|-------|
| CNAME | www  | `<your-app>.up.railway.app` |
| CNAME | @    | `<your-app>.up.railway.app` (or use redirect) |

**For root domain (`ingredientiq.ai`):**
- If your registrar supports CNAME flattening (Cloudflare, Route53), add a CNAME
- Otherwise, set up a redirect from `ingredientiq.ai` to `www.ingredientiq.ai`

### 7. SSL Certificate

Railway automatically provisions and renews SSL certificates via Let's Encrypt once DNS is configured.

## Deployment Configuration Files

The following files configure Railway deployment:

| File | Purpose |
|------|---------|
| `railway.json` | Railway-specific configuration |
| `Procfile` | Process command (alternative to railway.json) |
| `nixpacks.toml` | Nixpacks build configuration |

## Health Check

Railway performs health checks at `/api/health/`. This endpoint:
- Checks database connectivity
- Returns JSON status

## Post-Deployment Checklist

- [ ] Verify health check: `https://www.ingredientiq.ai/api/health/`
- [ ] Test admin panel: `https://www.ingredientiq.ai/admin-panel/`
- [ ] Test public website: `https://www.ingredientiq.ai/`
- [ ] Test API endpoints: `https://www.ingredientiq.ai/foodapp/`
- [ ] Configure Stripe webhook URL: `https://www.ingredientiq.ai/foodapp/webhook/stripe/`
- [ ] Update OAuth redirect URLs in Google/Apple consoles

## Monitoring

Railway provides:
- Real-time logs
- Memory/CPU metrics
- Deployment history
- Automatic restarts on failure

Access logs via: **Project** → **Deployments** → **View Logs**

## Scaling

Railway allows:
- Horizontal scaling (multiple instances)
- Custom resource allocation
- Sleep mode for cost savings

## Troubleshooting

### Static files not loading
```bash
# Ensure collectstatic runs
python manage.py collectstatic --noinput
```

### Database connection issues
- Check `DATABASE_URL` is set
- Verify PostgreSQL service is running

### 502/503 errors
- Check deployment logs
- Verify PORT environment variable usage
- Ensure gunicorn is binding to `0.0.0.0:$PORT`

## Cost Estimate

Railway pricing (as of 2026):
- **Hobby Plan**: $5/month base + usage
- **PostgreSQL**: ~$5-10/month for small databases
- **Estimated total**: $10-25/month for small-medium traffic

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

---

## VS Code Extensions for Streamlined Workflow

### Already Installed (Recommended)
- **GitHub Copilot** - AI pair programmer
- **GitHub Copilot Chat** - AI chat features
- **GitHub Pull Requests** - PR management
- **GitLens** - Git supercharged
- **Git Graph** - Visual git history

### Install for Railway Integration
- **GitHub Actions** (`github.vscode-github-actions`) - Workflow editing
- **Railway** (`buildwithlayer.railway-integration-expert-x3o0c`) - Railway Copilot integration

---

## GitHub Actions CI/CD (Optional)

A GitHub Actions workflow is included at `.github/workflows/deploy.yml` for automatic deployment.

### Setup Steps:
1. Get Railway token: `railway login` → `railway whoami` 
2. Add GitHub secrets:
   - `RAILWAY_TOKEN` - Your Railway API token
   - `RAILWAY_SERVICE_ID` - Your service ID from Railway dashboard

### Workflow:
- **On PR**: Runs Django checks (syntax, deploy checks)
- **On push to main**: Deploys to Railway automatically

Note: Railway also supports automatic GitHub integration without Actions - just connect your repo in the Railway dashboard.
