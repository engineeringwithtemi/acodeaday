# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

acodeaday is a daily coding practice app that uses spaced repetition to help users master the Blind 75 interview problems. Users solve one new problem per day plus review problems at optimal intervals.

**Core Philosophy**: "A code a day keeps rejection away" - focused on understanding through consistent practice, not cramming.

## Tech Stack

- **Backend**: FastAPI (Python 3.13+) with async SQLAlchemy 2.0
- **Database**: Supabase PostgreSQL (managed via Alembic migrations)
- **Auth**: Supabase Auth with JWT Bearer tokens
- **Code Execution**: Judge0 CE (self-hosted via Docker)
- **Frontend**: TanStack (React 19) with TanStack Router and React Query
- **Code Editor**: Monaco Editor
- **Package Manager**: uv (for Python backend)
- **Logging**: structlog (structured logging)
- **LLM Integration**: litellm (multi-provider: Gemini, OpenAI, Anthropic)

## Architecture

### Spaced Repetition System (Anki SM-2)

The app implements the Anki SM-2 spaced repetition algorithm:

**Rating System**: After successful submission, user rates difficulty:
- **Again**: Reset to 1-day interval, decrease ease factor by 0.2
- **Hard**: Slower growth (interval × 1.2), decrease ease by 0.15
- **Good**: Normal growth (interval × ease factor)
- **Mastered**: Immediately exit rotation

**Algorithm Constants**:
- Default ease factor: 2.5
- Minimum ease factor: 1.3
- Auto-mastery threshold: 30 days (when interval reaches 30+ days)

**First Review**: Fixed intervals (hard=1 day, good=3 days)

**"Show Again"**: User can manually re-add mastered problems to rotation (resets ease to 2.5)

### Daily Session Logic

Each day presents up to 3 problems in priority order:
1. **Review #1**: Oldest overdue problem (if any)
2. **Review #2**: Second oldest overdue problem (if any)
3. **New Problem**: Next unsolved in Blind 75 sequence

### Database Schema

Seven core tables (see `backend/app/db/tables.py` for complete SQLAlchemy model definitions):

1. **problems**: Core problem metadata
   - `sequence_number` (1-75) determines order in Blind 75
   - `difficulty` (ENUM: easy/medium/hard), `pattern` (ARRAY), `constraints` (ARRAY), `examples` (JSONB)

2. **problem_languages**: Language-specific code
   - Stores `starter_code`, `reference_solution`, `function_signature` (JSONB)
   - Supports Python and JavaScript

3. **test_cases**: Test inputs and expected outputs
   - `input` and `expected` stored as JSONB
   - `sequence` determines execution order

4. **user_progress**: Spaced repetition tracking (Anki SM-2)
   - `times_solved`, `next_review_date`, `is_mastered`, `show_again`
   - `ease_factor` (default 2.5), `interval_days`, `review_count`

5. **submissions**: Code submission history
   - Stores code, language, pass/fail status, runtime_ms, memory_kb
   - `total_test_cases`, `passed_count`, failed test details

6. **user_code**: Server-side code persistence
   - Stores user's current code per problem/language
   - Enables auto-save and code restoration

7. **chat_sessions** & **chat_messages**: AI chat assistant
   - Per-problem chat sessions with mode (socratic/direct)
   - Message history with code/test result snapshots

### Judge0 Integration

User code is wrapped with auto-generated test harness before execution:

1. User's function injected into template
2. Template reads test cases from stdin as JSON
3. Executes function against all test cases
4. Returns results as JSON with pass/fail for each case

See spec.md:247-274 for Python wrapper example.

## Problem Format

Problems stored as JSON with structure:
- Function signature metadata (name, params, return type)
- Starter code per language (Python, JavaScript planned)
- Test cases as JSON arrays
- Examples, constraints, and pattern tags

See spec.md:167-211 for complete example.

## Key Routes

- `/` - Dashboard showing today's review + new problems
- `/problem/:slug` - Split-pane: description left, Monaco editor right
- `/progress` - Blind 75 progress overview
- `/mastered` - List of mastered problems with "Show Again" option

## API Endpoints

**Problems** (prefix: `/api/problems`):
- `GET /api/problems/` - List all problems ordered by sequence
- `GET /api/problems/{slug}` - Get problem details with test cases and saved code

**Code Execution** (prefix: `/api`):
- `POST /api/run` - Execute code against first 3 test cases (no auth required)
- `POST /api/submit` - Submit code (all tests, creates submission record)
- `POST /api/rate-submission` - Rate submission difficulty (again/hard/good/mastered)

**Code Persistence** (prefix: `/api/code`):
- `POST /api/code/save` - Save user's current code (auto-save)
- `POST /api/code/reset` - Reset to starter code
- `POST /api/code/load-submission` - Load code from past submission

