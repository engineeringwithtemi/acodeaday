# Implementation Plan: AI-Powered Problem Import

## Overview

A feature that allows users to import coding problems via natural language prompts. A multi-agent pipeline generates, verifies, and persists problems using Pydantic AI for agent orchestration and `asyncio.create_task()` for background execution. All generated problems are first-class citizens — identical to manually seeded ones in the `problems` table.

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
                        Starts background task (asyncio.create_task)
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
ORCHESTRATOR (asyncio background task)
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
│  └─ 3f. UPDATE PROGRESS
│     Update import_jobs table with progress/message
│
└─ Final: Mark ImportJob as completed
```

---

## Tech Stack Additions

| Component | Purpose |
|-----------|---------|
| **pydantic-ai** | Multi-agent orchestration, structured LLM outputs |
| *(no new infra)* | Background tasks via `asyncio.create_task()` with `import_jobs` table for state tracking |

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
    # No slug — derived at persist time via title_to_slug(title)
    difficulty: Literal["easy", "medium", "hard"]
    pattern: list[str]
    description: str
    constraints: list[str]
    examples: list[GeneratedProblemExample]
    languages: dict[str, GeneratedProblemLanguage]  # { "python": { ... } }
    leetcode_no: int  # REQUIRED — every problem must have a LeetCode number
    comparison_strategy: str | None = None  # "exact", "unordered_array" (v1 only)

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

## Workflow Implementation

### Workflow Steps

```python
# ── services/import_workflow.py ──
# No DBOS — uses asyncio.create_task() with direct DB state tracking.

async def parse_intent(prompt: str) -> ImportPlan:
    """Parse user prompt into structured plan."""
    result = await intent_parser_agent.run(prompt)
    return result.output

async def query_existing_by_pattern(pattern: str) -> list[str]:
    """Query DB for existing problem slugs matching pattern."""
    async with get_db() as db:
        result = await db.execute(
            select(Problem.slug).where(Problem.pattern.contains([pattern]))
        )
        return [row[0] for row in result.fetchall()]

async def query_existing_leetcode_nos() -> list[int]:
    """Query DB for ALL existing leetcode_no values to prevent duplicates."""
    async with get_db() as db:
        result = await db.execute(
            select(Problem.leetcode_no).where(Problem.leetcode_no.isnot(None))
        )
        return [row[0] for row in result.fetchall()]

async def generate_problem_step(
    pattern: str,
    exclude_slugs: list[str],
    exclude_leetcode_nos: list[int],
    difficulty: str | None,
    specific_problem: str | None,
    leetcode_number: int | None,
) -> GeneratedProblem:
    """Generate a single problem using the LLM agent."""
    if specific_problem:
        prompt = (
            f"Generate LeetCode problem #{leetcode_number} ('{specific_problem}') with full details. "
            f"The leetcode_no must be {leetcode_number}."
        )
    else:
        prompt = (
            f"Generate a {difficulty + ' ' if difficulty else ''}{pattern} coding problem "
            f"from LeetCode. It must be a REAL LeetCode problem with the correct leetcode_no. "
            f"Do NOT use any of these LeetCode numbers (already in system): {exclude_leetcode_nos}. "
            f"Do NOT generate problems with these titles/slugs: {exclude_slugs}"
        )
    result = await problem_generator_agent.run(prompt)
    return result.output

async def verify_problem_step(problem: GeneratedProblem) -> VerificationResult:
    """Verify generated problem quality."""
    result = await problem_verifier_agent.run(
        f"Verify this problem:\n{problem.model_dump_json(indent=2)}"
    )
    return result.output

async def refine_problem_step(
    problem: GeneratedProblem,
    issues: list[str],
    exclude_slugs: list[str],
    exclude_leetcode_nos: list[int],
) -> GeneratedProblem:
    """Refine a problem incorporating verifier feedback. Preserves good parts."""
    result = await problem_generator_agent.run(
        f"Fix these issues with the problem below: {issues}\n\n"
        f"Original problem:\n{problem.model_dump_json(indent=2)}\n\n"
        f"Preserve what's correct. Only fix what's broken.\n"
        f"Excluded slugs: {exclude_slugs}\n"
        f"Excluded leetcode_nos: {exclude_leetcode_nos}"
    )
    return result.output

async def generate_test_cases_step(problem: GeneratedProblem) -> list[GeneratedTestCase]:
    """Generate test cases for a verified problem."""
    result = await test_case_generator_agent.run(
        f"Generate test cases for:\n{problem.model_dump_json(indent=2)}"
    )
    return result.output.test_cases
async def validate_with_judge0_step(
    reference_solution: str,
    function_signature: dict,
    language: str,
    test_cases: list[GeneratedTestCase],
    comparison_strategy: str | None,
) -> ExecutionResult:
    """Run reference solution against test cases via Judge0.
    Uses services/execution_validator.py (extracted shared logic).
    Calls judge0 via asyncio.to_thread() to avoid blocking the event loop.
    """
    ...

