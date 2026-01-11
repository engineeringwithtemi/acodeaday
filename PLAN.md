# Fix Plan: UI & Backend Issues

## Backend Agent Tasks

### 1. Fix typing imports in wrapper.py
**File:** `backend/app/services/wrapper.py`
- Add common typing imports to generated wrapper code BEFORE user code:
  ```python
  from typing import List, Optional, Dict, Tuple, Set, Any
  ```

### 2. Simplify test case logic (ignore is_hidden)
**Files:**
- `backend/app/routes/execution.py`

**Change:**
- Always return first 3 test cases (by sequence) for both `/run` and `/submit`
- Ignore the `is_hidden` field entirely (don't filter by it)
- No DB changes needed

### 3. Modify /api/run to support custom input
**File:** `backend/app/routes/execution.py`, `backend/app/schemas/execution.py`

**Change to RunCodeRequest:**
- Add optional field: `custom_input: list[list[Any]] | None = None`

**Logic in /api/run:**
- If `custom_input` is provided:
  1. Get reference solution from problem_languages
  2. Run reference solution against custom_input → get expected outputs
  3. Run user code against custom_input → get actual outputs
  4. Return comparison for each custom test case
- If `custom_input` is NOT provided:
  - Use first 3 test cases from DB (current behavior, minus is_hidden filtering)

### 4. Fix settings to read .env from project root
**File:** `backend/app/config/settings.py`
- Change `env_file=".env"` to look at project root: `env_file="../.env"` or use tuple `env_file=(".env", "../.env")`

### 5. Verify examples are returned by API
**File:** `backend/app/routes/problems.py`
- Check that `GET /api/problems/{slug}` returns the `examples` field
- Examples are stored in Problem.examples (JSONB) - verify it's included in response schema

---

## Frontend Agent Tasks

### 1. Fix auth persistence on refresh
**Files:**
- `frontend/src/routes/__root.tsx`
- `frontend/src/lib/api-client.ts`

**Problem:** `beforeLoad` runs `isAuthenticated()` before Supabase restores session from localStorage

**Solution:**
- Wait for Supabase auth to initialize before checking
- Use `supabase.auth.getSession()` with proper async handling
- Add loading state while determining auth status

### 2. Use markdown renderer for description
**File:** `frontend/src/components/ProblemDescription.tsx`
- Install `react-markdown` and `remark-gfm`
- Replace `dangerouslySetInnerHTML` with `<ReactMarkdown>` component
- Apply Tailwind prose classes for styling

### 3. Add test cases panel in bottom section
**Files:**
- `frontend/src/routes/problem.$slug.tsx`
- Create: `frontend/src/components/TestCasesPanel.tsx`

**Requirements:**
- Tabs: "Testcase" | "Test Result"
- Testcase tab shows:
  - Sub-tabs for each test case (Case 1, Case 2, Case 3, + Add)
  - Input fields (editable for custom cases)
  - Expected output display
- User can add custom test cases via "+" button
- Custom test cases send `custom_input` to backend

### 4. Improve test result display (LeetCode style)
**File:** `frontend/src/components/TestResults.tsx`

For each test case, show (like LeetCode):
- **Input:** the test input
- **Output:** user's actual output
- **Expected:** expected output
- **Stdout:** user's print() statements (if any)

### 5. Improve error display
**File:** `frontend/src/components/TestResults.tsx`
- Match LeetCode style:
  - Compile Error: red box with error message
  - Runtime Error: show exception + line info
  - Wrong Answer: show input, expected, actual
  - Accepted: green success with runtime

### 6. Update types and hooks for custom input
**File:** `frontend/src/types/api.ts`, `frontend/src/hooks/useCodeExecution.ts`
- Add `custom_input` to RunCodeRequest type
- Update useRunCode hook to accept custom input

---

## Execution

Both agents can run in parallel since backend and frontend work is independent.
Frontend can build UI with mock data first, then wire up to backend.
