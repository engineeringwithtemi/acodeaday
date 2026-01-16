# Problem Data Files

This directory contains YAML files for coding problems.

## File Format

Each problem is defined in a YAML file with the naming convention: `NNN-slug.yaml`
- `NNN` = 3-digit sequence number (001, 002, etc.)
- `slug` = URL-friendly identifier (two-sum, best-time-to-buy-stock, etc.)

## Creating a New Problem

Use the seeder CLI to scaffold a new problem:

```bash
cd backend
uv run python scripts/seed_problems.py new my-problem-slug --lang python
```

This will:
1. Auto-detect the next sequence number
2. Create a template file with all required fields
3. Pre-fill language sections for specified languages

## Seeding to Database

```bash
# Seed all problems (skips existing)
uv run python scripts/seed_problems.py seed

# Seed specific file
uv run python scripts/seed_problems.py seed 001-two-sum.yaml

# Force update existing problems
uv run python scripts/seed_problems.py seed --force
```

## YAML Schema

```yaml
title: Two Sum                    # Display title (slug derived automatically)
sequence_number: 1                # Order in problem list (unique)
difficulty: easy                  # easy | medium | hard
pattern: hash-map                 # Algorithm pattern tag

description: |                    # Problem description (markdown)
  Given an array of integers...

constraints:                      # List of constraints
  - "2 <= nums.length <= 10^4"
  - "-10^9 <= nums[i] <= 10^9"

examples:                         # List of examples shown in problem
  - input: "nums = [2,7,11,15], target = 9"
    output: "[0,1]"
    explanation: "Optional explanation"

languages:                        # Language-specific code
  python:
    starter_code: |               # Code shown to user
      class Solution:
          def twoSum(self, nums: List[int], target: int) -> List[int]:
              pass
    reference_solution: |         # Official solution
      class Solution:
          def twoSum(self, nums: List[int], target: int) -> List[int]:
              seen = {}
              for i, num in enumerate(nums):
                  if target - num in seen:
                      return [seen[target - num], i]
                  seen[num] = i
              return []
    function_signature:           # Metadata for wrapper generation
      name: twoSum
      params:
        - name: nums
          type: "List[int]"
        - name: target
          type: int
      return_type: "List[int]"

test_cases:                       # Test inputs/outputs
  - input: [[2, 7, 11, 15], 9]    # Arguments as JSON array
    expected: [0, 1]              # Expected output (any JSON type)
  - input: [[3, 2, 4], 6]
    expected: [1, 2]
```

## Notes

- `slug` is automatically derived from the title (e.g., "Two Sum" → "two-sum")
- `input` is a JSON array of function arguments
- `expected` can be any JSON type (array, object, string, number, boolean)
- Problems are seeded with **skip on existing** by default to protect user progress data
