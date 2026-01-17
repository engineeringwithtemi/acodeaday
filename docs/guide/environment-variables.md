# Environment Variables

Complete reference for all environment variables used in acodeaday.

## Configuration File Location

All environment variables are stored in a single `.env` file at the project root. Both the backend and frontend read from this file.

**Location:** `.env` (project root)

The backend uses `pydantic-settings` which loads from `../.env` (parent directory) first, then `.env` in the current directory. The frontend uses Vite's `envDir` configuration to read from the parent directory.

## Required Variables

### Database

```bash
# PostgreSQL connection string (async format required)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54322/postgres
```

**Important:** Must use `postgresql+asyncpg://` (not `postgresql://`) for async SQLAlchemy.

For local Supabase, get this from `supabase status` output (look for "DB URL") and replace `postgresql://` with `postgresql+asyncpg://`.

### Supabase Authentication

```bash
# Supabase project URL
SUPABASE_URL=http://127.0.0.1:54321

# Supabase anon/public key (for JWT validation)
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Supabase JWT secret (for token validation)
SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
```

For local Supabase, these values are available from `supabase status` after running `supabase start`.

### Default User Credentials

```bash
# Default user email (created on backend startup via Supabase Auth)
DEFAULT_USER_EMAIL=admin@acodeaday.local

# Default user password (min 6 characters)
DEFAULT_USER_PASSWORD=changeme123
```

**Important:** Change these in production! The backend automatically creates this user on startup if it doesn't exist.

**Note:** There is no signup flow. Users must either:
1. Use the default credentials configured above
2. Create a user manually in the Supabase dashboard

### Judge0 Code Execution

```bash
# Judge0 CE API endpoint (self-hosted via Docker)
JUDGE0_URL=http://localhost:2358

# Optional: Judge0 API key (for hosted/authenticated Judge0 instances)
JUDGE0_API_KEY=your_api_key_here
```

For local development, Judge0 runs via Docker Compose on port 2358.

### Frontend Variables

Frontend variables must start with `VITE_` to be exposed to the browser:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Supabase configuration (must match backend values)
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Optional Variables

### Application Settings

```bash
# Environment (development, staging, production)
ENVIRONMENT=development

# Debug mode (enables verbose SQL logging)
DEBUG=true

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log to file
LOG_TO_FILE=true
LOG_FILE_PATH=logs/acodeaday.log
```

### AI Chat (LLM)

```bash
# Comma-separated list of supported LLM models (via litellm)
LLM_SUPPORTED_MODELS=gemini/gemini-2.5-flash,gemini/gemini-2.5-pro,gpt-4o-mini,claude-3-5-sonnet-20241022

# LLM configuration
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7
LLM_MAX_CONTEXT_TOKENS=8000

# API keys for LLM providers (only needed if using those models)
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Complete .env.example

```bash
# =============================================================================
# acodeaday - Environment Variables
# =============================================================================
# Copy this file to .env and fill in your values:
#   cp .env.example .env

# =============================================================================
# Database (Supabase PostgreSQL)
# =============================================================================
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres

# =============================================================================
# Supabase Authentication
# =============================================================================
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long

# =============================================================================
# Default User (created on startup)
# =============================================================================
DEFAULT_USER_EMAIL=admin@acodeaday.local
DEFAULT_USER_PASSWORD=changeme123

# =============================================================================
# Judge0 Code Execution
# =============================================================================
JUDGE0_URL=http://localhost:2358
# JUDGE0_API_KEY=  # Optional: for authenticated Judge0 instances

# =============================================================================
# Application Settings
# =============================================================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/acodeaday.log

# =============================================================================
# Frontend (VITE_ prefix required)
# =============================================================================
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

# =============================================================================
# AI Chat (Optional - only if using AI features)
# =============================================================================
# LLM_SUPPORTED_MODELS=gemini/gemini-2.5-flash,gpt-4o-mini
# GOOGLE_API_KEY=
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
```

## How Environment Variables Are Loaded

### Backend (pydantic-settings)

The backend uses `pydantic-settings` for type-safe configuration:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = Field(...)
    judge0_url: str = Field("http://localhost:2358")
    # ...

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # Check parent dir first, then current
        extra="ignore"
    )

settings = Settings()
```

Access settings in code:

```python
from app.config.settings import settings

print(settings.database_url)
print(settings.judge0_url)
```

### Frontend (Vite)

Vite automatically loads `.env` files and exposes `VITE_*` variables:

```typescript
const apiUrl = import.meta.env.VITE_API_URL
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
```

The frontend's `vite.config.ts` is configured to read from the parent directory:

```typescript
export default defineConfig({
  envDir: path.resolve(__dirname, '..'),
  // ...
})
```

## Security Best Practices

### 1. Never Commit Secrets

Ensure `.gitignore` includes:

```
.env
.env.local
.env.*.local
```

Keep `.env.example` in the repo (with placeholder values, no real secrets).

### 2. Use Different Credentials Per Environment

Never reuse production credentials in development/staging.

### 3. Rotate Secrets Regularly

- Change passwords periodically
- Rotate API keys after team member changes
- Update Supabase keys if compromised

## Troubleshooting

### "Environment variable not found"

1. Verify the variable is set in `.env`
2. Restart the dev server after adding env vars
3. For frontend: ensure variable starts with `VITE_`

### Database connection fails

1. Check `DATABASE_URL` uses `postgresql+asyncpg://`
2. Verify Supabase is running: `supabase status`
3. Test connection manually: `psql $DATABASE_URL`

### Judge0 not responding

1. Verify Judge0 is running: `docker compose ps`
2. Test endpoint: `curl http://localhost:2358/about`
3. Check container logs: `docker compose logs judge0-server`

## Next Steps

- [Backend Setup](/guide/backend-setup) - Set up the FastAPI backend
- [Frontend Setup](/guide/frontend-setup) - Set up the TanStack frontend
- [Judge0 Setup](/guide/judge0-setup) - Configure code execution
