# acodeaday - Development Tasks

## Project Structure
```
acodeaday/
├── backend/              # FastAPI backend with Judge0 integration
├── frontend/             # TanStack (React) + Monaco Editor
├── supabase/             # Auth only (supabase init)
├── docker-compose.yml    # Orchestrates all services
├── .env.example          # Environment variables template
└── README.md             # Setup instructions
```

---

## Phase 1: Project Setup & Infrastructure ✅ COMPLETE

### 1.1 Initialize Project Structure
- [x] Create directory structure (backend/, frontend/, supabase/)
- [x] Initialize git repository with .gitignore
- [x] Create .env.example with all required environment variables

### 1.2 Supabase Setup (Database Only)
- [x] Option A: Use hosted Supabase (supabase.com)
  - Create project and get DATABASE_URL, SUPABASE_URL, SUPABASE_KEY
- [x] Option B: Use local Supabase
  - Run `supabase init` to initialize
  - Run `supabase start` to start local instance
  - Get connection details from output
- [x] Note: We only use Supabase for its PostgreSQL database
- [x] Using Supabase Auth (JWT validation) instead of HTTP Basic Auth
- [x] Database schema is managed by SQLAlchemy + Alembic in backend

### 1.3 Backend Setup (FastAPI + uv)
- [x] Initialize Python project with `uv init` in backend/
- [x] Create `pyproject.toml` with dependencies (based on aide backend):
  - `fastapi[standard]>=0.125.0`
  - `sqlalchemy[asyncio]>=2.0.45` (note: [asyncio] extra required)
  - `asyncpg>=0.31.0` (PostgreSQL async driver, NOT psycopg2)
  - `alembic>=1.17.2`
  - `pydantic-settings>=2.12.0`
  - `httpx` for Judge0 REST API directly (removed SDK dependency)
  - `structlog>=25.5.0` (structured logging)
  - `httpx>=0.28.1` (async HTTP client)
  - `python-multipart>=0.0.21` (for form data)
- [x] Add dev dependencies:
  - `pytest>=9.0.2`
  - `pytest-asyncio>=1.3.0`
  - `pytest-cov>=7.0.0`
  - `python-dotenv>=1.2.1`
  - `ruff>=0.14.9` (linting)
- [x] Configure pytest for async in pyproject.toml:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["tests"]
  ```
- [x] Create backend directory structure (following aide backend pattern):
  ```
  backend/
  ├── alembic.ini                    # Alembic config
  ├── migrations/                    # Alembic migrations (not "alembic/")
  │   ├── __init__.py
  │   ├── env.py                    # Async migration configuration
  │   ├── script.py.mako
  │   └── versions/                 # Migration files
  ├── app/
  │   ├── __init__.py
  │   ├── main.py                   # FastAPI app entry point
  │   ├── config/
  │   │   ├── __init__.py
  │   │   ├── settings.py          # Pydantic settings
  │   │   └── logging.py           # Structlog configuration
  │   ├── db/
  │   │   ├── __init__.py
  │   │   ├── connection.py        # Async engine & session
  │   │   ├── tables.py            # SQLAlchemy models (all in one file)
  │   │   └── repositories.py      # Database access layer (optional)
  │   ├── schemas/                  # Pydantic schemas
  │   │   ├── __init__.py
  │   │   ├── problem.py
  │   │   ├── execution.py
  │   │   └── progress.py
  │   ├── routes/                   # API routes (not "api/")
  │   │   ├── __init__.py
  │   │   ├── problems.py
  │   │   ├── execution.py         # /run, /submit
  │   │   ├── progress.py          # /today, /progress, /mastered
  │   │   ├── submissions.py
  │   │   └── exceptions.py        # Exception handlers
  │   ├── services/
  │   │   ├── __init__.py
  │   │   ├── judge0.py            # Judge0 integration
  │   │   ├── wrapper.py           # Code wrapper generation
  │   │   └── progress.py          # Spaced repetition logic
  │   └── middleware/
  │       ├── __init__.py
  │       └── auth.py              # HTTP Basic Auth middleware
  ├── scripts/
  │   └── seed_problems.py         # Seed first 15 problems
  ├── tests/
  ├── logs/                         # Log files directory
  ├── .env
  ├── .python-version              # Python version for uv
  └── pyproject.toml
  ```
- [x] Set up uv virtual environment: `uv venv`
- [x] Install dependencies: `uv sync`
- [x] Initialize Alembic: `alembic init migrations` (creates migrations/ directory)

### 1.4 Frontend Setup (TanStack/React)
- [ ] Initialize TanStack project in frontend/
- [ ] Install dependencies:
  - React Router
  - Monaco Editor for React
  - Supabase JS client (auth only)
  - TanStack Query (for data fetching)
  - Tailwind CSS (for styling)
- [ ] Create frontend directory structure:
  ```
  frontend/
  ├── src/
  │   ├── main.tsx
  │   ├── App.tsx
  │   ├── routes/              # Route definitions
  │   ├── pages/
  │   │   ├── Dashboard.tsx    # /
  │   │   ├── ProblemView.tsx  # /problem/:slug
  │   │   ├── Progress.tsx     # /progress
  │   │   └── Mastered.tsx     # /mastered
  │   ├── components/
  │   │   ├── ProblemDescription.tsx
  │   │   ├── CodeEditor.tsx   # Monaco wrapper
  │   │   ├── TestCasePanel.tsx
  │   │   ├── TestResultPanel.tsx
  │   │   └── ProblemCard.tsx
  │   ├── lib/
  │   │   ├── supabase.ts      # Supabase client (auth)
  │   │   └── api.ts           # Backend API client
  │   ├── hooks/
  │   │   ├── useAuth.ts
  │   │   ├── useProblems.ts
  │   │   └── useCodeExecution.ts
  │   └── types/
  │       └── index.ts
  ├── public/
  └── package.json
  ```

### 1.5 Docker Setup
- [x] Create `docker-compose.yml` with services:
  - [x] Judge0 CE (judge0-server, judge0-workers, redis, postgres for judge0)
  - [x] Backend (FastAPI) - optional, can run locally with `uv run uvicorn app.main:app --reload`
  - [x] Frontend (Vite dev server) - optional, can run locally with `npm run dev`
  - [x] postgres-test (isolated test database on port 54325)
- [ ] Create backend Dockerfile (optional, for production deployment)
- [ ] Create frontend Dockerfile (optional, for production deployment)
- [x] Configure networking between services
- [x] Set up health checks for Judge0
- [x] Create start script: `docker-compose up`
- [x] **Important notes**:
  - **No PostgreSQL container**: Database comes from Supabase (hosted or local Supabase instance)
  - Using Supabase Auth (JWT validation)
  - Backend connects to Supabase PostgreSQL via DATABASE_URL in .env
  - For local dev: Backend and Frontend can run outside Docker, only Judge0 in Docker

---

## Phase 2: Database & ORM Setup ✅ COMPLETE

### 2.1 Settings Configuration (app/config/settings.py)
- [x] Create Pydantic settings class using `pydantic-settings`:
  ```python
  from pydantic import Field
  from pydantic_settings import BaseSettings, SettingsConfigDict

  class Settings(BaseSettings):
      # Database (note: postgresql+asyncpg format from Supabase)
      database_url: str = Field(
          description="PostgreSQL async connection URL from Supabase"
      )

      # HTTP Basic Auth (simple username/password)
      auth_username: str = Field("admin", description="Basic auth username")
      auth_password: str = Field("changeme", description="Basic auth password")

      # Judge0
      judge0_url: str = Field("http://localhost:2358", description="Judge0 API URL")

      # App config
      environment: str = Field("development")
      debug: bool = Field(False)
      project_name: str = Field("acodeaday")
      version: str = Field("0.1.0")
      log_level: str = Field("INFO")
      log_to_file: bool = Field(True)
      log_file_path: str = Field("logs/acodeaday.log")

      model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  settings = Settings()
  ```
- [x] Database URL format: `postgresql+asyncpg://user:password@host:port/database`
  - Example from Supabase: `postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres`
