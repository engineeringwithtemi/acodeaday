# acodeaday

> A daily coding practice app with spaced repetition to help you master the Blind 75.

**Open source.** Self-host it, fork it, make it yours.

---

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- [Supabase CLI](https://supabase.com/docs/guides/cli)
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Setup

1. **Start Supabase (PostgreSQL database)**
   ```bash
   supabase start
   ```

   Copy the `DB URL` from the output and update `.env`:
   ```bash
   # Change postgresql:// to postgresql+asyncpg://
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54322/postgres
   ```

2. **Start Judge0 (Code execution engine)**
   ```bash
   # Start Judge0 in background
   docker-compose up -d

   # Verify it's running
   curl http://localhost:2358/

   # View logs if needed
   docker-compose logs -f judge0-server
   ```

   See [DOCKER.md](./DOCKER.md) for detailed Docker commands and troubleshooting.

3. **Set up Backend**
   ```bash
   cd backend
   uv venv
   uv sync

   # Run database migrations
   uv run alembic upgrade head

   # Seed problems (first 15 Blind 75)
   uv run python scripts/seed_problems.py

   # Start backend server
   uv run uvicorn app.main:app --reload
   ```

4. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the app**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Default login: `admin` / `changeme`

---

## Project Structure

```
acodeaday/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── config/      # Settings & logging
│   │   ├── db/          # Database models & connection
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   └── middleware/  # Auth & request handling
│   ├── migrations/      # Alembic database migrations
│   ├── scripts/         # Seed data & utilities
│   └── tests/
├── frontend/            # React + TanStack frontend
│   ├── src/
│   │   ├── pages/      # Route components
│   │   ├── components/ # UI components
│   │   ├── hooks/      # Custom React hooks
│   │   └── lib/        # API client & utilities
│   └── public/
├── supabase/           # Supabase configuration
├── docker-compose.yml  # Judge0 & services
└── .env               # Environment variables
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + TanStack Router |
| Code Editor | Monaco Editor |
| Backend | FastAPI (async) |
| Database | PostgreSQL (via Supabase) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Code Execution | Judge0 CE |
| Auth | HTTP Basic Auth |
| Logging | Structlog |

---

## Development

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run with auto-reload
uv run uvicorn app.main:app --reload --port 8000

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Database

```bash
# Start Supabase
supabase start

# Stop Supabase
supabase stop

# Reset database (WARNING: deletes all data)
supabase db reset

# View Supabase Studio
# URL shown in 'supabase start' output (usually http://localhost:54323)
```

### Docker

```bash
# Start all services
docker-compose up

# Start only Judge0
docker-compose up judge0

# Stop all services
docker-compose down

# View logs
docker-compose logs -f judge0
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection (asyncpg) | `postgresql+asyncpg://...` |
| `AUTH_USERNAME` | Basic auth username | `admin` |
| `AUTH_PASSWORD` | Basic auth password | `changeme` |
| `JUDGE0_URL` | Judge0 API endpoint | `http://localhost:2358` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/problems` | List all problems |
| GET | `/api/problems/{slug}` | Get problem details |
| POST | `/api/run` | Run code against test cases |
| POST | `/api/submit` | Submit solution (all tests) |
| GET | `/api/today` | Get today's session |
| GET | `/api/progress` | Get user progress |
| GET | `/api/mastered` | Get mastered problems |
| POST | `/api/mastered/{id}/show-again` | Re-add to rotation |

---

## Architecture

### Spaced Repetition

The app uses a simplified spaced repetition algorithm:

1. **First solve**: Problem enters review queue, due in 7 days
2. **Second solve**: Problem marked as "Mastered", removed from rotation
3. **"Show Again"**: User can manually re-add mastered problems

### Daily Session Logic

Each day presents up to 3 problems:

1. **Review #1**: Oldest overdue problem (if any)
2. **Review #2**: Second oldest overdue problem (if any)
3. **New Problem**: Next unsolved in Blind 75 sequence

### Code Execution Flow

```
User writes code in Monaco Editor
    ↓
Frontend sends to /api/submit
    ↓
Backend wraps code with test harness
    ↓
Sends to Judge0 for execution
    ↓
Judge0 runs code in sandbox
    ↓
Returns results (pass/fail per test case)
    ↓
Backend updates user_progress if all passed
    ↓
Frontend displays results
```

---

## Documentation

- **[README.md](./README.md)** (this file) - Quick start and overview
- **[TASKS.md](./TASKS.md)** - Detailed implementation tasks and patterns
- **[DOCKER.md](./DOCKER.md)** - Docker commands and troubleshooting
- **[spec.md](./spec.md)** - Complete product specification
- **[CLAUDE.md](./CLAUDE.md)** - Project instructions for Claude Code

---

## License

MIT — do whatever you want with it.

---

## Core Philosophy

> "A code a day keeps rejection away"

Focus on understanding through consistent practice, not cramming. One problem at a time, reviewed at optimal intervals for long-term retention.
