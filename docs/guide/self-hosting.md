# Self-Hosting acodeaday

Run acodeaday on your own infrastructure - from a personal laptop to a production VPS.

## Requirements

Before you begin, you'll need:

- **Docker & Docker Compose** - For running Judge0 (code execution engine)
- **Supabase account** - For authentication and database ([free tier](https://supabase.com) works)
- **2+ CPU cores, 4GB+ RAM** - Judge0 is resource-intensive

## Choose Your Deployment Method

### Option 1: Personal Machine (Manual)

Best for: Local development, learning the codebase

Run services separately with hot-reload:

```bash
# Clone the repo
git clone https://github.com/engineeringwithtemi/acodeaday.git
cd acodeaday

# Start Judge0 (requires Docker)
docker compose up -d judge0-server judge0-workers judge0-db judge0-redis

# Start backend
cd backend
uv sync
cp .env.example .env  # Edit with your Supabase credentials
uv run alembic upgrade head
uv run python scripts/seed_problems.py seed
uv run uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm install
cp .env.example .env  # Set VITE_API_URL=http://localhost:8000
npm run dev
```

See [Quick Start](/guide/quick-start) for detailed instructions.

---

### Option 2: Personal Machine (Docker Compose)

Best for: Running everything locally with one command

```bash
# Clone the repo
git clone https://github.com/engineeringwithtemi/acodeaday.git
cd acodeaday

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Start all services
docker compose up -d

# Run migrations (first time only)
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_problems.py seed
```

Access the app at `http://localhost:3000`

---

### Option 3: VPS with Docker

Best for: Self-hosted production on your own server

Same as Option 2, but on a remote server. SSH into your VPS and follow the same steps.

**Additional considerations:**
- Open ports 3000 (frontend) and 8000 (backend) in your firewall
- Set `VITE_API_URL` to your server's public IP or domain
- Consider using a reverse proxy (nginx/Caddy) for SSL

---

### Option 4: Pre-built Images (Recommended for Production)

Best for: Quick deployment without building from source

Use our pre-built Docker images:

```bash
# Download the production compose file
curl -O https://raw.githubusercontent.com/engineeringwithtemi/acodeaday/main/docker-compose.prod.yml

# Edit environment variables (search for CHANGE_ME)
# Required: DATABASE_URL, SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY

# Start all services
docker compose -f docker-compose.prod.yml up -d
```

The backend automatically runs migrations and seeds problems on startup.

**Images available at:**
- `ghcr.io/engineeringwithtemi/acodeaday-backend:latest`
- `ghcr.io/engineeringwithtemi/acodeaday-frontend:latest`

---

### Option 5: Coolify / PaaS

Best for: One-click deployment with automatic SSL and updates

See [Deploy to Coolify](/guide/deploy-coolify) for detailed instructions.

**Quick overview:**
1. Add your GitHub repo to Coolify
2. Configure environment variables
3. Set up domain routing (recommended: path-based)
4. Deploy

---

### Option 6: Distributed Deployment

Best for: Scaling frontend and backend independently

Deploy each component to its optimal platform:

| Component | Recommended Platforms |
|-----------|----------------------|
| Frontend | Vercel, Netlify, Cloudflare Pages |
| Backend | Railway, Fly.io, Render |
| Judge0 | Self-hosted VPS or RapidAPI |

See [Distributed Deployment](/guide/deploy-distributed) for details.

---

## Environment Variables

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:6543/db` |
| `SUPABASE_URL` | Your Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon/public key | `eyJ...` |
| `JUDGE0_URL` | Judge0 API endpoint | `http://judge0-server:2358` |

### Backend (Recommended)

| Variable | Description |
|----------|-------------|
| `SUPABASE_SERVICE_ROLE_KEY` | Auto-confirms user email on creation (from Supabase Settings > API) |

### Backend (Optional)

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | For Gemini AI chat |
| `OPENAI_API_KEY` | For GPT AI chat |
| `ANTHROPIC_API_KEY` | For Claude AI chat |

### Frontend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` or `/api` |
| `VITE_SUPABASE_URL` | Your Supabase project URL | `https://xxx.supabase.co` |
| `VITE_SUPABASE_KEY` | Supabase anon/public key | `eyJ...` |

See [Environment Variables](/guide/environment-variables) for complete reference.

---

## Troubleshooting

### Judge0 not starting

Judge0 requires **privileged mode** to run sandboxed code execution:

```yaml
services:
  judge0-server:
    privileged: true  # Required!
```

Some container platforms (like certain Kubernetes setups) don't support privileged containers. In that case, use an external Judge0 instance or RapidAPI.

### Database connection failed

- Ensure `DATABASE_URL` uses `postgresql+asyncpg://` (not `postgresql://`)
- **For Supabase Cloud**: Use the **Transaction pooler** URL (port 6543), NOT direct connection (port 5432)
- Check if your IP is allowed in Supabase (Settings > Database > Network)
- Verify the database exists and is accessible
- **If using local Supabase with Docker**: See the section below

::: tip Getting the Right Supabase Cloud Connection String
1. Go to Supabase Dashboard → **Settings** → **Database**
2. Under **Connection string**, select **URI**
3. Choose **Transaction pooler** (port 6543)
4. Copy and replace `postgresql://` with `postgresql+asyncpg://`

Example:
```bash
# From Supabase:
postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Convert to:
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```
:::

### Using Local Supabase with Docker

::: warning Important
If you're running Supabase locally (`supabase start`) and want to run the backend in Docker, you **must** use `host.docker.internal` instead of `localhost` or `127.0.0.1`.
:::

**Why?** Docker containers have their own network. When the backend container tries to connect to `127.0.0.1:54322`, it's looking inside the container—not your Mac/PC where Supabase is running.

**Solution**: In your `.env` file, use `host.docker.internal`:

```bash
# For Docker + local Supabase
DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:54322/postgres
SUPABASE_URL=http://host.docker.internal:54321

# For local dev WITHOUT Docker (running backend directly)
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres
# SUPABASE_URL=http://127.0.0.1:54321
```

**Note**: Shell environment variables override `.env` file values. If you previously ran `export DATABASE_URL=...`, unset it first:

```bash
unset DATABASE_URL SUPABASE_URL
docker compose up -d
```

**Alternative**: Use Supabase Cloud instead of local Supabase to avoid this complexity.

### Frontend can't reach backend

- Check `VITE_API_URL` is set correctly
- For same-machine deployment: use `http://localhost:8000`
- For VPS with domain: use the public URL (e.g., `https://api.yourdomain.com`)
- For Coolify with path routing: use `/api`

### CORS errors

Update the `CORS_ORIGINS` environment variable to include your frontend domain:

```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Browser showing old configuration after environment variable change

**Problem:** After changing `VITE_API_URL` or other frontend environment variables, the browser still uses the old values.

**Cause:** Browser caches JavaScript files. The frontend replaces environment variable placeholders at container startup, but browsers may serve cached versions of the old files.

**Solution:**
1. **Hard refresh**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Clear browser cache** if hard refresh doesn't work
3. **Try incognito/private mode** to verify with a clean cache
4. **Log out and log back in** to force a fresh page load

::: tip
After changing environment variables:
1. Restart the frontend container
2. Tell users to hard refresh their browsers
:::

---

## Next Steps

- [Deploy to Coolify](/guide/deploy-coolify) - PaaS deployment guide
- [Distributed Deployment](/guide/deploy-distributed) - Deploy on multiple platforms
- [Environment Variables](/guide/environment-variables) - Complete reference
- [Adding Problems](/guide/adding-problems) - Customize problem set
