# Implementation Plan: AI-Powered Problem Import

## Overview

A feature that allows users to import coding problems via natural language prompts. A multi-agent pipeline generates, verifies, and persists problems using Pydantic AI with DBOS for durable background execution. All generated problems are first-class citizens — identical to manually seeded ones in the `problems` table.

**User input examples:**
- `"Add 10 sliding window problems"`
- `"Add LeetCode 4"`
- `"Add 5 easy array problems"`

---

## Architecture

### High-Level Flow

```
User submits prompt
       │
       ▼
POST /api/import  ──→  Creates ImportJob record
                        Starts DBOS workflow in background
                        Returns { id, status: "queued" }
       │
       ▼
Frontend polls GET /api/import/{id}
       │
       ▼
Returns clean ImportJob:
  - status: queued | processing | completed | failed
  - message: "Generating problem 3 of 10..."
  - progress: 3
  - total: 10
  - problems: [{ title, slug, difficulty, pattern }]  ← clickable → /problem/:slug
```

### Multi-Agent Pipeline

```
ORCHESTRATOR (DBOS Workflow)
│
├─ Step 1: PARSE INTENT
│  Input:  "Add 10 sliding window problems"
│  Output: { intent: "pattern", pattern: "sliding-window", count: 10 }
│
├─ Step 2: QUERY EXISTING (DB tool, not LLM)
│  Input:  pattern = "sliding-window"
│  Output: ["longest-substring-without-repeating", "sliding-window-maximum", ...]
│
├─ Step 3..N: FOR EACH PROBLEM (loop count times):
│  │
│  ├─ 3a. GENERATE PROBLEM (Problem Generator Agent)
│  │  Input:  pattern, exclude_slugs (refreshed each iteration)
│  │  Output: GeneratedProblem { title, slug, description, difficulty,
│  │          pattern, constraints, examples, languages: { python: {
│  │          starter_code, reference_solution, function_signature } } }
│  │
│  ├─ 3b. VERIFY PROBLEM (Problem Verifier Agent)
│  │  Input:  GeneratedProblem
│  │  Output: { valid: bool, issues: [...] }
│  │  On fail: Return to 3a with feedback (max 3 retries)
│  │
│  ├─ 3c. GENERATE TEST CASES (Test Case Generator Agent)
│  │  Input:  Verified GeneratedProblem
│  │  Output: 10-15 test cases including edge cases
│  │
│  ├─ 3d. VALIDATE EXECUTION (Judge0)
│  │  Input:  reference_solution + test_cases
│  │  Action: Run reference solution against Judge0
│  │  Output: { all_passed: bool, failures: [...] }
│  │  On fail: Return to 3c or 3a with failure feedback (max 3 retries)
│  │
│  ├─ 3e. PERSIST TO DB
│  │  Action: Insert into problems + problem_languages + test_cases
│  │          Auto-assign next sequence_number (MAX + 1)
│  │          Link to import_job via import_job_problems junction table
│  │  On IntegrityError(slug): Add to exclude list, retry from 3a
│  │
│  └─ 3f. EMIT PROGRESS EVENT
│     DBOS.set_event("results", [...accumulated results...])
│
└─ Final: Mark ImportJob as completed
```

---

## Tech Stack Additions

| Component | Purpose |
|-----------|---------|
| **pydantic-ai** | Multi-agent orchestration, structured LLM outputs |
| **dbos** | Durable workflow execution, step checkpointing, events |
| *(no new infra)* | DBOS uses your existing Supabase PostgreSQL |

---

## Database Changes

### New Tables

#### `import_jobs`

Tracks user-initiated import requests. This is the **user-facing** record.

```python
class ImportJobStatus(enum.StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ImportJobStatus] = mapped_column(
        Enum(ImportJobStatus), nullable=False, default=ImportJobStatus.QUEUED
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Internal DBOS workflow ID (never exposed to user)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    problems: Mapped[list["ImportJobProblem"]] = relationship(
        back_populates="import_job", cascade="all, delete"
    )

    __table_args__ = (
        Index("ix_import_jobs_user_id", "user_id"),
        Index("ix_import_jobs_status", "status"),
    )
```

#### `import_job_problems`

Junction table linking import jobs to the problems they created.

```python
class ImportJobProblem(Base):
    __tablename__ = "import_job_problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    import_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    import_job: Mapped["ImportJob"] = relationship(back_populates="problems")
    problem: Mapped["Problem"] = relationship()

    __table_args__ = (
        Index("ix_import_job_problems_job_id", "import_job_id"),
        Index("ix_import_job_problems_problem_id", "problem_id"),
        Index("ix_import_job_problems_unique", "import_job_id", "problem_id", unique=True),
    )
```