- [x] Create `.env` file with all required variables:
  ```bash
  DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54322/postgres
  AUTH_USERNAME=admin
  AUTH_PASSWORD=your-secure-password
  JUDGE0_URL=http://localhost:2358
  ENVIRONMENT=development
  DEBUG=true
  ```
- [x] Default credentials (admin/changeme) should work if .env not provided

### 2.2 Async Database Connection (app/db/connection.py)
- [x] Create async engine using `create_async_engine()`:
  ```python
  from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

  engine = create_async_engine(
      settings.database_url,
      pool_pre_ping=True,      # Verify connections before using
      pool_recycle=300,        # Recycle connections every 5 minutes
      echo=settings.debug      # Log SQL in debug mode
  )

  AsyncSessionLocal = async_sessionmaker(
      autocommit=False,
      autoflush=True,
      bind=engine,
      class_=AsyncSession
  )
  ```
- [x] Create async `get_db()` dependency:
  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with AsyncSessionLocal() as session:
          try:
              yield session
          except Exception:
              await session.rollback()
              raise
  ```
- [x] Key points:
  - Use `asyncpg` driver (already installed)
  - Use `create_async_engine()` NOT `create_engine()`
  - Use `async_sessionmaker()` NOT `sessionmaker()`
  - Use `AsyncSession` type hint

### 2.3 SQLAlchemy Models (app/db/tables.py)
- [x] Create Base class and enums:
  ```python
  import uuid
  import enum
  from datetime import datetime, date
  from sqlalchemy import ForeignKey, String, Text, func, Enum, Integer, Boolean, Date, Index
  from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
  from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

  class Base(DeclarativeBase):
      """Base class for all models"""
      pass

  class Difficulty(enum.StrEnum):
      """Problem difficulty levels"""
      EASY = "easy"
      MEDIUM = "medium"
      HARD = "hard"
  ```

- [x] Define models using SQLAlchemy 2.0 style:
  - Use `Mapped[type]` for type hints
  - Use `mapped_column()` for all columns
  - Use `UUID(as_uuid=True)` for UUID columns
  - Use `JSONB` for nested/complex JSON data
  - Use `ARRAY(Text)` for simple string arrays
  - Use `Enum()` for enum columns
  - Use `server_default=func.now()` for timestamps
  - Use `ForeignKey(..., ondelete="CASCADE")` for foreign keys

- [x] **Model 1: Problem** (core problem data)
  ```python
  class Problem(Base):
      __tablename__ = "problems"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      title: Mapped[str] = mapped_column(Text, nullable=False)
      slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
      description: Mapped[str] = mapped_column(Text, nullable=False)
      difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)  # ENUM!
      pattern: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "hash-map", "two-pointers"

      # SEQUENCE_NUMBER: Determines order in Blind 75 (1-75)
      # Used to find "next unsolved problem": SELECT * WHERE sequence_number = (min unsolved)
      sequence_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

      # Constraints as ARRAY of strings (not JSONB)
      constraints: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

      # Examples stored as JSONB (complex structure with input/output/explanation)
      examples: Mapped[dict] = mapped_column(JSONB, nullable=False)

      created_at: Mapped[datetime] = mapped_column(server_default=func.now())

      # Relationships
      languages: Mapped[list["ProblemLanguage"]] = relationship(
          back_populates="problem", cascade="all, delete", passive_deletes=True
      )
      test_cases: Mapped[list["TestCase"]] = relationship(
          back_populates="problem", cascade="all, delete", passive_deletes=True
      )
      user_progress: Mapped[list["UserProgress"]] = relationship(
          back_populates="problem", cascade="all, delete", passive_deletes=True
      )
      submissions: Mapped[list["Submission"]] = relationship(
          back_populates="problem", cascade="all, delete", passive_deletes=True
      )
  ```

- [x] **Model 2: ProblemLanguage** (language-specific code & solutions)
  ```python
  class ProblemLanguage(Base):
      __tablename__ = "problem_languages"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      problem_id: Mapped[uuid.UUID] = mapped_column(
          ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
      )
      language: Mapped[str] = mapped_column(String(50), nullable=False)  # "python", "javascript", etc.
      starter_code: Mapped[str] = mapped_column(Text, nullable=False)
      reference_solution: Mapped[str] = mapped_column(Text, nullable=False)

      # Function signature as JSONB: {"name": "twoSum", "params": [...], "return_type": "List[int]"}
      function_signature: Mapped[dict] = mapped_column(JSONB, nullable=False)

      created_at: Mapped[datetime] = mapped_column(server_default=func.now())

      # Relationship
      problem: Mapped["Problem"] = relationship(back_populates="languages")

      __table_args__ = (
          Index("ix_problem_languages_problem_id", "problem_id"),
          Index("ix_problem_languages_language", "language"),
      )
  ```

- [x] **Model 3: TestCase** (test inputs and expected outputs)
  ```python
  class TestCase(Base):
      __tablename__ = "test_cases"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      problem_id: Mapped[uuid.UUID] = mapped_column(
          ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
      )

      # Input as JSONB array: [[2,7,11,15], 9] means twoSum([2,7,11,15], 9)
      input: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Stored as JSON array

      # Expected output as JSONB: [0,1] or "hello" or {"key": "value"}
      expected: Mapped[dict] = mapped_column(JSONB, nullable=False)

      # Hidden test cases only shown on submit (not on "Run Code")
      is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

      # Sequence determines order of test case execution
      sequence: Mapped[int] = mapped_column(Integer, nullable=False)

      created_at: Mapped[datetime] = mapped_column(server_default=func.now())

      # Relationship
      problem: Mapped["Problem"] = relationship(back_populates="test_cases")

      __table_args__ = (
          Index("ix_test_cases_problem_id", "problem_id"),
      )
  ```

- [x] **Model 4: UserProgress** (tracks user's progress and spaced repetition)
  ```python
  class UserProgress(Base):
      __tablename__ = "user_progress"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

      # No auth.users table - user_id is just a string identifier (username)
      user_id: Mapped[str] = mapped_column(String(255), nullable=False)

      problem_id: Mapped[uuid.UUID] = mapped_column(
          ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
      )

      # Spaced repetition fields
      times_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
      last_solved_at: Mapped[datetime | None] = mapped_column(nullable=True)
      next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
      is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
      show_again: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

      created_at: Mapped[datetime] = mapped_column(server_default=func.now())

      # Relationship
      problem: Mapped["Problem"] = relationship(back_populates="user_progress")

      __table_args__ = (
          Index("ix_user_progress_user_id", "user_id"),
          Index("ix_user_progress_problem_id", "problem_id"),
          Index("ix_user_progress_next_review_date", "next_review_date"),
          Index("ix_user_progress_user_problem", "user_id", "problem_id", unique=True),
      )
  ```

- [x] **Model 5: Submission** (history of all code submissions)
  ```python
  class Submission(Base):
      __tablename__ = "submissions"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id: Mapped[str] = mapped_column(String(255), nullable=False)
      problem_id: Mapped[uuid.UUID] = mapped_column(
          ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
      )

      code: Mapped[str] = mapped_column(Text, nullable=False)
      language: Mapped[str] = mapped_column(String(50), nullable=False)
      passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
      runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

      submitted_at: Mapped[datetime] = mapped_column(server_default=func.now())

      # Relationship
      problem: Mapped["Problem"] = relationship(back_populates="submissions")

      __table_args__ = (
          Index("ix_submissions_user_problem", "user_id", "problem_id"),
      )
  ```

- [x] **Key Schema Decisions Explained**:
  - `difficulty`: Enum (easy/medium/hard) for type safety
  - `sequence_number`: Order in Blind 75 (1-75), used to find "next problem"
  - `constraints`: ARRAY(Text) because it's just a list of strings
  - `examples`, `function_signature`, `input`, `expected`: JSONB for complex nested data
  - `user_id`: String (username) since no auth table needed
  - All foreign keys have `ondelete="CASCADE"` for automatic cleanup
  - Indexes on all frequently-queried columns

### 2.4 Alembic Async Migrations (migrations/env.py)
- [x] Configure migrations/env.py for async (following aide backend pattern):
  ```python
  import asyncio
  from logging.config import fileConfig
  from sqlalchemy import pool
  from sqlalchemy.engine import Connection
  from sqlalchemy.ext.asyncio import async_engine_from_config
  from alembic import context
  from app.db.tables import Base
  from app.config.settings import settings

  config = context.config
  target_metadata = Base.metadata

  # Override database URL from settings
  config.set_main_option("sqlalchemy.url", settings.database_url)

  async def run_async_migrations() -> None:
      connectable = async_engine_from_config(
          config.get_section(config.config_ini_section, {}),
          prefix="sqlalchemy.",
          poolclass=pool.NullPool,
      )
      async with connectable.connect() as connection:
          await connection.run_sync(do_run_migrations)
      await connectable.dispose()

  def run_migrations_online() -> None:
      asyncio.run(run_async_migrations())
  ```
- [x] Key points:
  - Import `Base` from app/db/tables.py
  - Import `settings` to get database URL
  - Override `sqlalchemy.url` from settings
  - Use `async_engine_from_config()` for async engine
  - Use `asyncio.run()` to run async migrations
- [x] Configure alembic.ini:
  - Set `script_location = %(here)s/migrations`
  - Set `prepend_sys_path = .` (allows importing from app/)
- [x] Create initial migration: `alembic revision --autogenerate -m "initial schema"`
- [x] Review generated migration file
- [x] Run migration: `alembic upgrade head`
- [x] Verify tables created in PostgreSQL

### 2.5 Pydantic Schemas
- [x] Create Pydantic schemas in app/schemas/:
  - [x] ProblemSchema, ProblemDetailSchema
  - [x] TestCaseSchema
  - [x] RunCodeRequest, RunCodeResponse
  - [x] SubmitCodeRequest, SubmitCodeResponse
  - [x] TodaySessionResponse
  - [x] ProgressResponse
  - [x] MasteredProblemSchema
  - [x] SubmissionSchema

### 2.6 Seed Data
- [x] Create seed system: YAML files + CLI seeder (app/services/seeder.py)
- [x] Add 16 Blind 75 problems as YAML files in data/problems/:
  - [x] Problem metadata (title, slug, description, difficulty, pattern, sequence)
  - [x] Python language config (starter code, reference solution, function signature)
  - [x] Test cases (minimum 5 per problem: 3 visible, 2 hidden)
- [x] Run seeder to populate database: `uv run python -m app.services.seeder seed`
- [x] Create test users via Supabase Auth dashboard/API

---

## Phase 3: Backend Implementation ✅ COMPLETE

### 3.1 Core FastAPI Setup (following aide backend pattern)
- [x] Configure structlog for logging (app/config/logging.py):
  - [x] Set up JSON logging for production
  - [x] Set up console logging for development
  - [x] Add request_id to all logs
- [x] Create main.py with async lifespan:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # Startup
      logger.info("Application starting up")
      # No additional setup needed (no Supabase client, Judge0 is stateless)

      yield

      # Shutdown
      logger.info("Application shutting down")
      await engine.dispose()  # Close database connections

  app = FastAPI(
      title=settings.project_name,
      version=settings.version,
      lifespan=lifespan,
      description="Backend for acodeaday - daily coding practice with spaced repetition"
  )
  ```
