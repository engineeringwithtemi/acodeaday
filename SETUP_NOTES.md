# Setup Notes

## What Happened

The initial `docker compose up -d` failed because of a **startup timing issue**.

### The Problem

```
could not translate host name "judge0-db" to address: Name or service not known
```

Judge0 server was trying to connect to PostgreSQL before it was fully ready, even though `depends_on` was configured.

### Root Cause

Docker Compose's `depends_on` only waits for containers to **start**, not for services inside them to be **ready**. PostgreSQL needs time to initialize its database before accepting connections.

### The Fix

Added **health checks** to ensure services wait for dependencies to be fully ready:

1. **PostgreSQL health check:**
   ```yaml
   healthcheck:
     test: ["CMD-SHELL", "pg_isready -U judge0"]
     interval: 5s
     timeout: 5s
     retries: 5
   ```

2. **Redis health check:**
   ```yaml
   healthcheck:
     test: ["CMD", "redis-cli", "ping"]
     interval: 5s
     timeout: 3s
     retries: 5
   ```

3. **Updated depends_on to wait for health:**
   ```yaml
   depends_on:
     judge0-db:
       condition: service_healthy  # ← Wait for healthy, not just started
     judge0-redis:
       condition: service_healthy
   ```

### Port Conflict

Also fixed port conflict:
- Changed Judge0 PostgreSQL from port **5433** → **5434**
- Reason: Port 5433 was already in use by aide project's PostgreSQL

---

## Current Status

✅ **All services running successfully:**

```bash
$ docker compose ps
NAME                       STATUS
acodeaday-judge0-db        Up (healthy)
acodeaday-judge0-redis     Up (healthy)
acodeaday-judge0-server    Up
acodeaday-judge0-workers   Up
```

✅ **Judge0 API responding:**
```bash
$ curl http://localhost:2358/about
{"version":"1.13.0",...}
```

✅ **Python 3.8.1 available (Language ID: 71)**

---

## Service Endpoints

| Service | Endpoint |
|---------|----------|
| Judge0 API | http://localhost:2358 |
| Judge0 PostgreSQL | localhost:5434 |
| Judge0 Redis | localhost:6380 |

---

## Testing Judge0

Quick test to verify code execution works:

```bash
# Submit a Python "Hello World"
curl -X POST http://localhost:2358/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello from Judge0!\")",
    "language_id": 71,
    "stdin": ""
  }'
```

Response will include a `token`. Use it to get results:

```bash
# Replace TOKEN with the token from above
curl "http://localhost:2358/submissions/TOKEN?base64_encoded=false"
```

---

## Key Takeaways

1. **Health checks are essential** for services with dependencies
2. **Port conflicts** can happen with multiple projects - always check with `docker ps`
3. **Startup order matters** - database must be ready before app servers
4. **Docker Compose v3.8+ deprecates `version`** field - removed from config

---

## Next Steps

1. Start Supabase: `supabase start`
2. Initialize backend: `cd backend && uv init`
3. Set up database models and migrations
4. Build FastAPI routes

See [TASKS.md](./TASKS.md) for full implementation plan.