### Existing Tables (No Changes)

- `problems` — Generated problems saved here, identical to seeded ones
- `problem_languages` — Starter code + reference solutions per language
- `test_cases` — Generated test cases saved here

`UNIQUE(slug)` on `problems` and `UNIQUE(sequence_number)` on `problems` are the existing constraints that protect against duplicates.

---

## Pydantic AI Agent Definitions

### Structured Output Schemas

```python
# ── schemas/import_schemas.py ──

class ImportPlan(BaseModel):
    """Parsed user intent."""
    intent: Literal["pattern", "specific"]
    pattern: str | None = None           # "sliding-window"
    problem_name: str | None = None      # "Median of Two Sorted Arrays"
    leetcode_number: int | None = None   # 4
    count: int = 1
    difficulty: str | None = None        # "easy", "medium", "hard" or None

class GeneratedProblemLanguage(BaseModel):
    """Language-specific code for a generated problem."""
    starter_code: str
    reference_solution: str
    function_signature: dict  # { name, params: [{ name, type }], return_type }

class GeneratedProblemExample(BaseModel):
    """A problem example."""
    input: str
    output: str
    explanation: str | None = None

class GeneratedProblem(BaseModel):
    """Full generated problem matching existing YAML structure."""
    title: str
    slug: str
    difficulty: Literal["easy", "medium", "hard"]
    pattern: list[str]
    description: str
    constraints: list[str]
    examples: list[GeneratedProblemExample]
    languages: dict[str, GeneratedProblemLanguage]  # { "python": { ... } }
    leetcode_no: int | None = None  # LeetCode problem number (if known)
    comparison_strategy: str | None = None  # "exact", "unordered_array", etc.

class GeneratedTestCase(BaseModel):
    """A single test case."""
    input: list[Any]    # Function arguments as array
    expected: Any       # Expected return value

class GeneratedTestCases(BaseModel):
    """Output from test case generator."""
    test_cases: list[GeneratedTestCase]
    edge_cases_covered: list[str]  # Description of edge cases

class VerificationResult(BaseModel):
    """Output from verifier agents."""
    valid: bool
    issues: list[str] = []
    suggestions: list[str] = []

class ExecutionResult(BaseModel):
    """Output from Judge0 execution."""
    all_passed: bool
    total: int
    passed: int
    failures: list[dict] = []  # [{ test_index, input, expected, actual, error }]
```

### Agent Definitions

```python
# ── services/import_agents.py ──

from pydantic_ai import Agent, RunContext

# Dependencies passed to agents via RunContext
@dataclass
class ImportDeps:
    db: AsyncSession
    judge0_client: httpx.AsyncClient

# ─── 1. INTENT PARSER ───
intent_parser_agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=ImportPlan,
    system_prompt="""You parse user requests for importing coding problems.
    Determine if the user wants:
    - A batch of problems by pattern (e.g., "10 sliding window problems")
    - A specific LeetCode problem by name or number (e.g., "LeetCode 4")
    Extract: intent type, pattern/name/number, count, difficulty if specified.
    For pattern names, use kebab-case: "sliding-window", "two-pointers", "dynamic-programming".""",
)

# ─── 2. PROBLEM GENERATOR ───
problem_generator_agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=GeneratedProblem,
    system_prompt="""You generate LeetCode-style coding problems.

    Requirements:
    - Title: Clear, descriptive (e.g., "Sliding Window Maximum")
    - Slug: kebab-case (e.g., "sliding-window-maximum")
    - Description: Clear markdown with bold/code formatting. Include examples inline.
    - Constraints: Realistic bounds matching the problem
    - Examples: 2-3 examples with input, output, and explanation
    - Reference solution: Correct, efficient, idiomatic Python inside class Solution
    - Starter code: class Solution with method signature and `pass`
    - Function signature: { name, params: [{ name, type }], return_type }

    The solution MUST use the `class Solution` pattern:
      class Solution:
          def methodName(self, param1: type1) -> return_type:

    IMPORTANT: Generate problems that are DIFFERENT from the excluded list.""",
)

# ─── 3. PROBLEM VERIFIER ───
problem_verifier_agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=VerificationResult,
    system_prompt="""You verify coding problem quality. Check:
    1. Description is clear, unambiguous, and solvable
    2. Reference solution correctly solves the stated problem
    3. Function signature matches the solution method
    4. Starter code has correct method signature with `pass`
    5. Constraints are realistic and complete
    6. Examples are correct (output matches what the solution would return)
    7. The problem is a legitimate coding interview question

    Be strict. Flag anything that would confuse a solver.""",
)

# ─── 4. TEST CASE GENERATOR ───
test_case_generator_agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=GeneratedTestCases,
    system_prompt="""You generate comprehensive test cases for coding problems.

    For each problem, generate 10-15 test cases covering:
    - Basic cases from the examples
    - Edge cases: empty input, single element, minimum values
    - Boundary cases: maximum constraint values
    - Corner cases specific to the algorithm
    - Cases that commonly trip up incorrect solutions

    Format: input is an array of function arguments, expected is the return value.
    Example: input: [[2,7,11,15], 9], expected: [0,1]

    IMPORTANT: Run through the reference solution mentally to verify each expected value.""",
)
```

