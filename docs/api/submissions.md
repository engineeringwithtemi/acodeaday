# Submissions API

Endpoints for submitting solutions and viewing submission history.

## Submit Solution

Submit code to be tested against all test cases. On success, updates user progress for spaced repetition.

### Endpoint

```http
POST /api/submit
```

### Authentication

**Required** - Include Authorization header

### Request Body

```json
{
  "problem_slug": "two-sum",
  "language": "python",
  "code": "class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, num in enumerate(nums):\n            complement = target - num\n            if complement in seen:\n                return [seen[complement], i]\n            seen[num] = i\n        return []"
}
```

### Response (All Tests Pass)

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
    },
    {
      "test_number": 4,
      "passed": true,
      "input": [[1, 5, 3, 7, 2, 8], 10],
      "output": [2, 4],
      "expected": [2, 4],
      "stdout": null,
      "error": null
    },
    {
      "test_number": 5,
      "passed": true,
      "input": [[0, 4, 3, 0], 0],
      "output": [0, 3],
      "expected": [0, 3],
      "stdout": null,
      "error": null
    }
  ],
  "summary": {
    "total": 5,
    "passed": 5,
    "failed": 0
  },
  "total_test_cases": 5,
  "submission_id": "uuid",
  "runtime_ms": 45,
  "memory_kb": 14320,
  "compile_error": null,
  "runtime_error": null,
  "times_solved": 1,
  "is_mastered": false,
  "next_review_date": "2024-01-15"
}
```

### Response (Test Fails - Early Exit)

When a test fails, execution stops (early exit) to save resources:

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
      "passed": true,
      "input": [[3, 2, 4], 6],
      "output": [1, 2],
      "expected": [1, 2],
      "stdout": null,
      "error": null
    },
    {
      "test_number": 3,
      "passed": false,
      "input": [[3, 3], 6],
      "output": [1, 0],
      "expected": [0, 1],
      "stdout": "Debug: checking index 1\n",
      "error": null
    }
  ],
  "summary": {
    "total": 3,
    "passed": 2,
    "failed": 1
  },
  "total_test_cases": 5,
  "submission_id": "uuid",
  "runtime_ms": 12,
  "memory_kb": 14100,
  "compile_error": null,
  "runtime_error": null,
  "times_solved": null,
  "is_mastered": null,
  "next_review_date": null
}
```

**Note:** `summary.total` shows tests executed (3), while `total_test_cases` shows total tests for the problem (5). Use `total_test_cases` for "X / Y passed" display.

### Response (Compile Error)

```json
{
  "success": false,
  "results": [],
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0
  },
  "total_test_cases": 5,
  "submission_id": "uuid",
  "runtime_ms": 0,
  "memory_kb": 0,
  "compile_error": "SyntaxError: invalid syntax (line 3)",
  "runtime_error": null,
  "times_solved": null,
  "is_mastered": null,
  "next_review_date": null
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
  },
  "total_test_cases": 5,
  "submission_id": "uuid",
  "runtime_ms": 5,
  "memory_kb": 13000,
  "compile_error": null,
  "runtime_error": "IndexError: list index out of range",
  "times_solved": null,
  "is_mastered": null,
  "next_review_date": null
}
```

### Progress Updates (Anki SM-2)

When all tests pass, the submission is recorded but progress is NOT automatically updated. You must call the **rate-submission** endpoint to update progress with your difficulty rating.

See [Rate Submission](#rate-submission) below.

### Example

```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "problem_slug": "two-sum",
    "language": "python",
    "code": "class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, num in enumerate(nums):\n            if target - num in seen:\n                return [seen[target - num], i]\n            seen[num] = i"
  }'
```

## Rate Submission

After a successful submission, rate the difficulty to update your spaced repetition progress (Anki SM-2).

### Endpoint

```http
POST /api/rate-submission
```

### Authentication

**Required** - Include Authorization header

### Request Body

```json
{
  "submission_id": "uuid",
  "rating": "good"
}
```

**Rating options:**
| Rating | Description | Effect |
|--------|-------------|--------|
| `again` | Couldn't solve / needed hints | Reset interval to 1 day, decrease ease |
| `hard` | Solved but struggled | Slower growth (×1.2), decrease ease |
| `good` | Solved with some effort | Normal growth (×ease factor) |
| `mastered` | Solved easily, confident | Exit rotation immediately |

### Response

```json
{
  "success": true,
  "progress": {
    "times_solved": 2,
    "ease_factor": 2.5,
    "interval_days": 8,
    "is_mastered": false,
    "next_review_date": "2024-01-15"
  }
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/rate-submission \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": "abc123-uuid",
    "rating": "good"
  }'
```

## Get Submission History

Retrieve past submissions for a specific problem.

### Endpoint

```http
GET /api/submissions/:problem_id
```

### Authentication

**Required** - Include Authorization header

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `problem_id` | UUID | Problem ID (not slug) |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Number of submissions per page |
| `offset` | integer | 0 | Number to skip |

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "admin",
      "problem_id": "uuid",
      "code": "class Solution:\n    def twoSum(self, nums, target):\n        ...",
      "language": "python",
      "passed": true,
      "runtime_ms": 45,
      "submitted_at": "2024-01-08T10:30:00Z"
    },
    {
      "id": "uuid",
      "user_id": "admin",
      "problem_id": "uuid",
      "code": "class Solution:\n    def twoSum(self, nums, target):\n        ...",
      "language": "python",
      "passed": false,
      "runtime_ms": 12,
      "submitted_at": "2024-01-08T10:15:00Z"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

### Example

```bash
# Get submission history
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/submissions/abc123-uuid

# Pagination
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/submissions/abc123-uuid?limit=10&offset=0"
```

## Data Models

### Submit Request

```typescript
{
  problem_slug: string;
  language: string;
  code: string;
}
```

### Submit Response

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
    total: number;        // Tests executed
    passed: number;
    failed: number;
  };
  total_test_cases: number;  // Total tests for problem
  submission_id: string;
  runtime_ms: number;
  memory_kb: number;
  compile_error: string | null;
  runtime_error: string | null;
  times_solved: number | null;
  is_mastered: boolean | null;
  next_review_date: string | null;
}
```

### Submission

```typescript
{
  id: string;
  user_id: string;
  problem_id: string;
  code: string;
  language: string;
  passed: boolean;
  runtime_ms: number;
  submitted_at: string;  // ISO 8601
}
```

## Frontend Integration

### Submit Solution

```typescript
import { supabase } from './lib/supabase';

