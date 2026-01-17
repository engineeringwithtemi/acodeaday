# Adding Language Support

This guide explains how to add support for a new programming language to acodeaday. Currently, the platform supports Python, with infrastructure ready for JavaScript and other languages.

## Overview

Adding a new language requires changes in three areas:

1. **Backend**: Code wrapper generator and Judge0 language mapping
2. **Problem Data**: Language-specific starter code and solutions
3. **Frontend**: Language selector and Monaco Editor configuration

## Step 1: Backend - Judge0 Language Mapping

First, add the new language to the Judge0 language map.

### Find the Judge0 Language ID

Judge0 supports 60+ languages. Find your language ID:

```bash
# List all supported languages
curl http://localhost:2358/languages
```

Common language IDs:
| Language | ID |
|----------|-----|
| Python 3 | 71 |
| JavaScript (Node.js) | 63 |
| TypeScript | 74 |
| Java | 62 |
| C++ | 54 |
| Go | 60 |
| Rust | 73 |
| Ruby | 72 |
| C# | 51 |

### Update the Language Map

Edit `backend/app/services/judge0.py`:

```python
# Language IDs for Judge0
LANGUAGE_MAP = {
    "python": 71,      # Python 3
    "javascript": 63,  # JavaScript (Node.js)
    "java": 62,        # Java (OpenJDK 13)
    "cpp": 54,         # C++ (GCC 9)
    "go": 60,          # Go (1.13)
}
```

## Step 2: Backend - Code Wrapper Generator

The wrapper generator wraps user code with a test harness that:
1. Runs the user's function against test cases
2. Captures stdout/stderr
3. Outputs results as JSON

### Create a New Wrapper Function

Edit `backend/app/services/wrapper.py` to add a generator for your language.

#### Example: JavaScript Wrapper

```python
def generate_javascript_wrapper(
    user_code: str,
    test_cases: list[TestCase],
    function_name: str,
    early_exit: bool = False,
) -> str:
    """Generate JavaScript wrapper code for Judge0 execution."""

    if not function_name.isidentifier():
        raise ValueError(f"Invalid function name: {function_name}")

    test_cases_json = json.dumps([
        {
            "input": tc.input if isinstance(tc.input, list) else [tc.input],
            "expected": tc.expected,
        }
        for tc in test_cases
    ])

    wrapper = f'''
{user_code}

const testCases = {test_cases_json};
const results = [];

for (let i = 0; i < testCases.length; i++) {{
    const test = testCases[i];
    let stdout = '';

    // Capture console.log output
    const originalLog = console.log;
    console.log = (...args) => {{
        stdout += args.join(' ') + '\\n';
    }};

    try {{
        const result = {function_name}(...test.input);
        const passed = JSON.stringify(result) === JSON.stringify(test.expected);

        results.push({{
            test_number: i + 1,
            passed: passed,
            input: test.input,
            output: result,
            expected: test.expected,
            stdout: stdout || null
        }});

        if ({str(early_exit).lower()} && !passed) break;

    }} catch (e) {{
        results.push({{
            test_number: i + 1,
            passed: false,
            input: test.input,
            error: e.message,
            error_type: e.name,
            expected: test.expected,
            stdout: stdout || null
        }});

        if ({str(early_exit).lower()}) break;
    }}

    console.log = originalLog;
}}

console.log(JSON.stringify(results));
'''
    return wrapper
```

#### Example: Java Wrapper

```python
def generate_java_wrapper(
    user_code: str,
    test_cases: list[TestCase],
    function_name: str,
    early_exit: bool = False,
) -> str:
    """Generate Java wrapper code for Judge0 execution."""

    test_cases_json = json.dumps([
        {
            "input": tc.input if isinstance(tc.input, list) else [tc.input],
            "expected": tc.expected,
        }
        for tc in test_cases
    ])

    # Java requires a Main class with main method
    wrapper = f'''
import java.util.*;
import com.google.gson.Gson;

{user_code}

public class Main {{
    public static void main(String[] args) {{
        Gson gson = new Gson();
        String testCasesJson = "{test_cases_json.replace('"', '\\"')}";
        // ... test execution logic
    }}
}}
'''
    return wrapper
```

