# Database Setup

acodeaday uses PostgreSQL for storing problems, user progress, submissions, and test cases. We recommend using Supabase, which provides a managed PostgreSQL database with additional features.

## Database Overview

The application requires five core tables:

1. **problems** - Problem metadata (title, description, difficulty, etc.)
2. **problem_languages** - Language-specific code (starter code, solutions, function signatures)
3. **test_cases** - Test inputs and expected outputs
4. **user_progress** - Spaced repetition tracking (times solved, next review date, mastery)
5. **submissions** - Submission history (code, results, runtime)

## Option 1: Supabase Cloud (Recommended)

Supabase provides a free PostgreSQL database with 500 MB storage and unlimited API requests.

### 1. Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Sign up for a free account
3. Click "New Project"

### 2. Create Project

Fill in project details:
- **Name**: acodeaday
- **Database Password**: Choose a strong password (save this!)
- **Region**: Choose closest to your location
- **Pricing Plan**: Free

Wait 2-3 minutes for project initialization.

### 3. Get Database Credentials

#### Connection String

1. Go to **Settings** > **Database**
2. Scroll to "Connection string"
3. Copy the **URI** format
4. Replace `[YOUR-PASSWORD]` with your database password

Example:
```
postgresql://postgres:your-password@db.abc123xyz.supabase.co:5432/postgres
```

Convert to async format for SQLAlchemy:
```
postgresql+asyncpg://postgres:your-password@db.abc123xyz.supabase.co:5432/postgres
```

#### API Credentials

