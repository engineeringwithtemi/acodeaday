# acodeaday

> A daily coding practice app with spaced repetition to help you master the Blind 75.

**Open source.** Self-host it, fork it, make it yours.

---

## Overview

acodeaday helps you prepare for technical interviews by serving one new problem per day from the Blind 75 list, plus review problems using spaced repetition. The goal is understanding, not cramming.

---

## Design Principles

This project is built with senior engineer quality standards:

1. **Extensibility** — Architecture decisions support future growth (new languages, problem sets)
2. **Separation of concerns** — Clear boundaries between UI, API, and execution layers
3. **Normalized data** — Proper database design, no redundant data
4. **Simple first** — No overengineering, but no shortcuts that create tech debt
5. **Clone what works** — UI/UX mirrors LeetCode exactly; no need to reinvent

---

## Core Concept

```
"An apple a day keeps the doctor away"
"A code a day keeps rejection away"
```

Users solve one new problem daily. Problems they've solved before resurface at optimal intervals to ensure long-term retention.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.13+) with async SQLAlchemy 2.0 |
| Frontend | TanStack (React 19) with TanStack Router/Query |
| Code Editor | Monaco Editor |
| Code Execution | Judge0 CE (self-hosted) |
| Database | Supabase PostgreSQL (7 tables) |
| Auth | Supabase Auth (JWT Bearer tokens) |
| AI Chat | litellm (Gemini, OpenAI, Anthropic) |
| Infrastructure | Docker (Judge0), local dev for backend/frontend |
| Language Support | Python (JavaScript structure in place) |

---

## User Flow

### Daily Session

```
┌─────────────────────────────────────────┐
│            User opens app               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     Check for problems due review       │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   Has reviews         No reviews
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ Show up to 2  │   │ Show 1 new    │
│ review problems│   │ problem       │
│ + 1 new problem│   │               │
└───────────────┘   └───────────────┘
```

### Daily Problem Queue

| Priority | Type | Description |
|----------|------|-------------|
| 1 | Review | Oldest due problem |
| 2 | Review | Second oldest due problem |
| 3 | New | Next unsolved in Blind 75 sequence |

---

## Spaced Repetition Logic (Anki SM-2)

The app uses the Anki SM-2 spaced repetition algorithm for optimal long-term retention.

### Rating System

After each successful submission, the user rates difficulty:

| Rating | Effect |
|--------|--------|
| **Again** | Reset to 1-day interval, decrease ease factor by 0.2 |
| **Hard** | Interval grows slowly (×1.2), decrease ease by 0.15 |
| **Good** | Normal growth (interval × ease factor) |
| **Mastered** | Immediately exit rotation |

### Algorithm Constants

- **Default ease factor**: 2.5
- **Minimum ease factor**: 1.3
- **Auto-mastery threshold**: 30 days (when interval reaches 30+ days)

### First Review Intervals

| Rating | Interval |
|--------|----------|
| Hard | 1 day |
| Good | 3 days |

### State Diagram

```
                    ┌─────────────┐
                    │   Unsolved  │
                    └──────┬──────┘
                           │
                      Solve + Rate
                           │
                           ▼
                    ┌─────────────┐
                    │  In Review  │◄─────────────┐
                    │(interval grows│              │
                    │ based on SM-2)│              │
                    └──────┬──────┘              │
                           │                    │
                   Interval ≥ 30d          "Show Again"
                    or rate "mastered"     (resets ease)
                           │                    │
                           ▼                    │
                    ┌─────────────┐             │
                    │  Mastered   │─────────────┘
                    └─────────────┘
```

---

## Data Models

### Problems

```sql
CREATE TABLE problems (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  slug            TEXT UNIQUE NOT NULL,
  description     TEXT NOT NULL,
  difficulty      TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
  pattern         TEXT NOT NULL,
  sequence_number INTEGER UNIQUE NOT NULL,  -- 1-75 (order in Blind 75)
  constraints     JSONB NOT NULL,           -- array of constraint strings
  examples        JSONB NOT NULL,           -- array of {input, output, explanation?}
  created_at      TIMESTAMP DEFAULT NOW()
);
```

