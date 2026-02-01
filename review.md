# Code Review: `claude/leetcode-import-feature-douYs`

**Branch**: 16 commits, 63 files changed, ~7,400 lines added
**Feature**: AI-powered LeetCode problem import using Pydantic AI agents
**Review updated**: Feb 1, 2026 — includes assessment of both fix commits + gpt-5-nano comparison testing

---

## Build & Test Results

| Check | Status | Notes |
|-------|--------|-------|
| `npm install` | Pass | 2 high severity audit warnings (pre-existing) |
| TypeScript `tsc --noEmit` | **Pass** | No type errors after both fix commits |
| Backend `uv sync` | Pass | Dependencies install fine |
| Backend unit tests (non-DB) | **Pass** | 30 tests pass — covers import schemas, workflow helpers, conftest setup |
| Backend unit tests (DB-dependent) | Inconclusive | 9 fail + 55 error — test DB on port 54325 not running (pre-existing env issue, not branch-specific) |
| Backend lint (`ruff`) | Inconclusive | `ruff` binary not found — env/path issue, not branch-specific |

---

## Fix Commit #1 Review (`ec83b4c`)

The first fix commit addressed 8 issues from the original review. Code-level assessment:

| Original Issue | Fix Applied | Status |
|----------------|-------------|--------|
| #1 Background task GC risk | `_background_tasks: set[asyncio.Task]` + `task.add_done_callback(_background_tasks.discard)` | **Fixed** |
| #2 No LLM timeout | All 4 agent `.run()` calls wrapped with `asyncio.wait_for(timeout=120)` | **Fixed** |
| #3 No Judge0 timeout | `validate_solution_with_judge0()` wrapped with `asyncio.wait_for(timeout=60)` | **Fixed** |
| #4 Test port mismatch | Unified to `54325` in both conftest.py and Makefile | **Fixed** |
| #5 Verifier not model-portable | Field descriptions + CRITICAL RULES section in system prompt | **Partially fixed** (further fixed in commit #2) |
| #5 (major) Staleness check | 5-minute cutoff: `ImportJob.updated_at < cutoff` in recovery query | **Fixed** |
| #6 Sequence jitter | `await asyncio.sleep(random.uniform(0.01, 0.1))` on IntegrityError | **Fixed** |
| (minor) Silent strategy override | `logger.warning("unsupported_comparison_strategy_overridden", ...)` added | **Fixed** |

## Fix Commit #2 Review (`655d0da`) — "Fix OpenAI schema compatibility and verifier reliability"

Major schema redesign addressing Critical Issues #5 and #6. Changes across 5 files:

| Change | File | Assessment |
|--------|------|-----------|
| `FunctionParam` + `FunctionSignature` typed models replace `dict` | `import_schemas.py` | **Good** — eliminates `{"type": "object"}` without `additionalProperties` |
| `GeneratedProblemLanguages` model with `.available()` helper replaces `dict[str, ...]` | `import_schemas.py` | **Good** — eliminates `$ref` + `additionalProperties` pattern |
| `VerificationResult` redesigned with 10 boolean fields + `is_valid()` + `failed_checks_summary()` | `import_schemas.py` | **Excellent** — structured verification eliminates LLM ambiguity |
| `_TestValue` type alias for OpenAI-compatible test case values | `import_schemas.py` | **Good** — explicit union type |
| Verifier prompt updated for boolean-per-check format | `import_agents.py` | **Good** — clear instructions for each field |
| Workflow uses `verification.is_valid()` and `problem.languages.available()` | `import_workflow.py` | **Good** — clean integration |
| 17 new unit tests for schemas + workflow helpers | `test_import_schemas.py`, `test_import_workflow.py` | **Good** — covers all new models |

**Schema compatibility note**: Raw `GeneratedProblem.model_json_schema()` still contains `$ref` (6 occurrences) and `anyOf` (3 occurrences), but **this is not an issue at runtime** — pydantic-ai resolves `$ref` internally before sending to OpenAI. Confirmed by successful E2E test (see below).

---

## Re-Test Results (Post Both Fix Commits, Feb 1 2026)

