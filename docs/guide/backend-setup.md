# Backend Setup

This guide walks you through setting up the FastAPI backend for acodeaday.

## Prerequisites

Before starting, ensure you have:
- Python 3.12+ installed
- `uv` package manager installed
- Supabase project created (or local Supabase running)
- Judge0 running in Docker

See [Prerequisites](/guide/prerequisites) for installation instructions.

## Clone the Repository

```bash
git clone https://github.com/engineeringwithtemi/acodeaday.git
cd acodeaday/backend
```

## Install Dependencies

The project uses `uv` for dependency management, which reads from `pyproject.toml`.

```bash
uv sync
```

This will:
- Create a virtual environment (`.venv`)
- Install all dependencies from `pyproject.toml`
- Lock dependencies in `uv.lock`

To activate the virtual environment:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

## Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres

# Supabase (if using Supabase cloud)
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_ANON_KEY]

# Judge0
JUDGE0_URL=http://localhost:2358

# Authentication (Basic Auth)
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password

# Environment
ENVIRONMENT=development
```

**Important:** Replace the placeholder values with your actual credentials.

### Getting Supabase Credentials

1. Go to your Supabase project dashboard
2. Click "Settings" > "API"
3. Copy:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_KEY`
4. Click "Database" > "Connection string"
5. Copy the URI and convert to async format:
   - Change `postgresql://` to `postgresql+asyncpg://`
   - Replace `[YOUR-PASSWORD]` with your database password

## Run Database Migrations

Apply all database migrations to create the required tables:

```bash
uv run alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial, Initial schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_user_progress, Add user progress
...
```

### Verify Migrations

Check current migration status:

```bash
uv run alembic current
```

View migration history:

```bash
uv run alembic history
```

## Seed Initial Problems

Load the problems into the database:

```bash
uv run python scripts/seed_problems.py seed
```

This will:
- Read YAML files from `backend/data/problems/`
- Insert problems, test cases, and language-specific code
- Skip problems that already exist (safe to run multiple times)

### Seed Specific Problems

```bash
# Seed a specific file
uv run python scripts/seed_problems.py seed 001-two-sum.yaml

# Force update existing problems
uv run python scripts/seed_problems.py seed --force
```

### Create New Problem Template

```bash
uv run python scripts/seed_problems.py new my-problem-slug --lang python
```

See [Adding Problems](/guide/adding-problems) for more details.

## Start the Development Server

Start the FastAPI server with auto-reload:

```bash
uv run uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000`

### Verify Backend is Running

Open `http://localhost:8000/docs` in your browser to see the interactive API documentation (Swagger UI).

Test a simple endpoint:

```bash
curl http://localhost:8000/api/problems
```

You should see a JSON response with the list of problems.

## Run Tests

The backend includes pytest tests for API endpoints and core logic:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_problems.py

# Run with verbose output
uv run pytest -v
```

## Common Commands

```bash
# Install new dependency
uv add package-name

# Install dev dependency
uv add --dev package-name

# Update dependencies
uv sync

# Run alembic commands
uv run alembic upgrade head    # Apply migrations
uv run alembic downgrade -1    # Rollback one migration
uv run alembic revision --autogenerate -m "message"  # Create new migration

# Run Python scripts
uv run python scripts/seed_problems.py seed

# Start server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── routes/              # API route handlers
│   ├── services/            # Business logic
│   └── db.py                # Database session management
├── alembic/
│   ├── versions/            # Migration files
│   └── env.py               # Alembic configuration
├── data/
│   └── problems/            # YAML problem definitions
├── scripts/
│   └── seed_problems.py     # Problem seeder CLI
├── tests/                   # Pytest tests
├── pyproject.toml           # Python dependencies
├── uv.lock                  # Locked dependencies
└── .env                     # Environment variables
```

## Troubleshooting

### "No module named 'app'"

Make sure you're running commands with `uv run`:
```bash
uv run uvicorn app.main:app --reload
```

### Database connection errors

- Verify `DATABASE_URL` in `.env` uses `postgresql+asyncpg://` (not `postgresql://`)
- Check your Supabase project is active
- Ensure your IP is allowed in Supabase (Settings > Database > Connection pooling)

### Judge0 connection errors

- Verify Judge0 is running: `docker-compose ps` in `backend/judge0/`
- Check `JUDGE0_URL` in `.env` is correct (`http://localhost:2358`)
- Test Judge0 directly: `curl http://localhost:2358/about`

### Migration errors

```bash
# Reset migrations (WARNING: deletes all data)
uv run alembic downgrade base
uv run alembic upgrade head
```

## Next Steps

- [Frontend Setup](/guide/frontend-setup) - Set up the React frontend
- [Judge0 Setup](/guide/judge0-setup) - Configure code execution
- [Adding Problems](/guide/adding-problems) - Add more problems
- [API Reference](/api/overview) - Explore API endpoints
