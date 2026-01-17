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

Judge0 is configured in the root `docker-compose.yml` file along with other services.

### 1. Start Judge0 Services

From the project root directory:

```bash
# Start all Judge0 services
docker compose up -d judge0-server judge0-workers judge0-db judge0-redis

# Or start all services including backend/frontend
docker compose up -d
```

This will:
- Pull necessary Docker images (first time only, ~2-3 GB)
- Start all Judge0 services in detached mode
- Expose the API on `http://localhost:2358`

### 2. Wait for Initialization

Judge0 workers need ~30 seconds to initialize. Check status:

```bash
docker compose ps
```

All services should show `Up` status:
```
NAME                        STATUS
acodeaday-judge0-server     Up
acodeaday-judge0-workers    Up
acodeaday-judge0-db         Up (healthy)
acodeaday-judge0-redis      Up (healthy)
```

### 3. Verify Judge0 is Running

Test the API:

```bash
curl http://localhost:2358/about
```

You should see JSON response with Judge0 version info:
```json
{
  "version": "1.13.1",
  "homepage": "https://judge0.com",
  ...
}
```

## Configuration

### Docker Compose Configuration

Judge0 configuration is in `docker-compose.yml` at the project root. Key settings:

```yaml
judge0-server:
  image: judge0/judge0:1.13.1
  environment:
    # Resource limits
    - MAX_CPU_TIME_LIMIT=15        # seconds
    - MAX_WALL_TIME_LIMIT=30       # seconds
    - MAX_MEMORY_LIMIT=512000      # KB (512 MB)
    - MAX_STACK_LIMIT=128000       # KB (128 MB)
    - MAX_PROCESSES_AND_OR_THREADS=60

    # Queue settings
    - MAX_QUEUE_SIZE=1000
    - ENABLE_WAIT_RESULT=true
```

### Environment Variable

Set the Judge0 URL in your `.env` file:

```bash
JUDGE0_URL=http://localhost:2358
```

For Docker deployment, the backend connects via the Docker network:
```bash
JUDGE0_URL=http://judge0-server:2358
```

## Testing Judge0

### Test Python Execution

Submit a test Python program:

```bash
curl -X POST "http://localhost:2358/submissions?base64_encoded=false&wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello from Judge0!\")",
    "language_id": 71
  }'
```

You should get a response like:
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
| Language | ID |
|----------|-----|
| Python 3 | 71 |
| JavaScript (Node.js) | 63 |
| Java | 62 |
| C++ | 54 |
| Go | 60 |
| Rust | 73 |

Get all supported languages:
```bash
curl http://localhost:2358/languages
```

## Integration with Backend

The backend communicates with Judge0 via synchronous HTTP requests:

```python
# backend/app/services/judge0.py
class Judge0Service:
    def __init__(self):
        self.base_url = settings.judge0_url

    def execute_code(self, source_code: str, language: str, stdin: str = "") -> dict:
        response = httpx.post(
            f"{self.base_url}/submissions?base64_encoded=false&wait=true",
            json={
                "source_code": source_code,
                "language_id": LANGUAGE_MAP[language],
                "stdin": stdin,
            },
            timeout=30.0,
        )
        return response.json()
```

## Common Commands

```bash
# Start Judge0 services
docker compose up -d judge0-server judge0-workers judge0-db judge0-redis

# Stop Judge0 services
docker compose stop judge0-server judge0-workers judge0-db judge0-redis

# View logs
docker compose logs judge0-server
docker compose logs judge0-workers

# Restart services
docker compose restart judge0-server judge0-workers

# Remove all data (WARNING: deletes all Judge0 data)
docker compose down -v
```

## Troubleshooting

### Services not starting

```bash
# Check logs for errors
docker compose logs judge0-server

# Ensure ports are not in use
lsof -i :2358
```

### "Connection refused" errors

1. Wait 30 seconds after `docker compose up` for initialization
2. Check services are running: `docker compose ps`
3. Verify firewall isn't blocking port 2358

### Submissions stuck in "Processing"

```bash
# Check worker logs
docker compose logs judge0-workers

# Restart workers
docker compose restart judge0-workers
```

### High memory usage

Judge0 workers cache language environments. This is normal. To reduce memory:

1. Reduce worker processes in the worker command
2. Set stricter memory limits in environment variables

### Permission errors

```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./judge0-data
```

## Coming Soon

Support for hosted Judge0 services (like RapidAPI) is planned for a future release. This will allow using Judge0 without self-hosting.

## Next Steps

- [Backend Setup](/guide/backend-setup) - Configure FastAPI to use Judge0
- [Adding Problems](/guide/adding-problems) - Create problems with test cases
- [Environment Variables](/guide/environment-variables) - Configure all env vars
