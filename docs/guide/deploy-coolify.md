# Deploy to Coolify

[Coolify](https://coolify.io) is a self-hostable PaaS that makes deploying Docker applications easy. This guide covers deploying acodeaday to Coolify.

## Prerequisites

- A Coolify instance (self-hosted or cloud)
- A VPS with at least 2 CPU cores and 4GB RAM
- A domain name (optional but recommended)
- Supabase account for auth and database

## Deployment Methods

### Method 1: Docker Compose (Recommended)

Deploy using the production compose file with pre-built images.

#### Step 1: Create a New Project

1. In Coolify, go to **Projects** → **New Project**
2. Name it `acodeaday`

#### Step 2: Add Docker Compose Resource

1. Click **+ New** → **Docker Compose**
2. Choose **Empty Docker Compose**
3. Paste the contents of `docker-compose.prod.yml` from the repo

#### Step 3: Configure Environment Variables

In the Coolify UI, add these environment variables:

**Required:**
```
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_URL=https://[your-project].supabase.co
SUPABASE_KEY=[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]
VITE_SUPABASE_URL=https://[your-project].supabase.co
VITE_SUPABASE_KEY=[your-anon-key]
```

::: tip Service Role Key
The `SUPABASE_SERVICE_ROLE_KEY` enables auto-confirmation of the default user's email. Without it, you'll need to manually confirm the user in Supabase Dashboard → Authentication → Users.
:::

**For path-based routing (recommended):**
```
VITE_API_URL=/api
```

**Optional (for AI chat):**
```
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

#### Step 4: Configure Domain Routing

**Recommended: Path-based routing (single domain)**

Configure Coolify/Caddy to route:
- `yourdomain.com/` → frontend container (port 3000)
- `yourdomain.com/api/` → backend container (port 8000)

With this setup, set `VITE_API_URL=/api` (relative URL).

**Alternative: Separate domains**

- `app.yourdomain.com` → frontend
- `api.yourdomain.com` → backend

Set `VITE_API_URL=https://api.yourdomain.com`

#### Step 5: Enable Privileged Mode for Judge0

Judge0 requires privileged mode. In Coolify:

1. Go to the Judge0 server container settings
2. Enable **Privileged Mode**
3. Do the same for Judge0 workers

::: warning
Privileged mode is required for Judge0's sandboxed code execution. Without it, code submissions will fail.
:::

#### Step 6: Deploy

Click **Deploy** and wait for all services to start. The backend will automatically:
- Run database migrations
- Seed the problem database

---

### Method 2: GitHub Repository

Let Coolify build from source.

#### Step 1: Connect GitHub

1. In Coolify, go to **Sources** → **Add GitHub App**
2. Authorize Coolify to access your repo

#### Step 2: Create Services

Add each service separately:

**Frontend:**
1. **+ New** → **Public Repository** or **Private Repository**
2. Enter: `https://github.com/engineeringwithtemi/acodeaday`
3. Set **Build Pack**: Docker
4. Set **Dockerfile Location**: `frontend/Dockerfile`
5. Set **Docker Context**: `frontend`

**Backend:**
1. Same process, but:
   - **Dockerfile Location**: `backend/Dockerfile`
   - **Docker Context**: `backend`

**Judge0 Stack:**
1. Add as Docker Compose
2. Include only Judge0 services from `docker-compose.yml`

#### Step 3: Configure Networking

Ensure all services are on the same Docker network so they can communicate.

#### Step 4: Set Environment Variables

Same as Method 1.

---

## Health Checks

The services include health checks:

**Backend:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 60s
  retries: 3
```

**Frontend:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  start_period: 30s
  retries: 3
```

Coolify will use these to determine when services are ready.

---

## Troubleshooting

### Judge0 fails to start

**Problem:** Judge0 requires privileged mode.

**Solution:** Enable privileged mode in Coolify container settings.

### Frontend can't reach backend

**Problem:** VITE_API_URL is incorrect.

**Solution:**
- Path-based routing: Set `VITE_API_URL=/api`
- Separate domains: Set `VITE_API_URL=https://api.yourdomain.com`

### Database connection timeout

**Problem:** Supabase connection pooler timeout or connection errors.

**Solution:** You **must** use the **Transaction pooler** URL (port 6543), not direct connection (port 5432):

```bash
# ✅ Correct - Transaction pooler (port 6543)
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# ❌ Wrong - Direct connection (port 5432)
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

**To get the correct connection string:**
1. Supabase Dashboard → **Settings** → **Database**
2. Under **Connection string**, select **URI**
3. Choose **Transaction pooler** (port 6543)
4. Replace `postgresql://` with `postgresql+asyncpg://`

### Migrations not running

**Problem:** Database tables don't exist.

**Solution:** The backend runs migrations automatically on startup. Check container logs:
```bash
docker logs acodeaday-backend
```

If migrations failed, you can run them manually:
```bash
docker exec acodeaday-backend alembic upgrade head
docker exec acodeaday-backend python scripts/seed_problems.py seed
```

### Browser showing old API URLs after config change

**Problem:** After changing `VITE_API_URL` or other environment variables, the browser still makes requests to the old URL.

**Cause:** Browser caches the compiled JavaScript files. Even though the container replaces environment variables at startup, browsers may serve cached versions.

**Solution:**
1. **Hard refresh** the page: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. If that doesn't work, **clear browser cache**:
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Or open DevTools (F12) → Network tab → Check "Disable cache" → Refresh
3. **Log out and log back in** - This forces a fresh page load
4. Try **incognito/private mode** to verify the fix works with a clean cache

::: tip For Production
After changing environment variables in Coolify:
1. Redeploy the frontend service
2. Ask users to hard refresh if they experience issues
:::

### SSL/HTTPS issues

**Problem:** Mixed content errors.

**Solution:** Ensure all URLs use HTTPS:
- `VITE_API_URL=https://api.yourdomain.com` (not http)
- `VITE_SUPABASE_URL=https://[project].supabase.co`

---

## Updates

To update to a new version:

1. Pull latest images: `docker compose pull`
2. Restart services: `docker compose up -d`

Or in Coolify, click **Redeploy**.

---

## Next Steps

- [Self-Hosting Overview](/guide/self-hosting) - Other deployment options
- [Environment Variables](/guide/environment-variables) - Complete reference
- [Adding Problems](/guide/adding-problems) - Customize problem set