### Update the Wrapper Dispatcher

Add your new wrapper to the `SUPPORTED_LANGUAGES` list and `get_wrapper_for_language()` function in `backend/app/services/wrapper.py`:

```python
# Supported languages for code execution
SUPPORTED_LANGUAGES = ["python", "javascript", "java"]  # Add your language here

def get_wrapper_for_language(language: str) -> Callable:
    """Get the appropriate wrapper generator function for a language."""
    wrappers = {
        "python": generate_python_wrapper,
        "javascript": generate_javascript_wrapper,  # Add when implemented
        "java": generate_java_wrapper,              # Add when implemented
    }

    language_lower = language.lower()
    if language_lower not in wrappers:
        supported = list(wrappers.keys())
        raise ValueError(f"Unsupported language: {language}. Supported: {supported}")

    return wrappers[language_lower]


def get_supported_languages() -> list[str]:
    """Get list of supported programming languages."""
    return SUPPORTED_LANGUAGES.copy()
```

## Step 3: Problem Data - YAML Configuration

Add language-specific code to problem YAML files.

### Update Problem YAML

Edit files in `backend/data/problems/`:

```yaml
title: Two Sum
sequence_number: 1
difficulty: easy
pattern: hash-map

description: |
  Given an array of integers...

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
                  if target - num in seen:
                      return [seen[target - num], i]
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

  javascript:
    starter_code: |
      function twoSum(nums, target) {
          // Write your code here
      }

    reference_solution: |
      function twoSum(nums, target) {
          const seen = {};
          for (let i = 0; i < nums.length; i++) {
              const complement = target - nums[i];
              if (complement in seen) {
                  return [seen[complement], i];
              }
              seen[nums[i]] = i;
          }
          return [];
      }

    function_signature:
      name: twoSum
      params:
        - name: nums
          type: "number[]"
        - name: target
          type: number
      return_type: "number[]"

  java:
    starter_code: |
      class Solution {
          public int[] twoSum(int[] nums, int target) {
              // Write your code here
              return new int[]{};
          }
      }

    reference_solution: |
      class Solution {
          public int[] twoSum(int[] nums, int target) {
              Map<Integer, Integer> seen = new HashMap<>();
              for (int i = 0; i < nums.length; i++) {
                  int complement = target - nums[i];
                  if (seen.containsKey(complement)) {
                      return new int[]{seen.get(complement), i};
                  }
                  seen.put(nums[i], i);
              }
              return new int[]{};
          }
      }

    function_signature:
      name: twoSum
      params:
        - name: nums
          type: "int[]"
        - name: target
          type: int
      return_type: "int[]"

test_cases:
  - input: [[2, 7, 11, 15], 9]
    expected: [0, 1]
  # ... more test cases
```

### Re-seed Problems

After updating YAML files:

```bash
cd backend
uv run python scripts/seed_problems.py seed --force
```

## Step 4: Frontend - Language Selector

Update the frontend to support the new language. The frontend fetches available languages from the backend API.

### Backend Endpoint

The backend exposes an endpoint to get supported languages:

```bash
GET /api/languages
```

Response:
```json
{
  "languages": ["python", "javascript"]
}
```

This endpoint uses `get_supported_languages()` from `wrapper.py`.

### Frontend Language Selector

The `LanguageSelector` component fetches available languages from the backend and allows users to switch between them:

