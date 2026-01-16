# Prerequisites

Before setting up acodeaday, ensure you have the following tools installed on your machine.

## Required Software

### Node.js 22+

The frontend is built with React and requires Node.js 22 or higher.

**Install:**
- **macOS**: `brew install node@22`
- **Linux**: Use [nvm](https://github.com/nvm-sh/nvm) or [official downloads](https://nodejs.org/)
- **Windows**: [Download from nodejs.org](https://nodejs.org/)

**Verify:**
```bash
node --version  # Should show v22.x.x or higher
npm --version
```

### Python 3.12+

The backend is built with FastAPI and requires Python 3.12 or higher.

**Install:**
- **macOS**: `brew install python@3.12`
- **Linux**: Use your package manager or [pyenv](https://github.com/pyenv/pyenv)
- **Windows**: [Download from python.org](https://www.python.org/downloads/)

**Verify:**
```bash
python3 --version  # Should show 3.12.x or higher
```

### uv (Python Package Manager)

acodeaday uses `uv` for fast, reliable Python dependency management.

**Install:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or using pip:
```bash
pip install uv
```

**Verify:**
```bash
uv --version
```

[Official uv documentation](https://github.com/astral-sh/uv)

### Docker & Docker Compose

Docker is required to run Judge0, the code execution engine.

**Install:**
- **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/)
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

**Verify:**
```bash
docker --version
docker-compose --version
```

## Supabase Setup

You need a PostgreSQL database for acodeaday. We recommend Supabase (free tier available).

### Option 1: Supabase Cloud (Recommended)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Note your project URL and API keys from Settings > API
4. Note your database connection string from Settings > Database

You'll need these values for your `.env` file:
- `DATABASE_URL` (Direct connection string)
- `SUPABASE_URL` (Project URL)
- `SUPABASE_KEY` (anon/public key)

### Option 2: Local Supabase (Advanced)

For local development, you can run Supabase locally:

```bash
# Install Supabase CLI
brew install supabase/tap/supabase  # macOS
# or
npm install -g supabase  # Cross-platform

# Initialize in your project
cd acodeaday
supabase init

# Start local Supabase
supabase start
```

Local Supabase runs on:
- API: `http://localhost:54321`
- DB: `postgresql://postgres:postgres@localhost:54322/postgres`

## Optional Tools

### Git

For version control and cloning the repository.

```bash
git --version
```

Install from [git-scm.com](https://git-scm.com/) if not already installed.

### Postman or curl

For testing API endpoints during development.

### VS Code

Recommended editor with extensions:
- Python
- ESLint
- Prettier
- Docker

## System Requirements

**Minimum:**
- 4 GB RAM
- 2 CPU cores
- 5 GB free disk space

**Recommended:**
- 8 GB RAM
- 4 CPU cores
- 10 GB free disk space (for Docker images)

## Network Requirements

The following ports must be available:
- `8000` - FastAPI backend
- `5173` - Frontend dev server
- `2358` - Judge0 API
- `5432` - PostgreSQL (if using local Supabase)
- `54321` - Supabase API (if using local Supabase)

## Next Steps

Once you have all prerequisites installed, proceed to:
- [Backend Setup](/guide/backend-setup)
- [Frontend Setup](/guide/frontend-setup)
- [Judge0 Setup](/guide/judge0-setup)