---

## DBOS Workflow Implementation

### Workflow Steps

```python
# ── services/import_workflow.py ──

from dbos import DBOS

@DBOS.step()
async def parse_intent(prompt: str) -> ImportPlan:
    """Parse user prompt into structured plan."""
    result = await intent_parser_agent.run(prompt)
    return result.output

@DBOS.step()
async def query_existing_by_pattern(pattern: str) -> list[str]:
    """Query DB for existing problem slugs matching pattern."""
    async with get_db() as db:
        result = await db.execute(
            select(Problem.slug).where(Problem.pattern.contains([pattern]))
        )
        return [row[0] for row in result.fetchall()]

@DBOS.step()
async def query_all_existing_slugs() -> list[str]:
    """Query DB for ALL existing problem slugs (for specific problem imports)."""
    async with get_db() as db:
        result = await db.execute(select(Problem.slug))
        return [row[0] for row in result.fetchall()]

@DBOS.step()
async def generate_problem_step(
    pattern: str,
    exclude_slugs: list[str],
    difficulty: str | None,
    specific_problem: str | None,
) -> GeneratedProblem:
    """Generate a single problem using the LLM agent."""
    if specific_problem:
        prompt = (
            f"Generate the LeetCode problem '{specific_problem}' with full details. "
            f"These slugs already exist, ensure yours is different: {exclude_slugs}"
        )
    else:
        prompt = (
            f"Generate a {difficulty + ' ' if difficulty else ''}{pattern} coding problem. "
            f"It must be DIFFERENT from these existing problems: {exclude_slugs}"
        )
    result = await problem_generator_agent.run(prompt)
    return result.output

@DBOS.step()
async def verify_problem_step(problem: GeneratedProblem) -> VerificationResult:
    """Verify generated problem quality."""
    result = await problem_verifier_agent.run(
        f"Verify this problem:\n{problem.model_dump_json(indent=2)}"
    )
    return result.output

@DBOS.step()
async def regenerate_problem_step(
    problem: GeneratedProblem,
    issues: list[str],
    exclude_slugs: list[str],
) -> GeneratedProblem:
    """Regenerate a problem incorporating verifier feedback."""
    result = await problem_generator_agent.run(
        f"Regenerate this problem, fixing these issues: {issues}\n\n"
        f"Original problem:\n{problem.model_dump_json(indent=2)}\n\n"
        f"Exclude these slugs: {exclude_slugs}"
    )
    return result.output

@DBOS.step()
async def generate_test_cases_step(problem: GeneratedProblem) -> list[GeneratedTestCase]:
    """Generate test cases for a verified problem."""
    result = await test_case_generator_agent.run(
        f"Generate test cases for:\n{problem.model_dump_json(indent=2)}"
    )
    return result.output.test_cases

@DBOS.step()
async def validate_with_judge0_step(
    reference_solution: str,
    function_signature: dict,
    language: str,
    test_cases: list[GeneratedTestCase],
) -> ExecutionResult:
    """Run reference solution against test cases via Judge0."""
    # Uses existing Judge0 integration (wrapper.py + judge0.py)
    # Build the wrapped code + stdin JSON, submit to Judge0, parse results
    ...

@DBOS.step()
async def persist_problem_step(
    problem: GeneratedProblem,
    test_cases: list[GeneratedTestCase],
    import_job_id: uuid.UUID,
) -> str:
    """Save problem to DB and link to import job. Returns problem_id."""
    async with get_db() as db:
        # Get next sequence number
        max_seq_result = await db.execute(select(func.max(Problem.sequence_number)))
        next_seq = (max_seq_result.scalar() or 0) + 1

        # Insert problem (reuse existing seeder logic)
        problem_data = {
            "title": problem.title,
            "sequence_number": next_seq,
            "difficulty": problem.difficulty,
            "pattern": problem.pattern,
            "description": problem.description,
            "constraints": problem.constraints,
            "examples": [e.model_dump() for e in problem.examples],
            "languages": {
                lang: {
                    "starter_code": data.starter_code,
                    "reference_solution": data.reference_solution,
                    "function_signature": data.function_signature,
                }
                for lang, data in problem.languages.items()
            },
            "test_cases": [
                {"input": tc.input, "expected": tc.expected}
                for tc in test_cases
            ],
        }
        db_problem = await insert_problem(db, problem_data)

        # Link to import job
        link = ImportJobProblem(
            import_job_id=import_job_id,
            problem_id=db_problem.id,
        )
        db.add(link)
        await db.commit()
        return str(db_problem.id)

@DBOS.step()
async def update_import_job_status(
    import_job_id: uuid.UUID,
    status: str,
    message: str,
    progress: int | None = None,
    total: int | None = None,
    error: str | None = None,
    completed_at: datetime | None = None,
) -> None:
    """Update the user-facing import job record."""
    async with get_db() as db:
        job = await db.get(ImportJob, import_job_id)
        job.status = ImportJobStatus(status)
        job.message = message
        job.progress = progress
        job.total = total
        job.error = error
        job.completed_at = completed_at
        await db.commit()
```

