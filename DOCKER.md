# Docker Setup Guide

## Quick Start

### Start Judge0 Only (Recommended for Development)

```bash
# Start Judge0 services in background
docker-compose up -d judge0-server judge0-workers judge0-db judge0-redis

# Or simply (all judge0 services):
docker-compose up -d

# View logs
docker-compose logs -f judge0-server

# Check if Judge0 is ready
curl http://localhost:2358/
```

### Start All Services (Including Backend/Frontend in Docker)

If you uncommented backend/frontend in `docker-compose.yml`:

```bash
# Build and start all services
docker-compose up -d --build

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
```

---

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d judge0-server

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart a service
docker-compose restart judge0-server

# Rebuild a service
docker-compose up -d --build backend
```

### Logs & Debugging

```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f judge0-server

# View last 100 lines
docker-compose logs --tail=100 judge0-server

# Check service status
docker-compose ps

# Execute command in running container
docker-compose exec judge0-server bash
```

### Cleanup

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Remove unused images
docker image prune -a

# Clean up everything (careful!)
docker system prune -a --volumes
```

---

## Service URLs

| Service | URL | Port |
|---------|-----|------|
| Judge0 API | http://localhost:2358 | 2358 |
| Judge0 PostgreSQL | localhost:5434 | 5434 |
| Judge0 Redis | localhost:6380 | 6380 |
| Backend (if enabled) | http://localhost:8000 | 8000 |
| Frontend (if enabled) | http://localhost:5173 | 5173 |

---

## Judge0 Configuration

### Supported Languages

Judge0 CE supports 60+ languages.

**Python versions available:**
- Language ID 70: Python 2.7.17 (deprecated)
- **Language ID 71: Python 3.8.1** ← Use this for acodeaday

Check all available languages:
```bash
curl http://localhost:2358/languages | jq
```

Check Python versions:
```bash
curl http://localhost:2358/languages | jq '.[] | select(.name | contains("Python"))'
```

### Test Judge0

Create a test Python submission:

```bash
curl -X POST http://localhost:2358/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello, World!\")",
    "language_id": 71,
    "stdin": ""
  }'
```

Get submission result (replace TOKEN with the token from above response):
```bash
curl http://localhost:2358/submissions/TOKEN?base64_encoded=false
```

### Resource Limits

Configured in `docker-compose.yml`:

| Limit | Value |
|-------|-------|
| Max CPU Time | 15 seconds |
| Max Wall Time | 30 seconds |
| Max Memory | 512 MB |
| Max Stack | 128 MB |
| Max Processes | 60 |

---

## Troubleshooting

### Judge0 Not Starting

1. **Check if ports are available:**
   ```bash
   lsof -i :2358
   lsof -i :5433
   lsof -i :6380
   ```

2. **View logs for errors:**
   ```bash
   docker-compose logs judge0-server
   docker-compose logs judge0-workers
   ```

3. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Judge0 Database Connection Issues

```bash
# Check if postgres is running
docker-compose ps judge0-db

# Connect to postgres
docker-compose exec judge0-db psql -U judge0 -d judge0

# View database logs
docker-compose logs judge0-db
```

### Redis Connection Issues

```bash
# Check if redis is running
docker-compose ps judge0-redis

# Connect to redis
docker-compose exec judge0-redis redis-cli

# Test redis connection
docker-compose exec judge0-redis redis-cli ping
```

### High Memory Usage

Judge0 workers can use significant memory. To limit:

```bash
# Edit docker-compose.yml and add under judge0-workers:
#   deploy:
#     resources:
#       limits:
#         memory: 2G
```

### Cleanup Stuck Submissions

```bash
# Access Judge0 database
docker-compose exec judge0-db psql -U judge0 -d judge0

# Clear old submissions
DELETE FROM submissions WHERE created_at < NOW() - INTERVAL '1 day';
```

---

## Production Deployment

### Environment Variables

For production, create a `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  judge0-server:
    environment:
      - AUTHENTICATION_TOKEN=your-secure-token-here
      - ENABLE_SUBMISSION_DELETE=true
      - CALLBACKS_MAX_TRIES=5

  backend:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=WARNING
```

### Security Considerations

1. **Enable Judge0 authentication:**
   - Set `AUTHENTICATION_TOKEN` in environment
   - Include token in backend requests to Judge0

2. **Use secrets for sensitive data:**
   ```bash
   echo "your-secret" | docker secret create judge0_password -
   ```

3. **Limit resource access:**
   - Run containers with `--read-only` where possible
   - Use `--security-opt=no-new-privileges`

4. **Network isolation:**
   - Use internal networks for service communication
   - Only expose necessary ports

### Monitoring

Add monitoring services to `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## Development Workflow

### Recommended Setup

For local development, we recommend:

1. **Run Judge0 in Docker** (this guide)
2. **Run Backend locally** with `uv run uvicorn app.main:app --reload`
3. **Run Frontend locally** with `npm run dev`
4. **Run Supabase locally** with `supabase start`

This gives you:
- ✅ Fast backend/frontend hot-reload
- ✅ Easy debugging
- ✅ Isolated Judge0 environment
- ✅ Better IDE integration

### Running Backend/Frontend in Docker

If you prefer everything in Docker:

1. Uncomment backend/frontend services in `docker-compose.yml`
2. Create `backend/Dockerfile` (see TASKS.md for template)
3. Create `frontend/Dockerfile` (see TASKS.md for template)
4. Run: `docker-compose up -d --build`

---

## Additional Resources

- [Judge0 Documentation](https://github.com/judge0/judge0/blob/master/README.md)
- [Judge0 API Documentation](https://ce.judge0.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [TASKS.md](./TASKS.md) - Implementation tasks
- [README.md](./README.md) - Project setup guide
