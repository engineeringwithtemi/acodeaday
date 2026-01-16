"""Problem seeding service for loading YAML data into the database."""

from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.db.tables import Difficulty, Language, Problem, ProblemLanguage, TestCase

logger = get_logger(__name__)


def load_problem_yaml(path: Path) -> dict:
    """Load a problem YAML file and return parsed data."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def title_to_slug(title: str) -> str:
    """Convert a problem title to a URL-friendly slug."""
    import re
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def validate_problem_data(data: dict) -> None:
    """
    Validate problem data structure.

    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = [
        "title",
        "sequence_number",
        "difficulty",
        "pattern",
        "description",
        "constraints",
        "examples",
        "languages",
        "test_cases",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate difficulty
    valid_difficulties = [d.value for d in Difficulty]
    if data["difficulty"] not in valid_difficulties:
        raise ValueError(f"Invalid difficulty: {data['difficulty']}. Must be one of {valid_difficulties}")

    # Validate at least one language
    if not data["languages"]:
        raise ValueError("At least one language is required")

    # Validate language keys
    valid_languages = [lang.value for lang in Language]
    for lang_key in data["languages"]:
        if lang_key not in valid_languages:
            raise ValueError(f"Invalid language: {lang_key}. Must be one of {valid_languages}")

    # Validate at least one test case
    if not data["test_cases"]:
        raise ValueError("At least one test case is required")


async def problem_exists(db: AsyncSession, title: str) -> bool:
    """Check if a problem with the given title exists (slug derived from title)."""
    slug = title_to_slug(title)
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    return result.scalar_one_or_none() is not None


async def insert_problem(db: AsyncSession, data: dict) -> Problem:
    """
    Insert a new problem from YAML data.

    Args:
        db: Database session
        data: Parsed YAML data (slug derived from title if not provided)

    Returns:
        Created Problem object
    """
    # Derive slug from title
    slug = title_to_slug(data["title"])

    # Create the problem
    problem = Problem(
        title=data["title"],
        slug=slug,
        description=data["description"],
        difficulty=Difficulty(data["difficulty"]),
        pattern=data["pattern"],
        sequence_number=data["sequence_number"],
        constraints=data["constraints"],
        examples={"examples": data["examples"]},
    )
    db.add(problem)
    await db.flush()  # Get problem.id

    # Create language configs
    for lang_key, lang_data in data["languages"].items():
        problem_lang = ProblemLanguage(
            problem_id=problem.id,
            language=Language(lang_key),
            starter_code=lang_data["starter_code"],
            reference_solution=lang_data["reference_solution"],
            function_signature=lang_data["function_signature"],
        )
        db.add(problem_lang)

    # Create test cases
    for i, tc_data in enumerate(data["test_cases"]):
        test_case = TestCase(
            problem_id=problem.id,
            input=tc_data["input"],
            expected=tc_data["expected"],
            sequence=tc_data.get("sequence", i + 1),
        )
        db.add(test_case)

    logger.info("inserted_problem", slug=slug, title=data["title"])
    return problem


async def upsert_problem(db: AsyncSession, data: dict) -> Problem:
    """
    Insert or update a problem from YAML data.

    If slug exists, updates all fields. Otherwise inserts new.

    Args:
        db: Database session
        data: Parsed YAML data (slug derived from title)

    Returns:
        Created or updated Problem object
    """
    # Derive slug from title
    slug = title_to_slug(data["title"])

    result = await db.execute(select(Problem).where(Problem.slug == slug))
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing problem
        existing.title = data["title"]
        existing.description = data["description"]
        existing.difficulty = Difficulty(data["difficulty"])
        existing.pattern = data["pattern"]
        existing.sequence_number = data["sequence_number"]
        existing.constraints = data["constraints"]
        existing.examples = {"examples": data["examples"]}

        # Delete and recreate languages and test cases
        await db.execute(
            ProblemLanguage.__table__.delete().where(ProblemLanguage.problem_id == existing.id)
        )
        await db.execute(
            TestCase.__table__.delete().where(TestCase.problem_id == existing.id)
        )

        # Recreate language configs
        for lang_key, lang_data in data["languages"].items():
            problem_lang = ProblemLanguage(
                problem_id=existing.id,
                language=Language(lang_key),
                starter_code=lang_data["starter_code"],
                reference_solution=lang_data["reference_solution"],
                function_signature=lang_data["function_signature"],
            )
            db.add(problem_lang)

        # Recreate test cases
        for i, tc_data in enumerate(data["test_cases"]):
            test_case = TestCase(
                problem_id=existing.id,
                input=tc_data["input"],
                expected=tc_data["expected"],
                sequence=tc_data.get("sequence", i + 1),
            )
            db.add(test_case)

        logger.info("updated_problem", slug=slug, title=data["title"])
        return existing

    # Insert new problem
    return await insert_problem(db, data)


async def seed_from_directory(
    db: AsyncSession, data_dir: Path, force: bool = False
) -> tuple[int, int]:
    """
    Seed all YAML files from a directory.

    Args:
        db: Database session
        data_dir: Directory containing YAML files
        force: If True, upsert existing. If False, skip existing.

    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    yaml_files = sorted(data_dir.glob("*.yaml"))
    inserted = 0
    skipped = 0

    for yaml_file in yaml_files:
        if yaml_file.name == "README.md":
            continue

        try:
            data = load_problem_yaml(yaml_file)
            validate_problem_data(data)

            # Derive slug from title for existence check
            slug = title_to_slug(data["title"])
            exists = await problem_exists(db, data["title"])

            if exists and not force:
                logger.info("skipped_existing", slug=slug, file=yaml_file.name)
                skipped += 1
                continue

            if force:
                await upsert_problem(db, data)
            else:
                await insert_problem(db, data)

            inserted += 1

        except Exception as e:
            logger.error("seed_error", file=yaml_file.name, error=str(e))
            raise

    await db.commit()
    return inserted, skipped


def get_next_sequence_number(data_dir: Path) -> int:
    """Get the next available sequence number based on existing files."""
    yaml_files = list(data_dir.glob("*.yaml"))
    if not yaml_files:
        return 1

    max_seq = 0
    for f in yaml_files:
        # Extract sequence from filename like "001-two-sum.yaml"
        try:
            seq = int(f.name.split("-")[0])
            max_seq = max(max_seq, seq)
        except (ValueError, IndexError):
            continue

    return max_seq + 1


def generate_problem_template(title: str, sequence_number: int, languages: list[str]) -> str:
    """
    Generate a YAML template for a new problem.

    Args:
        title: Problem title (e.g., "Two Sum") - slug is derived automatically
        sequence_number: Problem sequence (e.g., 1)
        languages: List of language keys (e.g., ["python"])

    Returns:
        YAML template string
    """
    lang_sections = []
    for lang in languages:
        if lang == "python":
            lang_sections.append(f"""  {lang}:
    starter_code: |
      class Solution:
          def solutionMethod(self, param1: List[int]) -> int:
              pass
    reference_solution: |
      class Solution:
          def solutionMethod(self, param1: List[int]) -> int:
              # TODO: Implement solution
              pass
    function_signature:
      name: solutionMethod
      params:
        - name: param1
          type: "List[int]"
      return_type: int""")
        elif lang == "javascript":
            lang_sections.append(f"""  {lang}:
    starter_code: |
      /**
       * @param {{number[]}} param1
       * @return {{number}}
       */
      var solutionMethod = function(param1) {{

      }};
    reference_solution: |
      var solutionMethod = function(param1) {{
          // TODO: Implement solution
      }};
    function_signature:
      name: solutionMethod
      params:
        - name: param1
          type: "number[]"
      return_type: number""")

    languages_yaml = "\n".join(lang_sections)

    template = f"""title: {title}
sequence_number: {sequence_number}
difficulty: easy  # easy, medium, hard
pattern: array  # hash-map, two-pointers, sliding-window, etc.

description: |
  TODO: Add problem description here.

  You can use markdown formatting.

constraints:
  - "TODO: Add constraints"
  - "1 <= n <= 10^4"

examples:
  - input: "param1 = [1, 2, 3]"
    output: "6"
    explanation: "TODO: Explain the example"

languages:
{languages_yaml}

test_cases:
  - input: [[1, 2, 3]]
    expected: 6
  - input: [[4, 5, 6]]
    expected: 15
  - input: [[10, 20, 30]]
    expected: 60
"""
    return template