1. Go to **Settings** > **API**
2. Copy:
   - **Project URL** (e.g., `https://abc123xyz.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

### 4. Configure Backend .env

Update `backend/.env`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=YOUR_ANON_KEY
```

### 5. Allow Your IP Address

If connecting from your local machine:

1. Go to **Settings** > **Database**
2. Scroll to "Connection Pooling"
3. Add your IP to the allowlist (or disable IP restrictions for development)

### 6. Run Migrations

```bash
cd backend
uv run alembic upgrade head
```

This creates all required tables in your Supabase database.

### 7. Verify Tables

1. In Supabase dashboard, go to **Table Editor**
2. You should see: `problems`, `problem_languages`, `test_cases`, `user_progress`, `submissions`

## Option 2: Local Supabase

For offline development or full control, run Supabase locally.

### 1. Install Supabase CLI

**macOS:**
```bash
brew install supabase/tap/supabase
```

**Windows/Linux:**
```bash
npm install -g supabase
```

### 2. Initialize Supabase

```bash
cd acodeaday
supabase init
```

This creates a `supabase/` directory with configuration.

### 3. Start Local Supabase

```bash
supabase start
```

This starts:
- PostgreSQL on `http://localhost:54322`
- Studio (web UI) on `http://localhost:54323`
- API on `http://localhost:54321`

**First run takes ~5 minutes to download Docker images.**

### 4. Get Local Credentials

After startup, the CLI displays credentials:

```
API URL: http://localhost:54321
DB URL: postgresql://postgres:postgres@localhost:54322/postgres
Studio URL: http://localhost:54323
anon key: eyJ...
service_role key: eyJ...
```

### 5. Configure Backend .env

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=eyJ...  # Use the anon key from CLI output
```

### 6. Run Migrations

```bash
cd backend
uv run alembic upgrade head
```

### 7. Access Supabase Studio

Open `http://localhost:54323` to view tables and data in the web UI.

## Option 3: Plain PostgreSQL

If you prefer plain PostgreSQL without Supabase:

### 1. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database

```bash
# Create database
psql postgres
CREATE DATABASE acodeaday;
\q
```

### 3. Configure Backend .env

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/acodeaday
```

**Note:** Without Supabase, authentication features won't work. You'll need to implement custom auth or disable auth in the backend.

### 4. Run Migrations

```bash
cd backend
uv run alembic upgrade head
```

## Database Migrations

### Run Migrations

Apply all pending migrations:

```bash
uv run alembic upgrade head
```

### Check Current Version

```bash
uv run alembic current
```

### View Migration History

```bash
uv run alembic history
```

### Rollback Migrations

```bash
# Rollback one migration
uv run alembic downgrade -1

# Rollback all migrations (WARNING: deletes all data)
uv run alembic downgrade base
```

### Create New Migration

After modifying models in `app/models.py`:

```bash
uv run alembic revision --autogenerate -m "Add new column"
```

Review the generated migration in `alembic/versions/`, then apply:

```bash
uv run alembic upgrade head
```

## Seed Data

### Seed Problems

Load initial problems from YAML files:

```bash
uv run python scripts/seed_problems.py seed
```

This loads problems from `backend/data/problems/`.

### Verify Seeded Data

**Via API:**
```bash
curl http://localhost:8000/api/problems
```

**Via Supabase Studio:**
1. Open Supabase Studio
2. Go to Table Editor > problems
3. You should see 15+ problems

**Via psql:**
```bash
psql $DATABASE_URL
SELECT title, difficulty FROM problems;
\q
```

## Database Schema

### problems
```sql
CREATE TABLE problems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
  pattern TEXT NOT NULL,
  sequence_number INTEGER UNIQUE NOT NULL,
  constraints JSONB NOT NULL,
  examples JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### problem_languages
```sql
CREATE TABLE problem_languages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
  language TEXT NOT NULL,
  starter_code TEXT NOT NULL,
  reference_solution TEXT NOT NULL,
  function_signature JSONB NOT NULL,
  UNIQUE(problem_id, language)
);
```

### test_cases
```sql
CREATE TABLE test_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
  input JSONB NOT NULL,
  expected JSONB NOT NULL,
  sequence INTEGER NOT NULL,
  UNIQUE(problem_id, sequence)
);
```

### user_progress
```sql
CREATE TABLE user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(255) NOT NULL,
  problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
  times_solved INTEGER DEFAULT 0,
  last_solved_at TIMESTAMP,
  next_review_date DATE,
  is_mastered BOOLEAN DEFAULT FALSE,
  show_again BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, problem_id)
);
```

### submissions
```sql
CREATE TABLE submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(255) NOT NULL,
  problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  language TEXT NOT NULL,
  passed BOOLEAN NOT NULL,
  runtime_ms INTEGER,
  submitted_at TIMESTAMP DEFAULT NOW()
);
```

## Backup and Restore

### Backup (Supabase Cloud)

Use `pg_dump` via Supabase connection:

```bash
pg_dump "postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres" > backup.sql
```

### Restore

```bash
psql "postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres" < backup.sql
```

### Backup (Local Supabase)

```bash
supabase db dump -f backup.sql
```

## Troubleshooting

### "Connection refused"

- Verify database is running (Supabase dashboard or `pg_isready`)
- Check `DATABASE_URL` format: `postgresql+asyncpg://` (not `postgresql://`)
- Ensure your IP is allowlisted in Supabase

### "SSL required"

Add `?sslmode=require` to connection string:
```
postgresql+asyncpg://...?sslmode=require
```

### Migration errors

```bash
# Check current migration state
uv run alembic current

# View pending migrations
uv run alembic history

# Force to specific version (use with caution)
uv run alembic stamp head
```

### "Database does not exist"

- Verify database name in connection string
- Create database if using plain PostgreSQL
- Check Supabase project status

### Slow queries

Add indexes for frequently queried columns:

```sql
CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_user_progress_next_review ON user_progress(next_review_date);
```

(These are already in migrations)

## Next Steps

- [Backend Setup](/guide/backend-setup) - Connect backend to database
- [Adding Problems](/guide/adding-problems) - Seed more problems
- [Environment Variables](/guide/environment-variables) - Configure all env vars
