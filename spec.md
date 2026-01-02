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
| Frontend | TanStack (React) |
| Code Editor | Monaco Editor |
| Code Execution | Judge0 (self-hosted) |
| Database | Supabase (local) |
| Auth | Supabase Auth |
| Infrastructure | Docker (everything containerized) |
| Language Support | Python only (MVP) |

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

## Spaced Repetition Logic

### Mastery Rules

| Event | Result |
|-------|--------|
| Solve problem 1st time | Added to review queue, due in 7 days |
| Solve problem 2nd time | Marked as "Mastered", removed from rotation |
| User clicks "Show Again" | Problem re-enters rotation |

### State Diagram

```
                    ┌─────────────┐
                    │   Unsolved  │
                    └──────┬──────┘
                           │
                      Solve once
                           │
                           ▼
                    ┌─────────────┐
                    │  In Review  │◄─────────────┐
                    │  (due 7d)   │              │
                    └──────┬──────┘              │
                           │                    │
                      Solve twice          "Show Again"
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
  user_id          UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  problem_id       UUID REFERENCES problems(id) ON DELETE CASCADE,
  times_solved     INTEGER DEFAULT 0,
  last_solved_at   TIMESTAMP,
  next_review_date DATE,
  is_mastered      BOOLEAN DEFAULT FALSE,
  show_again       BOOLEAN DEFAULT FALSE,
  created_at       TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id, problem_id)
);

CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_user_progress_next_review ON user_progress(next_review_date);
```

### Submissions

```sql
CREATE TABLE submissions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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

## Code Execution

### Architecture

Everything runs in Docker containers. User never interacts with Judge0 directly — all code execution goes through our API.

```
┌──────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Client  │──────▶│  API Layer      │──────▶│ Judge0 (Docker) │
│          │       │  (Docker)       │       │                 │
└──────────┘       └─────────────────┘       └─────────────────┘
```

### Execution Modes

| Action | Test Cases Used | Reference Solution Used |
|--------|-----------------|-------------------------|
| Run Code | Example test cases from DB | No |
| Run Code (custom input) | User's custom input | Yes — to generate expected output |
| Submit | ALL test cases from DB (including hidden) | No |

### API Endpoints

**Run Code**
```typescript
POST /api/run
{
  "problem_id": "two-sum",
  "language": "python",
  "code": "def twoSum(nums, target): ..."
}

// Response
{
  "success": true,
  "results": [
    {
      "test": 1,
      "passed": true,
      "input": "[2,7,11,15], 9",
      "stdout": "Debug: checking values",
      "output": "[0,1]",
      "expected": "[0,1]"
    }
  ],
  "runtime_ms": 42
}
```

**Run Code with Custom Input**
```typescript
POST /api/run
{
  "problem_id": "two-sum",
  "language": "python",
  "code": "def twoSum(nums, target): ...",
  "custom_input": [[1,5,3,7], 8]  // user-provided
}

// Server runs BOTH user code and reference solution
// Compares outputs
```

**Submit Solution**
```typescript
POST /api/submit
{
  "problem_id": "two-sum",
  "language": "python",
  "code": "def twoSum(nums, target): ..."
}

// Runs against ALL test cases (including hidden)
// Response
{
  "success": true,
  "all_passed": true,
  "passed_count": 15,
  "total_count": 15,
  "runtime_ms": 128
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

### Problems

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/problems` | List all problems |
| GET | `/api/problems/:slug` | Get single problem with language config |

### Code Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/run` | Run code against example test cases |
| POST | `/api/submit` | Submit solution against all test cases |

### User Progress

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/today` | Get today's session (reviews + new) |
| GET | `/api/progress` | Get user's overall progress |
| GET | `/api/mastered` | Get mastered problems |
| POST | `/api/mastered/:id/show-again` | Add problem back to rotation |

### Submissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/submissions/:problem_id` | Get past submissions for a problem |

---

## MVP Scope

### Phase 1 (MVP)
- [ ] Docker setup (API, Judge0, Supabase)
- [ ] 15 Blind 75 problems with test cases
- [ ] LeetCode-clone problem view UI
- [ ] Code execution (Run Code, Submit)
- [ ] Custom test case support
- [ ] Daily session logic (2 reviews + 1 new)
- [ ] Basic spaced repetition (7 day interval, 2x mastery)
- [ ] Python only

### Phase 2
- [ ] Full Blind 75 (all 75 problems)
- [ ] Progress visualization
- [ ] Mastered problems page with "Show Again"
- [ ] Submission history

### Phase 3
- [ ] JavaScript support
- [ ] Additional languages
- [ ] Multiple problem sets (NeetCode 150, company-specific)
- [ ] Adjustable spaced repetition intervals

---

## Open Questions

1. **Offline support** — needed?
2. **Mobile** — responsive web or native app later?

---

## Next Steps

1. Set up project structure with TanStack + Supabase
2. Self-host Judge0 instance
3. Create first 15 problems in JSON format
4. Build core UI components
5. Implement daily session logic
6. Test end-to-end flow

---

## License

MIT — do whatever you want with it.