- [x] Add CORS middleware (allow localhost:3000 and localhost:5173)
- [x] Add logging middleware with request ID and duration tracking
- [x] Register exception handlers (app/routes/exceptions.py)
- [x] Register all route modules with tags
- [x] Add health check endpoint: `GET /health`
- [x] Add root endpoint: `GET /` (returns name and version)
- [x] Key points:
  - All route handlers MUST be `async def`
  - Dispose engine on shutdown
  - Use structlog for structured logging

### 3.2 Judge0 Integration
- [x] Implement Judge0 client in services/judge0.py:
  - [x] Direct HTTP client (removed SDK dependency)
  - [x] submit_code() method
  - [x] get_submission() method
  - [x] Wait for completion with polling
- [x] Implement code wrapper generator in services/wrapper.py:
  - [x] Python wrapper template with class Solution instantiation
  - [x] Test case JSON serialization
  - [x] Result parsing from Judge0 stdout
  - [x] Error handling (timeout, runtime errors, syntax errors)
- [x] Test Judge0 connectivity and execution

### 3.3 Supabase JWT Auth (app/middleware/auth.py)
- [x] Create Supabase JWT validation dependency (upgraded from HTTP Basic):
  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBasic, HTTPBasicCredentials
  from app.config.settings import settings

  security = HTTPBasic()

  async def get_current_user(
      credentials: HTTPBasicCredentials = Depends(security)
  ) -> str:
      """
      Validate HTTP Basic Auth credentials and return username.

      Compares provided credentials against settings.auth_username and settings.auth_password.
      Returns username if valid, raises 401 if invalid.
      """
      is_valid_username = credentials.username == settings.auth_username
      is_valid_password = credentials.password == settings.auth_password

      if not (is_valid_username and is_valid_password):
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Incorrect username or password",
              headers={"WWW-Authenticate": "Basic"},
          )

      return credentials.username  # Return username as user_id
  ```
- [x] Usage in routes:
  ```python
  @router.get("/api/today")
  async def get_today(
      user_id: str = Depends(get_current_user),
      db: AsyncSession = Depends(get_db)
  ):
      # user_id is the username from Basic Auth
      # Query user_progress for this user_id
      ...
  ```
- [x] Key points:
  - Uses Supabase JWT validation (more secure than HTTP Basic)
  - User ID from Supabase token used in database queries
  - Frontend sends Bearer token in Authorization header
  - SUPABASE_URL and SUPABASE_KEY in .env file

### 3.4 API Endpoints - Problems (app/routes/problems.py)
- [x] GET /api/problems - List all problems:
  ```python
  @router.get("/")
  async def get_problems(db: AsyncSession = Depends(get_db)):
      result = await db.execute(select(Problem).order_by(Problem.sequence_number))
      problems = result.scalars().all()
      return problems
  ```
  - Key: Use `await db.execute()` with `select()`
- [x] GET /api/problems/{slug} - Get problem details:
  ```python
  @router.get("/{slug}")
  async def get_problem(slug: str, db: AsyncSession = Depends(get_db)):
      result = await db.execute(
          select(Problem)
          .options(joinedload(Problem.languages), joinedload(Problem.test_cases))
          .where(Problem.slug == slug)
      )
      problem = result.unique().scalar_one_or_none()
      if not problem:
          raise HTTPException(status_code=404, detail="Problem not found")
      return problem
  ```
  - Key: Use `joinedload()` for eager loading relationships
  - Key: Use `unique()` when using joinedload
  - Filter test_cases for is_hidden=False in response

### 3.4 API Endpoints - Code Execution
- [x] POST /api/run - Run code against visible test cases
  - [x] Fetch problem and test cases (is_hidden=false) via SQLAlchemy
  - [x] Generate wrapper code
  - [x] Submit to Judge0
  - [x] Parse results and return
- [ ] POST /api/run (with custom_input) - Run with user's custom input (deferred)
  - [ ] Execute user code with custom input
  - [ ] Execute reference solution with custom input
  - [ ] Compare outputs
  - [ ] Handle reference solution errors (invalid input)
- [x] POST /api/submit - Submit solution against all test cases
  - [x] Fetch all test cases (including hidden)
  - [x] Execute code
  - [x] If all passed, update UserProgress (spaced repetition logic)
  - [x] Create Submission record in database
  - [x] Return detailed results (which tests failed, with input/output)

### 3.5 API Endpoints - User Progress
- [x] GET /api/today - Get today's session
  - [x] Query UserProgress for due reviews (next_review_date <= today, is_mastered=false)
  - [x] Sort by next_review_date ASC, take up to 2
  - [x] Query next unsolved problem by sequence_number
  - [x] Return array of up to 3 problems
- [x] GET /api/progress - Get user's overall progress
  - [x] Query UserProgress for counts
  - [x] Total problems solved
  - [x] Problems mastered count
  - [x] Progress percentage (solved / 75)
- [x] GET /api/mastered - Get mastered problems list
  - [x] Query UserProgress where is_mastered=true
  - [x] Join with Problem table
  - [x] Return with last_solved_at date
- [x] POST /api/mastered/:id/show-again - Re-add to rotation
  - [x] Update UserProgress: show_again=true, is_mastered=false
  - [x] Set next_review_date=today
  - [x] Commit transaction

### 3.6 API Endpoints - Submissions
- [x] GET /api/submissions/:problem_id - Get submission history
  - [x] Query Submission table for user + problem
  - [x] Order by submitted_at DESC
  - [x] Return list with code, passed status, runtime

### 3.7 Spaced Repetition Logic (services/progress.py)
- [x] Implement update_user_progress function:
  - [x] Check if UserProgress record exists, create if not
  - [x] If times_solved=0: Set times_solved=1, next_review_date=today+7days
  - [x] If times_solved=1: Set times_solved=2, is_mastered=true, next_review_date=null
  - [x] If times_solved>=2: Do nothing (already mastered)
  - [x] Update last_solved_at
  - [x] Commit transaction
- [x] Test edge cases (already mastered, show_again flag)

---

## Phase 4: Frontend Implementation

### 4.1 Authentication
- [ ] Create Supabase client with auth configuration
- [ ] Implement useAuth hook (login, signup, logout, session)
- [ ] Create Login/Signup page
- [ ] Add protected route wrapper
- [ ] Store JWT token for API calls

### 4.2 API Client
- [ ] Create API client (lib/api.ts) with:
  - [ ] Axios/fetch wrapper with auth headers (JWT from Supabase)
  - [ ] Type-safe request/response interfaces
  - [ ] Error handling

### 4.3 Dashboard Page (/)
- [ ] Fetch today's session from GET /api/today
- [ ] Display review problems section (if any)
- [ ] Display new problem section
- [ ] Show overall progress bar at bottom
- [ ] Create ProblemCard component (title, difficulty, pattern, due date)
- [ ] Handle empty states (no reviews, all caught up)

### 4.4 Problem View Page (/problem/:slug)
- [ ] Split-pane layout (description left, editor right)
- [ ] Fetch problem details from GET /api/problems/:slug
- [ ] Render ProblemDescription component:
  - [ ] Title, difficulty badge, pattern tag
  - [ ] Description with examples
  - [ ] Constraints
- [ ] Integrate Monaco Editor:
  - [ ] Load starter code
  - [ ] Python syntax highlighting
  - [ ] Configure editor options (theme, font size, minimap)
- [ ] Add language dropdown (Python only for MVP)
- [ ] Add "Run Code" and "Submit" buttons in header

### 4.5 Test Case Panel
- [ ] Display visible test cases as tabs
- [ ] Allow user to add custom test cases
- [ ] Format test case inputs (pretty-print JSON)
- [ ] Show "Add Custom Input" button

### 4.6 Code Execution (Run Code)
- [ ] Create useCodeExecution hook
- [ ] Handle "Run Code" button click:
  - [ ] POST user code to /api/run
  - [ ] Show loading state
  - [ ] Display results in TestResultPanel
- [ ] Handle custom input:
  - [ ] POST user code + custom_input to /api/run
  - [ ] Show reference solution output comparison
  - [ ] Handle invalid input errors

### 4.7 Test Result Panel
- [ ] Display test case tabs with pass/fail indicators (✓/✗)
- [ ] For each test case, show:
  - [ ] Input (formatted)
  - [ ] User's output
  - [ ] Expected output
  - [ ] Stdout (if any)
  - [ ] Error message (if failed)
- [ ] Show runtime at bottom
- [ ] Highlight failed test cases in red

### 4.8 Code Submission (Submit)
- [ ] Handle "Submit" button click:
  - [ ] POST user code to /api/submit
  - [ ] Show loading state
  - [ ] Display results with all test cases (including hidden)
- [ ] Show success modal if all passed:
  - [ ] "Accepted" message
  - [ ] Runtime stats
  - [ ] Progress update (if applicable)
- [ ] Show failure results if any tests failed:
  - [ ] "X/Y tests passed"
  - [ ] Show failed test inputs/outputs

### 4.9 Progress Page (/progress)
- [ ] Fetch progress data from GET /api/progress
- [ ] Display Blind 75 list with status indicators:
  - [ ] Not started (gray)
  - [ ] In review (yellow)
  - [ ] Mastered (green)
- [ ] Show sequence numbers (1-75)
- [ ] Filter by pattern (hash-map, two-pointers, etc.)
- [ ] Show overall completion percentage

### 4.10 Mastered Page (/mastered)
- [ ] Fetch mastered problems from GET /api/mastered
- [ ] Display list with:
  - [ ] Problem title, difficulty, pattern
  - [ ] Date mastered
  - [ ] "Show Again" button
- [ ] Handle "Show Again" click:
  - [ ] POST to /api/mastered/:id/show-again
  - [ ] Show confirmation
  - [ ] Update list

---

## Phase 5: Testing & Polish

### 5.1 Backend Tests ✅ COMPLETE
- [x] Unit tests for code wrapper generation
- [x] Unit tests for spaced repetition logic
- [x] Integration tests for API endpoints with test database
- [x] Test Judge0 error scenarios (timeout, syntax errors)
- [x] Test SQLAlchemy models and relationships
- [x] 20 tests passing (execution, problems, progress, submissions)
- [x] Test database isolation (postgres-test on port 54325)

### 5.2 Frontend Tests
- [ ] Component tests for key UI components
- [ ] E2E test for full problem solve flow
- [ ] Test authentication flows

### 5.3 Error Handling
- [ ] Backend: Proper error responses with status codes
- [ ] Frontend: User-friendly error messages
- [ ] Handle Judge0 downtime gracefully
- [ ] Handle network errors
- [ ] Database transaction rollbacks on errors

### 5.4 UI Polish
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states for all async operations
- [ ] Empty states (no problems, no submissions)
- [ ] Success/error toast notifications
- [ ] Keyboard shortcuts (Cmd+Enter to run code)

### 5.5 Documentation
- [ ] README.md with setup instructions
- [ ] Environment variables documentation
- [ ] API documentation (OpenAPI/Swagger via FastAPI)
- [ ] Database schema documentation
- [ ] Alembic migration guide

---

## Phase 6: Deployment Preparation

### 6.1 Production Docker Setup
- [ ] Optimize Docker images (multi-stage builds)
- [ ] Configure production environment variables
- [ ] Set up Docker Compose production profile
- [ ] Add nginx reverse proxy (optional)

### 6.2 Security
- [ ] Add rate limiting to API endpoints
- [ ] Validate all user inputs (Pydantic schemas)
- [ ] Secure Judge0 instance (network isolation)
- [ ] Review CORS configuration
- [ ] SQL injection protection (SQLAlchemy parameterized queries)
- [ ] Secure password hashing (handled by Supabase Auth)

### 6.3 Performance
- [ ] Add caching for problem data (Redis optional)
- [ ] Optimize database queries with proper indexes
- [ ] Database connection pooling (SQLAlchemy)
- [ ] Lazy load Monaco Editor
- [ ] Code splitting in frontend

---

## MVP Checklist (Must-Have for Phase 1 Launch)

- [ ] User can sign up and log in (Supabase Auth)
- [ ] Dashboard shows today's problems (reviews + new)
- [ ] User can solve problems with Monaco editor
- [ ] "Run Code" executes against visible test cases
- [ ] "Submit" executes against all test cases and updates progress
- [ ] Spaced repetition works (7-day interval, 2x mastery)
- [ ] 15 Blind 75 problems seeded and working
- [ ] Python execution works via Judge0
- [ ] All services run via docker-compose
- [ ] Basic error handling throughout
- [ ] Database managed with SQLAlchemy + Alembic

---

## Nice-to-Have (Post-MVP)

- [ ] Submission history view per problem
- [ ] Code templates/snippets
- [ ] Dark mode toggle
- [ ] Problem bookmarking
- [ ] Notes per problem
- [ ] Discussion forum per problem
- [ ] Streak tracking (consecutive days solved)
- [ ] Email reminders for overdue reviews
- [ ] Database migrations rollback support
- [ ] Admin panel for managing problems

---

## Commands Reference

### Supabase (Auth Only)
```bash
supabase init                    # Initialize Supabase locally (auth)
supabase start                   # Start local Supabase (GoTrue for auth)
supabase stop                    # Stop Supabase services
```

### Backend (uv)
```bash
cd backend
uv init                          # Initialize project
uv add fastapi uvicorn sqlalchemy alembic psycopg2-binary  # Add dependencies
uv run uvicorn app.main:app --reload  # Run dev server
uv run pytest                    # Run tests
```

### Database (Alembic)
```bash
cd backend
alembic init alembic             # Initialize Alembic
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head             # Apply migrations
alembic downgrade -1             # Rollback one migration
alembic history                  # View migration history
alembic current                  # Show current revision
```

### Seed Data
```bash
cd backend
uv run python scripts/seed_problems.py  # Seed first 15 problems
```

### Frontend
```bash
cd frontend
npm install                      # Install dependencies
npm run dev                      # Start dev server
npm run build                    # Production build
npm run test                     # Run tests
```

### Docker
```bash
docker-compose up                # Start all services
docker-compose down              # Stop all services
docker-compose logs -f backend   # View backend logs
docker-compose build             # Rebuild images
docker-compose exec backend bash # Access backend container
docker-compose exec postgres psql -U postgres  # Access PostgreSQL
```

### PostgreSQL (inside container)
```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d acodeaday