### Problem Languages (Normalized for Extensibility)

```sql
CREATE TABLE problem_languages (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  problem_id          UUID REFERENCES problems(id) ON DELETE CASCADE,
  language            TEXT NOT NULL,  -- 'python', 'javascript', 'go', etc.
  starter_code        TEXT NOT NULL,
  reference_solution  TEXT NOT NULL,
  function_signature  JSONB NOT NULL, -- {name, params: [{name, type}], return_type}
  
  UNIQUE(problem_id, language)
);

-- Index for fast lookups
CREATE INDEX idx_problem_languages_problem_id ON problem_languages(problem_id);
CREATE INDEX idx_problem_languages_language ON problem_languages(language);
```

### Test Cases

```sql
CREATE TABLE test_cases (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  problem_id  UUID REFERENCES problems(id) ON DELETE CASCADE,
  input       JSONB NOT NULL,     -- array of arguments
  expected    JSONB NOT NULL,     -- expected output
  is_hidden   BOOLEAN DEFAULT FALSE,  -- hidden tests for submit only
  sequence    INTEGER NOT NULL,   -- ordering
  
  UNIQUE(problem_id, sequence)
);

CREATE INDEX idx_test_cases_problem_id ON test_cases(problem_id);
```

### User Progress

```sql
CREATE TABLE user_progress (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          VARCHAR(255) NOT NULL,  -- Supabase Auth user ID (string)
  problem_id       UUID REFERENCES problems(id) ON DELETE CASCADE,
  times_solved     INTEGER DEFAULT 0,
  last_solved_at   TIMESTAMP,
  next_review_date DATE,
  is_mastered      BOOLEAN DEFAULT FALSE,
  show_again       BOOLEAN DEFAULT FALSE,
  -- Anki SM-2 fields
  ease_factor      FLOAT DEFAULT 2.5,      -- Current ease factor
  interval_days    INTEGER DEFAULT 0,       -- Current interval in days
  review_count     INTEGER DEFAULT 0,       -- Number of reviews completed
  created_at       TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, problem_id)
);

CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_user_progress_next_review ON user_progress(next_review_date);
```

### User Code (Server-side persistence)

```sql
CREATE TABLE user_code (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      VARCHAR(255) NOT NULL,
  problem_id   UUID REFERENCES problems(id) ON DELETE CASCADE,
  language     TEXT DEFAULT 'python',
  code         TEXT NOT NULL,
  updated_at   TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, problem_id, language)
);
```

### Chat Sessions & Messages (AI Assistant)

```sql
CREATE TABLE chat_sessions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      VARCHAR(255) NOT NULL,
  problem_id   UUID REFERENCES problems(id) ON DELETE CASCADE,
  title        VARCHAR(50),
  mode         TEXT NOT NULL,  -- 'socratic' or 'direct'
  model        VARCHAR(100),
  is_active    BOOLEAN DEFAULT TRUE,
  created_at   TIMESTAMP DEFAULT NOW(),
  updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_messages (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id            UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role                  TEXT NOT NULL,  -- 'user', 'assistant', 'system'
  content               TEXT NOT NULL,
  code_snapshot         TEXT,
  test_results_snapshot JSONB,
  created_at            TIMESTAMP DEFAULT NOW()
);
```

### Submissions

```sql
CREATE TABLE submissions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      VARCHAR(255) NOT NULL,  -- Supabase Auth user ID (string)
  problem_id   UUID REFERENCES problems(id) ON DELETE CASCADE,
  code         TEXT NOT NULL,
  language     TEXT NOT NULL,
  passed       BOOLEAN NOT NULL,
  runtime_ms   INTEGER,
  submitted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_submissions_user_problem ON submissions(user_id, problem_id);
```

---

## Problem Format

Problems are stored across normalized tables. Here's an example of how Two Sum would be represented:

### problems table
```json
{
  "id": "uuid-here",
  "title": "Two Sum",
  "slug": "two-sum",
  "difficulty": "easy",
  "pattern": "hash-map",
  "sequence_number": 1,
  "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.\n\nYou can return the answer in any order.",
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
  ],
  "constraints": [
    "2 <= nums.length <= 10^4",
    "-10^9 <= nums[i] <= 10^9",
    "-10^9 <= target <= 10^9",
    "Only one valid answer exists."
  ]
}
```

### problem_languages table
```json
{
  "id": "uuid-here",
  "problem_id": "uuid-from-above",
  "language": "python",
  "starter_code": "def twoSum(nums: List[int], target: int) -> List[int]:\n    pass",
  "reference_solution": "def twoSum(nums: List[int], target: int) -> List[int]:\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i",
  "function_signature": {
    "name": "twoSum",
    "params": [
      {"name": "nums", "type": "List[int]"},
      {"name": "target", "type": "int"}
    ],
    "return_type": "List[int]"
  }
}
```

### test_cases table
```json
[
  {"problem_id": "uuid", "input": [[2,7,11,15], 9], "expected": [0,1], "is_hidden": false, "sequence": 1},
  {"problem_id": "uuid", "input": [[3,2,4], 6], "expected": [1,2], "is_hidden": false, "sequence": 2},
  {"problem_id": "uuid", "input": [[3,3], 6], "expected": [0,1], "is_hidden": false, "sequence": 3},
  {"problem_id": "uuid", "input": [[1,5,3,7,2,8], 10], "expected": [2,4], "is_hidden": true, "sequence": 4},
  {"problem_id": "uuid", "input": [[0,4,3,0], 0], "expected": [0,3], "is_hidden": true, "sequence": 5}
]
```

---

## Important Data Flow Notes

### Test Case Visibility

**Critical distinction**: The frontend does NOT have access to all test cases.

```
| Source                          | Test Cases Returned         |
|---------------------------------|-----------------------------|
| GET /api/problems/:slug         | First 3 visible tests ONLY  |
| POST /api/run                   | First 3 visible tests ONLY  |
| POST /api/submit                | ALL tests (visible + hidden)|
```

For Two Sum:
- **YAML file**: 5 test cases (3 visible + 2 hidden)
- **Frontend `problem.test_cases`**: 3 (visible only)
- **Submit execution**: 5 (all test cases)

**Why this matters**:
- Frontend cannot use `problem.test_cases.length` as total test count
- Backend must return `total_test_cases` in `SubmitCodeResponse`

### Run Code vs Submit Separation

| Feature | Run Code | Submit |
|---------|----------|--------|
| Endpoint | `POST /api/run` | `POST /api/submit` |
| Auth required | No | Yes |
| Test cases | First 3 visible | ALL (incl. hidden) |
| Early exit | No (runs all) | Yes (stops at failure) |
| Saves submission | No | Yes |
| Updates progress | No | Yes (if passed) |
| UI display | Test Result Panel (inline) | Submission Result Modal |
| Custom input | Supported | Not supported |

**IMPORTANT**: These are INDEPENDENT operations. Submit results should NEVER appear in the Test Result Panel.

---

## Code Execution

### Architecture

Judge0 runs in Docker. Backend (FastAPI) can run locally or in Docker. User never interacts with Judge0 directly — all code execution goes through our API.

```
┌──────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Client  │──────▶│  FastAPI        │──────▶│ Judge0 (Docker) │
│ (React)  │       │  Backend        │       │                 │
└──────────┘       └─────────────────┘       └─────────────────┘
                           │
                           ▼
                   ┌─────────────────┐
                   │ Supabase        │
                   │ PostgreSQL      │
                   └─────────────────┘
```

### Execution Modes

| Action | Test Cases Used | Reference Solution Used |
|--------|-----------------|-------------------------|
| Run Code | Example test cases from DB | No |
| Run Code (custom input) | User's custom input | Yes — to generate expected output |
| Submit | ALL test cases from DB (including hidden) | No |