async def persist_problem_step(
    problem: GeneratedProblem,
    test_cases: list[GeneratedTestCase],
    import_job_id: uuid.UUID,
) -> str:
    """Save problem to DB and link to import job. Returns problem_id.
    Inserts directly — does NOT use seeder's insert_problem().
    Derives slug from title via title_to_slug() for consistency."""
    from app.services.seeder import title_to_slug

    async with get_db() as db:
        slug = title_to_slug(problem.title)

        # Retry on IntegrityError (sequence_number or slug conflict)
        for attempt in range(3):
            try:
                max_seq_result = await db.execute(select(func.max(Problem.sequence_number)))
                next_seq = (max_seq_result.scalar() or 0) + 1

                db_problem = Problem(
                    title=problem.title,
                    slug=slug,
                    description=problem.description,
                    difficulty=Difficulty(problem.difficulty),
                    pattern=problem.pattern,
                    sequence_number=next_seq,
                    leetcode_no=problem.leetcode_no,
                    constraints=problem.constraints,
                    examples={"examples": [e.model_dump() for e in problem.examples]},
                    comparison_strategy=problem.comparison_strategy,
                )
                db.add(db_problem)
                await db.flush()
                break
            except IntegrityError:
                await db.rollback()
                continue

        # Create language configs
        for lang_key, lang_data in problem.languages.items():
            db.add(ProblemLanguage(
                problem_id=db_problem.id,
                language=Language(lang_key),
                starter_code=lang_data.starter_code,
                reference_solution=lang_data.reference_solution,
                function_signature=lang_data.function_signature,
            ))

        # Create test cases
        for i, tc in enumerate(test_cases):
            db.add(TestCase(
                problem_id=db_problem.id,
                input=tc.input,
                expected=tc.expected,
                sequence=i + 1,
            ))

        # Link to import job
        db.add(ImportJobProblem(
            import_job_id=import_job_id,
            problem_id=db_problem.id,
        ))

        await db.commit()
        return str(db_problem.id)

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
async def import_problems_workflow(import_job_id: str, prompt: str) -> None:
    """
    Main orchestration workflow. Runs as asyncio.create_task().
    Updates import_jobs table directly for user-facing status.
    No DBOS — no pause/resume. On crash, startup recovery marks stuck jobs as failed.
    """
    job_id = uuid.UUID(import_job_id)
    MAX_RETRIES = 3

    try:
        # ── Phase 1: Parse intent ──
        await update_import_job_status(job_id, "processing", "Analyzing your request...")
        plan = await parse_intent(prompt)

        # For specific LeetCode imports, check if it already exists
        if plan.intent == "specific" and plan.leetcode_number:
            async with get_db() as db:
                existing = await db.execute(
                    select(Problem).where(Problem.leetcode_no == plan.leetcode_number)
                )
                if existing.scalar_one_or_none():
                    await update_import_job_status(
                        job_id, "failed",
                        f"LeetCode #{plan.leetcode_number} already exists in the system.",
                        error="duplicate",
                    )
                    return

        total = plan.count
        await update_import_job_status(
            job_id, "processing",
            f"Will generate {total} problem(s)", progress=0, total=total,
        )

        # ── Phase 2: Query existing problems for exclusion ──
        if plan.intent == "pattern" and plan.pattern:
            exclude_slugs = await query_existing_by_pattern(plan.pattern)
        else:
            exclude_slugs = []

        exclude_leetcode_nos = await query_existing_leetcode_nos()

        # ── Phase 3: Generate, verify, test, persist each problem ──
        succeeded = 0
        failed = 0
        batch_leetcode_nos: list[int] = []

        for i in range(total):
            # ── Check for cancellation ──
            async with get_db() as db:
                job = await db.get(ImportJob, job_id)
                if job.status == ImportJobStatus.CANCELLED:
                    break

            await update_import_job_status(
                job_id, "processing",
                f"Generating problem {i + 1} of {total}...",
                progress=i, total=total,
            )

            all_exclude_slugs = exclude_slugs[:]
            all_exclude_nos = exclude_leetcode_nos + batch_leetcode_nos

            # ── Retry loop with refinement ──
            previous_problem: GeneratedProblem | None = None
            issues: list[str] = []

            for attempt in range(MAX_RETRIES):
                try:
                    # 3a. Generate (or refine)
                    if previous_problem and issues:
                        problem = await refine_problem_step(
                            previous_problem, issues, all_exclude_slugs, all_exclude_nos,
                        )
                    else:
                        problem = await generate_problem_step(
                            plan.pattern or "",
                            all_exclude_slugs,
                            all_exclude_nos,
                            plan.difficulty,
                            plan.problem_name if plan.intent == "specific" else None,
                            plan.leetcode_number if plan.intent == "specific" else None,
                        )

                    # 3b. Verify
                    await update_import_job_status(
                        job_id, "processing",
                        f"Verifying: {problem.title}",
                        progress=i, total=total,
                    )
                    verification = await verify_problem_step(problem)

                    if not verification.valid:
                        previous_problem = problem
                        issues = verification.issues
                        continue  # retry with refinement

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
                            problem.comparison_strategy,
                        )
                        if not execution.all_passed:
                            previous_problem = problem
                            issues = [f"Judge0 validation failed: {execution.failures}"]
                            continue

                    # 3e. Persist (inserts directly, not via seeder)
                    await update_import_job_status(
                        job_id, "processing",
                        f"Saving {problem.title}",
                        progress=i, total=total,
                    )
                    await persist_problem_step(problem, test_cases, job_id)

                    batch_leetcode_nos.append(problem.leetcode_no)
                    succeeded += 1
                    break  # success, next problem

                except IntegrityError:
                    # Duplicate slug or leetcode_no — add to excludes and retry fresh
                    if problem:
                        all_exclude_nos.append(problem.leetcode_no)
                    previous_problem = None
                    issues = []
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
```

---

## API Endpoints

### Routes

```python
# ── routes/imports.py ──