```typescript
// frontend/src/components/LanguageSelector.tsx
interface LanguageSelectorProps {
  value: string;
  onChange: (lang: string) => void;
  availableLanguages: string[];
}

export function LanguageSelector({ value, onChange, availableLanguages }: LanguageSelectorProps) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {availableLanguages.map((lang) => (
        <option key={lang} value={lang}>
          {lang.charAt(0).toUpperCase() + lang.slice(1)}
        </option>
      ))}
    </select>
  );
}
```

### Configure Monaco Editor

Monaco Editor has built-in support for most languages. Update the editor configuration:

```typescript
<Editor
  language={selectedLanguage}  // 'python', 'javascript', 'java', etc.
  value={code}
  onChange={setCode}
  options={{
    minimap: { enabled: false },
    fontSize: 14,
  }}
/>
```

For languages that need special configuration, you may need to register custom language definitions.

## Step 5: Testing

### Verify Solutions Locally

Use the `verify_solutions.py` script to test reference solutions:

```bash
cd backend

# Verify all problems using local Python execution (default)
uv run python scripts/verify_solutions.py

# Verify all problems using Judge0 API
uv run python scripts/verify_solutions.py --mode judge0

# Verify a specific problem
uv run python scripts/verify_solutions.py 001-two-sum.yaml

# Verbose output (show all test cases)
uv run python scripts/verify_solutions.py --verbose

# Combine options
uv run python scripts/verify_solutions.py --mode judge0 --verbose 001-two-sum.yaml
```

### Test with Judge0 Directly

```bash
# Submit to Judge0 directly
curl -X POST http://localhost:2358/submissions?wait=true \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "console.log(JSON.stringify([{test_number: 1, passed: true}]))",
    "language_id": 63
  }'
```

### Test via API

```bash
# Test code execution via the backend API
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "problem_slug": "two-sum",
    "language": "javascript",
    "code": "function twoSum(nums, target) { ... }"
  }'
```

## Language-Specific Considerations

### Python
- Uses `class Solution` pattern (LeetCode style)
- Type hints use `List[int]`, `Optional[T]`, etc.
- Common imports added automatically: `List`, `Optional`, `Dict`, etc.

### JavaScript
- Uses standalone function pattern
- No class wrapper needed
- Type annotations in function_signature use TypeScript syntax for documentation

### Java
- Uses `class Solution` pattern
- Requires proper class structure
- May need additional imports (ArrayList, HashMap, etc.)
- Output comparison must handle array equality

### C++
- Uses `class Solution` pattern
- Requires includes for containers (`vector`, `unordered_map`)
- Memory management considerations
- Output comparison for vectors/arrays

### Go
- Uses package main with standalone functions
- Different import syntax
- Multiple return values handling

## Checklist

When adding a new language:

- [ ] Find Judge0 language ID
- [ ] Add to `LANGUAGE_MAP` in `judge0.py`
- [ ] Create wrapper generator function in `wrapper.py`
- [ ] Add to `SUPPORTED_LANGUAGES` list in `wrapper.py`
- [ ] Update `get_wrapper_for_language()` dispatcher in `wrapper.py`
- [ ] Add language config to problem YAML files
- [ ] Re-seed problems to database
- [ ] Verify with `verify_solutions.py --mode judge0`
- [ ] Test frontend language selector
- [ ] Configure Monaco Editor (if needed)
- [ ] Update documentation

## Troubleshooting

### "Unsupported language" Error

Ensure the language is in `LANGUAGE_MAP` and the string matches exactly (case-insensitive).

### Wrapper Output Not JSON

Check that the wrapper properly captures stdout and only outputs JSON on the final line.

### Test Results Incorrect

Verify the comparison logic handles language-specific equality (arrays, objects, etc.).

### Judge0 Timeout

Some languages need longer timeouts. Adjust in Judge0 submission or wrapper code.

## Next Steps

- [Adding Problems](/guide/adding-problems) - Add problems with multi-language support
- [Judge0 Setup](/guide/judge0-setup) - Configure code execution
- [Contributing](/guide/contributing) - Submit your language support as a PR