**Progress** (prefix: `/api`):
- `GET /api/today` - Today's session (2 reviews + 1 new problem)
- `GET /api/progress` - Overall progress on all 75 problems
- `GET /api/mastered` - List all mastered problems
- `POST /api/mastered/{problem_id}/show-again` - Re-add to review rotation

**Submissions** (prefix: `/api/submissions`):
- `GET /api/submissions/{problem_id}` - Get submission history for a problem

**Chat** (prefix: `/api/chat`):
- `GET /api/chat/models` - List available LLM models
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions/{slug}` - List sessions for a problem
- `GET /api/chat/session/{session_id}` - Get session with messages
- `POST /api/chat/session/{session_id}/message` - Send message in session

## Current Features

- First 15 Blind 75 problems seeded
- Python and JavaScript support
- Anki SM-2 spaced repetition with ratings
- Monaco editor with auto-save
- Judge0 for code execution
- AI Chat assistant (Socratic/Direct modes)
- Submission history and code persistence

## Development Workflow

For detailed task breakdown, see TASKS.md which contains comprehensive phase-by-phase implementation guide including:
- Phase 1: Project Setup & Infrastructure (Supabase, Backend with uv, Frontend, Docker)
- Phase 2: Database & ORM Setup (SQLAlchemy models, Alembic migrations, Pydantic schemas)
- Phase 3: Backend Implementation (FastAPI routes, Judge0 integration, Auth)
- Phase 4: Frontend Implementation (TanStack/React, Monaco Editor)
- Phase 5: Testing & Polish
- Phase 6: Deployment Preparation

Current implementation:
1. **Backend**: FastAPI with async SQLAlchemy, managed with uv
2. **Database**: Supabase PostgreSQL with Alembic migrations
3. **Auth**: Supabase Auth with JWT Bearer tokens
4. **Judge0**: Self-hosted via Docker Compose
5. **Frontend**: TanStack (React 19) with Monaco Editor
6. **AI Chat**: litellm for multi-provider LLM support

## Important Implementation Details

**Test Case Execution**: When submitting code, the backend must:
1. Generate language-specific wrapper around user code
2. Serialize test cases to JSON
3. Submit to Judge0 with test cases as stdin
4. Parse JSON results to determine pass/fail
5. Update `user_progress` table based on outcome

**Daily Session Query**: Must check `next_review_date <= today` and `is_mastered = false` to find due reviews, then fetch next unsolved by `sequence_number`.

**Mastery Logic** (Anki SM-2): On successful submission:
- User is prompted to rate difficulty (again/hard/good/mastered)
- Rating determines next interval using SM-2 algorithm
- Auto-mastery when interval reaches 30+ days
- See `backend/app/services/progress.py` for implementation

## Code Style Rules

### Imports
- All imports MUST be at the top of the file
- Never use inline/local imports inside functions
- Follow standard Python import ordering: stdlib, third-party, local

## Key Implementation Patterns

### Async SQLAlchemy (Critical!)
See TASKS.md "Async SQLAlchemy Patterns" section for comprehensive guide. Key points:
- Use `postgresql+asyncpg://` in DATABASE_URL (NOT `postgresql://`)
- Use `create_async_engine()`, `async_sessionmaker()`, `AsyncSession`
- Use `await db.execute(select(...))` NOT `db.query(...)`
- Use `Mapped[type]` and `mapped_column()` for models (SQLAlchemy 2.0 style)
- All FastAPI route handlers MUST be `async def`

### Supabase Auth
JWT Bearer token authentication:
- Uses Supabase Auth service for user management
- `get_current_user()` middleware validates JWT tokens
- User ID from JWT used as `user_id` in database queries
- Frontend sends token in `Authorization: Bearer <token>` header
- See `backend/app/middleware/auth.py` for implementation

### Code Wrapper Generation
See TASKS.md section "Judge0 Code Wrapper Generator" for complete implementation:
- User code wrapped with test harness
- Test cases serialized to JSON
- Results returned as JSON from stdout
- Supports `class Solution` pattern (LeetCode style)

### Spaced Repetition Logic (Anki SM-2)
See `backend/app/services/progress.py` for complete implementation:
- Rating system: again/hard/good/mastered
- First review: hard=1 day, good=3 days
- Subsequent reviews: interval grows based on rating and ease factor
- Auto-mastery at 30+ day interval
- "Show Again" resets ease factor to 2.5

## Project Documentation

- **TASKS.md**: Comprehensive phase-by-phase implementation guide with code examples
- **CONTINUITY.md**: Session state tracking (goal, constraints, decisions, progress)
- **spec.md**: Original detailed specification
- **README.md**: Setup instructions and quick start
- **DOCKER.md**: Docker commands and troubleshooting

## Continuity Ledger

Maintain session state in `CONTINUITY.md`:
- Read at start of every turn, update when state changes
- Track: Goal, Constraints, Key Decisions, State (Done/Now/Next), Open Questions
- Begin replies with "Ledger Snapshot" (Goal + Now/Next + Open Questions)
