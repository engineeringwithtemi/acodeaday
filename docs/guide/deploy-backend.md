# Deploy Backend

This guide covers deploying the FastAPI backend to production.

## Quick Deploy to Railway

Railway is the easiest platform for deploying Python applications with a generous free tier.

### 1. Prerequisites

- GitHub account
- Railway account ([railway.app](https://railway.app))
- Code pushed to GitHub repository

### 2. Create New Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `acodeaday` repository
5. Railway auto-detects Python and starts deployment

### 3. Configure Root Directory

If your backend is in a subdirectory:

1. Go to project Settings
2. Set **Root Directory**: `backend`
3. Redeploy

### 4. Add Environment Variables

Go to project Variables tab and add:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@HOST:5432/postgres
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_ANON_KEY
JUDGE0_URL=https://your-judge0-instance.com
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password
ENVIRONMENT=production
PYTHONUNBUFFERED=1
```

### 5. Configure Build Command

Railway auto-detects `uvicorn`, but you can customize:

1. Go to Settings > Deploy
2. **Build Command**: `pip install uv && uv sync`
3. **Start Command**: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 6. Run Migrations

After first deployment:

1. Go to project Deployments
2. Click on active deployment
3. Open "Deploy Logs"
4. You'll see the app URL

SSH into Railway (if needed):
```bash
railway run uv run alembic upgrade head
```

Or run migrations locally against production DB:
```bash
# Set DATABASE_URL to production
uv run alembic upgrade head
```

### 7. Seed Problems

```bash
# Connect to production database
railway run uv run python scripts/seed_problems.py seed
```

Or locally:
```bash
# Set DATABASE_URL to production
uv run python scripts/seed_problems.py seed
```

### 8. Get Deployment URL

Railway provides a URL like:
```
https://acodeaday-production.up.railway.app
```

Test it:
```bash
curl https://your-app.up.railway.app/api/problems
```

## Deploy to Fly.io

Fly.io offers more control and excellent performance.

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Login to Fly.io

```bash
flyctl auth login
```

### 3. Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Run migrations and start server
CMD uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 4. Create fly.toml

```bash
cd backend
flyctl launch
```

This creates `fly.toml`. Edit it:

```toml
app = "acodeaday"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  ENVIRONMENT = "production"
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[services.http_checks]
  interval = "10s"
  timeout = "2s"
  grace_period = "5s"
  path = "/health"
```

### 5. Set Secrets

```bash
flyctl secrets set DATABASE_URL="postgresql+asyncpg://..."
flyctl secrets set SUPABASE_URL="https://..."
flyctl secrets set SUPABASE_KEY="..."
flyctl secrets set JUDGE0_URL="https://..."
flyctl secrets set AUTH_USERNAME="admin"
flyctl secrets set AUTH_PASSWORD="your-password"
```

### 6. Deploy

```bash
flyctl deploy
```

### 7. Run Migrations

```bash
flyctl ssh console
uv run alembic upgrade head
exit
```

### 8. Get URL

```bash
flyctl info
```

Your app will be at `https://acodeaday.fly.dev`

## Deploy to Render

Render offers a free tier with automatic deploys from Git.

### 1. Create Web Service

1. Go to [render.com](https://render.com)
2. Click "New +" > "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Name**: acodeaday-backend
   - **Region**: Choose closest
   - **Branch**: main
   - **Root Directory**: backend
   - **Runtime**: Python 3
   - **Build Command**: `pip install uv && uv sync`
   - **Start Command**: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2. Add Environment Variables

In Environment tab:

```bash
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
JUDGE0_URL=https://...
AUTH_USERNAME=admin
AUTH_PASSWORD=your-password
ENVIRONMENT=production
```

### 3. Deploy

Click "Create Web Service". Render auto-deploys on every Git push.

### 4. Run Migrations

After first deploy, open Shell:

```bash
uv run alembic upgrade head
uv run python scripts/seed_problems.py seed
```

## Environment Variables Reference

Required for all deployment platforms:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE

# Supabase
SUPABASE_URL=https://PROJECT_ID.supabase.co
SUPABASE_KEY=your_anon_key

# Judge0
JUDGE0_URL=https://your-judge0-instance.com
# Optional: JUDGE0_API_KEY=your_key (if using auth)

# Authentication
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password

# Environment
ENVIRONMENT=production

# Optional
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend.com
```

## Health Check Endpoint

Add health check to `backend/app/main.py`:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

Most platforms use this for uptime monitoring.

## CORS Configuration

Update CORS for production in `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Logging

Configure structured logging for production:

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## Monitoring

### Add Sentry

```bash
uv add sentry-sdk[fastapi]
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
    traces_sample_rate=1.0,
)
```

## SSL/TLS

All platforms (Railway, Fly.io, Render) provide automatic HTTPS. No configuration needed!

## Database Connection Pooling

For production, use connection pooling:

```python
# backend/app/db.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
```

## Performance Optimization

### Enable Gzip Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Add Caching

Use Redis for caching:

```bash
uv add redis
```

```python
import redis.asyncio as redis

cache = redis.from_url("redis://localhost:6379")
```

## Troubleshooting

### Deployment fails

```bash
# Check logs
railway logs  # Railway
flyctl logs   # Fly.io
# Render: View logs in dashboard
```

### Database connection errors

- Verify `DATABASE_URL` includes `+asyncpg`
- Check Supabase allows connections from your platform
- Ensure SSL mode is correct

### Import errors

```bash
# Ensure all deps in pyproject.toml
uv add missing-package
git commit && git push
```

## Next Steps

- [Deploy Frontend](/guide/deploy-frontend)
- [Environment Variables](/guide/environment-variables)
- [Judge0 Setup](/guide/judge0-setup) for production Judge0