### Main Workflow

```python
@DBOS.workflow()
async def import_problems_workflow(import_job_id: str, prompt: str) -> None:
    """
    Main orchestration workflow. Durable — resumes from last step on failure.
    Updates import_job record directly (user-facing table, not DBOS events).
    """
    job_id = uuid.UUID(import_job_id)
    MAX_RETRIES = 3

    try:
        # ── Phase 1: Parse intent ──
        await update_import_job_status(job_id, "processing", "Analyzing your request...")
        plan = await parse_intent(prompt)

        total = plan.count
        await update_import_job_status(
            job_id, "processing",
            f"Will generate {total} problem(s)", progress=0, total=total,
        )

        # ── Phase 2: Query existing problems ──
        if plan.intent == "pattern" and plan.pattern:
            exclude_slugs = await query_existing_by_pattern(plan.pattern)
        else:
            exclude_slugs = await query_all_existing_slugs()

        # ── Phase 3: Generate, verify, test, persist each problem ──
        succeeded = 0
        failed = 0
        batch_slugs: list[str] = []

        for i in range(total):
            await update_import_job_status(
                job_id, "processing",
                f"Generating problem {i + 1} of {total}...",
                progress=i, total=total,
            )

            problem = None
            all_excludes = exclude_slugs + batch_slugs

            for attempt in range(MAX_RETRIES):
                try:
                    # 3a. Generate
                    problem = await generate_problem_step(
                        plan.pattern or "",
                        all_excludes,
                        plan.difficulty,
                        plan.problem_name if plan.intent == "specific" else None,
                    )

                    # 3b. Verify
                    await update_import_job_status(
                        job_id, "processing",
                        f"Verifying: {problem.title}",
                        progress=i, total=total,
                    )
                    verification = await verify_problem_step(problem)

                    if not verification.valid:
                        problem = await regenerate_problem_step(
                            problem, verification.issues, all_excludes,
                        )
                        verification = await verify_problem_step(problem)
                        if not verification.valid:
                            continue  # retry outer loop

                    # 3c. Generate test cases
                    await update_import_job_status(
                        job_id, "processing",
                        f"Generating test cases for {problem.title}",
                        progress=i, total=total,
                    )
                    test_cases = await generate_test_cases_step(problem)

                    # 3d. Validate with Judge0
                    await update_import_job_status(
                        job_id, "processing",
                        f"Validating solution for {problem.title}",
                        progress=i, total=total,
                    )
                    python_lang = problem.languages.get("python")
                    if python_lang:
                        execution = await validate_with_judge0_step(
                            python_lang.reference_solution,
                            python_lang.function_signature,
                            "python",
                            test_cases,
                        )
                        if not execution.all_passed:
                            # Add failure context and retry
                            all_excludes.append(problem.slug)
                            continue

                    # 3e. Persist
                    await update_import_job_status(
                        job_id, "processing",
                        f"Saving {problem.title}",
                        progress=i, total=total,
                    )
                    await persist_problem_step(problem, test_cases, job_id)

                    batch_slugs.append(problem.slug)
                    succeeded += 1
                    break  # success, next problem

                except IntegrityError:
                    # Duplicate slug — add to excludes and retry
                    if problem:
                        all_excludes.append(problem.slug)
                    continue

            else:
                # All retries exhausted for this problem
                failed += 1

        # ── Phase 4: Complete ──
        if succeeded > 0:
            await update_import_job_status(
                job_id, "completed",
                f"Imported {succeeded} of {total} problems"
                + (f" ({failed} failed)" if failed else ""),
                progress=total, total=total,
                completed_at=datetime.utcnow(),
            )
        else:
            await update_import_job_status(
                job_id, "failed",
                f"All {total} problems failed to generate",
                progress=0, total=total, error="Generation failed for all problems",
            )

    except Exception as e:
        await update_import_job_status(
            job_id, "failed", f"Workflow error: {str(e)}",
            error=str(e),
        )
        raise  # Re-raise so DBOS marks workflow as failed
```