### API Request/Response Examples

**Run Code**
```typescript
POST /api/run
{
  "problem_slug": "two-sum",  // uses slug, not id
  "language": "python",
  "code": "class Solution:\n    def twoSum(self, nums, target): ..."
}

// Response
{
  "success": true,
  "results": [
    {
      "test_number": 1,
      "passed": true,
      "output": [0, 1],
      "expected": [0, 1],
      "error": null,
      "is_hidden": false
    }
  ],
  "summary": {
    "total": 3,
    "passed": 3,
    "failed": 0
  }
}
```

**Submit Solution**
```typescript
POST /api/submit
{
  "problem_slug": "two-sum",
  "language": "python",
  "code": "class Solution:\n    def twoSum(self, nums, target): ..."
}
// Requires Authorization: Bearer <token>

// Runs against ALL test cases (including hidden) with early_exit=True
// (stops at first failure to save resources)

// Response (all tests pass)
{
  "success": true,
  "results": [
    {
      "test_number": 1,
      "passed": true,
      "input": [[2, 7, 11, 15], 9],
      "output": [0, 1],
      "expected": [0, 1],
      "stdout": null,
      "error": null,
      "is_hidden": false
    },
    // ... more test results
  ],
  "summary": {
    "total": 5,       // tests actually executed
    "passed": 5,
    "failed": 0
  },
  "total_test_cases": 5,  // REQUIRED: total tests in problem (for "X/Y passed" display)
  "submission_id": "uuid",
  "runtime_ms": 45,
  "memory_kb": 14320,
  "compile_error": null,
  "runtime_error": null,
  "times_solved": 1,      // only on success
  "is_mastered": false,   // only on success
  "next_review_date": "2024-01-15"  // only on success
}

// Response (first test fails - early exit)
{
  "success": false,
  "results": [
    {
      "test_number": 1,
      "passed": false,
      "input": [[2, 7, 11, 15], 9],
      "output": [1, 0],      // wrong answer
      "expected": [0, 1],
      "stdout": "Debug: checking...",
      "error": null,
      "is_hidden": false
    }
  ],
  "summary": {
    "total": 1,       // only 1 test executed (early exit)
    "passed": 0,
    "failed": 1
  },
  "total_test_cases": 5,  // REQUIRED: still shows total (for "0/5 passed")
  "submission_id": "uuid",
  "runtime_ms": 12,
  "memory_kb": 14100,
  "compile_error": null,
  "runtime_error": null,
  "times_solved": null,
  "is_mastered": null,
  "next_review_date": null
}

// Response (third test fails - early exit)
{
  "success": false,
  "results": [
    { "test_number": 1, "passed": true, ... },
    { "test_number": 2, "passed": true, ... },
    { "test_number": 3, "passed": false, "input": [...], "output": [...], "expected": [...], ... }
  ],
  "summary": {
    "total": 3,       // 3 tests executed before early exit
    "passed": 2,
    "failed": 1
  },
  "total_test_cases": 5,  // for "2/5 passed" display
  ...
}
```

### Server-Side Flow

```python
# /api/run endpoint

def run_code(problem_id, language, user_code, custom_input=None):
    problem = db.get_problem(problem_id)
    language_config = db.get_problem_language(problem_id, language)
    
    if custom_input:
        # Custom input: run both user code and reference solution
        user_output = execute_in_judge0(user_code, custom_input)
        expected_output = execute_in_judge0(
            language_config.reference_solution, 
            custom_input
        )
        return compare(user_output, expected_output)
    else:
        # Standard run: use stored test cases with known expected outputs
        test_cases = db.get_test_cases(problem_id, hidden=False)
        return execute_and_compare(user_code, test_cases)


# /api/submit endpoint

def submit_solution(problem_id, language, user_code):
    # Get ALL test cases including hidden
    test_cases = db.get_test_cases(problem_id, hidden=None)  # all
    
    results = execute_and_compare(user_code, test_cases)
    
    if all_passed(results):
        update_user_progress(user_id, problem_id)
    
    return results
```

