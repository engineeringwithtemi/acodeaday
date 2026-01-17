#!/usr/bin/env python3
"""
Problem seeder CLI for acodeaday.

Usage:
    # Scaffold a new problem file (slug is auto-generated from title)
    uv run python scripts/seed_problems.py new "Two Sum" --lang python
    uv run python scripts/seed_problems.py new "Contains Duplicate" --lang python --lang javascript

    # Seed all YAML files to database (skips existing)
    uv run python scripts/seed_problems.py seed

    # Seed specific file
    uv run python scripts/seed_problems.py seed 001-two-sum.yaml

    # Force update existing problems
    uv run python scripts/seed_problems.py seed --force
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection import AsyncSessionLocal
from app.services.seeder import (
    generate_problem_template,
    get_next_sequence_number,
    load_problem_yaml,
    problem_exists,
    seed_from_directory,
    title_to_slug,
    upsert_problem,
    validate_problem_data,
)

# Default data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "problems"


async def cmd_new(args: argparse.Namespace) -> int:
    """Create a new problem YAML template."""
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Get next sequence number
    seq = get_next_sequence_number(DATA_DIR)

    # Generate slug from title
    slug = title_to_slug(args.title)

    # Generate filename
    filename = f"{seq:03d}-{slug}.yaml"
    filepath = DATA_DIR / filename

    if filepath.exists():
        print(f"Error: File already exists: {filepath}")
        return 1

    # Generate template
    template = generate_problem_template(args.title, seq, args.lang)

    # Write file
    filepath.write_text(template)
    print(f"Created: {filepath}")
    print(f"Title: {args.title}")
    print(f"Slug: {slug}")
    print(f"Sequence number: {seq}")
    print(f"Languages: {', '.join(args.lang)}")
    print("\nNext steps:")
    print(f"  1. Edit {filepath} to fill in problem details")
    print(f"  2. Run: uv run python scripts/seed_problems.py seed {filename}")

    return 0


async def cmd_seed(args: argparse.Namespace) -> int:
    """Seed problems to database."""
    if not DATA_DIR.exists():
        print(f"Error: Data directory not found: {DATA_DIR}")
        print("Run 'new' command first to create a problem.")
        return 1

    async with AsyncSessionLocal() as db:
        if args.file:
            # Seed specific file
            filepath = DATA_DIR / args.file
            if not filepath.exists():
                print(f"Error: File not found: {filepath}")
                return 1

            data = load_problem_yaml(filepath)
            validate_problem_data(data)

            exists = await problem_exists(db, data["slug"])
            if exists and not args.force:
                print(f"Skipped: {data['slug']} (already exists, use --force to update)")
                return 0

            await upsert_problem(db, data)
            await db.commit()
            action = "Updated" if exists else "Inserted"
            print(f"{action}: {data['slug']}")
        else:
            # Seed all files
            yaml_files = list(DATA_DIR.glob("*.yaml"))
            if not yaml_files:
                print(f"No YAML files found in {DATA_DIR}")
                return 0

            print(f"Found {len(yaml_files)} problem files")
            inserted, skipped = await seed_from_directory(db, DATA_DIR, force=args.force)

            print(f"\nResults:")
            print(f"  Inserted: {inserted}")
            print(f"  Skipped:  {skipped}")

            if skipped > 0 and not args.force:
                print("\nTip: Use --force to update existing problems")

    return 0


async def cmd_list(args: argparse.Namespace) -> int:
    """List all problem files."""
    if not DATA_DIR.exists():
        print(f"No data directory: {DATA_DIR}")
        return 0

    yaml_files = sorted(DATA_DIR.glob("*.yaml"))
    if not yaml_files:
        print("No problem files found.")
        return 0

    print(f"Problem files in {DATA_DIR}:\n")
    for f in yaml_files:
        try:
            data = load_problem_yaml(f)
            print(f"  {f.name}")
            print(f"    Title: {data.get('title', 'N/A')}")
            print(f"    Difficulty: {data.get('difficulty', 'N/A')}")
            print(f"    Pattern: {data.get('pattern', 'N/A')}")
            print()
        except Exception as e:
            print(f"  {f.name} (ERROR: {e})")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Problem seeder for acodeaday",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'new' command
    new_parser = subparsers.add_parser("new", help="Create a new problem template")
    new_parser.add_argument("title", help="Problem title (e.g., \"Two Sum\") - slug is auto-generated")
    new_parser.add_argument(
        "--lang",
        action="append",
        default=[],
        choices=["python", "javascript"],
        help="Language to include (can repeat)",
    )

    # 'seed' command
    seed_parser = subparsers.add_parser("seed", help="Seed problems to database")
    seed_parser.add_argument("file", nargs="?", help="Specific file to seed (optional)")
    seed_parser.add_argument(
        "--force", "-f", action="store_true", help="Update existing problems"
    )

    # 'list' command
    subparsers.add_parser("list", help="List all problem files")

    args = parser.parse_args()

    # Default to python if no languages specified
    if args.command == "new" and not args.lang:
        args.lang = ["python"]

    # Run async command
    if args.command == "new":
        return asyncio.run(cmd_new(args))
    elif args.command == "seed":
        return asyncio.run(cmd_seed(args))
    elif args.command == "list":
        return asyncio.run(cmd_list(args))


if __name__ == "__main__":
    sys.exit(main())