---

## API Endpoints

### Routes

```python
# ── routes/imports.py ──

router = APIRouter(prefix="/api/import", tags=["import"])

# ─── Start Import ───
@router.post("/")
async def start_import(
    request: ImportRequest,          # { prompt: str }
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a problem import workflow."""

    # Debounce: check for active import with same prompt
    active = await db.execute(
        select(ImportJob).where(
            ImportJob.user_id == user.id,
            ImportJob.prompt == request.prompt,
            ImportJob.status.in_(["queued", "processing"]),
        )
    )
    existing = active.scalar_one_or_none()
    if existing:
        return ImportJobResponse.from_orm(existing)

    # Create import job record
    job = ImportJob(
        user_id=user.id,
        prompt=request.prompt,
        status=ImportJobStatus.QUEUED,
        message="Your request has been accepted",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Start DBOS workflow in background
    handle = await DBOS.start_workflow(
        import_problems_workflow,
        str(job.id),
        request.prompt,
    )

    # Store workflow_id for internal tracking
    job.workflow_id = handle.workflow_id
    await db.commit()

    return ImportJobResponse.from_orm(job)


# ─── Get Import Job Status ───
@router.get("/{import_id}")
async def get_import(
    import_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get import job status with linked problems."""

    job = await db.get(ImportJob, import_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Import job not found")

    # Get linked problems
    problems_result = await db.execute(
        select(Problem)
        .join(ImportJobProblem, Problem.id == ImportJobProblem.problem_id)
        .where(ImportJobProblem.import_job_id == job.id)
        .order_by(Problem.sequence_number)
    )
    problems = problems_result.scalars().all()

    return ImportJobDetailResponse(
        id=job.id,
        prompt=job.prompt,
        status=job.status,
        message=job.message,
        progress=job.progress,
        total=job.total,
        problems=[
            ImportedProblemResponse(
                id=p.id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty,
                pattern=p.pattern,
            )
            for p in problems
        ],
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


# ─── List User's Import Jobs ───
@router.get("/")
async def list_imports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all import jobs for the current user."""

    result = await db.execute(
        select(ImportJob)
        .where(ImportJob.user_id == user.id)
        .order_by(ImportJob.created_at.desc())
    )
    jobs = result.scalars().all()

    return [
        ImportJobSummaryResponse(
            id=j.id,
            prompt=j.prompt,
            status=j.status,
            message=j.message,
            progress=j.progress,
            total=j.total,
            created_at=j.created_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]
```

### Response Schemas

```python
# ── schemas/import_schemas.py ──

class ImportRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)

class ImportedProblemResponse(BaseModel):
    """A problem linked to an import job. Clickable → /problem/:slug"""
    id: UUID
    title: str
    slug: str
    difficulty: str
    pattern: list[str]
    model_config = {"from_attributes": True}

class ImportJobResponse(BaseModel):
    id: UUID
    prompt: str
    status: ImportJobStatus
    message: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class ImportJobDetailResponse(BaseModel):
    """Full import job with linked problems."""
    id: UUID
    prompt: str
    status: ImportJobStatus
    message: str | None
    progress: int | None
    total: int | None
    problems: list[ImportedProblemResponse]  # ← The actual result
    created_at: datetime
    completed_at: datetime | None

class ImportJobSummaryResponse(BaseModel):
    id: UUID
    prompt: str
    status: ImportJobStatus
    message: str | None
    progress: int | None
    total: int | None
    created_at: datetime
    completed_at: datetime | None
```