router = APIRouter(prefix="/api/imports", tags=["imports"])

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

    # Start background task (asyncio, not DBOS)
    import asyncio
    asyncio.create_task(
        import_problems_workflow(str(job.id), request.prompt)
    )

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
1. Add `pydantic-ai` to `pyproject.toml`
2. Add LLM model configuration (reuse existing litellm config or use pydantic-ai's model config)

### Phase 2: Database Schema
4. Create `ImportJob` and `ImportJobProblem` SQLAlchemy models in `tables.py`
5. Generate Alembic migration for new tables
6. Add response/request schemas in `schemas/import_schemas.py`

### Phase 3: Agent Definitions
7. Create `services/import_agents.py` with all 4 agent definitions
8. Create structured output schemas (`GeneratedProblem`, `VerificationResult`, etc.)
9. Write agent system prompts with examples from existing YAML problems

### Phase 4: Workflow & Services
10. Create `services/import_workflow.py` with all step functions
11. Implement `persist_problem_step` with direct DB insertion (not seeder)
12. Create `services/execution_validator.py` — extract shared parse-and-compare logic from `routes/execution.py`
13. Add `judge0.async_execute_code()` or wrap sync call with `asyncio.to_thread()`
14. Implement `validate_with_judge0_step` using the extracted validator
15. Implement main `import_problems_workflow()` orchestration function
16. Add startup recovery: mark stuck "processing" jobs as "failed" on app boot

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
23. Test workflow orchestration with mocked steps
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
| Background execution | DBOS / Temporal / asyncio.create_task | `asyncio.create_task()` — see Build vs Buy analysis below |

---

## Build vs Buy: Job Tracking & Durable Execution

### Options Evaluated

We evaluated four approaches for background workflow execution:

| Option | Infrastructure | Code Overhead | Crash Recovery | Verdict |
|--------|---------------|---------------|----------------|---------|
| **Custom** (`asyncio.create_task()` + `import_jobs` table) | None — just our existing Postgres | ~100 lines | Startup recovery marks stuck jobs "failed"; user re-submits | **Selected for v1** |
| **DBOS** (via Pydantic AI integration) | DBOS system tables in Postgres (`dbos` schema) | ~100 lines (neutral — removes startup recovery, adds init/decorators) | Automatic resume from last completed step | Strong option, but adds complexity |
| **Temporal** | Separate multi-component server (frontend, matching, history, worker) | ~100+ additional lines + rearchitect into 2 services | Full replay-based recovery | Overkill |
| **Prefect** | Prefect server or Prefect Cloud | Flow/task decorators + server config | Task-level retry and recovery | Designed for data pipelines, not API background tasks |

**Temporal and Prefect rejected immediately.** Temporal requires running a separate multi-component server and rearchitecting into two services (API server + Temporal worker). Prefect requires its own server/cloud and is designed for data pipelines, not background API tasks. Both are heavy infrastructure for a simple background import job.

### Custom vs DBOS: Detailed Comparison

#### Code Overhead (roughly neutral)

| Component | Custom | DBOS |
|-----------|--------|------|
| `import_jobs` + `import_job_problems` tables | ~50 lines | ~50 lines (still needed) |
| `update_import_job_status()` | ~15 lines | ~15 lines (still needed) |
| Startup recovery | ~20 lines | 0 (DBOS handles) |
| Cancel endpoint | ~15 lines | ~15 lines (cooperative either way) |
| DBOS init + config | 0 | ~10 lines |
| `@DBOS.workflow()` + `@DBOS.step()` + `DBOSAgent` | 0 | ~10 lines |
| New dependency | 0 | `dbos` library |
| System tables in Postgres | 0 | `dbos.workflow_status`, `dbos.operation_outputs`, `dbos.events` |

DBOS removes ~20 lines of startup recovery code but adds ~20 lines of initialization and decorators. Net code difference: **~0 lines.**

#### The Dual-State Problem (DBOS weakness)

With DBOS, we'd have **two state tracking systems**:

1. **DBOS system tables** (`dbos.workflow_status`, `dbos.operation_outputs`) — for durability and crash recovery
2. **Our `import_jobs` table** — for user-facing API queries (list by user, filter by status, link to problems)

We cannot drop our `import_jobs` table because:
- DBOS doesn't provide user-scoped workflow queries
- We need `import_job_problems` junction table for linking problems to imports
- Our API response schemas are our own, not DBOS's internal format

Maintaining two systems tracking the same workflow state is **more complex** than either system alone. They must stay in sync, and discrepancies would create confusing bugs.

#### Crash Recovery: How Often Does It Matter?

| Scenario | Probability per Import | Impact Without DBOS | Impact With DBOS |
|----------|----------------------|---------------------|-----------------|
| Deploy during import | ~1-2% (15 min window / 24h × ~2 deploys/day) | Already-persisted problems survive. Job marked "failed". User re-submits, skips duplicates. ~$0.01-0.05 in wasted LLM calls. | Automatic resume from last step. Seamless. |
| OOM kill | Very low (no large data in memory) | Same as deploy | Same benefit |
| Unhandled exception | Near zero (top-level try/catch) | Caught and handled | Same |

The crash scenario is rare (~1-2% of imports), and when it occurs, our custom approach handles it gracefully:
- Each problem is committed individually, so partial progress survives
- Startup recovery marks the stuck job as `"failed"` with message `"Interrupted — please retry"`
- Re-submission detects already-persisted problems via `UNIQUE(slug)` and `UNIQUE(leetcode_no)` and skips them

User experience on crash: *"Your import was interrupted. We saved 7 of 10 problems. Please retry for the remaining 3."*

#### DBOS Determinism Constraint

DBOS replays workflows from the beginning on recovery, checking Postgres for cached step outputs at each step. This requires the workflow to be **deterministic** — same steps in same order on every execution. Our workflow has a subtlety: the "query existing problems for exclusion" step reads from the DB. Between original execution and replay, another workflow might have persisted new problems, changing the result. We'd need to make this a DBOS step so the original result is cached during replay, which means understanding DBOS's replay semantics deeply and designing around them.

#### Migration Path (trivial either direction)

If we later decide DBOS is worth adding:
1. `pip install pydantic-ai[dbos]`
2. Add `DBOS.launch()` to app startup
3. Add `@DBOS.workflow()` to `import_problems_workflow()`
4. Add `@DBOS.step()` to each step function
5. Remove startup recovery code

Total: ~20 lines of changes. The workflow logic, agent definitions, and DB schema remain identical. The hard work is the same regardless of execution strategy.

### Decision: Custom for v1

**`asyncio.create_task()` + `import_jobs` table + startup recovery.**

Our custom approach **is** the DBOS pattern, just simpler: we checkpoint each problem by committing individually, we track state in `import_jobs`, and we recover stuck jobs on startup. The only gap vs DBOS is step-level replay — but our idempotent re-submission achieves the same end result (user gets all their problems).

The marginal benefit of automatic resume on the ~1-2% of imports affected by crashes does not justify:
- A new dependency on a relatively young library
- Dual-state complexity (DBOS tables + our `import_jobs` table)
- Determinism constraints on workflow logic
- Additional system tables in our Postgres

If crash recovery proves important in production (e.g., we're deploying much more frequently or imports are much longer), adding DBOS is a ~20-line migration.

---

## Review — Critical Analysis & Decisions

### 1. DBOS Complexity vs. Simpler Alternatives

**Concern**: DBOS adds system tables and a dependency. `asyncio.create_task()` could be lighter.

**Analysis**: See the **"Build vs Buy: Job Tracking & Durable Execution"** section above for the full comparative analysis.

**Decision: Use `asyncio.create_task()` + a startup recovery mechanism.**
- On app startup, query `import_jobs` for records stuck in `"processing"` that haven't been updated recently.
- Mark them as `"failed"` with message `"Interrupted — please retry"`.
- Since each problem is committed to DB individually, the already-persisted problems survive. If the user re-submits the same prompt, the workflow detects existing problems via `UNIQUE(slug)` / `UNIQUE(leetcode_no)` and skips them.
- Migrate to DBOS is a ~20-line change if crash recovery proves important in production.

### 2. Sequence Number Race Condition

**Concern**: `MAX(sequence_number) + 1` isn't safe under concurrency. Suggested PG SEQUENCE.

**Analysis**: The concern is valid, but a PG SEQUENCE introduces a **coordination problem with YAML seeding.** Existing problems are seeded with hardcoded sequence numbers (001–153 in filenames). If the sequence starts at 154 but someone later seeds YAML file `154-new-problem.yaml`, the sequence and the seeded data collide. Keeping the sequence in sync with two different insertion paths (YAML seeding and import workflow) is fragile.

**Decision: Use `MAX(sequence_number) + 1` with retry on `IntegrityError`.** This is the same pattern we already use for duplicate slugs. If two concurrent inserts race on the same sequence number, one gets an `IntegrityError`, retries with a fresh `MAX + 1`, and succeeds. No new infrastructure, no coordination with the seeding path, and the race is extremely unlikely in practice (how often will two imports persist at the exact same instant?).

```python
for attempt in range(3):
    try:
        max_seq = await db.execute(select(func.max(Problem.sequence_number)))
        next_seq = (max_seq.scalar() or 0) + 1
        problem.sequence_number = next_seq
        db.add(problem)
        await db.flush()
        break
    except IntegrityError:
        await db.rollback()
        continue
```

### 3. `validate_with_judge0_step` Implementation Details

**Concern**: Placeholder implementation, questions about wrapper compatibility and error handling.

**Analysis**: Three issues the reviewer raised, plus one they missed:

1. **Wrapper compatibility**: `generate_python_wrapper()` in `wrapper.py:69-75` builds test case data from `tc.input` (list) and `tc.expected`. It uses `repr()` to serialize into the wrapper source code (`wrapper.py:86`). `GeneratedTestCase.input: list[Any]` aligns — `repr()` handles all JSON-compatible types (int, float, str, bool, None, list, dict) correctly.

2. **Judge0 unavailable**: Retry 3x with backoff, then **fail the problem** and continue to the next. Agreed.

3. **Error distinction**: Judge0 status codes (6=compile, 11/12/13=runtime/TLE/MLE) are already handled in `execution.py`. However, `_parse_execution_results()` is a **private function** in `routes/execution.py` (underscore prefix). It's coupled to the HTTP route layer — it returns `TestResult` Pydantic schemas for API responses. The import workflow doesn't need HTTP response schemas.

4. **Issue the reviewer missed**: `judge0.execute_code()` uses `httpx.Client()` (synchronous) — see `judge0.py:64`. This blocks the event loop. In the import workflow (which runs inside `asyncio.create_task()`), this would block other async tasks. We need an `async` version using `httpx.AsyncClient()` or run the sync call in a thread executor.

**Decision: Extract shared validation logic into `services/execution_validator.py`.**
- Move the core parse-and-compare logic out of the private route function into a reusable service.
- Both the route layer and the import workflow call this service.
- Create `judge0.async_execute_code()` using `httpx.AsyncClient` for the import workflow, or wrap the sync call with `asyncio.to_thread()`.

### 4. `insert_problem` Interface Compatibility

**Concern**: The seeder's expected dict format may not match.

**Analysis**: The reviewer is right there's a format mismatch, but there's a **deeper issue they didn't catch**: `seeder.py:93` derives the slug internally via `title_to_slug(data["title"])`. It **ignores any slug in the data dict.** Meanwhile, the import workflow uses the agent-generated slug for deduplication throughout the pipeline (exclude lists, `IntegrityError` handling). If `title_to_slug("Sliding Window Maximum")` produces `"sliding-window-maximum"` but the agent generated `slug: "sliding-window-max"`, the slug stored in DB differs from what the workflow thinks it is. Subsequent deduplication checks would fail to find the problem.

**Decision: Don't use the seeder's `insert_problem()`. Insert directly in the persist step.** The persist step builds the `Problem`, `ProblemLanguage`, and `TestCase` objects itself — it's not much code, and we maintain full control over the slug. We reuse `title_to_slug()` from the seeder as a utility to GENERATE the slug (rather than trusting the LLM's slug), ensuring consistency with existing problems.

```python
from app.services.seeder import title_to_slug

async def persist_problem(db, problem: GeneratedProblem, test_cases: list[GeneratedTestCase], import_job_id):
    slug = title_to_slug(problem.title)  # Derive slug deterministically, don't trust LLM
    # ... insert Problem, ProblemLanguage, TestCase directly ...
```

This means the `slug` field on `GeneratedProblem` is **unused** — we always derive it from the title. The agent doesn't need to generate slugs at all. Remove `slug` from the schema and derive it at persist time.

### 5. `comparison_strategy` Field

**Concern**: The generator agent should determine the comparison strategy.

**Analysis**: The concern is valid, but the answer of "let the agent determine all 4 strategies" is **too optimistic for v1.** Looking at the actual code:

- `in_place_only` expects the wrapper to return `{"mutated_input": [...], "return_value": ...}` — but the current wrapper (`wrapper.py:103`) just returns `solution.func(*test["input"])`. It does NOT capture mutations to the input array. For in-place problems, **the wrapper itself would need modification** to snapshot the input before and after execution.
- `in_place_with_length` has the same issue plus additional logic for `first k elements`.

Asking the LLM to pick `in_place_only` is meaningless if the wrapper can't execute it. Generated problems using these strategies would pass Judge0 validation (because the reference solution runs against itself), but **fail at user submission time** when the comparison service tries to compare in-place outputs that the wrapper doesn't capture.

**Decision: Restrict v1 to `exact` and `unordered_array` only.** The generator prompt should:
- Default to `exact` (NULL) for most problems
- Use `unordered_array` when the problem description says "return in any order" or output order is undefined
- **Never generate** in-place mutation problems until the wrapper supports capturing mutations

Add a validation check in the persist step: reject any problem with `comparison_strategy` set to `in_place_only` or `in_place_with_length`.

### 6. Rate Limiting & Cost Controls

**Concern**: 40+ LLM calls per batch, no throttling.

**Analysis**: The concern is valid. The numbers:
- 10 problems × (1 generate + 1 verify + 1 test cases + 1 Judge0 validation) = 40 LLM calls minimum
- With retries: could be 60–80 calls
- At ~$0.003–0.01 per call (Sonnet): $0.12–0.80 per import
- At 20 problems max: up to $1.60 per import

The 3 concurrent job limit means one user could trigger $4.80 in parallel. That's manageable, but the reviewer didn't ask the real question: **is this feature for all users or admin-only?**

**Decision:**
- **Hard cap**: 20 problems per import, enforced at API validation
- **Concurrent limit**: Max 3 active import jobs per user
- **Feature access**: For v1, available to all authenticated users. Add admin-only restriction if cost becomes a concern. This is a product decision we can revisit.
- **Cost tracking**: Log token usage per agent call via structlog. Not a blocker for v1, but implement from the start since Pydantic AI's `result.usage()` makes it trivial.

### 7. Cancel Mechanism

**Concern**: No cancel endpoint.

**Analysis**: Valid concern. With `asyncio.create_task()`, the cancel is **cooperative** — we set a DB flag, the task checks it at the top of each iteration. If the task is mid-LLM-call (which can take 30+ seconds), it won't cancel until the call returns. This is acceptable UX — the user clicks cancel, sees "cancelling...", and within a minute the status flips to "cancelled".

One edge case: if the process crashed and the job is stuck in "processing", the cancel endpoint should still work — the startup recovery mechanism (from Decision #1) will handle it.

**Decision: Yes, add `POST /api/imports/{import_id}/cancel`.** The workflow checks `import_jobs.status` at the top of each problem iteration. Already-persisted problems survive. The cancel is cooperative, not instant — document this in the API response.

### 8. LeetCode-Specific Import Handling

**Concern**: Ambiguities around `leetcode_no` and `UNIQUE` constraint.

**Analysis**: `leetcode_no` is **mandatory** for all generated problems. Every problem in the system must map to a real LeetCode problem number. This means:

1. The generator agent must always output a valid `leetcode_no`.
2. For `intent: "specific"` (e.g., "Add LeetCode 4") — the number is known upfront.
3. For `intent: "pattern"` (e.g., "10 sliding window problems") — the agent must identify real LeetCode problems that match the pattern and output their correct numbers.

The `UNIQUE(leetcode_no)` constraint means we must check for conflicts before persisting. Two scenarios:

- **Conflict with existing seeded problem**: LeetCode #3 (Longest Substring) is already seeded. If the agent tries to generate it again, the persist step catches the `IntegrityError` and skips it.
- **Conflict within same batch**: Agent generates two problems that both claim `leetcode_no: 567`. The second fails on insert.

In both cases, the agent needs the existing `leetcode_no` values in its exclusion context.

**Decision:**
- `leetcode_no` is a **required field** on `GeneratedProblem` (not optional).
- Before generation, query ALL existing `leetcode_no` values from DB and pass them to the agent as an exclusion list alongside slug exclusions.
- For `intent: "specific"`: Check if `leetcode_no` already exists BEFORE starting generation. If yes, return immediately: `"LeetCode #4 already exists in the system."`
- For `intent: "pattern"`: Agent must identify real LeetCode problems and provide correct numbers. The exclusion list prevents duplicates. On `IntegrityError` for `leetcode_no`, add to exclusion list and retry.
- The verifier agent should sanity-check that the `leetcode_no` is plausible for the given problem title (e.g., "Two Sum" = 1, not 999).

### 9. Retry Logic Flow

**Concern**: Nested retry is hard to reason about.

**Analysis**: Agreed, flatten it. But the reviewer's flattened version generates a **completely new** problem each attempt. This wastes the good parts of the previous attempt. If the verifier says "the constraint bounds are wrong but everything else is fine," regenerating from scratch throws away a good description, solution, and examples.

Better approach: **pass the previous problem AND issues for refinement**, not just issues:

```python
previous_problem: GeneratedProblem | None = None
issues: list[str] = []

for attempt in range(MAX_RETRIES):
    if previous_problem and issues:
        # Refine the previous attempt
        problem = await refine_problem_step(previous_problem, issues, exclude_slugs)
    else:
        # Fresh generation
        problem = await generate_problem_step(pattern, exclude_slugs, ...)

    verification = await verify_problem_step(problem)
    if verification.valid:
        break

    previous_problem = problem
    issues = verification.issues
else:
    failed += 1
    continue
```

This way the generator can fix specific issues ("constraint bounds wrong", "example output incorrect") without discarding the rest. If the problem is fundamentally flawed (e.g., "this isn't actually a sliding window problem"), the refinement prompt should handle that too — the agent has enough context to decide whether to patch or start over.

### 10. Route Registration Order

**Concern**: `GET /api/import/` and `GET /api/import/{import_id}` could conflict.

**Analysis**: Minor concern, trivial fix. Use `/api/imports` (plural) for the router prefix. List = `GET /api/imports`, Detail = `GET /api/imports/{import_id}`. Consistent with existing routes (`/api/problems`, `/api/submissions`).

**Decision: Router prefix = `/api/imports`.** Register list before detail. No ambiguity.

---

## Experiment Plan: Validate Before Building

Five focused spikes to prove the approach works before committing to the full implementation. Each spike is isolated, testable, and answers a specific architectural question. If any spike fails, we stop and re-evaluate before wasting effort on the rest.

### Prerequisites

```bash
# 1. Install pydantic-ai (add to pyproject.toml)
uv add pydantic-ai

# 2. Ensure test infrastructure is running
docker compose --profile test up -d postgres-test   # Test DB on :54325
docker compose up -d judge0-server judge0-workers judge0-db judge0-redis  # Judge0 stack

# 3. Set LLM API key (for agent spikes)
export ANTHROPIC_API_KEY=sk-ant-...   # or whichever provider
```

All experiment code goes in `backend/tests/experiments/` — isolated from production code. Nothing from this directory ships. Each spike has a `test_spike_*.py` file that can be run independently.

---

### Spike 1: Pydantic AI Structured Output Quality

**Question**: Can Pydantic AI reliably produce a `GeneratedProblem` that matches our schema, has valid code, and correct `leetcode_no`?

**What to build** (`tests/experiments/test_spike_structured_output.py`):
```python
# 1. Define GeneratedProblem schema (copy from plan)
# 2. Create a minimal problem_generator agent with output_type=GeneratedProblem
# 3. Call it 3 times with different prompts:
#    - "Generate LeetCode #1 (Two Sum)" → verify leetcode_no=1
#    - "Generate a sliding window problem" → verify pattern contains "sliding-window"
#    - "Generate a medium difficulty tree problem" → verify difficulty="medium"
# 4. For each output, assert:
#    - All required fields are present and valid types
#    - leetcode_no is a positive integer
#    - languages["python"].reference_solution contains "class Solution"
#    - languages["python"].starter_code contains "pass"
#    - function_signature has name, params, return_type
#    - examples has at least 2 entries
#    - constraints is non-empty
```

**Success criteria**:
- 3/3 outputs parse into `GeneratedProblem` without validation errors
- `leetcode_no` is correct for the specific request (Two Sum = 1)
- Reference solution syntax is valid Python (compile check)

**Failure action**: If structured output is unreliable, we may need to switch models, add retry logic, or simplify the schema.

**What this does NOT test**: Verifier quality, test case quality, Judge0 execution. Those are separate spikes.

---

### Spike 2: Background Task + DB State Tracking

**Question**: Does `asyncio.create_task()` work correctly with our async SQLAlchemy session factory? Can we update `import_jobs` from a background task while the API serves status polls?

**What to build**:

1. **Migration** (`alembic revision`): Add `import_jobs` and `import_job_problems` tables exactly as specified in the plan. This is real — it ships. Run it against the test DB.

2. **Test file** (`tests/experiments/test_spike_background_task.py`):
```python
# 1. Create an ImportJob record via direct DB insert
# 2. Start a fake background task (asyncio.create_task) that:
#    - Sleeps 0.5s
#    - Updates import_jobs.status to "processing", message to "Working..."
#    - Sleeps 0.5s
#    - Updates import_jobs.status to "completed"
# 3. While the task runs, poll import_jobs via a second DB session
#    and verify the status transitions: queued → processing → completed
# 4. Verify the background task uses its OWN db session from AsyncSessionLocal
#    (not the request's session — that's the key isolation question)
```

3. **Startup recovery test** (`tests/experiments/test_spike_startup_recovery.py`):
```python
# 1. Insert an ImportJob with status="processing", updated_at=10 minutes ago
# 2. Call the startup recovery function
# 3. Assert status changed to "failed", message contains "Interrupted"
# 4. Insert an ImportJob with status="processing", updated_at=1 minute ago
# 5. Call startup recovery again
# 6. Assert status is STILL "processing" (not stale enough to mark failed)
```

**Success criteria**:
- Background task can read/write `import_jobs` via its own `AsyncSessionLocal()` session
- No session conflicts with the request-scoped session
- Status transitions are visible to concurrent readers
- Startup recovery correctly identifies stale vs active jobs

**Failure action**: If session isolation doesn't work, we need a different DB session strategy for background tasks (e.g., a dedicated session factory, or running the workflow in a separate process via `multiprocessing`).

---

### Spike 3: Judge0 Validates AI-Generated Code

**Question**: Can AI-generated reference solutions run through our existing wrapper + Judge0 pipeline? Does `asyncio.to_thread()` work for the sync Judge0 client?

**What to build** (`tests/experiments/test_spike_judge0_validation.py`):
```python
# 1. Hardcode a known-good GeneratedProblem (Two Sum, from Spike 1 output or manually crafted)
# 2. Hardcode matching test cases: [{"input": [[2,7,11,15], 9], "expected": [0,1]}, ...]
# 3. Use existing generate_python_wrapper() to wrap the reference solution
# 4. Call Judge0 via asyncio.to_thread(judge0_service.execute_code, ...)
# 5. Parse the stdout JSON result
# 6. Assert all test cases pass
#
# Also test a FAILING case:
# 7. Modify the reference solution to return wrong answer
# 8. Run through Judge0
# 9. Assert at least one test case fails
```

**This spike requires Judge0 running locally** (`docker compose up judge0-server judge0-workers`).

**Success criteria**:
- `generate_python_wrapper()` works with AI-generated function signatures and test cases
- `asyncio.to_thread(judge0_service.execute_code, ...)` doesn't block or deadlock
- JSON output from Judge0 parses correctly
- Correct solution passes, incorrect solution fails

**Failure action**: If the wrapper can't handle AI-generated code format, we need adapter logic between `GeneratedProblem` and the wrapper's expected input format.

---

### Spike 4: End-to-End Single Problem (The Big One)

**Question**: Can we go from prompt → generate → verify → test cases → Judge0 → persist → query back via existing API?

**What to build** (`tests/experiments/test_spike_e2e_single.py`):
```python
# This spike chains Spikes 1-3 together for ONE problem.
#
# 1. Call intent_parser_agent with "Add LeetCode 1"
#    Assert: intent="specific", leetcode_number=1
#
# 2. Call problem_generator_agent with the parsed intent
#    Assert: GeneratedProblem with leetcode_no=1, title contains "Two Sum"
#
# 3. Call problem_verifier_agent with the generated problem
#    Assert: valid=True (or if not, log the issues for manual review)
#
# 4. Call test_case_generator_agent with the verified problem
#    Assert: ≥10 test cases, each has input (list) and expected (value)
#
# 5. Run reference solution through Judge0 with generated test cases
#    Assert: all_passed=True
#
# 6. Persist to test DB:
#    - Insert Problem (sequence_number = MAX + 1)
#    - Insert ProblemLanguage
#    - Insert TestCases
#    - Insert ImportJob + ImportJobProblem link
#    Assert: no IntegrityError, problem has valid slug
#
# 7. Query back via existing API:
#    GET /api/problems/{slug} with auth headers
#    Assert: returns the problem with starter_code, test_cases, etc.
#    Assert: response schema matches ProblemDetailSchema exactly
#
# 8. (Optional) Submit the reference solution via POST /api/submit
#    Assert: all test cases pass, submission recorded
```

**Success criteria**:
- Full pipeline completes without errors for 1 problem
- Persisted problem is queryable via existing API
- Response matches existing problem schema (no missing fields)
- (Bonus) Submitting the reference solution passes all tests

**Failure action**: Depends on which step fails. The isolated spikes (1-3) should have already caught most issues, so failures here are likely in the persist/query integration.

---

### Spike 5: Regression Check

**Question**: Do the new `import_jobs` / `import_job_problems` tables and migration break anything?

**What to build**:
```bash
# No new test code — just run the existing test suite against the
# DB that now has the new tables from Spike 2's migration.

# 1. Run the full existing test suite:
uv run pytest tests/ -v --ignore=tests/experiments/

# 2. Specifically verify:
#    - test_routes_problems.py: problem listing/detail still works
#    - test_routes_execution.py: code execution still works
#    - test_routes_progress.py: spaced repetition still works
#    - test_routes_submissions.py: submission history still works
#    - test_comparison.py: comparison service still works
```

**Success criteria**: All existing tests pass with zero changes. The new migration adds tables but doesn't modify existing ones, so this should be a formality — but verify anyway.

**Failure action**: If any existing test breaks, the migration touched something it shouldn't have. Fix the migration before proceeding.

---

### Execution Order & Dependencies

```
Spike 1 (Structured Output)     ──┐
Spike 2 (Background Task + DB)  ──┼── can run in parallel (independent)
                                   │
Spike 3 (Judge0 Validation)     ──┘
         │
         ▼
Spike 4 (End-to-End)           ── depends on all three above
         │
         ▼
Spike 5 (Regression)           ── depends on Spike 2 (needs migration applied)
```

- **Spikes 1, 2, and 3 are independent** — run them in parallel to save time
- **Spike 4 chains them together** — only start once all three pass
- **Spike 5 runs after Spike 2** — needs the migration applied

### Estimated Effort

| Spike | Code to Write | External Dependencies | Approximate LLM Cost |
|-------|--------------|----------------------|---------------------|
| 1. Structured Output | ~80 lines | Anthropic API key | ~$0.05 (3 agent calls) |
| 2. Background Task | ~120 lines + migration | Test Postgres | $0 (no LLM) |
| 3. Judge0 Validation | ~60 lines | Judge0 running locally | $0 (no LLM) |
| 4. End-to-End | ~150 lines | All of the above | ~$0.10 (6 agent calls) |
| 5. Regression | 0 lines (run existing tests) | Test Postgres | $0 |

Total: ~410 lines of throwaway test code, ~$0.15 in LLM costs.

### Go / No-Go Decision

After all spikes pass:

| Question | Where Answered | Go Criteria |
|----------|---------------|-------------|
| Can Pydantic AI produce valid problems? | Spike 1 | ≥2/3 outputs valid without retry |
| Does background DB state tracking work? | Spike 2 | Status transitions visible to concurrent readers |
| Can Judge0 run AI-generated code? | Spike 3 | Correct solution passes, wrong solution fails |
| Does the full pipeline work end-to-end? | Spike 4 | Problem persisted and queryable via existing API |
| Do existing features still work? | Spike 5 | All existing tests pass |

If ALL five pass → proceed with full implementation.
If Spike 1 fails → re-evaluate LLM model or schema complexity.
If Spike 2 fails → re-evaluate session management or consider process-based execution.
If Spike 3 fails → re-evaluate wrapper compatibility.
If Spike 4 fails → identify which integration point broke and fix.
If Spike 5 fails → fix migration before any implementation work.
