# Continuity Ledger - acodeaday

## Goal
Build a daily coding practice app using spaced repetition (Anki SM-2 algorithm) for Blind 75 interview problems. MVP: 16 problems seeded, Python support, LeetCode-clone UI, self-hosted Judge0 execution, AI chat assistant.

Success criteria: Users can solve problems daily, get spaced repetition reviews with difficulty ratings, submit code that runs in Judge0 sandbox, get AI-powered hints.

## Constraints/Assumptions
- **Backend**: FastAPI (Python 3.13+) with async SQLAlchemy 2.0
- **Frontend**: TanStack (React 19) with Monaco Editor, TanStack Router/Query
- **Auth**: Supabase Auth (JWT Bearer token validation)
- **Database**: Supabase PostgreSQL (7 tables)
- **Execution**: Judge0 CE (self-hosted, Community Edition)
- **LLM**: litellm (multi-provider: Gemini, OpenAI, Anthropic)
- **Docker**: All services containerized
- **Scope**: 16 Blind 75 problems seeded, Python and JavaScript support

## Key Decisions

### 1. Authentication
- **Supabase Auth** with JWT Bearer tokens
- **Default user** created on backend startup from env vars
- Frontend authenticates directly with Supabase JS client (email/password)
- Backend validates token using `supabase.auth.get_user(token)`
- User ID from Supabase used in database (user_progress, submissions)
- Token sent in Authorization header: "Bearer <token>"

### 2. Database
- **Supabase PostgreSQL** (hosted or local Supabase)
- Connect via DATABASE_URL: `postgresql+asyncpg://...`
- 7 tables: problems, problem_languages, test_cases, user_progress, submissions, user_code, chat_sessions/messages

### 3. Schema Decisions
- `difficulty`: Enum (easy/medium/hard) for type safety
- `sequence_number`: Order in Blind 75 (1-75), determines "next problem"
- `constraints`: ARRAY(Text) for simple string lists
- `examples`, `function_signature`, `input`, `expected`: JSONB for complex data
- `user_id`: String from Supabase JWT

### 4. Problem Format
- Use `class Solution` pattern (LeetCode standard)
- Test cases stored as JSONB: `{"input": [[2,7,11,15], 9], "expected": [0,1]}`
- Code wrapper instantiates Solution class and calls method

### 5. Code Execution
- **Run Code**: Shows first 3 test cases only
- **Submit**: Runs ALL test cases (early exit on first failure)
- **Custom Input**: Runs reference solution first to get expected output
- **Errors**: Surface all Judge0 errors (timeout, syntax, runtime)

### 6. Spaced Repetition (Anki SM-2)
- **Ratings**: again, hard, good, mastered
- **Ease factor**: Default 2.5, min 1.3
- **First review**: hard=1 day, good=3 days
- **Subsequent**: interval × ease factor (grows based on rating)
- **Auto-mastery**: When interval reaches 30+ days

### 7. AI Chat Assistant
- Per-problem chat sessions (Socratic or Direct mode)
- Multi-model support via litellm
- Code and test result snapshots in messages

## State

### Done

#### Phase 1: Infrastructure ✅
- Tech stack decisions finalized
- Supabase (local instance ready)
- Docker Compose with Judge0 CE

#### Phase 2: Database & ORM ✅
- All 7 SQLAlchemy models
- Alembic async migrations
- Pydantic schemas

#### Phase 3: Backend Implementation ✅
- All API routes implemented:
  - Problems: GET /api/problems/, GET /api/problems/{slug}
  - Execution: POST /api/run, POST /api/submit, POST /api/rate-submission
  - Code: POST /api/code/save, POST /api/code/reset, POST /api/code/load-submission
  - Progress: GET /api/today, GET /api/progress, GET /api/mastered
  - Submissions: GET /api/submissions/{problem_id}
  - Chat: Full AI chat session/message endpoints
- Anki SM-2 spaced repetition in services/progress.py
- Judge0 integration with Python wrapper
- 16 Blind 75 problems seeded

#### Phase 4: Frontend Implementation ✅
- TanStack (React 19) with file-based routing
- Monaco Editor with auto-save
- Split-pane layout with resizable panels
- All routes: /, /login, /problem/:slug, /progress, /mastered
- Supabase Auth integration
- AI Chat panel
- Rating modal for spaced repetition

#### Phase 5.1: Backend Tests ✅
- 20 tests passing
- Test database isolation

### Now
- **MVP COMPLETE** - all phases implemented
- Documentation audit and consistency fixes

### Next
- Phase 5.2-5.5: Frontend tests, error handling polish
- Phase 6: Deployment preparation
- More problems (expand beyond 16)
- JavaScript execution support

## Open Questions
None (all clarified)

## Working Set
- `backend/app/` - FastAPI application
- `frontend/src/` - TanStack React application
- `data/problems/` - YAML problem definitions

## References
- [Anki SM-2 Algorithm](https://docs.ankiweb.net/deck-options.html#new-cards)
- [Judge0 CE documentation](https://ce.judge0.com/)
- [LeetCode class Solution pattern](https://discuss.python.org/t/why-does-leetcode-use-solution-class-does-the-class-ever-help/13916)
