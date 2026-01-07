# 🚀 CORTEX - Railway/Render Deployment Guide

## ✅ Pre-Deployment Checklist

### Configuration Verified
- [x] `DEBUG=False` handled via environment variables
- [x] `ALLOWED_HOSTS` configured for cloud domains
- [x] WhiteNoise configured for static files
- [x] Supabase PostgreSQL connection via `dj-database-url`
- [x] No hardcoded paths in management commands
- [x] Landing page routed to `/` (core.views.index)
- [x] Freemium logic active (checked in templates)

### Files Created
- [x] `Procfile` - Gunicorn web server configuration
- [x] `runtime.txt` - Python 3.9.6 specification
- [x] `requirements.txt` - Cleaned production dependencies

---

## 🎯 Deployment Steps

### Option 1: Railway (Recommended)

#### 1. Create Railway Account
https://railway.app/

#### 2. Create New Project
```bash
# Install Railway CLI (optional)
npm i -g @railway/cli
railway login
railway init
```

**OR use Web UI:**
- Click "New Project"
- Select "Deploy from GitHub repo"
- Connect your repository

#### 3. Environment Variables
Add these in Railway Dashboard → Variables:

```env
# Django
DEBUG=False
SECRET_KEY=your-super-secret-key-here-min-50-chars
ALLOWED_HOSTS=.railway.app,yourdomain.com

# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:port/database

# Stripe
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_ID=price_xxxxx

# Email (Optional)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

#### 4. Deploy
Railway auto-detects Django and runs:
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi
```

#### 5. Run Migrations
In Railway CLI or dashboard:
```bash
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput
```

#### 6. Configure CRON Jobs
Railway supports native CRON:

**In `railway.toml`** (create at project root):
```toml
[build]
builder = "nixpacks"

[[crons]]
schedule = "0 12 * * *"
command = "python manage.py fetch_game_results"

[[crons]]
schedule = "0 16 * * *"
command = "python manage.py fetch_nhl_data"

[[crons]]
schedule = "30 16 * * *"
command = "python manage.py injury_guardian"
```

---

### Option 2: Render

#### 1. Create Render Account
https://render.com/

#### 2. Create Web Service
- New → Web Service
- Connect GitHub repository
- Root Directory: `/` (leave blank if root)

#### 3. Configuration
**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command:**
```bash
gunicorn config.wsgi:application
```

#### 4. Environment Variables
Same as Railway (see above)

#### 5. CRON Jobs (Render)
Create separate **Cron Jobs** in Render dashboard:

**Job 1: Fetch Results**
- Name: `fetch_game_results`
- Schedule: `0 12 * * *`
- Command: `python manage.py fetch_game_results`

**Job 2: Fetch NHL Data**
- Name: `fetch_nhl_data`
- Schedule: `0 16 * * *`
- Command: `python manage.py fetch_nhl_data`

**Job 3: Injury Guardian**
- Name: `injury_guardian`
- Schedule: `30 16 * * *`
- Command: `python manage.py injury_guardian`

---

## 🔒 Security Checklist

### Before Going Live

1. **Generate Strong SECRET_KEY**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

2. **Enable HTTPS-only cookies**
Already configured in `settings.py` when `DEBUG=False`

3. **Update ALLOWED_HOSTS**
Add your custom domain:
```env
ALLOWED_HOSTS=.railway.app,.onrender.com,cortexnhl.com,www.cortexnhl.com
```

4. **Enable Stripe Webhook Verification**
Update Stripe webhook endpoint to:
```
https://your-app.railway.app/webhook/stripe/
```

5. **Test Email Sending**
Configure SMTP credentials or use SendGrid/Mailgun

---

## 📊 Post-Deployment Verification

### 1. Check Static Files
Visit: `https://your-app.railway.app/static/style.css`
Should load without 404

### 2. Test Landing Page
Visit: `https://your-app.railway.app/`
Should show CORTEX landing page

### 3. Test Dashboard
Visit: `https://your-app.railway.app/nhl/nhl-dashboard/`
Should show NHL predictions

### 4. Verify Freemium Logic
- Login as Free user → See Top 3 only
- Subscribe → See Top 5

### 5. Test CRON Jobs
Check logs at scheduled times:
- Railway: Logs tab
- Render: Logs for each cron job

### 6. Monitor Database
Check Supabase dashboard for:
- New predictions appearing at 16h
- Results updating at 12h
- Injury statuses marked

---

## 🐛 Troubleshooting

### Static Files Not Loading
```bash
# Run collectstatic manually
railway run python manage.py collectstatic --noinput
# OR for Render
python manage.py collectstatic --noinput
```

### Database Connection Error
Check `DATABASE_URL` format:
```
postgresql://user:password@host:port/database?sslmode=require
```

### CRON Jobs Not Running
- Railway: Check `railway.toml` syntax
- Render: Verify timezone (UTC by default)

### 500 Server Error
Check logs:
```bash
railway logs
# OR in Render dashboard: Logs tab
```

Common causes:
- Missing environment variables
- Database migration not run
- Static files not collected

---

## 🎯 Production Readiness

### ✅ Configuration Complete
- Django settings optimized for production
- WhiteNoise serving static files
- Gunicorn WSGI server configured
- PostgreSQL via Supabase
- HTTPS enforced (when DEBUG=False)

### ✅ Security Hardened
- Debug mode off in production
- Secret key from environment
- CSRF/XSS protection enabled
- Secure cookies (HTTPS-only)

### ✅ Scripts Cloud-Ready
- No hardcoded paths
- Relative imports only
- Environment variables loaded via `python-dotenv`

### ✅ Automation Configured
- CRON schedule documented
- Railway/Render configurations provided

---

## 🚀 Ready to Deploy!

Choose your platform:
1. **Railway** - Simpler, better CRON support
2. **Render** - More control, separate cron jobs

Both work perfectly for Django. Deploy in **under 10 minutes**! 🏒

---

## 📞 Support Resources

- Railway Docs: https://docs.railway.app/
- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/

**Next Step**: Push to GitHub → Connect to Railway/Render → Deploy! 🎉
