# Troubleshooting

Common issues and solutions when deploying or running acodeaday.

## Database Issues

### Connection failed / timeout

**Symptoms:** Backend fails to start, "connection refused", or timeout errors.

**Solutions:**

1. **Verify connection string format** - Must use `postgresql+asyncpg://` (not `postgresql://`)

2. **For Supabase Cloud** - Use the **Transaction pooler** URL (port 6543), not direct connection:
   ```bash
   # ✅ Correct - Transaction pooler (port 6543)
   postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

   # ❌ Wrong - Direct connection (port 5432)
   postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
   ```

   **To get the correct string:** Supabase Dashboard → Settings → Database → Connection string → URI → Transaction pooler

3. **For local Supabase with Docker** - Use `host.docker.internal` instead of `localhost`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:54322/postgres
   ```

4. **Check IP allowlist** - In Supabase Dashboard → Settings → Database → Network, ensure your server's IP is allowed.

---

## Authentication Issues

### "Email not confirmed" error

**Problem:** User can't log in because email isn't confirmed.

**Solutions:**

1. **Check email inbox** (including spam folder) for confirmation link

2. **Manually confirm in Supabase Dashboard:**
   - Go to Authentication → Users
   - Find the user and click "Confirm email"

3. **Use service role key for auto-confirm** (recommended):
   - Set `SUPABASE_SERVICE_ROLE_KEY` in your environment
   - The backend will auto-confirm users when creating them
   - Get this from Supabase Dashboard → Settings → API → `service_role` key

### "Invalid credentials" error

**Problem:** Login fails even with correct email/password.

**Solutions:**

1. Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
2. Check Supabase project is active (not paused)
3. Verify user exists in Supabase Dashboard → Authentication → Users
4. Ensure email is confirmed (see above)

---

## Frontend Issues

### Browser showing old API URLs after config change

**Problem:** After changing `VITE_API_URL` or other environment variables, the browser still makes requests to the old URL.

**Cause:** Browser caches JavaScript files. The frontend replaces environment variable placeholders at container startup, but browsers serve cached versions.

**Solutions:**

1. **Hard refresh**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

2. **Clear browser cache:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Or: DevTools (F12) → Network tab → Check "Disable cache" → Refresh

3. **Try incognito/private mode** to verify with a clean cache

4. **Log out and log back in** to force fresh page load

::: tip After Changing Environment Variables
1. Restart the frontend container
2. Tell users to hard refresh their browsers
:::

### Frontend can't reach backend

**Problem:** API requests fail, CORS errors, or "Network Error".

**Solutions:**

1. **Verify `VITE_API_URL`** is set correctly:
   - Local dev: `http://localhost:8000`
   - Subdomain routing: `https://api.yourdomain.com`
   - Path-based routing: `/api` or `https://yourdomain.com/api`

2. **Check CORS configuration** - Backend's `CORS_ORIGINS` must include the frontend domain:
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

3. **Verify backend is running:**
   ```bash
   curl https://api.yourdomain.com/health
   ```

### Double /api/api in URLs (path-based routing)

**Problem:** Requests go to `/api/api/...` instead of `/api/...`.

**Cause:** `VITE_API_URL` includes `/api` suffix AND frontend code adds `/api` prefix to endpoints.

**Solutions:**

1. **Use subdomain routing instead** (recommended):
   - Backend at `api.yourdomain.com`
   - Set `VITE_API_URL=https://api.yourdomain.com`
   - No path stripping needed

2. **For path-based routing:** Ensure the reverse proxy isn't stripping `/api` prefix, or adjust `VITE_API_URL` accordingly.

---

## Judge0 Issues

### Judge0 not starting

**Problem:** Judge0 container fails to start or stays unhealthy.

**Cause:** Judge0 requires privileged mode for sandboxed code execution.

**Solution:** Ensure `privileged: true` is set:
```yaml
services:
  judge0-server:
    privileged: true  # Required!
```

::: warning
Some platforms (like certain Kubernetes setups) don't support privileged containers. Use an external Judge0 instance or RapidAPI in that case.
:::

### Code execution times out

**Problem:** Submissions hang or timeout.

**Solutions:**

1. **Check Judge0 is healthy:**
   ```bash
   curl http://localhost:2358/about
   ```

2. **Check Judge0 workers are running:**
   ```bash
   docker compose logs judge0-workers
   ```

3. **Restart Judge0 services:**
   ```bash
   docker compose restart judge0-server judge0-workers
   ```

---

## Deployment Issues (Coolify/VPS)

### 502 Bad Gateway

**Problem:** Reverse proxy returns 502 error.

**Solutions:**

1. **Check container is running:**
   ```bash
   docker compose ps
   ```

2. **Check container logs:**
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

3. **Verify port configuration** in your reverse proxy matches the container's exposed port

### SSL/HTTPS issues

**Problem:** Mixed content errors or SSL certificate issues.

**Solutions:**

1. Ensure all URLs use HTTPS:
   - `VITE_API_URL=https://...` (not http)
   - `VITE_SUPABASE_URL=https://...`

2. Verify SSL certificate is valid and not expired

3. Check reverse proxy SSL configuration

---

## Getting Help

If you're still stuck:

1. **Check container logs** for detailed error messages:
   ```bash
   docker compose logs backend
   docker compose logs frontend
   docker compose logs judge0-server
   ```

2. **Search existing issues** on [GitHub](https://github.com/engineeringwithtemi/acodeaday/issues)

3. **Open a new issue** with:
   - What you're trying to do
   - Error messages (from logs and browser console)
   - Your environment (Docker, Coolify, etc.)
   - Relevant config (sanitize secrets!)
