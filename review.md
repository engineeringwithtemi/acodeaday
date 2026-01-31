# Code Review: `claude/leetcode-import-feature-douYs`

**Branch**: 14 commits, 63 files changed, ~7,400 lines added
**Feature**: AI-powered LeetCode problem import using Pydantic AI agents

---

## Build & Test Results

| Check | Status | Notes |
|-------|--------|-------|
| `npm install` | Pass | 2 high severity audit warnings (pre-existing) |
| TypeScript `tsc --noEmit` | **Pass** | No type errors |
| Frontend `npm run build` | Inconclusive | Failed in main worktree, likely environment artifact — needs retest in clean worktree |
| Backend `uv sync` | Pass | Dependencies install fine |
| Backend tests | Inconclusive | `alembic` import error — likely pre-existing env issue, not branch-specific |
| Backend lint (`ruff`) | Inconclusive | `ruff` binary not found — env/path issue, not branch-specific |

Build/test results were run from the wrong checkout. They need to be re-verified in the worktree.

---

## Critical Issues (Must Fix Before Merge)

### 1. Background task GC risk — `routes/imports.py:77-80`
```python
asyncio.create_task(
    import_problems_workflow(str(job.id), request.prompt),
    name=f"import-{job.id}",
)
```
The task reference is never stored. Python's docs explicitly warn: "Save a reference to the result of this function, to avoid a task disappearing mid-execution." The GC can collect fire-and-forget tasks, silently cancelling running imports. Unhandled exceptions are also swallowed.

**Fix**: Store task refs in a module-level `set()` with a `done_callback` to discard.

### 2. No timeout on LLM agent calls — `import_workflow.py:214, 289, 322, 344`
All Pydantic AI agent `.run()` calls have no timeout. If the LLM provider hangs, the workflow blocks forever. The top-level `except Exception` at line 429 won't catch a hung `await`. Cancellation is cooperative (only checked at loop boundaries), so a stuck call can't be cancelled either.

**Fix**: Wrap with `asyncio.wait_for(..., timeout=60)`.

### 3. No timeout on Judge0 call — `execution_validator.py:159-164`
`asyncio.to_thread(judge0.execute_code, ...)` has no timeout. While Judge0 itself has internal timeouts for code execution, the HTTP/network layer has no protection against hangs.

**Fix**: Wrap with `asyncio.timeout(30)`.

### 4. Test database port mismatch
`import_tests/conftest.py:26` defaults to port `5432`. `tests/conftest.py:35` defaults to port `54325`. The Makefile `test-backend-all` (line 39) also hardcodes `5432`. If `TEST_DATABASE_URL` env var is set, both use it (fine for CI), but local development will break for one set or the other.

**Fix**: Unify the default port across both conftest files and the Makefile.

---

## Major Issues

### 5. Startup recovery too aggressive — `import_workflow.py:444-470`
`recover_stuck_import_jobs()` marks ALL `QUEUED`/`PROCESSING` jobs as `FAILED` with no timestamp filter. In a single-process uvicorn setup (which this is), no tasks are running at startup after a crash, so this is mostly safe. However, if the app restarts quickly, a QUEUED job created by a user 1 second before the restart would be incorrectly marked FAILED.

**Fix**: Add a staleness check — only mark jobs as failed if `updated_at` is older than a few minutes.

### 6. Sequence number race condition — `import_workflow.py:119-124`
```python
max_seq_result = await db.execute(select(func.max(Problem.sequence_number)))
next_seq = (max_seq_result.scalar() or 0) + 1
```
The retry loop (3 attempts) catches `IntegrityError` but doesn't add backoff. Since problems are generated sequentially within each job (line 260 is a `for` loop), the actual concurrency is limited to the number of simultaneous import jobs (max 3, one insert at a time each). Still, adding jitter is cheap insurance.

**Fix**: Add `await asyncio.sleep(random.uniform(0.01, 0.1))` in the IntegrityError retry.

---

## Minor Issues

- **Silent comparison_strategy override** (`import_workflow.py:314-316`): Unsupported strategies are silently set to `None` with no log message. Should add a `logger.warning()`.
- **Manual import type definitions** (`api.ts:101-145`): Import types are manually defined with a "until backend regenerates OpenAPI schema" comment. Expected for a feature branch, but should be generated before merging to main.
- **Modal accessibility** (`ImportModal.tsx`): No `role="dialog"`, no ESC key handler, no focus trap. Standard gaps for a small project, but worth noting.
- **Stale pyiceberg warning filter** (`pyproject.toml:34`): `filterwarnings` suppresses `DeprecationWarning` from `pyiceberg` which is not a dependency.
- **Makefile skips import tests** (`Makefile:41-44`): `test-backend-all` has `--ignore` flags for route test files but doesn't explicitly include or exclude `tests/import_tests/`. The import tests should be covered by the default `tests/` path, but the `--ignore` pattern should be reviewed.

---

## Items Removed From Original Review (Not Actual Issues)

- **`any` types in api-client.ts**: The actual code uses `unknown` for `ApiError.data` (line 16), `apiPost` data param (line 146), and all similar params. The only `any` is `errorData` at line 98, which has an eslint-disable comment explaining why. Not an issue.
- **ActiveImportTracker infinite polling**: Polling correctly stops when status is terminal (`useImport.ts:36-40` returns `false`). The component shows a "Dismiss" button for the user to manually clear it (line 58-65). This is a deliberate UX choice, not a bug.
- **Error swallowed in ImportModal**: The catch block at line 26 is empty, but the error IS displayed via `startImport.isError` at line 81-85. The modal does NOT close on error because `onClose()` at line 25 is inside the `try` block before the `catch`. Error handling works correctly.
- **TOCTOU race in debounce/limit checks**: Technically possible but the window is milliseconds. The debounce is a UX convenience, not a security boundary. Standard web app pattern.
- **Unbounded exclude list**: With ~153 problems, this is a list of ~153 integers. Trivially small.
- **Judge0 only validates Python**: The generator agent's system prompt requires both Python and JavaScript. Validating Python-only is a reasonable first-pass strategy, not an oversight.

---

## What's Good

- **Clean architecture**: Routes -> Workflow -> Agents -> Validator — well-separated concerns
- **Cooperative cancellation**: Users can cancel in-progress imports via status check at each loop iteration
- **Pydantic schemas**: Strong validation at API boundaries with `GeneratedProblem`, `ImportPlan`, etc.
- **TypeScript passes**: No type errors despite significant frontend additions
- **Test structure**: Dedicated `import_tests/` directory with isolated fixtures and mocked auth
- **Progress tracking**: Real-time progress bar, status icons, linked problems, and import history
- **Structured logging**: Uses `structlog` throughout with contextual info
- **Error handling**: Top-level try/catch in workflow with status updates on failure
- **Correct frontend error handling**: Modal stays open on error, mutation state drives error display

---

## Recommendations

**Before merge (blockers)**:
1. Store background task references to prevent GC collection
2. Add timeouts to all LLM agent and Judge0 calls
3. Unify test database port across conftest files and Makefile
4. Verify build passes in a clean environment

**Before production**:
5. Add staleness check to startup recovery
6. Add jitter to sequence number retry loop
7. Regenerate OpenAPI types to replace manual import type definitions
8. Add a `logger.warning()` for comparison_strategy overrides

**Overall grade: B+** — Good architecture, separation of concerns, and correct frontend patterns. The main risks are reliability (no timeouts on external calls, GC-able background tasks) and test infrastructure consistency.
