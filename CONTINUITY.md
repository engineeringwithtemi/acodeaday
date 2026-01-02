# Continuity Ledger - acodeaday

## Goal
Build a daily coding practice app using spaced repetition for Blind 75 interview problems. MVP: 15 problems, Python only, LeetCode-clone UI, self-hosted Judge0 execution.

Success criteria: Users can solve problems daily, get spaced repetition reviews, submit code that runs in Judge0 sandbox.

## Constraints/Assumptions
- **Backend**: FastAPI (Python) with Judge0 Python SDK
- **Frontend**: TanStack (React) with Monaco Editor
- **Auth**: Supabase Auth (email/password, JWT validation)
- **Database**: Supabase (local instance)
- **Execution**: Judge0 CE (self-hosted, Community Edition)
- **Docker**: All services containerized
- **MVP Scope**: First 15 Blind 75 problems, Python only, arrays/primitives (no linked lists/trees yet)

## Key Decisions

### 1. Authentication
- **Supabase Auth** with JWT tokens
- Frontend authenticates with Supabase (email/password, OAuth, etc.)
- Supabase returns JWT token
- Backend validates token using Supabase client
- User ID from Supabase used in database (user_progress, submissions)
- Token sent in Authorization header: "Bearer <token>"

### 2. Database
- **Supabase PostgreSQL** (hosted or local Supabase)
- Connect via DATABASE_URL: `postgresql+asyncpg://...`
- No separate PostgreSQL container
- No Supabase Docker image needed (just connection string)

### 3. Schema Decisions
- `difficulty`: Enum (easy/medium/hard) for type safety
- `sequence_number`: Order in Blind 75 (1-75), determines "next problem"
- `constraints`: ARRAY(Text) for simple string lists
- `examples`, `function_signature`, `input`, `expected`: JSONB for complex data
- `user_id`: String (username) from Basic Auth

### 4. Problem Format
- Use `class Solution` pattern (LeetCode standard)
- Test cases stored as JSONB: `{"input": [[2,7,11,15], 9], "expected": [0,1]}`
- Code wrapper instantiates Solution class and calls method
- Complex data structures (linked lists, trees) deferred to Phase 2

### 5. Code Execution
- **Run Code**: Shows example test cases only (non-hidden)
- **Submit**: Runs ALL test cases (including hidden), shows which failed with input/output
- **Custom Input**: Runs both user code and reference solution, compares output. If reference errors, user input is invalid.
- **Errors**: Surface all Judge0 errors (timeout = user code issue, import errors shown if they occur)

### 6. Judge0 Configuration
- Self-hosted Judge0 CE (Docker)
- Python 3 (standard library only for MVP - no numpy/pandas)
- Default sandbox limits
- On LeetCode, users cannot import external packages not in stdlib - same restriction here

### 7. Test Case Visibility
- **Hidden test cases**: Only hidden during "Run Code" (to prevent spoilers)
- **On Submit**: Show ALL failed test cases with full input/output, even if marked hidden
- If submission fails, record in `submissions` table but don't update `user_progress`

### 8. Mastery Logic
- After mastered (times_solved=2), subsequent solves do nothing (no state change)
- Failed submissions recorded but don't affect progress

## State

### Done
- Spec reviewed and clarified
- Tech stack decisions finalized
- Reviewed aide backend structure for async SQLAlchemy + Alembic patterns
- Updated TASKS.md with:
  - Async SQLAlchemy configuration (asyncpg, sqlalchemy[asyncio])
  - SQLAlchemy 2.0 style with Mapped[] and mapped_column()
  - Async Alembic migrations configuration
  - FastAPI app structure following aide backend pattern
  - HTTP Basic Auth (replaced Supabase Auth)
  - Structlog logging setup
  - Complete async patterns reference guide
  - All 5 database models with relationships and indexes
  - Seed data examples (Two Sum problem)
  - Judge0 wrapper code generator
  - Spaced repetition logic implementation
- Initialized Supabase (local instance ready)
- Created environment files:
  - `.env.example` (template with all variables)
  - `.env` (development defaults)
  - `.gitignore` (comprehensive exclusions for Python, Node, Docker, etc.)
- Created documentation:
  - `README.md` - Setup instructions and quick start
  - `DOCKER.md` - Docker commands, troubleshooting, and configuration
- Created `docker-compose.yml` with:
  - Judge0 CE (server, workers, redis, postgres)
  - Optional backend/frontend services (commented out)
  - Proper networking and volume management
  - Production-ready configuration
- Fixed Judge0 Docker startup issues:
  - Added health checks to PostgreSQL and Redis
  - Fixed port conflict (5433 → 5434)
  - Created SETUP_NOTES.md documenting the fix
- Verified Judge0 running successfully:
  - All containers healthy
  - API responding at http://localhost:2358
  - Python 3.8.1 (Language ID 71) available
- Initialized backend/ directory with uv:
  - Created pyproject.toml with all dependencies (FastAPI, SQLAlchemy, Alembic, asyncpg, etc.)
  - Installed dependencies with uv sync
  - Created app/ directory structure (config, db, routes, services, middleware, schemas)
- Implemented database layer:
  - app/db/connection.py - Async database connection with session factory
  - app/db/tables.py - All 5 models (Problem, ProblemLanguage, TestCase, UserProgress, Submission)
  - All models use SQLAlchemy 2.0 style (Mapped[], mapped_column())
  - Proper indexes and foreign key constraints
- Configured application settings:
  - app/config/settings.py - Pydantic settings with .env support
  - app/config/logging.py - Structlog configuration (JSON for prod, console for dev)
- Set up Alembic migrations:
  - Configured alembic.ini and migrations/env.py for async
  - Created initial migration with all 5 tables
  - Applied migration successfully to Supabase PostgreSQL
- Created FastAPI application:
  - app/main.py - FastAPI app with lifespan management, CORS, health checks
  - app/middleware/auth.py - HTTP Basic Auth (username/password)
  - Verified server starts and endpoints respond correctly

### Now
- Backend foundation complete and verified
- All database tables created in Supabase PostgreSQL
- FastAPI server running successfully with health checks
- Ready to implement API routes and business logic

### Next
- Implement API routes (problems, execution, progress, submissions)
- Create Pydantic schemas for request/response models
- Implement Judge0 wrapper generator (services/wrapper.py)
- Implement Judge0 client (services/judge0.py)
- Implement spaced repetition logic (services/progress.py)
- Create seed script for first 15 Blind 75 problems
- Test end-to-end code submission flow

## Open Questions
None (all clarified)

## Working Set
- `/spec.md` - Full specification
- `/CLAUDE.md` - Project instructions
- Need to create: Docker setup, FastAPI app, database migrations, problem seed data

## References
- [LeetCode class Solution pattern](https://discuss.python.org/t/why-does-leetcode-use-solution-class-does-the-class-ever-help/13916)
- [Judge0 CE documentation](https://ce.judge0.com/)
- [LeetCode data structure serialization](https://support.leetcode.com/hc/en-us/articles/32442719377939-How-to-create-test-cases-on-LeetCode)