### Code Wrapper (Python)

User code is wrapped before sending to Judge0:

```python
import json
import sys
from io import StringIO

# ========== USER CODE START ==========
def twoSum(nums, target):
    print("Debug: starting")  # user stdout captured
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
# ========== USER CODE END ==========

# ========== AUTO-GENERATED WRAPPER ==========
if __name__ == "__main__":
    test_cases = json.loads(sys.stdin.read())
    results = []
    
    for i, test in enumerate(test_cases):
        # Capture stdout per test
        stdout_capture = StringIO()
        sys.stdout = stdout_capture
        
        try:
            result = twoSum(*test["input"])
            stdout_output = stdout_capture.getvalue()
            sys.stdout = sys.__stdout__
            
            results.append({
                "test": i + 1,
                "output": result,
                "stdout": stdout_output,
                "error": None
            })
        except Exception as e:
            sys.stdout = sys.__stdout__
            results.append({
                "test": i + 1,
                "output": None,
                "stdout": stdout_capture.getvalue(),
                "error": str(e)
            })
    
    print(json.dumps(results))
```

---

## UI Components

### Design Principle

The problem-solving UI is a **LeetCode clone**. No reinventing — same layout, same interactions.

### Pages

| Page | Description |
|------|-------------|
| `/` | Dashboard — today's problems |
| `/problem/:slug` | Problem view with editor (LeetCode layout) |
| `/progress` | Blind 75 progress overview |
| `/mastered` | List of mastered problems |

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  acodeaday                                    [User Avatar] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Good morning! Here's your practice for today.              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📝 REVIEW                                            │   │
│  │                                                      │   │
│  │ ┌──────────────────────────────────────────────┐    │   │
│  │ │ Two Sum                              Easy    │    │   │
│  │ │ Hash Map • Due 3 days ago                    │    │   │
│  │ │                                     [Solve]  │    │   │
│  │ └──────────────────────────────────────────────┘    │   │
│  │                                                      │   │
│  │ ┌──────────────────────────────────────────────┐    │   │
│  │ │ Valid Palindrome                     Easy    │    │   │
│  │ │ Two Pointers • Due today                     │    │   │
│  │ │                                     [Solve]  │    │   │
│  │ └──────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🆕 NEW PROBLEM                                       │   │
│  │                                                      │   │
│  │ ┌──────────────────────────────────────────────┐    │   │
│  │ │ Contains Duplicate                   Easy    │    │   │
│  │ │ Arrays • Problem 3 of 75                     │    │   │
│  │ │                                     [Solve]  │    │   │
│  │ └──────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Progress: 5/75 ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 6.7%    │
│  Mastered: 2 problems                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Problem View Layout (LeetCode Clone)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  acodeaday                                    [▶ Run Code]  [Submit]        │
├────────────────────────────────┬────────────────────────────────────────────┤
│                                │  Python ▼                                  │
│  14. Two Sum              Easy │  ┌────────────────────────────────────────┐│
│                                │  │ def twoSum(nums, target):              ││
│  Given an array of integers    │  │     pass                               ││
│  nums and an integer target,   │  │                                        ││
│  return indices of the two     │  │                                        ││
│  numbers such that they add    │  │                                        ││
│  up to target.                 │  │                                        ││
│                                │  │                                        ││
│  Example 1:                    │  │                                        ││
│  ┌────────────────────────┐   │  │                                        ││
│  │ Input: nums = [2,7,11, │   │  └────────────────────────────────────────┘│
│  │ 15], target = 9        │   ├────────────────────────────────────────────┤
│  │ Output: [0,1]          │   │  [Testcase]  [Test Result]                 │
│  └────────────────────────┘   │  ┌────────────────────────────────────────┐│
│                                │  │ Case 1 │ Case 2 │ Case 3 │ + Add      ││
│  Constraints:                  │  ├────────────────────────────────────────┤│
│  • 2 <= nums.length <= 10^4    │  │ Input                                  ││
│  • Only one valid answer       │  │ nums =                                 ││
│    exists.                     │  │ [2,7,11,15]                            ││
│                                │  │ target =                               ││
│  Pattern: Hash Map             │  │ 9                                      ││
│                                │  └────────────────────────────────────────┘│
└────────────────────────────────┴────────────────────────────────────────────┘
```

### Test Result Panel (After Running Code)

**IMPORTANT**: This panel is ONLY for "Run Code" results. Submit results appear in the Submission Result Modal (see below).

```
┌────────────────────────────────────────────────────────────┐
│  [Testcase]  [>_ Test Result]                              │
├────────────────────────────────────────────────────────────┤
│  ✓ Case 1    ✓ Case 2    ✗ Case 3                         │
├────────────────────────────────────────────────────────────┤
│  Input                                                     │
│  nums =                                                    │
│  [3,3]                                                     │
│  target =                                                  │
│  6                                                         │
├────────────────────────────────────────────────────────────┤
│  Stdout                                                    │
│  Debug: checking index 0                                   │
│  Debug: found match                                        │
├────────────────────────────────────────────────────────────┤
│  Output                                                    │
│  [1,0]                                                     │
├────────────────────────────────────────────────────────────┤
│  Expected                                                  │
│  [0,1]                                                     │
└────────────────────────────────────────────────────────────┘
```

### Submission Result Modal (After Submitting Code)

**IMPORTANT**: This is a MODAL that appears after clicking "Submit". It is SEPARATE from the Test Result Panel.

The modal shows:
1. **Status Banner**: "Accepted" (green) or "Wrong Answer" / "Compile Error" / "Runtime Error" (red)
2. **Test Count**: "X / Y testcases passed" where Y is `total_test_cases` from backend response
3. **Failed Test Details** (if wrong answer and test is not hidden):
   - "Failed on Test Case X"
   - Input (formatted with param names from function signature)
   - Output (user's wrong output)
   - Expected (correct output)
4. **Runtime & Memory**: From submission response
5. **Code**: The submitted code
6. **Progress Info**: Times solved, mastered status, next review date

```
┌───────────────────────────────────────────────────────────────┐
│  Submission Result                                      [X]   │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  ✗ Wrong Answer                      2 / 5 testcases   │  │
│  │                                          passed         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  Failed on Test Case 3                                        │
│                                                               │
│  Input                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ nums = [3, 3]                                           │  │
│  │ target = 6                                              │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  Output                                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ [1, 0]                                                  │  │  ← red text
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  Expected                                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ [0, 1]                                                  │  │  ← green text
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  Runtime: 45 ms          Memory: 14.32 MB                     │
│                                                               │
│  Code  [Python]                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ class Solution:                                         │  │
│  │     def twoSum(self, nums, target):                     │  │
│  │         ...                                             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│                         [Close]                               │
└───────────────────────────────────────────────────────────────┘
```

**Test Count Display Logic**:
```
| Scenario              | summary.passed | total_test_cases | Display         |
|-----------------------|----------------|------------------|-----------------|
| All pass              | 5              | 5                | "5 / 5 passed"  |
| First test fails      | 0              | 5                | "0 / 5 passed"  |
| Third test fails      | 2              | 5                | "2 / 5 passed"  |
| Compile error         | 0              | 5                | "0 / 5 passed"  |
```

**When viewing old submissions** (from Submissions tab):
- Old submissions don't have full result data
- Show only: Status, Runtime, Memory, Code
- Don't show test count (we don't have the detailed results)

### Mastered Problems Page

```
┌─────────────────────────────────────────────────────────────┐
│  acodeaday                                    [Back]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Mastered Problems (3)                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ Two Sum                                          │   │
│  │    Easy • Hash Map • Mastered Jan 1                 │   │
│  │                                       [Show Again]  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ ✅ Valid Palindrome                                 │   │
│  │    Easy • Two Pointers • Mastered Dec 28            │   │
│  │                                       [Show Again]  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ ✅ Best Time to Buy and Sell Stock                  │   │
│  │    Easy • Sliding Window • Mastered Dec 25          │   │
│  │                                       [Show Again]  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Authentication