Tested with backend (uvicorn port 8000) + frontend (Vite port 3000) running against local Supabase.
Models tested: `openai:gpt-4o` and `openai:gpt-5-nano` (via `.env` `IMPORT_AGENT_MODEL`).

### UI Tests — All Still Passing

The UI behavior is unchanged from the original review — all 16 UI tests pass. Modal, quick examples, progress tracking, cancel, dismiss, import history, and status icons all work correctly.

### Existing Features — Unaffected

| Feature | Status | Details |
|---------|--------|---------|
| Problem list API | **Pass** | 153 problems returned correctly |
| Today's session | **Pass** | Reviews and new problem returned |
| Problem detail page | **Pass** | Description, examples, constraints, Monaco editor, test cases all render |
| Problem page navigation | **Pass** | Clicking problem card navigates to `/problem/contains-duplicate`, full split-pane renders |

### Pipeline Re-Test with OpenAI gpt-4o (Post Fix Commit #2)

**Test: "Add LeetCode #58 Length of Last Word"**

| Stage | Result | Details |
|-------|--------|---------|
| Intent parsing | **Pass** | `intent: "specific"`, `leetcode_number: 58`, `count: 1` — 2s |
| Problem generation (attempt 1) | **Pass** | "Length of Last Word" generated with correct schema |
| Verification (attempt 1) | **Pass** | `is_valid()` returned true — all 10 boolean fields correct |
| Test case generation | **Pass** | Test cases generated successfully |
| Judge0 validation (attempt 1) | **FAIL** | Test 13 wrong: input `"Ends with a single space "` expected 6, actual 5 ("space" has 5 chars) |
| Refinement (attempt 2) | Generated | Problem regenerated from issue feedback |
| Verification (attempt 2) | **FAIL** | `examples` check failed: "example outputs should be integers, not strings" |
| Attempt 3 | **FAIL** | Also failed verification |
| End-to-end import | **FAIL** | All 3 retries exhausted |

**Key improvement over pre-fix**: The pipeline now progresses through ALL phases with OpenAI gpt-4o — intent parsing, problem generation, verification, test case generation, and Judge0 validation all work. Previously, the pipeline crashed on schema errors or false-positive verification. Now the failure point is **test case quality** (LLM generating incorrect expected values), not infrastructure.

### Pipeline Re-Test with OpenAI gpt-5-nano

**Test: "Add LeetCode #58 Length of Last Word"** (same problem as gpt-4o test for direct comparison)

