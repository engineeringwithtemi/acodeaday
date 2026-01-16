# Judge0 Setup

Judge0 is the code execution engine for acodeaday. It runs user code in isolated Docker containers for security.

## What is Judge0?

Judge0 CE (Community Edition) is an open-source online code execution system. It:
- Executes code in 60+ programming languages
- Runs code in isolated Docker containers
- Provides CPU and memory limits
- Returns execution results (stdout, stderr, runtime, memory)

## Prerequisites

- Docker installed
- Docker Compose installed

See [Prerequisites](/guide/prerequisites) for installation instructions.

## Setup via Docker Compose

The easiest way to run Judge0 is using the provided Docker Compose configuration.

### 1. Navigate to Judge0 Directory

```bash
cd acodeaday/backend/judge0
```

### 2. Review docker-compose.yml

The configuration includes:
- **judge0-server**: Main API server (port 2358)
- **judge0-workers**: Code execution workers (configurable count)
- **judge0-db**: PostgreSQL database for Judge0 metadata
- **redis**: Queue for job management

### 3. Start Judge0 Services

```bash
docker-compose up -d
```

This will:
- Pull necessary Docker images (first time only, ~2-3 GB)
- Start all services in detached mode
- Expose the API on `http://localhost:2358`

### 4. Wait for Initialization

Judge0 workers need ~30 seconds to initialize. Check status:

```bash
docker-compose ps
```

All services should show `Up` status:
```
NAME                STATUS
judge0-server       Up
judge0-worker-1     Up
judge0-worker-2     Up
judge0-db           Up
redis               Up
```

### 5. Verify Judge0 is Running

Test the API:

```bash
curl http://localhost:2358/about
```

You should see JSON response with Judge0 version info:
```json
{
  "version": "1.13.0",
  "homepage": "https://judge0.com",
  ...
}
```

## Configuration

### Environment Variables

Judge0 configuration is in `docker-compose.yml`. Key settings:

```yaml
environment:
  # Disable authentication (for local dev only)
  JUDGE0_AUTHENTICATION_ENABLED: "false"

  # Worker count (adjust based on CPU cores)
  WORKERS_COUNT: "2"

  # Resource limits
  CPU_TIME_LIMIT: "2"      # seconds
  MAX_CPU_TIME_LIMIT: "5"  # seconds
  MEMORY_LIMIT: "128000"   # KB
  MAX_MEMORY_LIMIT: "256000" # KB
```

### Adjust Worker Count

For better performance, adjust worker count based on your CPU cores:

```yaml
# In docker-compose.yml
services:
  worker:
    deploy:
      replicas: 4  # Set to number of CPU cores
```

Then restart:
```bash
docker-compose up -d --scale worker=4
```

### Resource Limits

Adjust limits in `docker-compose.yml` based on your needs:

```yaml
environment:
  # Increase for complex problems
  CPU_TIME_LIMIT: "5"
  MEMORY_LIMIT: "256000"
```

## Testing Judge0

### Test Python Execution

Create a test submission:

```bash
curl -X POST http://localhost:2358/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello from Judge0!\")",
    "language_id": 71,
    "stdin": ""
  }'
```

You'll get a response with a token:
```json
{"token": "abc123..."}
```

Retrieve the result:

```bash
curl http://localhost:2358/submissions/abc123...?base64_encoded=false
```

Result:
```json
{
  "stdout": "Hello from Judge0!\n",
  "status": {"id": 3, "description": "Accepted"},
  "time": "0.02",
  "memory": 1024
}
```

### Language IDs

Common languages supported:
- Python 3: `71`
- JavaScript (Node.js): `63`
- Java: `62`
- C++: `54`
- Go: `60`

[Full list of language IDs](https://github.com/judge0/judge0/blob/master/CHANGELOG.md#languages)

## Integration with acodeaday Backend

The FastAPI backend communicates with Judge0 via HTTP:

```python
# backend/app/services/judge0.py
async def execute_code(code: str, language_id: int, stdin: str):
    # Submit code to Judge0
    response = await http_client.post(
        f"{JUDGE0_URL}/submissions",
        json={
            "source_code": base64.b64encode(code.encode()).decode(),
            "language_id": language_id,
            "stdin": base64.b64encode(stdin.encode()).decode(),
        }
    )

    token = response.json()["token"]

    # Poll for results
    result = await get_submission(token)
    return result
```

Configure Judge0 URL in backend `.env`:
```bash
JUDGE0_URL=http://localhost:2358
```

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs judge0-server
docker-compose logs judge0-worker

# Restart services
docker-compose restart

# Scale workers
docker-compose up -d --scale worker=4

# Remove all data (WARNING: deletes all)
docker-compose down -v
```

## Troubleshooting

### Services not starting

```bash
# Check logs for errors
docker-compose logs

# Ensure ports are not in use
lsof -i :2358  # Check if port 2358 is free
```

### "Connection refused" errors

- Wait 30 seconds after `docker-compose up`
- Check services are running: `docker-compose ps`
- Verify firewall isn't blocking port 2358

### Submissions stuck in "Processing"

```bash
# Check worker logs
docker-compose logs judge0-worker

# Restart workers
docker-compose restart judge0-worker
```

### High memory usage

Judge0 workers cache language environments. This is normal. To reduce:

```yaml
# In docker-compose.yml
environment:
  WORKERS_COUNT: "1"  # Reduce worker count
```

### Permission errors

```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./judge0-data
```

## Production Considerations

For production deployments:

1. **Enable authentication**:
   ```yaml
   environment:
     JUDGE0_AUTHENTICATION_ENABLED: "true"
     JUDGE0_AUTHENTICATION_TOKEN: "your-secret-token"
   ```

2. **Use persistent volumes** for database:
   ```yaml
   volumes:
     - ./judge0-data/postgres:/var/lib/postgresql/data
   ```

3. **Configure resource limits** per your server capacity

4. **Use Docker Swarm or Kubernetes** for scaling

5. **Monitor resource usage**:
   ```bash
   docker stats
   ```

## Alternative: Hosted Judge0

Instead of self-hosting, you can use Judge0's hosted service:

1. Sign up at [rapidapi.com/judge0](https://rapidapi.com/judge0-judge0-default/api/judge0-ce)
2. Get API key
3. Configure in backend `.env`:
   ```bash
   JUDGE0_URL=https://judge0-ce.p.rapidapi.com
   JUDGE0_API_KEY=your-api-key
   ```

**Note:** Free tier has rate limits.

## Next Steps

- [Backend Setup](/guide/backend-setup) - Configure FastAPI to use Judge0
- [Adding Problems](/guide/adding-problems) - Create problems with test cases
- [Environment Variables](/guide/environment-variables) - Configure all env vars