# Useful commands
\dt                              # List tables
\d+ problems                     # Describe problems table
SELECT * FROM problems LIMIT 5;  # Query data
```

---

## Async SQLAlchemy Patterns (Critical!)

### Database Connection
- ✅ Use `postgresql+asyncpg://` in DATABASE_URL (NOT `postgresql://` or `postgresql+psycopg2://`)
- ✅ Use `asyncpg` driver (NOT `psycopg2-binary`)
- ✅ Use `sqlalchemy[asyncio]` extra in dependencies
- ✅ Use `create_async_engine()` NOT `create_engine()`
- ✅ Use `async_sessionmaker()` NOT `sessionmaker()`
- ✅ Use `AsyncSession` type hint

### Models (SQLAlchemy 2.0 Style)
- ✅ Use `Mapped[type]` for column type hints
- ✅ Use `mapped_column()` for all columns
- ✅ Use `UUID(as_uuid=True)` for UUID columns
- ✅ Use `JSONB` for JSON data (PostgreSQL specific)
- ✅ Use `server_default=func.now()` for auto-timestamps
- ✅ Use `ForeignKey(..., ondelete="CASCADE")` for cascading deletes
- ✅ Use `relationship(..., cascade="all, delete", passive_deletes=True)`

### Queries (Async)
- ✅ Use `await db.execute(select(...))` NOT `db.query(...)`
- ✅ Use `await db.commit()` NOT `db.commit()`
- ✅ Use `await db.refresh(obj)` NOT `db.refresh(obj)`
- ✅ Use `await db.delete(obj)` NOT `db.delete(obj)`
- ✅ Use `result.scalars().all()` to get list of objects
- ✅ Use `result.scalar_one_or_none()` to get single object
- ✅ Use `joinedload()` for eager loading relationships
- ✅ Use `.unique()` when using joinedload: `result.unique().scalar_one()`

