# Adding Problems

This guide shows you how to add new coding problems to acodeaday using the YAML format and seeder CLI.

## Problem File Format

Problems are defined in YAML files located in `backend/data/problems/`.

### File Naming Convention

```
NNN-slug.yaml
```

- `NNN` = 3-digit sequence number (001, 002, etc.)
- `slug` = URL-friendly identifier (two-sum, valid-palindrome, etc.)

Examples:
- `001-two-sum.yaml`
- `002-best-time-to-buy-and-sell-stock.yaml`
- `015-valid-palindrome.yaml`

## YAML Schema

```yaml
title: Two Sum
sequence_number: 1
difficulty: easy  # easy | medium | hard
pattern: hash-map  # Algorithm pattern tag

description: |
  Given an array of integers `nums` and an integer `target`, return indices
  of the two numbers such that they add up to `target`.

  You may assume that each input would have exactly one solution, and you
  may not use the same element twice.

constraints:
  - "2 <= nums.length <= 10^4"
  - "-10^9 <= nums[i] <= 10^9"
  - "-10^9 <= target <= 10^9"
  - "Only one valid answer exists."

examples:
  - input: "nums = [2,7,11,15], target = 9"
    output: "[0,1]"
    explanation: "Because nums[0] + nums[1] == 9, we return [0, 1]."
  - input: "nums = [3,2,4], target = 6"
    output: "[1,2]"

languages:
  python:
    starter_code: |
      class Solution:
          def twoSum(self, nums: List[int], target: int) -> List[int]:
              pass

    reference_solution: |
      class Solution:
          def twoSum(self, nums: List[int], target: int) -> List[int]:
              seen = {}
              for i, num in enumerate(nums):
                  complement = target - num
                  if complement in seen:
                      return [seen[complement], i]
                  seen[num] = i
              return []

    function_signature:
      name: twoSum
      params:
        - name: nums
          type: "List[int]"
        - name: target
          type: int
      return_type: "List[int]"

test_cases:
  - input: [[2, 7, 11, 15], 9]
    expected: [0, 1]
  - input: [[3, 2, 4], 6]
    expected: [1, 2]
  - input: [[3, 3], 6]
    expected: [0, 1]
  - input: [[1, 5, 3, 7, 2, 8], 10]
    expected: [2, 4]
  - input: [[0, 4, 3, 0], 0]
    expected: [0, 3]
```

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Display title of the problem |
| `sequence_number` | integer | Yes | Order in problem list |
| `difficulty` | enum | Yes | `easy`, `medium`, or `hard` |
| `pattern` | string | Yes | Algorithm pattern (hash-map, two-pointers, etc.) |
| `description` | string | Yes | Problem statement (supports Markdown) |
| `constraints` | array | Yes | List of constraint strings |
| `examples` | array | Yes | Example inputs/outputs shown to user |
| `languages` | object | Yes | Language-specific code (Python, JavaScript, etc.) |
| `test_cases` | array | Yes | Test inputs and expected outputs |

### Language Configuration

Each language needs:

```yaml
languages:
  python:
    starter_code: |
      # Code shown to user in editor

    reference_solution: |
      # Official solution for validation

    function_signature:
      name: functionName
      params:
        - name: paramName
          type: "Type"
      return_type: "ReturnType"
```

### Test Cases

```yaml
test_cases:
  - input: [arg1, arg2, arg3]  # JSON array of function arguments
    expected: result           # Expected output (any JSON type)
```

**Important:**
- First 3 test cases are shown as examples in the problem description
- All test cases are run during submission
- Input is array of function arguments in order
- Expected can be any JSON type (array, object, number, string, boolean)

## Creating New Problems

### Method 1: CLI Tool (Recommended)

Use the seeder CLI to generate a template:

```bash
cd backend

# Create new problem with auto-detected sequence number
uv run python scripts/seed_problems.py new my-problem-slug --lang python

# Specify sequence number manually
uv run python scripts/seed_problems.py new my-problem-slug --seq 100 --lang python

# Multiple languages
uv run python scripts/seed_problems.py new my-problem --lang python --lang javascript
```

This creates `backend/data/problems/NNN-my-problem-slug.yaml` with template.

### Method 2: Manual Creation

1. Copy an existing problem YAML
2. Rename with next sequence number
3. Update all fields
4. Validate YAML syntax

```bash
# Copy template
cp data/problems/001-two-sum.yaml data/problems/016-my-problem.yaml

# Edit the file
code data/problems/016-my-problem.yaml
```

## Seeding to Database

### Seed All Problems

```bash
uv run python scripts/seed_problems.py seed
```

