# Continuity Ledger - acodeaday

## Goal
Build a daily coding practice app using spaced repetition for Blind 75 interview problems. MVP: 15 problems, Python only, LeetCode-clone UI, self-hosted Judge0 execution.

Success criteria: Users can solve problems daily, get spaced repetition reviews, submit code that runs in Judge0 sandbox.

## Constraints/Assumptions
- **Backend**: FastAPI (Python) with Judge0 Python SDK
- **Frontend**: TanStack (React) with Monaco Editor
- **Auth**: Supabase Auth (JWT validation, default user created on startup)
- **Database**: Supabase (local instance)
- **Execution**: Judge0 CE (self-hosted, Community Edition)
- **Docker**: All services containerized
- **MVP Scope**: First 15 Blind 75 problems, Python only, arrays/primitives (no linked lists/trees yet)

## Key Decisions

### 1. Authentication
- **Supabase Auth** with JWT tokens
- **No signup route** - default user created on backend startup from env vars
- Frontend authenticates directly with Supabase JS client (email/password)
- Supabase returns JWT token
- Backend validates token using Supabase client on protected routes
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

#### Phase 1: Infrastructure ✅
- Spec reviewed and clarified
- Tech stack decisions finalized
- Reviewed aide backend structure for async SQLAlchemy + Alembic patterns
- Initialized Supabase (local instance ready)
- Created environment files (.env.example, .env, .gitignore)
- Created documentation (README.md, DOCKER.md)
- Created docker-compose.yml with Judge0 CE (server, workers, redis, postgres)
- Fixed Judge0 Docker startup issues (health checks, port conflicts)
- Verified Judge0 running at http://localhost:2358

#### Phase 2: Database & ORM ✅
- Initialized backend/ with uv and all dependencies
- Implemented database layer:
  - app/db/connection.py - Async database connection
  - app/db/tables.py - All 5 models (Problem, ProblemLanguage, TestCase, UserProgress, Submission)
  - SQLAlchemy 2.0 style (Mapped[], mapped_column())
- Configured settings (pydantic-settings) and logging (structlog)
- Set up Alembic async migrations
- Created Pydantic schemas (problem.py, execution.py, progress.py)

#### Phase 3: Backend Implementation ✅
- Created FastAPI app with lifespan, CORS, health checks
- Implemented auth middleware (Supabase JWT validation)
- Implemented all API routes:
  - GET /api/problems - List all problems
  - GET /api/problems/{slug} - Get problem details
  - POST /api/run - Run code against visible test cases
  - POST /api/submit - Submit against all test cases + update progress
  - GET /api/today - Get today's session (2 reviews + 1 new)
  - GET /api/progress - Get overall progress stats
  - GET /api/mastered - Get mastered problems list
  - POST /api/mastered/{id}/show-again - Re-add to rotation
  - GET /api/submissions/{problem_id} - Get submission history
- Implemented services:
  - services/judge0.py - Judge0 integration (direct HTTP, no SDK)
  - services/wrapper.py - Python code wrapper generator
  - services/progress.py - Spaced repetition logic
  - services/seeder.py - CLI seeder from YAML files
- Created seed data:
  - 16 Blind 75 problems as YAML files in data/problems/
  - CLI tool: `uv run python -m app.services.seeder seed`

#### Phase 5.1: Backend Tests ✅
- 15 tests passing (problems, progress, submissions)
- Fixed test database isolation:
  - Added postgres-test container on port 54325
  - Tests use TRUNCATE instead of DROP (preserves schema)
  - Dev database data persists after running tests

#### Auth Simplification ✅
- No auth routes in backend (frontend uses Supabase JS client directly)
- Added `ensure_default_user_exists()` in main.py lifespan
- Default user created from `DEFAULT_USER_EMAIL` and `DEFAULT_USER_PASSWORD` env vars
- Backend only validates JWT tokens on protected routes

### Now
- **Backend is COMPLETE** - all Phase 2 & 3 requirements implemented
- Ready to begin Phase 4: Frontend Implementation

### Next
- Phase 4: Frontend Implementation (TanStack/React + Monaco Editor)
  - Initialize TanStack project
  - Create API client with Supabase auth
  - Build Dashboard page (/)
  - Build Problem View page (/problem/:slug) with Monaco Editor
  - Build Progress page (/progress)
  - Build Mastered page (/mastered)
- Phase 5.2-5.5: Frontend tests, error handling, documentation
- Phase 6: Deployment preparation
- (Deferred) GitHub Actions CI workflow

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