---

## Frontend Implementation

### New Components

#### Import Button (in Header or Dashboard)

```
[ + Import Problems ]  ← Opens modal
```

#### Import Modal

```
┌──────────────────────────────────────────────────────────────┐
│  Import Problems                                        [X]  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Add 10 sliding window problems                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                               [ Import ]     │
│                                                              │
│  ── Recent Imports ──                                        │
│  ✓ "Add 5 array problems"        5 problems     Jan 25      │
│  ⏳ "Add 10 DP problems"         3/10           Jan 25      │
│  ✗ "Add LeetCode 4"              failed         Jan 24      │
└──────────────────────────────────────────────────────────────┘
```

#### Import Detail View (after clicking an import or while processing)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back                                                      │
│                                                              │
│  "Add 10 sliding window problems"                            │
│  Status: Processing • 3 of 10                                │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  30%              │
│                                                              │
│  Problems:                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ✓ Sliding Window Maximum             Hard      →    │   │  ← Click → /problem/sliding-window-maximum
│  │ ✓ Minimum Size Subarray Sum          Medium    →    │   │
│  │ ✓ Longest Repeating Character        Medium    →    │   │
│  │ ◌ Generating...                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  You can close this — we'll keep processing.                 │
└──────────────────────────────────────────────────────────────┘
```

### Frontend Data Fetching

```typescript
// ── hooks/useImport.ts ──

// Start import
const useStartImport = () =>
  useMutation({
    mutationFn: (prompt: string) =>
      api.post('/api/import', { prompt }),
  })

// Poll import status
const useImportStatus = (importId: string | null) =>
  useQuery({
    queryKey: ['import', importId],
    queryFn: () => api.get(`/api/import/${importId}`),
    enabled: !!importId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed'
        ? false
        : 2000  // Poll every 2 seconds while processing
    },
  })

// List imports
const useImportHistory = () =>
  useQuery({
    queryKey: ['imports'],
    queryFn: () => api.get('/api/import'),
  })
```

---

## Duplicate Prevention

| Layer | What It Catches | Mechanism |
|-------|----------------|-----------|
| `UNIQUE(slug)` on `problems` | Any duplicate slug at insert time | Database constraint |
| Fresh exclusion query | Problems inserted by concurrent workflows | Re-query before each generation |
| Batch exclusion list | Duplicates within same workflow batch | Accumulate slugs in-memory |
| Prompt debounce | Same user submitting same prompt twice | Check for active job with same prompt |
| Retry on `IntegrityError` | Race conditions | Catch error, add to exclude list, regenerate |

Sequence number assignment uses `MAX(sequence_number) + 1` inside the persist step's transaction, protected by Postgres serialization.

---

## Implementation Steps

### Phase 1: Dependencies & Config
1. Add `pydantic-ai` and `dbos` to `pyproject.toml`
2. Configure DBOS to use existing Supabase PostgreSQL
3. Add LLM model configuration (reuse existing litellm config or use pydantic-ai's model config)

### Phase 2: Database Schema
4. Create `ImportJob` and `ImportJobProblem` SQLAlchemy models in `tables.py`
5. Generate Alembic migration for new tables
6. Add response/request schemas in `schemas/import_schemas.py`

### Phase 3: Agent Definitions
7. Create `services/import_agents.py` with all 4 agent definitions
8. Create structured output schemas (`GeneratedProblem`, `VerificationResult`, etc.)
9. Write agent system prompts with examples from existing YAML problems

### Phase 4: Workflow Steps
10. Create `services/import_workflow.py` with all `@DBOS.step()` functions
11. Implement `persist_problem_step` reusing existing `seeder.py` logic
12. Implement `validate_with_judge0_step` reusing existing `judge0.py` + `wrapper.py`
13. Implement main `@DBOS.workflow()` orchestration function

### Phase 5: API Routes
14. Create `routes/imports.py` with POST/GET endpoints
15. Register router in `main.py`
16. Add prompt debounce logic

### Phase 6: Frontend
17. Create import modal component
18. Create import status/detail view component
19. Add polling with `refetchInterval`
20. Add import button to dashboard/header
21. Wire up problem links to existing `/problem/:slug` route

### Phase 7: Testing
22. Unit test each agent with mocked LLM responses
23. Test DBOS workflow with mocked steps
24. Test duplicate prevention (concurrent inserts)
25. Test API endpoints
26. End-to-end test: prompt → problems in DB

---

## Open Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| LLM provider for agents | Anthropic Claude / Google Gemini / OpenAI | Claude Sonnet for generation + verification (quality), Gemini Flash for test case generation (cost) |
| JavaScript support | Generate JS solutions alongside Python | Start with Python only, add JS in Phase 2 |
| Import history UI location | Modal tab / Dedicated page / Dashboard section | Dashboard section + modal for active imports |
| Max problems per import | Unlimited / Capped | Cap at 20 per request to control cost and runtime |
| DBOS tables location | Same database / Separate database | Same Supabase PostgreSQL (simpler, DBOS manages its own tables) |

---

## Review — Questions, Answers & Decisions

The following items were raised during plan review. Each has been resolved with a decision.

### 1. DBOS Complexity vs. Simpler Alternatives

**Concern**: DBOS introduces its own system tables (`dbos_*`) into the Supabase-managed database and adds a non-trivial dependency. The main value — durable resume-from-last-step — may not be critical here since successfully persisted problems survive any crash, and the user can re-import for any remainder.

**Question**: Has `asyncio.create_task()` (or FastAPI `BackgroundTasks`) with direct `import_jobs` table updates been considered as a lighter alternative? If DBOS is preferred, has its async compatibility been verified — specifically, do `@DBOS.workflow()` and `@DBOS.step()` support `async def` functions natively?

**Decision: Start with `asyncio.create_task()` + direct `import_jobs` table updates.** The workflow already writes progress to `import_jobs` after each problem succeeds. If the process dies, successfully persisted problems survive (they're committed to DB). The user can re-submit and we detect "N problems already linked to a prior job with the same prompt" and skip them. DBOS can be added later if the simpler approach proves insufficient. DBOS does support `async def` natively — verified from their docs and examples.

### 2. Sequence Number Race Condition

**Concern**: Two concurrent `persist_problem_step` calls can both read the same `MAX(sequence_number)` value before either commits, violating the `UNIQUE(sequence_number)` constraint.

**Question**: Should we use a PostgreSQL `SEQUENCE` object or `SELECT ... FOR UPDATE`?

**Decision: Use a PostgreSQL `SEQUENCE`.** It's atomic, lock-free, and purpose-built for this:

```sql
CREATE SEQUENCE problems_sequence_number_seq
    START WITH <current max + 1>;
