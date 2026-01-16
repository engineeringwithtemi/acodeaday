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
# Copy example env files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `.env` with your Supabase credentials:

```bash
# Database (from Supabase dashboard > Settings > Database)
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres

# Supabase (from Supabase dashboard > Settings > API)
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_ANON_KEY]

# AI features (optional - for AI tutor)
OPENAI_API_KEY=sk-...
# or
GOOGLE_API_KEY=...
```

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

### 4. Run Database Migrations

```bash
docker compose exec backend uv run alembic upgrade head
docker compose exec backend uv run python scripts/seed_problems.py seed
```

### 5. Create Your Account & Start Coding!

1. Open `http://localhost:3000` in your browser
2. Click **"Sign Up"** to create an account via Supabase Auth
3. Check your email for the confirmation link
4. After confirming, log in with your credentials
5. You'll see your daily problems - start solving!

## Option 2: Local Development

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

### 3. Backend Setup

```bash
cd backend
uv sync
cp .env.example .env
# Edit .env with your Supabase credentials

uv run alembic upgrade head
uv run python scripts/seed_problems.py seed
uv run uvicorn app.main:app --reload
```

Backend available at `http://localhost:8000`

### 4. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env - set VITE_API_URL=http://localhost:8000

npm run dev
```

Frontend available at `http://localhost:5173`

### 5. Create Account & Start Coding!

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