### Alembic Migrations
- ✅ Import `Base.metadata` in migrations/env.py
- ✅ Override `sqlalchemy.url` from settings
- ✅ Use `async_engine_from_config()` and `asyncio.run()`
- ✅ Use `connection.run_sync(do_run_migrations)` to bridge async/sync

### FastAPI Routes
- ✅ All route handlers MUST be `async def`
- ✅ Use `Depends(get_db)` for database access
- ✅ Type hint database parameter as `AsyncSession`
- ✅ Dispose engine on app shutdown in lifespan handler

### Common Mistakes to Avoid
- ❌ Don't use `psycopg2` or `psycopg2-binary` with async
- ❌ Don't forget `[asyncio]` extra in sqlalchemy dependency
- ❌ Don't use `db.query()` (SQLAlchemy 1.x style)
- ❌ Don't forget `await` on database operations
- ❌ Don't forget `unique()` when using joinedload
- ❌ Don't use sync functions in async route handlers

---

## Implementation Guide & Examples

### Seed Data Format

Create `scripts/seed_problems.py` with structure:

```python
import asyncio
from app.db.connection import AsyncSessionLocal
from app.db.tables import Problem, ProblemLanguage, TestCase, Difficulty

async def seed_two_sum():
    async with AsyncSessionLocal() as db:
        # 1. Create Problem
        problem = Problem(
            title="Two Sum",
            slug="two-sum",
            description="""Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.""",
            difficulty=Difficulty.EASY,
            pattern="hash-map",
            sequence_number=1,  # First problem in Blind 75
            constraints=[
                "2 <= nums.length <= 10^4",
                "-10^9 <= nums[i] <= 10^9",
                "-10^9 <= target <= 10^9",
                "Only one valid answer exists."
            ],
            examples={
                "examples": [
                    {
                        "input": "nums = [2,7,11,15], target = 9",
                        "output": "[0,1]",
                        "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."
                    },
                    {
                        "input": "nums = [3,2,4], target = 6",
                        "output": "[1,2]"
                    }
                ]
            }
        )
        db.add(problem)
        await db.flush()  # Get problem.id

        # 2. Create ProblemLanguage (Python)
        problem_lang = ProblemLanguage(
            problem_id=problem.id,
            language="python",
            starter_code="""class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass""",
            reference_solution="""class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, num in enumerate(nums):
            if target - num in seen:
                return [seen[target - num], i]
            seen[num] = i
        return []""",
            function_signature={
                "name": "twoSum",
                "params": [
                    {"name": "nums", "type": "List[int]"},
                    {"name": "target", "type": "int"}
                ],
                "return_type": "List[int]"
            }
        )
        db.add(problem_lang)

        # 3. Create TestCases
        test_cases = [
            TestCase(
                problem_id=problem.id,
                input=[[2, 7, 11, 15], 9],  # List of arguments
                expected=[0, 1],
                is_hidden=False,
                sequence=1
            ),
            TestCase(
                problem_id=problem.id,
                input=[[3, 2, 4], 6],
                expected=[1, 2],
                is_hidden=False,
                sequence=2
            ),
            TestCase(
                problem_id=problem.id,
                input=[[3, 3], 6],
                expected=[0, 1],
                is_hidden=False,
                sequence=3
            ),
            TestCase(
                problem_id=problem.id,
                input=[[1, 5, 3, 7, 2, 8], 10],
                expected=[2, 4],  # or [4, 2] - order doesn't matter
                is_hidden=True,  # Hidden test case
                sequence=4
            ),
        ]
        db.add_all(test_cases)

        await db.commit()
        print(f"✓ Seeded problem: {problem.title}")

asyncio.run(seed_two_sum())
```

