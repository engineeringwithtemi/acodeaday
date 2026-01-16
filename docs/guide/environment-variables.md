# Environment Variables

Complete reference for all environment variables used in acodeaday.

## Backend (.env)

Location: `backend/.env`

### Database

```bash
# PostgreSQL connection string (async format required)
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE

# Example (Supabase):
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db.abc123.supabase.co:5432/postgres

# Example (Local):
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/acodeaday
```

**Important:** Must use `postgresql+asyncpg://` (not `postgresql://`)

### Supabase

```bash
# Supabase project URL
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co

# Supabase anon/public key (for client auth)
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Supabase service role key (optional, for admin operations)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Where to find:**
1. Supabase Dashboard → Settings → API
2. Copy Project URL → `SUPABASE_URL`
3. Copy anon/public key → `SUPABASE_KEY`

### Judge0

```bash
# Judge0 API endpoint
JUDGE0_URL=http://localhost:2358

# Production (self-hosted):
JUDGE0_URL=https://judge0.yourapp.com

# Production (RapidAPI):
JUDGE0_URL=https://judge0-ce.p.rapidapi.com

# Judge0 API key (if authentication enabled)
JUDGE0_API_KEY=your_judge0_api_key
```

### Authentication

```bash
# HTTP Basic Auth credentials
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password-here

# Default user email (created on startup)
DEFAULT_USER_EMAIL=admin@example.com

# Default user password (created on startup)
DEFAULT_USER_PASSWORD=your-password
```

**Important:** Change default credentials in production!

### Application Settings

```bash
# Environment (development, staging, production)
ENVIRONMENT=development

# Allowed CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,https://yourapp.vercel.app

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Python buffering (recommended for production logs)
PYTHONUNBUFFERED=1
```

### Optional Settings

```bash
# Secret key for JWT/sessions (auto-generated if not set)
SECRET_KEY=your-random-secret-key-here

# Redis URL (for caching, optional)
REDIS_URL=redis://localhost:6379

# Sentry DSN (for error tracking, optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/123456
```

## Frontend (.env)

Location: `frontend/.env`

All frontend env vars must start with `VITE_` to be exposed to the browser.

### API Configuration

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Production:
VITE_API_URL=https://api.yourapp.com
```

### Supabase (Frontend)

```bash
# Supabase project URL
VITE_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co

# Supabase anon/public key
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Important:** Must match backend Supabase configuration.

### Optional

```bash
# Sentry DSN (error tracking)
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/123456

# Google Analytics ID
VITE_GA_ID=G-XXXXXXXXXX

# Environment name (for conditional rendering)
VITE_ENV=development
```

## Environment Templates

### Backend .env.example

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/acodeaday

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Judge0
JUDGE0_URL=http://localhost:2358
JUDGE0_API_KEY=

# Authentication
AUTH_USERNAME=admin
AUTH_PASSWORD=changeme
DEFAULT_USER_EMAIL=admin@example.com
DEFAULT_USER_PASSWORD=changeme

# Application
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
SECRET_KEY=

# Optional
REDIS_URL=
SENTRY_DSN=
```

### Frontend .env.example

```bash
# API
VITE_API_URL=http://localhost:8000

# Supabase
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key

# Optional
VITE_SENTRY_DSN=
VITE_GA_ID=
VITE_ENV=development
```

## Environment-Specific Configurations

### Development

**Backend:**
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/acodeaday
JUDGE0_URL=http://localhost:2358
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=DEBUG
```

**Frontend:**
```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=http://localhost:54321
VITE_ENV=development
```

### Staging

**Backend:**
```bash
ENVIRONMENT=staging
DATABASE_URL=postgresql+asyncpg://...@staging-db.supabase.co:5432/postgres
JUDGE0_URL=https://staging-judge0.yourapp.com
CORS_ORIGINS=https://staging.yourapp.com
LOG_LEVEL=INFO
```

**Frontend:**
```bash
VITE_API_URL=https://staging-api.yourapp.com
VITE_SUPABASE_URL=https://staging.supabase.co
VITE_ENV=staging
```

### Production

**Backend:**
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://...@prod-db.supabase.co:5432/postgres
JUDGE0_URL=https://judge0.yourapp.com
CORS_ORIGINS=https://yourapp.com
LOG_LEVEL=WARNING
SENTRY_DSN=https://...
```

**Frontend:**
```bash
VITE_API_URL=https://api.yourapp.com
VITE_SUPABASE_URL=https://prod.supabase.co
VITE_SENTRY_DSN=https://...
VITE_GA_ID=G-XXXXXXXXXX
VITE_ENV=production
```

## Security Best Practices

### 1. Never Commit Secrets

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

Keep in repo (safe):
```
.env.example
```

### 2. Use Different Credentials Per Environment

Don't reuse production credentials in staging/dev!

### 3. Rotate Secrets Regularly

- Change passwords every 90 days
- Rotate API keys quarterly
- Update after team member leaves

### 4. Use Platform Secret Management

**Railway:**
```bash
railway variables set KEY=value
```

**Fly.io:**
```bash
flyctl secrets set KEY=value
```

**Vercel:**
```bash
vercel env add KEY
```

### 5. Restrict Access

- Use Supabase Row Level Security (RLS)
- Limit database IP allowlist
- Use separate service accounts per environment

## Validating Configuration

### Backend Validation

The backend validates env vars on startup. Check logs:

```bash
uv run uvicorn app.main:app --reload
```

Look for:
```
INFO: DATABASE_URL configured
INFO: SUPABASE_URL configured
INFO: JUDGE0_URL configured
```

### Frontend Validation

Vite shows missing env vars during build:

```bash
npm run build
```

Check for warnings about undefined variables.

## Troubleshooting

### "Environment variable not found"

- Verify variable is set in `.env`
- Restart dev server after adding env vars
- Frontend vars must start with `VITE_`

### Database connection fails

- Check `DATABASE_URL` uses `postgresql+asyncpg://`
- Verify password doesn't contain special characters (URL encode if needed)
- Test connection: `psql $DATABASE_URL`

### CORS errors

- Add frontend URL to `CORS_ORIGINS`
- Use full URL including protocol (`https://`)
- Separate multiple origins with commas (no spaces)

### Judge0 not responding

- Verify `JUDGE0_URL` is accessible
- Test: `curl $JUDGE0_URL/about`
- Check firewall/network restrictions

## Loading Environment Variables

### Backend (Python)

```python
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JUDGE0_URL = os.getenv("JUDGE0_URL")
```

### Frontend (Vite)

```typescript
const apiUrl = import.meta.env.VITE_API_URL
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
```

## Next Steps

- [Backend Setup](/guide/backend-setup) - Configure backend env vars
- [Frontend Setup](/guide/frontend-setup) - Configure frontend env vars
- [Deployment](/guide/deployment-overview) - Set env vars in production
