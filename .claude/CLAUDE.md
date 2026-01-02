# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

acodeaday is a daily coding practice app that uses spaced repetition to help users master the Blind 75 interview problems. Users solve one new problem per day plus review problems at optimal intervals.

**Core Philosophy**: "A code a day keeps rejection away" - focused on understanding through consistent practice, not cramming.

## Tech Stack

- **Backend**: FastAPI (Python) with async SQLAlchemy 2.0
- **Database**: Supabase PostgreSQL (managed via Alembic migrations)
- **Auth**: HTTP Basic Auth (username/password)
- **Code Execution**: Judge0 CE (self-hosted via Docker)
- **Frontend**: TanStack (React)
- **Code Editor**: Monaco Editor
- **Package Manager**: uv (for Python backend)
- **Logging**: structlog (structured logging)

## Architecture

### Spaced Repetition System

The app implements a simplified spaced repetition algorithm:

1. **First solve**: Problem enters review queue, due in 7 days
2. **Second solve**: Problem marked as "Mastered", removed from rotation
3. **"Show Again"**: User can manually re-add mastered problems to rotation

### Daily Session Logic

Each day presents up to 3 problems in priority order:
1. **Review #1**: Oldest overdue problem (if any)
2. **Review #2**: Second oldest overdue problem (if any)
3. **New Problem**: Next unsolved in Blind 75 sequence

### Database Schema

Five core tables (see TASKS.md section 2.3 for complete SQLAlchemy model definitions):

1. **problems**: Core problem metadata
   - `sequence_number` (1-75) determines order in Blind 75
   - `difficulty` (ENUM: easy/medium/hard), `pattern`, `constraints` (ARRAY), `examples` (JSONB)

2. **problem_languages**: Language-specific code
   - Stores `starter_code`, `reference_solution`, `function_signature` (JSONB)
   - Supports Python initially, extensible to other languages

3. **test_cases**: Test inputs and expected outputs
   - `input` and `expected` stored as JSONB
   - `is_hidden` flag (hidden tests only run on Submit, not Run Code)
   - `sequence` determines execution order

4. **user_progress**: Spaced repetition tracking
   - `times_solved`: Counter for mastery (0→1→2)
   - `next_review_date`: When problem is due for review
   - `is_mastered`: True after 2 successful solves
   - `show_again`: Flag to re-enter rotation

5. **submissions**: Code submission history
   - Stores code, language, pass/fail status, runtime_ms
   - Full audit trail of all attempts

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

**Daily Session**:
- `GET /api/today` - Returns 2 reviews (if due) + 1 new problem

**Submissions**:
- `POST /api/submit` - Sends code to Judge0, updates user_progress based on result

**Mastery Management**:
- `GET /api/mastered` - Lists mastered problems
- `POST /api/mastered/:id/show-again` - Re-adds to review rotation

## MVP Scope (Phase 1)

- First 15 Blind 75 problems only
- Python support only
- Fixed 7-day review interval
- Basic Monaco editor integration
- Judge0 for code execution

## Development Workflow

For detailed task breakdown, see TASKS.md which contains comprehensive phase-by-phase implementation guide including:
- Phase 1: Project Setup & Infrastructure (Supabase, Backend with uv, Frontend, Docker)
- Phase 2: Database & ORM Setup (SQLAlchemy models, Alembic migrations, Pydantic schemas)
- Phase 3: Backend Implementation (FastAPI routes, Judge0 integration, Auth)
- Phase 4: Frontend Implementation (TanStack/React, Monaco Editor)
- Phase 5: Testing & Polish
- Phase 6: Deployment Preparation

Current implementation approach:
1. **Backend Setup**: Using FastAPI with async SQLAlchemy, managed with uv
2. **Database**: Supabase PostgreSQL with Alembic migrations
3. **Auth**: HTTP Basic Auth (simple username/password)
4. **Judge0**: Self-hosted via Docker Compose
5. **Frontend**: TanStack (React) with Monaco Editor (Phase 4)

## Important Implementation Details

**Test Case Execution**: When submitting code, the backend must:
1. Generate language-specific wrapper around user code
2. Serialize test cases to JSON
3. Submit to Judge0 with test cases as stdin
4. Parse JSON results to determine pass/fail
5. Update `user_progress` table based on outcome

**Daily Session Query**: Must check `next_review_date <= today` and `is_mastered = false` to find due reviews, then fetch next unsolved by `sequence_number`.

**Mastery Logic**: On successful submission:
- If `times_solved = 0`: Set `times_solved = 1`, `next_review_date = today + 7 days`
- If `times_solved = 1`: Set `times_solved = 2`, `is_mastered = true`, `next_review_date = null`

## Key Implementation Patterns

### Async SQLAlchemy (Critical!)
See TASKS.md "Async SQLAlchemy Patterns" section for comprehensive guide. Key points:
- Use `postgresql+asyncpg://` in DATABASE_URL (NOT `postgresql://`)
- Use `create_async_engine()`, `async_sessionmaker()`, `AsyncSession`
- Use `await db.execute(select(...))` NOT `db.query(...)`
- Use `Mapped[type]` and `mapped_column()` for models (SQLAlchemy 2.0 style)
- All FastAPI route handlers MUST be `async def`

### HTTP Basic Auth
Simple username/password authentication:
- No Supabase Auth (using HTTP Basic Auth instead)
- Username becomes `user_id` in database queries
- Credentials stored in `.env` file (AUTH_USERNAME, AUTH_PASSWORD)
- See TASKS.md section 3.3 for implementation

### Code Wrapper Generation
See TASKS.md section "Judge0 Code Wrapper Generator" for complete implementation:
- User code wrapped with test harness
- Test cases serialized to JSON
- Results returned as JSON from stdout
- Supports `class Solution` pattern (LeetCode style)

### Spaced Repetition Logic
See TASKS.md section "Spaced Repetition Logic" for complete implementation:
- First solve: `times_solved=1`, `next_review_date=today+7days`
- Second solve: `times_solved=2`, `is_mastered=true`
- Already mastered: No state change on subsequent solves

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