### Judge0 Code Wrapper Generator

Create `app/services/wrapper.py`:

```python
def generate_python_wrapper(
    user_code: str,
    test_cases: list[TestCase],
    function_name: str
) -> str:
    """
    Generate Python wrapper that:
    1. Includes user's code (class Solution)
    2. Reads test cases from stdin as JSON
    3. Executes each test case
    4. Returns results as JSON to stdout
    """
    # Serialize test cases to JSON
    test_cases_json = json.dumps([
        {"input": tc.input, "expected": tc.expected}
        for tc in test_cases
    ])

    wrapper = f'''import json
import sys
from io import StringIO
from typing import List, Optional

# ========== USER CODE START ==========
{user_code}
# ========== USER CODE END ==========

# ========== AUTO-GENERATED WRAPPER ==========
if __name__ == "__main__":
    test_cases = {test_cases_json}
    results = []

    for i, test in enumerate(test_cases):
        # Capture stdout per test
        stdout_capture = StringIO()
        sys.stdout = stdout_capture

        try:
            solution = Solution()
            result = solution.{function_name}(*test["input"])
            stdout_output = stdout_capture.getvalue()
            sys.stdout = sys.__stdout__

            results.append({{
                "test": i + 1,
                "output": result,
                "expected": test["expected"],
                "stdout": stdout_output,
                "passed": result == test["expected"],
                "error": None
            }})
        except Exception as e:
            sys.stdout = sys.__stdout__
            results.append({{
                "test": i + 1,
                "output": None,
                "expected": test["expected"],
                "stdout": stdout_capture.getvalue(),
                "passed": False,
                "error": str(e)
            }})

    print(json.dumps(results))
'''
    return wrapper
```