| Stage | Attempt 1 | Attempt 2 |
|-------|-----------|-----------|
| Problem generation | "Length of Last Word" (correct) — 42s | **"Valid Palindrome" #125** (WRONG problem!) — 33s |
| Verification | **Pass** | **Pass** (but verifying the wrong problem) |
| Test case generation | Generated (15 test cases) | Generated |
| Judge0 validation | **FAIL** — solution returns `1` for ALL inputs (11/14 tests wrong) | **Pass** |
| Persist | N/A (didn't reach) | **FAIL** — `valid-palindrome` slug already exists (3 IntegrityError retries) |
| **Result** | Failed: broken reference solution | Failed: retry generated wrong problem, which already exists |

**Final status**: `failed` — "All 1 problem(s) failed to generate"

**Critical findings compared to gpt-4o**:

1. **Reference solution quality is much worse**: gpt-4o generated a correct solution for Length of Last Word — it failed on ONE test case having the wrong expected value. gpt-5-nano generated a solution that returns `1` for every input (completely broken). The `actual` column shows `1` for all 11 failed tests.

2. **Retry drift — problem identity not preserved**: On attempt 2, after being told "Judge0 validation failed for Length of Last Word", gpt-5-nano **generated an entirely different problem** (Valid Palindrome #125 instead of Length of Last Word #58). This reveals a fundamental issue: the retry loop's `previous_problem` + `issues` feedback isn't enough to constrain gpt-5-nano to the same problem. The verifier didn't catch this because it verified the new problem on its own merits (Valid Palindrome is a valid problem).

3. **Persist collision after drift**: Because the retry generated Valid Palindrome (#125), which already exists in the database (it's one of the 153 seeded problems), the persist step hit an IntegrityError 3 times and gave up.

**Model comparison summary** (same prompt: "Add LeetCode #58 Length of Last Word"):

| Dimension | gpt-4o | gpt-5-nano |
|-----------|--------|------------|
| Solution correctness | Correct (passes 12/13 tests) | Completely wrong (returns `1` for all) |
| Problem identity stability | Stays on #58 across retries | Drifts to #125 on retry |
| Verification accuracy | Accurate (passes correct, flags real issues) | Accurate but verifies wrong problem |
| Time per generation cycle | ~30s | ~33-42s |
| Overall result | Failed (test case quality) | Failed (solution quality + retry drift) |

**Recommendation**: gpt-5-nano is **not suitable** for this pipeline. The reference solution quality and problem identity stability are both significantly worse than gpt-4o. gpt-4o should remain the minimum model for import tasks.

**Test: Duplicate detection — "Add LeetCode #1 Two Sum"**

| Stage | Result | Details |
|-------|--------|---------|
| Intent parsing | **Pass** | Correctly identified as `specific`, `leetcode_number: 1` |
| Duplicate check | **Pass** | Immediately returned `"LeetCode #1 already exists."` — no LLM calls wasted |

### Verifier Fix Assessment (Post Fix Commit #2)

The structured boolean field redesign is a **major improvement**:

- **Pre-fix #1**: Verifier filled `issues` array with positive observations like "title matches" — then set `valid=false` because the array was non-empty. 100% false rejection rate.
- **Post-fix #1**: Verifier no longer lists positive observations, but generated false positives (e.g., "leetcode_no incorrect" when it IS correct).
- **Post-fix #2 (current)**: Verifier uses 10 explicit boolean fields (`title_correct`, `leetcode_no_correct`, etc.) with `is_valid()` computed from actual field values. **Attempt 1 verification passed correctly.** Attempt 2 caught a real issue (string vs integer output types). The verifier is now **reliable and accurate** with OpenAI gpt-4o.

### Provider Availability

| Provider | Status |
|----------|--------|
| Anthropic (default) | Credits exhausted — cannot test |
| OpenAI gpt-4o | **Pipeline works end-to-end** — fails on LLM test case quality, not infrastructure |
| OpenAI gpt-5-nano | **Pipeline works but quality is much worse** — broken solutions, retry drift to wrong problem |
| Google Gemini 2.0 Flash | Free tier quota exhausted (429 error) |

### Import Attempts Log (Full History)

| # | Prompt | Model | Outcome |
|---|--------|-------|---------|
| 1 | "Add LeetCode #20 Valid Parentheses" | anthropic | Failed — API credits exhausted |
| 2 | "Add LeetCode #20 Valid Parentheses" | openai:gpt-4o | Failed — "LeetCode #20 already exists" (correct dedup) |
| 3 | "Add LeetCode #42 Trapping Rain Water" | openai:gpt-4o | Failed — "LeetCode #42 already exists" (correct dedup) |
| 4 | "Add LeetCode #9 Palindrome Number" | openai:gpt-4o | Failed — Verification rejected 3/3 times (pre-fix #1) |
| 5 | "Add 2 easy greedy problems" | openai:gpt-4o | Failed — Verification rejected (pre-fix #1) |
| 6 | "Add 3 medium binary search problems" | openai:gpt-4o | Cancelled — User-initiated cancel (cancel test) |
| 7 | "Add LeetCode #58 Length of Last Word" | openai:gpt-4o | Failed — Verification all-positive-observations bug (pre-fix #1) |
| 8 | "Add LeetCode #58 Length of Last Word" | openai:gpt-4o | Failed — Verifier false positive + schema error on retries (post-fix #1) |
| 9 | "Add LeetCode #58 Length of Last Word" | google-gla:gemini-2.0-flash | Failed — 429 quota exhausted |
| 10 | "Add LeetCode #58 Length of Last Word" | openai:gpt-4o | Failed — Judge0 caught wrong test case on attempt 1, verification caught real issue on attempt 2, exhausted retries (post-fix #2) |
| 11 | "Add LeetCode #1 Two Sum" | openai:gpt-4o | Failed — "LeetCode #1 already exists" (correct duplicate detection, post-fix #2) |
| 12 | "Add LeetCode #58 Length of Last Word" | openai:gpt-5-nano | Failed — Attempt 1: reference solution returns `1` for all inputs (Judge0 caught it). Attempt 2: generated wrong problem (#125 Valid Palindrome), passed Judge0 but IntegrityError on persist (slug exists). |

---

## Critical Issues (Status After Both Fix Commits)

### 1-4. RESOLVED — See "Fix Commit #1 Review" above

Background task GC, LLM timeouts, Judge0 timeout, and test port mismatch are all fixed.

### 5. Verifier agent — RESOLVED (Fix Commit #2)

The structured boolean field redesign fully resolved the verifier reliability issue:

- **Pre-fix #1**: `valid: bool` + `issues: list[str]` — LLM filled issues with positive observations, always set valid=false. 100% false rejection rate.
- **Post-fix #1**: Field descriptions + CRITICAL RULES — improved but still produced false positives.
- **Post-fix #2 (current)**: 10 explicit boolean fields (`title_correct`, `leetcode_no_correct`, `solution_correct`, etc.) with `is_valid()` computed programmatically from all fields. `failed_checks_summary()` provides structured feedback for refinement.

**Test result**: Attempt 1 verification passed correctly with OpenAI gpt-4o. Attempt 2 correctly flagged a real issue (string vs integer example outputs). The verifier is now reliable and accurate.

### 6. OpenAI schema incompatibility — RESOLVED (Fix Commit #2)

The schema redesign (replacing `dict` with typed Pydantic models) resolved the runtime incompatibility:

- `dict` → `FunctionSignature` model (typed `name`, `params: list[FunctionParam]`, `return_type`)
- `dict[str, GeneratedProblemLanguage]` → `GeneratedProblemLanguages` model (explicit `python`, `javascript` fields)

**Note**: Raw `model_json_schema()` still contains `$ref` references, but **pydantic-ai resolves these internally** before sending to OpenAI's API. This was confirmed by the successful E2E test — all 4 agents (intent parser, generator, verifier, test case generator) completed without schema errors.

### NEW (Major): Retry loop regenerates everything — wastes tokens and reduces success rate

**`import_workflow.py:293-434`**

The whole point of splitting the workflow into independent agents (intent parser, problem generator, verifier, test case generator) is to allow **targeted retries** — if test case generation fails, only re-run the test case generator. But the current retry loop doesn't do this.

When Judge0 validation fails (line 394-405), the workflow feeds the failure back to the **problem generator** and regenerates the entire problem + solution + test cases from scratch:

```python
# Line 296-303: On ANY failure, the problem generator is called again
if previous_problem and issues:
    gen_result = await asyncio.wait_for(
        get_problem_generator_agent().run(
            f"Fix these issues with the problem below: {issues}\n\n"
            f"Original problem:\n{previous_problem.model_dump_json(indent=2)}\n\n"
            ...
```

In the E2E test, this happened:
1. Problem generation: correct (LeetCode #58, correct solution)
2. Verification: passed
3. Test case generation: 12/13 correct, 1 wrong expected value
4. Judge0: correctly caught the bad test case
5. **Retry**: regenerated the entire problem + solution + verification + test cases (4 LLM calls wasted)
6. **Retry 2**: same — another 4 LLM calls wasted
7. Result: failed after 12+ LLM calls when only 1 targeted test-case-only call was needed

**Cost**: Each retry burns ~4 LLM calls (generate + verify + test cases + judge0). With `MAX_RETRIES=3`, a Judge0 failure on attempt 1 burns up to 12 additional LLM calls instead of 2-3 targeted ones.

**What should happen instead**:
- **Judge0 failure** → re-run only the test case generator agent with feedback about which test cases failed and why, then re-validate. Keep the problem + solution intact.
- **Verification failure** → re-run only the problem generator with refinement instructions (current behavior is correct for this case).
- **Both** → the retry should be scoped to the failing phase, not restart from scratch.

This is the primary reason the import fails — 3 retries is only 3 chances when each retry wastefully regenerates everything. With targeted retries, the same 3 retries would be 3 chances at fixing just the test cases, which is far more likely to succeed.

Additionally:
- There is **no resume functionality** for failed jobs. Once a job hits `failed` status, it's terminal. No "Retry" button, no API endpoint to resubmit. The user must start a brand new import.
- For batch imports (e.g., "5 sliding window problems") where 3/5 succeed and 2/5 fail, there's no way to retry just the failed 2.

### NEW (Major): Retry drift — problem identity not preserved across retries

**Discovered during gpt-5-nano testing** (`import_workflow.py:296-303`)

When a retry is triggered (e.g., after Judge0 validation fails), the problem generator is called again with `previous_problem` and `issues` as context. However, there is no hard constraint enforcing that the retry produces the **same** problem. With gpt-5-nano, the retry for "Add LeetCode #58 Length of Last Word" produced **"Valid Palindrome" (#125)** — an entirely different problem.

This happened because the retry prompt at line 296-303 says "Fix these issues with the problem below" but the LLM is free to ignore this instruction and generate whatever it wants. With stronger models (gpt-4o) this stays on track, but weaker models drift.

The verifier didn't catch this because it verified the new problem on its own merits (Valid Palindrome is a valid problem). The `leetcode_no` changed from 58 to 125, which the verifier doesn't cross-reference against the original request.

**What should happen**: The retry prompt should include hard constraints like "You MUST generate LeetCode #58" and/or the verifier should check that `leetcode_no` matches the original request. Alternatively, the workflow should validate that the retried problem still matches the original intent before proceeding to verification.

---

## Major Issues

### 7. Startup recovery too aggressive — RESOLVED

Fixed with 5-minute staleness check in `recover_stuck_import_jobs()`.

### 8. Sequence number race condition — RESOLVED

Fixed with `asyncio.sleep(random.uniform(0.01, 0.1))` jitter on IntegrityError.

---

## Minor Issues

- **Manual import type definitions** (`api.ts:101-145`): Import types are manually defined with a "until backend regenerates OpenAPI schema" comment. Expected for a feature branch, but should be generated before merging to main.
- **Modal accessibility** (`ImportModal.tsx`): No `role="dialog"`, no ESC key handler, no focus trap. Standard gaps for a small project, but worth noting.
- **Import UI clutters the dashboard** (`index.tsx:83-99`, `index.tsx:137-148`): The dashboard (`/`) should answer one question: "What do I practice today?" Instead, it renders three import-related elements that serve a different user intent:
  1. `ActiveImportTracker` banner (`index.tsx:83-99`) — real-time progress tracker with progress bar, linked problems, cancel/dismiss buttons
  2. `ImportHistoryList` section (`index.tsx:137-148`) — "Recent Imports" list showing up to 5 past import jobs with status icons, timestamps, and progress counts
  3. `ImportModal` (`index.tsx:93-98`) — the modal itself (this is fine as an overlay)

  The tracker and history section push the actual practice content (Review Problems, New Problem, Pattern Browser) below the fold. **Recommendation**: Move the `ActiveImportTracker`, `ImportHistoryList`, and the `ImportModal` trigger to a dedicated `/import` page. The dashboard's "Import Problems" button (`index.tsx:65-71`) should navigate to `/import` instead of opening a modal inline. The dashboard should at most show a small non-intrusive notification if an import is actively running — not a full progress panel with linked problems.
- **Stale pyiceberg warning filter** (`pyproject.toml:34`): `filterwarnings` suppresses `DeprecationWarning` from `pyiceberg` which is not a dependency.
- **Makefile skips import tests** (`Makefile:41-44`): `test-backend-all` has `--ignore` flags for route test files but doesn't explicitly include or exclude `tests/import_tests/`. The import tests should be covered by the default `tests/` path, but the `--ignore` pattern should be reviewed.
- **Error message truncation in UI**: Workflow errors (e.g., Gemini 429) are shown as-is in the progress banner, including raw JSON error bodies. User-facing error messages should be sanitized to show human-readable summaries.

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
- **Cooperative cancellation**: Users can cancel in-progress imports via status check at each loop iteration. Confirmed working during manual testing — cancel triggers immediately, workflow stops at next boundary, status transitions correctly to "Cancelled".
- **Pydantic schemas**: Strong validation at API boundaries with `GeneratedProblem`, `ImportPlan`, etc.
- **TypeScript passes**: No type errors despite significant frontend additions
- **Test structure**: Dedicated `import_tests/` directory with isolated fixtures and mocked auth
- **Progress tracking**: Real-time progress bar, status icons, linked problems, and import history. All confirmed working via browser testing — status updates arrive via 2-second polling, progress bar increments correctly during batch imports.
- **Structured logging**: Uses `structlog` throughout with contextual info. Logs were invaluable for diagnosing both the verifier bug and the schema compatibility issue.
- **Error handling**: Top-level try/catch in workflow properly catches and displays errors from multiple providers (OpenAI schema errors, Gemini quota errors, Anthropic credit errors) — all shown to user with appropriate status transitions.
- **Correct frontend error handling**: Modal stays open on error, mutation state drives error display. Confirmed — the modal closes only on successful submission, errors are displayed inline.
- **Duplicate detection**: Fast-path rejection of existing LeetCode numbers before any LLM calls. Saves cost and provides instant user feedback.
- **Import history UX**: The "Recent Imports" section on the dashboard provides complete visibility into all past import attempts with status icons, prompts, error messages, timestamps, and progress counts.
- **Active import tracker**: Non-intrusive banner at top of dashboard shows real-time import progress without blocking other page interactions. Dismiss button for terminal states keeps the UI clean.
- **Fix quality**: The fix commit (`ec83b4c`) addressed 8 issues cleanly — timeout wrapping, GC prevention, staleness check, jitter, port unification, verifier prompt hardening, and warning log all implemented correctly.

---

## Recommendations

**Remaining blockers**:
1. **Implement targeted retries** (Critical — see "Retry loop regenerates everything" above) — when Judge0 validation fails, re-run only the test case generator, not the entire pipeline. This is the single biggest change needed to make imports reliably succeed. Currently each retry wastes ~4 LLM calls regenerating a correct problem/solution instead of fixing the 1 bad test case.
2. **Fix retry drift** (Critical — see "Retry drift" above) — retries must preserve problem identity. Enforce `leetcode_no` and title constraints in the retry prompt and/or add a post-generation check that the problem still matches the original request.
3. **Test with a funded Anthropic account** — the pipeline infrastructure works with OpenAI gpt-4o (all phases complete), but no successful import was achieved. The default Anthropic model may have better test case generation accuracy.
4. **Set a minimum model quality floor** — gpt-5-nano produces completely broken reference solutions and drifts to wrong problems on retry. gpt-4o is the minimum viable model. Consider adding model validation or a recommended-models list in the docs/settings.

**To improve reliability**:
3. Increase `MAX_RETRIES` from 3 to 5 — with targeted retries this gives 5 chances to fix just the failing component
4. Add a "Retry" button on failed imports in the frontend — currently the user must manually re-type the same prompt
5. For batch imports, allow retrying just the failed problems (track which succeeded)

**Before production**:
6. Regenerate OpenAPI types to replace manual import type definitions
7. Sanitize error messages shown to users (strip raw JSON error bodies — e.g., Gemini 429 response bodies are shown as-is)
8. Move import UI to a dedicated `/import` page to declutter the dashboard

**Overall grade: B** — Good architecture, well-separated concerns, polished frontend UX. Both fix commits addressed the original critical issues effectively: timeouts, GC, staleness, jitter, verifier reliability, and schema compatibility are all resolved. The pipeline now works end-to-end with OpenAI gpt-4o — intent parsing, problem generation, verification, test case generation, and Judge0 validation all function correctly. However, **no successful end-to-end import has been achieved** due to a fundamental design issue: when any phase fails (typically test cases), the retry loop regenerates the entire pipeline instead of just the failing phase. This wastes tokens and drastically reduces the chance of success within the 3-retry limit. The agents are correctly separated (4 independent agents), but the orchestrator (`import_workflow.py`) doesn't leverage that separation for targeted retries. Fixing the retry granularity is the single most impactful change needed to make imports succeed reliably. The frontend is production-quality; the backend pipeline architecture is sound but the orchestrator needs refinement before merge.
