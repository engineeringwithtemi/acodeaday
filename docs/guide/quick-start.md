# Quick Start

Get acodeaday running locally in under 10 minutes.

## Prerequisites

Before you begin, ensure you have:

- **Docker & Docker Compose** (everything runs in containers)
- **Supabase account** (free tier is fine) for authentication and database

For local development without Docker:
- Node.js 22+ (for frontend)
- Python 3.12+ with [uv](https://github.com/astral-sh/uv) (for backend)

## Option 1: Docker Compose (Recommended)

The easiest way to run acodeaday - everything in one command.

### 1. Clone the Repository

```bash
git clone https://github.com/engineeringwithtemi/acodeaday.git
cd acodeaday
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```bash
# Database (from Supabase dashboard > Settings > Database > Connection string > URI)
# IMPORTANT: Use the "Transaction pooler" connection (port 6543), NOT direct connection (port 5432)
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Supabase (from Supabase dashboard > Settings > API)
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_ANON_KEY]
# Service role key - enables auto-confirm for default user (recommended)
SUPABASE_SERVICE_ROLE_KEY=[YOUR_SERVICE_ROLE_KEY]

# AI features (optional - for AI tutor)
OPENAI_API_KEY=sk-...
# or
GOOGLE_API_KEY=...
```

::: warning Supabase Cloud Connection
When using Supabase Cloud, you **must** use the **Transaction pooler** connection string (port 6543), not the direct connection (port 5432).

**To get the correct connection string:**
1. Go to Supabase Dashboard → **Settings** → **Database**
2. Under **Connection string**, select **URI**
3. Choose **Transaction pooler** (port 6543)
4. Copy the connection string and replace `postgresql://` with `postgresql+asyncpg://`

The pooler connection is required because:
- It handles connection pooling for serverless/async applications
- It works better with asyncpg (the async PostgreSQL driver)
- Direct connections may hit connection limits or timeout issues
:::

::: tip Using Local Supabase?
If you're running Supabase locally (`supabase start`) instead of Supabase Cloud, use `host.docker.internal` instead of `localhost`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:54322/postgres
SUPABASE_URL=http://host.docker.internal:54321
```

This is because Docker containers can't reach `localhost` on your machine. See [Self-Hosting Guide](/guide/self-hosting#using-local-supabase-with-docker) for details.
:::

### 3. Start Everything

```bash
docker compose up -d
```

This starts:
- **Judge0** (code execution) on port 2358
- **Backend** (FastAPI) on port 8000
- **Frontend** (React) on port 3000

Wait about 60 seconds for all services to initialize, then:

```bash
# Check all services are healthy
docker compose ps

# Verify Judge0 is ready
curl http://localhost:2358/about
```

### 4. Create Your Account & Start Coding!

1. Open `http://localhost:3000` in your browser
2. Click **"Sign Up"** to create an account via Supabase Auth
3. Check your email for the confirmation link
4. After confirming, log in with your credentials
5. You'll see your daily problems - start solving!

## Option 2: Self-Host with Pre-built Images

Deploy on your own server without building from source.

### 1. Download Production Compose File

```bash
curl -O https://raw.githubusercontent.com/engineeringwithtemi/acodeaday/main/docker-compose.prod.yml
```

### 2. Configure Environment

Edit `docker-compose.prod.yml` and update the `CHANGE_ME` values:

- `DATABASE_URL` - Your Supabase PostgreSQL connection string (use pooler URL with port 6543)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key (for auto-confirming users)
- `VITE_API_URL` - Where users access the backend (e.g., `http://localhost:8000`)

### 3. Start All Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

The backend automatically runs migrations and seeds the database on startup.

### 4. Access the App

Open `http://localhost:3000` in your browser.

::: tip Pre-built Images
This uses images from GitHub Container Registry:
- `ghcr.io/engineeringwithtemi/acodeaday-backend:latest`
- `ghcr.io/engineeringwithtemi/acodeaday-frontend:latest`

No building required!
:::

See [Self-Hosting Guide](/guide/self-hosting) for more deployment options.

---

## Option 3: Local Development

For development with hot-reload, run services locally.

### 1. Clone and Setup

```bash
git clone https://github.com/engineeringwithtemi/acodeaday.git
cd acodeaday
```

### 2. Start Judge0 (Docker required)

```bash
# Start only Judge0 services
docker compose up -d judge0-server judge0-workers judge0-db judge0-redis
```

Wait 30 seconds, then verify:

```bash
curl http://localhost:2358/about
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 4. Backend Setup

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python scripts/seed_problems.py seed
uv run uvicorn app.main:app --reload
```

Backend available at `http://localhost:8000`

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`

### 6. Create Account & Start Coding!

1. Open `http://localhost:5173`
2. Click **"Sign Up"** and enter your email/password
3. Check email for confirmation (or check Supabase dashboard if using local dev)
4. Log in and start solving problems!

## Authentication

acodeaday uses **Supabase Auth** for user management:

- **Sign Up**: Create account with email/password
- **Email Confirmation**: Required before first login (check spam folder)
- **Password Reset**: Available via "Forgot Password" link

::: tip Supabase Local Development
For local Supabase setup, see [Database Setup](/guide/database-setup). Users are auto-confirmed in local mode.
:::

## Using the AI Tutor

Once logged in, you can get AI assistance while solving problems:

1. Open any problem
2. Click the **"Chat"** button in the editor panel
3. Choose your mode:
   - **Socratic**: AI asks guiding questions (recommended for learning)
   - **Direct**: AI gives straightforward explanations
4. Ask questions like "What pattern should I use?" or "Why is my solution failing?"

::: info API Keys Required
AI features require at least one API key configured:
- `OPENAI_API_KEY` for GPT models
- `GOOGLE_API_KEY` for Gemini models
- `ANTHROPIC_API_KEY` for Claude models
:::

## What's Next?

- [Prerequisites](/guide/prerequisites) - Detailed environment setup
- [Adding Problems](/guide/adding-problems) - Create custom problems
- [Spaced Repetition](/guide/spaced-repetition) - Understand the algorithm
- [API Reference](/api/overview) - Build integrations

## Troubleshooting

### Services not starting

```bash
# Check container status
docker compose ps

# View logs for specific service
docker compose logs backend
docker compose logs judge0-server
```

### Can't create account / "Invalid credentials"

- Check Supabase project is active
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check email for confirmation link (including spam)
- In Supabase dashboard, check Authentication > Users

### Judge0 not responding

```bash
# Restart Judge0 services
docker compose restart judge0-server judge0-workers

# Check logs
docker compose logs judge0-server
```

### Database connection failed

- Verify `DATABASE_URL` uses `postgresql+asyncpg://` (not `postgresql://`)
- Check Supabase project is running
- Ensure your IP is allowed (Supabase > Settings > Database)

### Frontend can't reach backend

- Ensure backend is running on `http://localhost:8000`
- Verify `VITE_API_URL` in `frontend/.env`
- Check browser console for CORS errors

## Need More Help?

See detailed guides:
- [Backend Setup](/guide/backend-setup)
- [Frontend Setup](/guide/frontend-setup)
- [Judge0 Setup](/guide/judge0-setup)
- [Database Setup](/guide/database-setup)
