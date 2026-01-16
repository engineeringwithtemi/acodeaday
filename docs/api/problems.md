# Problems API

Endpoints for fetching problem data.

## List All Problems

Get a list of all available problems.

### Endpoint

```http
GET /api/problems
```

### Authentication

Not required (public endpoint)

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Number of problems per page (max: 100) |
| `offset` | integer | 0 | Number of problems to skip |
| `difficulty` | string | - | Filter by difficulty: `easy`, `medium`, `hard` |
| `pattern` | string | - | Filter by pattern: `hash-map`, `two-pointers`, etc. |

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Two Sum",
      "slug": "two-sum",
      "difficulty": "easy",
      "pattern": "hash-map",
      "sequence_number": 1
    },
    {
      "id": "uuid",
      "title": "Best Time to Buy and Sell Stock",
      "slug": "best-time-to-buy-and-sell-stock",
      "difficulty": "easy",
      "pattern": "sliding-window",
      "sequence_number": 2
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Example

```bash
# Get all problems
curl http://localhost:8000/api/problems

# Get easy problems only
curl http://localhost:8000/api/problems?difficulty=easy

# Get hash-map problems
curl http://localhost:8000/api/problems?pattern=hash-map

# Pagination
curl http://localhost:8000/api/problems?limit=10&offset=10
```

## Get Problem Details

Get full details for a specific problem, including description, examples, constraints, and starter code.

### Endpoint

```http
GET /api/problems/:slug
```

### Authentication

Not required (public endpoint)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `slug` | string | Problem slug (e.g., `two-sum`) |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | string | `python` | Programming language for code |

### Response

```json
{
  "id": "uuid",
  "title": "Two Sum",
  "slug": "two-sum",
  "description": "Given an array of integers `nums` and an integer `target`...",
  "difficulty": "easy",
  "pattern": "hash-map",
  "sequence_number": 1,
  "constraints": [
    "2 <= nums.length <= 10^4",
    "-10^9 <= nums[i] <= 10^9",
    "Only one valid answer exists."
  ],
  "examples": [
    {
      "input": "nums = [2,7,11,15], target = 9",
      "output": "[0,1]",
      "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."
    }
  ],
  "language_config": {
    "language": "python",
    "starter_code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
    "function_signature": {
      "name": "twoSum",
      "params": [
        {"name": "nums", "type": "List[int]"},
        {"name": "target", "type": "int"}
      ],
      "return_type": "List[int]"
    }
  },
  "test_cases": [
    {
      "input": [[2, 7, 11, 15], 9],
      "expected": [0, 1],
      "sequence": 1
    },
    {
      "input": [[3, 2, 4], 6],
      "expected": [1, 2],
      "sequence": 2
    },
    {
      "input": [[3, 3], 6],
      "expected": [0, 1],
      "sequence": 3
    }
  ]
}
```

**Note:** The first 3 test cases are shown as examples in the problem description. All test cases are run during submission.

### Example

```bash
# Get problem (default Python)
curl http://localhost:8000/api/problems/two-sum

# Get problem with JavaScript code
curl http://localhost:8000/api/problems/two-sum?language=javascript

# Get by slug
curl http://localhost:8000/api/problems/valid-palindrome
```

### Error Responses

**404 Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "PROBLEM_NOT_FOUND",
    "message": "Problem with slug 'invalid-slug' not found"
  }
}
```

**422 Unsupported Language:**
```json
{
  "success": false,
  "error": {
    "code": "LANGUAGE_NOT_SUPPORTED",
    "message": "Language 'ruby' is not supported for this problem"
  }
}
```

## Run Code

Execute user code against example test cases.

### Endpoint

```http
POST /api/run
```

### Authentication

Not required (allows testing without account)

### Request Body

```json
{
  "problem_slug": "two-sum",
  "language": "python",
  "code": "class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, num in enumerate(nums):\n            if target - num in seen:\n                return [seen[target - num], i]\n            seen[num] = i"
}
```

### Response (Success)

```json
{
  "success": true,
  "results": [
    {
      "test_number": 1,
      "passed": true,
      "input": [[2, 7, 11, 15], 9],
      "output": [0, 1],
      "expected": [0, 1],
      "stdout": null,
      "error": null
    },
    {
      "test_number": 2,
      "passed": true,
      "input": [[3, 2, 4], 6],
      "output": [1, 2],
      "expected": [1, 2],
      "stdout": null,
      "error": null
    },
    {
      "test_number": 3,
      "passed": true,
      "input": [[3, 3], 6],
      "output": [0, 1],
      "expected": [0, 1],
      "stdout": null,
      "error": null
    }
  ],
  "summary": {
    "total": 3,
    "passed": 3,
    "failed": 0
  }
}
```

### Response (Failure)

```json
{
  "success": false,
  "results": [
    {
      "test_number": 1,
      "passed": true,
      "input": [[2, 7, 11, 15], 9],
      "output": [0, 1],
      "expected": [0, 1],
      "stdout": null,
      "error": null
    },
    {
      "test_number": 2,
      "passed": false,
      "input": [[3, 2, 4], 6],
      "output": [2, 1],
      "expected": [1, 2],
      "stdout": "Debug: checking index 0\n",
      "error": null
    }
  ],
  "summary": {
    "total": 2,
    "passed": 1,
    "failed": 1
  }
}
```

### Response (Runtime Error)

```json
{
  "success": false,
  "results": [
    {
      "test_number": 1,
      "passed": false,
      "input": [[2, 7, 11, 15], 9],
      "output": null,
      "expected": [0, 1],
      "stdout": null,
      "error": "IndexError: list index out of range"
    }
  ],
  "summary": {
    "total": 1,
    "passed": 0,
    "failed": 1
  }
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "problem_slug": "two-sum",
    "language": "python",
    "code": "class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, num in enumerate(nums):\n            if target - num in seen:\n                return [seen[target - num], i]\n            seen[num] = i"
  }'