```

Then in the persist step: `nextval('problems_sequence_number_seq')`. If a problem insert fails (e.g., duplicate slug), the sequence number is "burned" — gaps in sequence numbers don't matter. This avoids lock contention entirely. The Alembic migration should initialize the sequence from the current max `sequence_number` in the `problems` table.

### 3. `validate_with_judge0_step` Implementation Details

**Concern**: This is the most critical quality gate and was left as a placeholder.

**Questions & Answers**:

- **Will this reuse `generate_python_wrapper()`?** Yes. The wrapper expects test cases as objects with `.input` (list) and `.expected` (any) attributes. The `GeneratedTestCase` schema stores `input` as `list[Any]` which aligns. We'll create mock test case objects (like the existing `_MockTestCase` in `execution.py:64-69`) from the generated test case data.

- **What if Judge0 is unavailable?** Retry with backoff (3 attempts: 5s, 15s, 30s). If still down, **fail the problem** — not skip. The whole point of this step is validation; skipping it defeats the purpose. The import job continues to the next problem.

- **How are execution errors distinguished?** Judge0 returns distinct status codes already handled in `execution.py:137-152`: status 6 = compilation error, status 11/12/13 = runtime error / time limit / memory limit. The `_parse_execution_results()` function in `execution.py` already maps these. The import workflow can reuse this function directly, passing the problem's `comparison_strategy` so the comparison service (`comparison.py`) applies the correct logic.

### 4. `insert_problem` Interface Compatibility

**Concern**: The `persist_problem_step` dict may not match the existing `seeder.py:insert_problem()` expected format.

**Decision: Write a thin adapter function `generated_problem_to_seed_dict()`.** The seeder expects specific nesting: `languages` as `{ "python": { "starter_code": ..., "reference_solution": ..., "function_signature": ... } }`, `test_cases` as `[{ "input": [...], "expected": ... }]`, and `examples` as a flat list (which the seeder wraps in `{"examples": [...]}`). The adapter converts `GeneratedProblem` + `list[GeneratedTestCase]` into this dict format. This avoids modifying the existing seeder while keeping the contract explicit. It also handles the new `leetcode_no` and `comparison_strategy` fields that `insert_problem()` now accepts via `data.get()`.

### 5. `comparison_strategy` Field

**Concern**: The `problems` table has a `comparison_strategy` column (`exact`, `unordered_array`, `in_place_only`, `in_place_with_length`) used by `comparison.py` at submission time. The `GeneratedProblem` schema did not include this field.

**Decision: The problem generator agent must determine the appropriate `comparison_strategy`.** Add it to the `GeneratedProblem` schema:

```python
class GeneratedProblem(BaseModel):
    ...
    comparison_strategy: str | None = None  # "exact", "unordered_array", etc.