This:
- Reads all YAML files in `data/problems/`
- Inserts problems, test cases, and language code
- **Skips existing problems** (safe to run multiple times)

### Seed Specific Problem

```bash
uv run python scripts/seed_problems.py seed 016-my-problem.yaml
```

### Force Update Existing

```bash
# WARNING: Overwrites existing problem data
uv run python scripts/seed_problems.py seed --force
```

## Best Practices

### 1. Clear Problem Statements

- Use Markdown for formatting
- Include code examples in backticks
- Explain edge cases
- Keep descriptions concise

```yaml
description: |
  Given an array of integers `nums`, return the **maximum** sum of any
  contiguous subarray.

  **Example:**
  ```
  Input: nums = [-2,1,-3,4,-1,2,1,-5,4]
  Output: 6
  Explanation: [4,-1,2,1] has the largest sum of 6
  ```
```

### 2. Comprehensive Test Cases

Include tests for:
- Basic cases
- Edge cases (empty, single element, etc.)
- Large inputs
- Negative numbers
- Duplicates

```yaml
test_cases:
  - input: [[1, 2, 3]]           # Basic
    expected: 6
  - input: [[]]                  # Edge: empty
    expected: 0
  - input: [[5]]                 # Edge: single
    expected: 5
  - input: [[-1, -2, -3]]        # Edge: all negative
    expected: -1
  - input: [[1, 1, 1, 1]]        # Duplicates
    expected: 4
```

### 3. Realistic Constraints

Base constraints on LeetCode standards:

```yaml
constraints:
  - "1 <= nums.length <= 10^5"
  - "-10^4 <= nums[i] <= 10^4"
```

### 4. Pattern Tagging

Use consistent pattern names:
- `array`
- `hash-map`
- `two-pointers`
- `sliding-window`
- `binary-search`
- `dynamic-programming`
- `tree`
- `graph`
- `backtracking`

### 5. Function Signatures

Match LeetCode conventions:

```yaml
# Python
function_signature:
  name: twoSum
  params:
    - name: nums
      type: "List[int]"
    - name: target
      type: int
  return_type: "List[int]"

# JavaScript (when implemented)
function_signature:
  name: twoSum
  params:
    - name: nums
      type: "number[]"
    - name: target
      type: number
  return_type: "number[]"
```

## Common Patterns

### Array Problem

```yaml
title: Maximum Subarray
difficulty: medium
pattern: dynamic-programming
function_signature:
  name: maxSubArray
  params:
    - name: nums
      type: "List[int]"
  return_type: int
```

### String Problem

```yaml
title: Valid Palindrome
difficulty: easy
pattern: two-pointers
function_signature:
  name: isPalindrome
  params:
    - name: s
      type: str
  return_type: bool
```

### Tree Problem

```yaml
title: Maximum Depth of Binary Tree
difficulty: easy
pattern: tree
function_signature:
  name: maxDepth
  params:
    - name: root
      type: "Optional[TreeNode]"
  return_type: int
```

## Validating Problems

### Test Locally

1. Seed the problem:
   ```bash
   uv run python scripts/seed_problems.py seed 016-my-problem.yaml
   ```

2. Start backend:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

3. Test via API:
   ```bash
   curl http://localhost:8000/api/problems/my-problem
   ```

4. Test in frontend:
   - Open problem in browser
   - Verify description renders correctly
   - Run code against test cases
   - Submit solution

### Validate YAML Syntax

```bash
# Install yamllint
pip install yamllint

# Validate file
yamllint data/problems/016-my-problem.yaml
```

## Troubleshooting

### "Sequence number already exists"

Each sequence number must be unique. Use the next available:

```bash
# Find highest sequence
ls backend/data/problems/ | sort -n | tail -1
# Use next number
```

### "Invalid function signature"

Ensure params and return_type are valid Python types:
- `int`, `str`, `bool`, `float`
- `List[int]`, `Dict[str, int]`, `Set[str]`
- `Optional[TreeNode]`, `Optional[ListNode]`

### Test cases failing

- Verify `input` is array of arguments in correct order
- Check `expected` matches reference solution output
- Test reference solution manually

### Slug conflicts

Slugs are auto-generated from title. If conflict, manually set:

```yaml
slug: my-unique-slug  # Optional override
```

## Adding Support for New Languages

For a comprehensive guide on adding support for new programming languages (JavaScript, Java, Go, etc.), see [Adding Languages](/guide/adding-languages).

## Next Steps

- [Spaced Repetition](/guide/spaced-repetition) - Understand the algorithm
- [Backend Setup](/guide/backend-setup) - Set up the seeder
- [Database Setup](/guide/database-setup) - Configure the database