**No auth routes in the backend.** Authentication is handled entirely by Supabase:

1. A default user is created on backend startup using `DEFAULT_USER_EMAIL` and `DEFAULT_USER_PASSWORD` environment variables
2. Frontend uses Supabase JS client directly to authenticate: `supabase.auth.signInWithPassword()`
3. Frontend includes the JWT in requests: `Authorization: Bearer <access_token>`
4. Backend validates the token on protected routes using `supabase.auth.get_user(token)`

### Problems

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/problems` | List all problems | No |
| GET | `/api/problems/:slug` | Get single problem with language config | No |

### Code Execution

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/run` | Run code against example test cases | No |
| POST | `/api/submit` | Submit solution against all test cases | Yes |
| POST | `/api/rate-submission` | Rate submission difficulty (Anki SM-2) | Yes |

### Code Persistence

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/code/save` | Save user's current code (auto-save) | Yes |
| POST | `/api/code/reset` | Reset to starter code | Yes |
| POST | `/api/code/load-submission` | Load code from past submission | Yes |

### User Progress

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/today` | Get today's session (reviews + new) | Yes |
| GET | `/api/progress` | Get user's overall progress | Yes |
| GET | `/api/mastered` | Get mastered problems | Yes |
| POST | `/api/mastered/:id/show-again` | Add problem back to rotation | Yes |

