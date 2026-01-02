# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

acodeaday is a daily coding practice app that uses spaced repetition to help users master the Blind 75 interview problems. Users solve one new problem per day plus review problems at optimal intervals.

**Core Philosophy**: "A code a day keeps rejection away" - focused on understanding through consistent practice, not cramming.

## Tech Stack

- **Frontend**: TanStack (React)
- **Code Editor**: VS Code Monaco Editor
- **Code Execution**: Judge0 (self-hosted)
- **Database**: Supabase (local)
- **Auth**: Supabase Auth

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

Three core tables:

**problems**: Stores Blind 75 problems with metadata
- `sequence_number` (1-75) determines order of introduction
- `starter_code` and `test_cases` stored as JSONB
- Each problem tagged with pattern (e.g., "hash-map", "two-pointers")

**user_progress**: Tracks per-user problem state
- `times_solved`: Counter for mastery logic
- `next_review_date`: Spaced repetition scheduling
- `is_mastered`: True after 2 successful solves
- `show_again`: Flag to re-enter rotation

**submissions**: Code submission history
- Stores code, language, pass/fail status, runtime

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

Since this is a new project, the initial development tasks will likely include:

1. **Project Setup**: Initialize TanStack project with Supabase client
2. **Database Setup**: Run Supabase locally and execute schema migrations
3. **Judge0 Setup**: Self-host Judge0 instance (likely via Docker)
4. **Problem Data**: Create first 15 problems in JSON format
5. **Core Components**: Build problem viewer, Monaco editor wrapper, dashboard
6. **API Layer**: Implement endpoints for daily session and submissions

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

## Continuity Ledger (compaction-safe)

Maintain a single Continuity Ledger for this workspace in `CONTINUITY.md`. The ledger is the canonical session briefing designed to survive context compaction; do not rely on earlier chat text unless it's reflected in the ledger.

### How it works

- At the start of every assistant turn: read `CONTINUITY.md`, update it to reflect the latest goal/constraints/decisions/state, then proceed with the work.
- Update `CONTINUITY.md` again whenever any of these change: goal, constraints/assumptions, key decisions, progress state (Done/Now/Next), or important tool outcomes.
- Keep it short and stable: facts only, no transcripts. Prefer bullets. Mark uncertainty as `UNCONFIRMED` (never guess).
- If you notice missing recall or a compaction/summary event: refresh/rebuild the ledger from visible context, mark gaps `UNCONFIRMED`, ask up to 1–3 targeted questions, then continue.

### `functions.update_plan` vs the Ledger

- `functions.update_plan` is for short-term execution scaffolding while you work (a small 3–7 step plan with pending/in_progress/completed).
- `CONTINUITY.md` is for long-running continuity across compaction (the "what/why/current state"), not a step-by-step task list.
- Keep them consistent: when the plan or state changes, update the ledger at the intent/progress level (not every micro-step).

### In replies

- Begin with a brief "Ledger Snapshot" (Goal + Now/Next + Open Questions). Print the full ledger only when it materially changes or when the user asks.

### `CONTINUITY.md` format (keep headings)

- Goal (incl. success criteria):
- Constraints/Assumptions:
- Key decisions:
- State:
  - Done:
  - Now:
  - Next:
- Open questions (UNCONFIRMED if needed):
- Working set (files/ids/commands):