async function submitSolution(
  problemSlug: string,
  code: string,
  language = 'python'
) {
  const { data: { session } } = await supabase.auth.getSession();

  const response = await fetch('/api/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`
    },
    body: JSON.stringify({ problem_slug: problemSlug, language, code })
  });

  if (response.status === 401) {
    throw new Error('Authentication required');
  }

  return response.json();
}

// Usage
const result = await submitSolution('two-sum', userCode);

if (result.success) {
  console.log('Accepted! Now rate the difficulty...');
  // Show rating modal, then call rateSubmission()
} else {
  const failedTest = result.results.find(t => !t.passed);
  console.log('Wrong answer on test', failedTest.test_number);
  console.log('Input:', failedTest.input);
  console.log('Expected:', failedTest.expected);
  console.log('Got:', failedTest.output);
}
```

### Rate Submission (Anki SM-2)

```typescript
async function rateSubmission(submissionId: string, rating: 'again' | 'hard' | 'good' | 'mastered') {
  const { data: { session } } = await supabase.auth.getSession();

  const response = await fetch('/api/rate-submission', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`
    },
    body: JSON.stringify({ submission_id: submissionId, rating })
  });

  return response.json();
}

// Usage after successful submission
const rateResult = await rateSubmission(result.submission_id, 'good');
console.log(`Next review: ${rateResult.progress.next_review_date}`);
console.log(`Ease factor: ${rateResult.progress.ease_factor}`);
```

### Fetch Submission History

```typescript
async function getSubmissionHistory(problemId: string) {
  const { data: { session } } = await supabase.auth.getSession();

  const response = await fetch(`/api/submissions/${problemId}`, {
    headers: {
      'Authorization': `Bearer ${session?.access_token}`
    }
  });

  const data = await response.json();
  return data.items;
}

// Usage
const submissions = await getSubmissionHistory(problem.id);
const lastSubmission = submissions[0]; // Most recent first
```

### Display Submission Results

```typescript
function displayResults(result) {
  if (result.compile_error) {
    return {
      status: 'Compile Error',
      message: result.compile_error
    };
  }

  if (result.runtime_error) {
    return {
      status: 'Runtime Error',
      message: result.runtime_error
    };
  }

  if (result.success) {
    return {
      status: 'Accepted',
      message: `All ${result.total_test_cases} test cases passed`,
      runtime: `${result.runtime_ms} ms`,
      memory: `${(result.memory_kb / 1024).toFixed(2)} MB`
    };
  }

  const failedTest = result.results.find(t => !t.passed);
  return {
    status: 'Wrong Answer',
    message: `Failed on test case ${failedTest.test_number}`,
    testsPassed: `${result.summary.passed} / ${result.total_test_cases}`,
    failedInput: failedTest.input,
    expected: failedTest.expected,
    output: failedTest.output
  };
}
```

## Error Responses

### 401 Unauthorized

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required"
  }
}
```

### 404 Problem Not Found

```json
{
  "success": false,
  "error": {
    "code": "PROBLEM_NOT_FOUND",
    "message": "Problem with slug 'invalid' not found"
  }
}
```

### 422 Validation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Code is required"
  }
}
```

### 500 Judge0 Error

```json
{
  "success": false,
  "error": {
    "code": "JUDGE0_ERROR",
    "message": "Code execution failed",
    "details": "Connection to Judge0 failed"
  }
}
```

## Best Practices

### Client-Side

1. **Show loading state during submission:**
   ```typescript
   const [submitting, setSubmitting] = useState(false);

   async function handleSubmit() {
     setSubmitting(true);
     try {
       const result = await submitSolution(slug, code);
       // Handle result
     } finally {
       setSubmitting(false);
     }
   }
   ```

2. **Display test count correctly:**
   ```typescript
   const testsPassed = `${result.summary.passed} / ${result.total_test_cases}`;
   ```

3. **Cache submissions locally:**
   ```typescript
   localStorage.setItem(`last-code-${problemSlug}`, code);
   ```

### Server-Side

1. **Validate input thoroughly** (already implemented)
2. **Rate limit submissions** to prevent abuse
3. **Log all submissions** for analytics
4. **Clean up old submissions** periodically

## Next Steps

- [Progress API](/api/progress) - Track user progress
- [Problems API](/api/problems) - Get problem data
- [Authentication](/api/authentication) - Secure your requests