### Submissions

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/submissions/:problem_id` | Get past submissions for a problem | Yes |

### AI Chat

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/chat/models` | List available LLM models | Yes |
| POST | `/api/chat/sessions` | Create new chat session | Yes |
| GET | `/api/chat/sessions/:slug` | List sessions for a problem | Yes |
| GET | `/api/chat/session/:id` | Get session with messages | Yes |
| POST | `/api/chat/session/:id/message` | Send message in session | Yes |

---

## MVP Scope

### Phase 1 - Backend ✅ COMPLETE
- [x] Docker setup (Judge0 CE with workers, redis, postgres)
- [x] FastAPI backend with async SQLAlchemy 2.0
- [x] Supabase Auth integration (JWT Bearer token validation)
- [x] 16 Blind 75 problems with test cases (YAML seed files)
- [x] Code execution (Run Code, Submit via Judge0)
- [x] Daily session logic (2 reviews + 1 new)
- [x] Anki SM-2 spaced repetition with ratings
- [x] Python execution
- [x] 20 backend tests passing

### Phase 2 - Frontend ✅ COMPLETE
- [x] TanStack (React 19) with file-based routing
- [x] LeetCode-clone problem view UI with split panes
- [x] Monaco Editor with auto-save
- [x] Dashboard page with daily problems
- [x] Progress visualization
- [x] Mastered problems page with "Show Again"
- [x] Submission history
- [x] AI Chat assistant (Socratic/Direct modes)
- [x] Rating modal for spaced repetition

### Phase 3 - Future
- [ ] Full Blind 75 (all 75 problems)
- [ ] Custom test case support
- [ ] JavaScript execution support
- [ ] Additional languages
- [ ] Multiple problem sets (NeetCode 150, company-specific)
- [ ] Mobile responsive design

---

## Open Questions

1. **Offline support** — needed?
2. **Mobile** — responsive web or native app later?

---

## Current Status

MVP is complete. Both backend and frontend are fully functional:

**Backend**: FastAPI with async SQLAlchemy, Supabase JWT auth, Judge0 execution, Anki SM-2 spaced repetition, AI chat via litellm.

**Frontend**: TanStack React 19 with file-based routing, Monaco Editor with auto-save, split-pane layout, all pages implemented.

**Next Steps**:
1. Add more Blind 75 problems (currently 16 seeded)
2. Implement JavaScript execution support
3. Add frontend tests
4. Improve error handling and edge cases

---

## License

MIT — do whatever you want with it.