```

The generator agent's system prompt must include guidance:
- `exact` (default): Output must match expected exactly (most problems)
- `unordered_array`: When the problem says "return in any order" (e.g., Two Sum, permutations)
- `in_place_only`: When the problem mutates input in-place and return value is ignored
- `in_place_with_length`: When the problem returns a count `k` and mutates first `k` elements

The verifier agent should also check that the chosen strategy is consistent with the problem description. `NULL` defaults to `exact` in the comparison service, so omitting it is safe as a fallback.

### 6. Rate Limiting & Cost Controls

**Concern**: Each problem requires 4+ LLM calls, potentially many more with retries. No per-user throttling exists.

**Decision**:
- **Hard cap**: 20 problems per import, enforced at the API validation layer
- **Concurrent limit**: Max 3 active import jobs per user (status = `queued` or `processing`)
- **No daily limit** initially — the concurrent job limit naturally throttles
- **Cost tracking**: Log token usage via Pydantic AI's `result.usage()` to structlog. Add an optional `total_tokens` column on `import_jobs` for visibility. Not a blocker for v1.

### 7. Cancel Mechanism

**Concern**: No way for a user to cancel an in-progress import.

**Decision: Yes, add `POST /api/imports/{import_id}/cancel`.** Implementation: set `import_jobs.status = "cancelled"` in DB. The workflow loop checks at the top of each problem iteration:

```python
for i in range(total):
    job = await get_import_job_status(job_id)
    if job.status == ImportJobStatus.CANCELLED:
        break
```

Already-persisted problems from the cancelled batch remain in the DB — they're valid, fully verified problems. The import job shows status "cancelled" with partial results.

### 8. LeetCode-Specific Import Handling

**Concern**: The `intent: "specific"` path for "Add LeetCode 4" has several ambiguities around `leetcode_no` and the `UNIQUE(leetcode_no)` constraint.

**Questions & Answers**:

- **Recreate exact or "inspired by"?** Recreate faithfully from LLM knowledge. These are well-known public problems. Descriptions are generated, not scraped.

- **How is `leetcode_number` mapped?** The intent parser outputs both `leetcode_number: int` and resolves `problem_name: str` (e.g., `4` → `"Median of Two Sorted Arrays"`). Both are passed to the generator. The generator populates `leetcode_no` on the `GeneratedProblem`. Add `leetcode_no: int | None = None` to the `GeneratedProblem` schema.

- **`UNIQUE(leetcode_no)` conflict?** Before generation, query the DB for the existing `leetcode_no`. If it already exists, return early with a clear message: "LeetCode #4 already exists in the system." For pattern-based imports (e.g., "10 sliding window problems"), `leetcode_no` should be populated when the LLM knows the canonical LeetCode number, and `None` otherwise. The `UNIQUE` constraint is nullable, so `NULL` values don't conflict.

### 9. Retry Logic Flow

**Concern**: The nested retry logic is hard to reason about.

**Decision: Flatten into a single loop.** One generate + one verify per attempt:

```python
issues: list[str] = []
for attempt in range(MAX_RETRIES):
    problem = await generate_problem_step(
        ..., previous_issues=issues
    )
    verification = await verify_problem_step(problem)
    if verification.valid:
        break
    issues = verification.issues
else:
    # All retries exhausted — skip this problem
    failed += 1
    continue
```

Clean, predictable, and the `issues` list carries feedback between iterations so the generator improves on each attempt.

### 10. Route Registration Order

**Concern**: `GET /api/import/` (list) and `GET /api/import/{import_id}` (detail) could conflict in FastAPI.

**Decision: Use pluralized list endpoint.** `GET /api/imports` (list, plural) and `GET /api/imports/{import_id}` (detail). Register the list route first. The router prefix becomes `/api/imports`. This avoids the ambiguity entirely and is consistent with REST conventions (`/api/problems`, `/api/submissions`).