```

## Data Models

### Problem (List)

```typescript
{
  id: string;              // UUID
  title: string;           // "Two Sum"
  slug: string;            // "two-sum"
  difficulty: "easy" | "medium" | "hard";
  pattern: string;         // "hash-map"
  sequence_number: number;
}
```

### Problem (Detail)

```typescript
{
  id: string;
  title: string;
  slug: string;
  description: string;     // Markdown
  difficulty: "easy" | "medium" | "hard";
  pattern: string;
  sequence_number: number;
  constraints: string[];
  examples: Array<{
    input: string;
    output: string;
    explanation?: string;
  }>;
  language_config: {
    language: string;
    starter_code: string;
    function_signature: {
      name: string;
      params: Array<{
        name: string;
        type: string;
      }>;
      return_type: string;
    };
  };
  test_cases: Array<{
    input: any[];
    expected: any;
    sequence: number;
  }>;
}
```

### Run Code Result

```typescript
{
  success: boolean;
  results: Array<{
    test_number: number;
    passed: boolean;
    input: any[];
    output: any;
    expected: any;
    stdout: string | null;
    error: string | null;
  }>;
  summary: {
    total: number;
    passed: number;
    failed: number;
  };
}
```

## Frontend Integration

### Fetch Problem List

```typescript
async function fetchProblems(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`/api/problems?${params}`);
  const data = await response.json();
  return data.items;
}

// Usage
const easyProblems = await fetchProblems({ difficulty: 'easy' });
const page2 = await fetchProblems({ limit: 10, offset: 10 });
```

### Fetch Problem Detail

```typescript
async function fetchProblem(slug: string, language = 'python') {
  const response = await fetch(`/api/problems/${slug}?language=${language}`);
  if (!response.ok) {
    throw new Error('Problem not found');
  }
  return response.json();
}

// Usage
const problem = await fetchProblem('two-sum');
```

### Run Code

```typescript
async function runCode(problemSlug: string, code: string, language = 'python') {
  const response = await fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem_slug: problemSlug, language, code })
  });
  return response.json();
}

// Usage
const result = await runCode('two-sum', userCode);
if (result.success) {
  console.log(`Passed ${result.summary.passed}/${result.summary.total} tests`);
} else {
  console.log('Some tests failed:', result.results);
}
```

## Next Steps

- [Submissions API](/api/submissions) - Submit solutions and track progress
- [Progress API](/api/progress) - View user progress
- [Authentication](/api/authentication) - Secure endpoints