### Spaced Repetition Logic

Create `app/services/progress.py`:

```python
from datetime import datetime, timedelta, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.tables import UserProgress
import uuid

async def update_user_progress(
    db: AsyncSession,
    user_id: str,
    problem_id: uuid.UUID,
    passed: bool
) -> None:
    """
    Update user progress after submission.

    Logic:
    - First solve (times_solved=0): Set times_solved=1, next_review_date = today + 7 days
    - Second solve (times_solved=1): Set times_solved=2, is_mastered=True, next_review_date=None
    - Already mastered: Do nothing
    """
    if not passed:
        return  # Don't update progress if submission failed

    # Find or create UserProgress
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # First time solving this problem
        progress = UserProgress(
            user_id=user_id,
            problem_id=problem_id,
            times_solved=1,
            last_solved_at=datetime.utcnow(),
            next_review_date=date.today() + timedelta(days=7),
            is_mastered=False,
            show_again=False
        )
        db.add(progress)
    elif progress.is_mastered and not progress.show_again:
        # Already mastered, don't update
        return
    elif progress.times_solved == 0:
        # First solve
        progress.times_solved = 1
        progress.last_solved_at = datetime.utcnow()
        progress.next_review_date = date.today() + timedelta(days=7)
    elif progress.times_solved == 1:
        # Second solve - mark as mastered
        progress.times_solved = 2
        progress.last_solved_at = datetime.utcnow()
        progress.is_mastered = True
        progress.next_review_date = None
        progress.show_again = False

    await db.commit()


async def get_todays_problems(
    db: AsyncSession,
    user_id: str
) -> list[Problem]:
    """
    Get today's problems: up to 2 reviews + 1 new problem.

    Returns list of Problem objects in order:
    1. Oldest overdue review (if any)
    2. Second oldest overdue review (if any)
    3. Next unsolved problem (by sequence_number)
    """
    problems = []

    # 1. Get up to 2 overdue reviews
    result = await db.execute(
        select(Problem)
        .join(UserProgress)
        .where(UserProgress.user_id == user_id)
        .where(UserProgress.is_mastered == False)
        .where(UserProgress.next_review_date <= date.today())
        .order_by(UserProgress.next_review_date.asc())
        .limit(2)
    )
    reviews = result.scalars().all()
    problems.extend(reviews)

    # 2. Get next unsolved problem (by sequence_number)
    # Find lowest sequence_number not in user_progress
    result = await db.execute(
        select(Problem)
        .where(
            ~Problem.id.in_(
                select(UserProgress.problem_id)
                .where(UserProgress.user_id == user_id)
            )
        )
        .order_by(Problem.sequence_number.asc())
        .limit(1)
    )
    new_problem = result.scalar_one_or_none()
    if new_problem:
        problems.append(new_problem)

    return problems
```

---

## Is This Spec Sufficient?

**Yes, with the additions above.** An engineer should now have:

✅ Complete database schema with all 5 models and explanations
✅ Async SQLAlchemy patterns and examples
✅ Seed data format and structure
✅ Judge0 wrapper code generation logic
✅ Spaced repetition algorithm implementation
✅ HTTP Basic Auth implementation
✅ FastAPI route patterns with async
✅ All dependencies and configuration

**What's still needed**:
- Frontend implementation details (TanStack/React)
- Monaco Editor integration specifics
- Judge0 CE Docker Compose configuration
- Complete API endpoint implementations

**Next step**: Start with Phase 1 (Project Setup) and follow tasks sequentially.
