# Progress API

Endpoints for tracking user progress, spaced repetition, and daily sessions.

## Get Daily Session

Get today's problems: up to 2 reviews (if due) + 1 new problem.

### Endpoint

```http
GET /api/today
```

### Authentication

**Required** - Include Authorization header

### Response

```json
{
  "date": "2024-01-08",
  "problems": [
    {
      "id": "uuid",
      "title": "Two Sum",
      "slug": "two-sum",
      "difficulty": "easy",
      "pattern": "hash-map",
      "sequence_number": 1,
      "type": "review",
      "progress": {
        "times_solved": 1,
        "next_review_date": "2024-01-08",
        "is_mastered": false,
        "last_solved_at": "2024-01-01T10:00:00Z"
      }
    },
    {
      "id": "uuid",
      "title": "Valid Palindrome",
      "slug": "valid-palindrome",
      "difficulty": "easy",
      "pattern": "two-pointers",
      "sequence_number": 15,
      "type": "review",
      "progress": {
        "times_solved": 1,
        "next_review_date": "2024-01-07",
        "is_mastered": false,
        "last_solved_at": "2023-12-31T15:30:00Z"
      }
    },
    {
      "id": "uuid",
      "title": "Contains Duplicate",
      "slug": "contains-duplicate",
      "difficulty": "easy",
      "pattern": "hash-map",
      "sequence_number": 3,
      "type": "new",
      "progress": null
    }
  ],
  "stats": {
    "reviews_due": 2,
    "new_available": true,
    "total_mastered": 5,
    "total_in_review": 10
  }
}
```

### Priority Logic

Problems are returned in this order:

1. **Review #1**: Oldest overdue problem (`next_review_date <= today`, `is_mastered = false`)
2. **Review #2**: Second oldest overdue problem
3. **New Problem**: Next unsolved by `sequence_number`

### Example

```bash
curl -u admin:password http://localhost:8000/api/today
```

## Get Overall Progress

Get user's progress across all problems.

### Endpoint

```http
GET /api/progress
```

### Authentication

**Required** - Include Authorization header

### Response

```json
{
  "user_id": "admin",
  "total_problems": 100,
  "problems_started": 15,
  "problems_mastered": 5,
  "problems_in_review": 10,
  "completion_percentage": 6.7,
  "mastery_percentage": 33.3,
  "problems": [
    {
      "id": "uuid",
      "title": "Two Sum",
      "slug": "two-sum",
      "difficulty": "easy",
      "pattern": "hash-map",
      "sequence_number": 1,
      "progress": {
        "times_solved": 2,
        "is_mastered": true,
        "last_solved_at": "2024-01-05T10:00:00Z",
        "next_review_date": null
      }
    },
    {
      "id": "uuid",
      "title": "Best Time to Buy and Sell Stock",
      "slug": "best-time-to-buy-and-sell-stock",
      "difficulty": "easy",
      "pattern": "sliding-window",
      "sequence_number": 2,
      "progress": {
        "times_solved": 1,
        "is_mastered": false,
        "last_solved_at": "2024-01-01T14:30:00Z",
        "next_review_date": "2024-01-08"
      }
    },
    {
      "id": "uuid",
      "title": "Contains Duplicate",
      "slug": "contains-duplicate",
      "difficulty": "easy",
      "pattern": "hash-map",
      "sequence_number": 3,
      "progress": null
    }
    // ... more problems
  ],
  "by_difficulty": {
    "easy": {
      "total": 26,
      "started": 8,
      "mastered": 3
    },
    "medium": {
      "total": 38,
      "started": 5,
      "mastered": 2
    },
    "hard": {
      "total": 11,
      "started": 2,
      "mastered": 0
    }
  },
  "by_pattern": {
    "hash-map": {
      "total": 8,
      "started": 3,
      "mastered": 2
    },
    "two-pointers": {
      "total": 6,
      "started": 2,
      "mastered": 1
    }
    // ... more patterns
  }
}
```

### Example

```bash
curl -u admin:password http://localhost:8000/api/progress
```

## Get Mastered Problems

Get all problems marked as mastered (solved 2+ times).

### Endpoint

```http
GET /api/mastered
```

### Authentication

**Required** - Include Authorization header

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
      "sequence_number": 1,
      "progress": {
        "times_solved": 2,
        "is_mastered": true,
        "last_solved_at": "2024-01-05T10:00:00Z",
        "next_review_date": null,
        "show_again": false
      }
    },
    {
      "id": "uuid",
      "title": "Valid Palindrome",
      "slug": "valid-palindrome",
      "difficulty": "easy",
      "pattern": "two-pointers",
      "sequence_number": 15,
      "progress": {
        "times_solved": 3,
        "is_mastered": true,
        "last_solved_at": "2023-12-28T15:30:00Z",
        "next_review_date": null,
        "show_again": false
      }
    }
  ],
  "total": 5
}
```

### Example

```bash
curl -u admin:password http://localhost:8000/api/mastered
```

## Show Again (Re-add to Rotation)

Re-add a mastered problem to your review rotation.

### Endpoint

```http
POST /api/mastered/:problem_id/show-again
```

### Authentication

**Required** - Include Authorization header

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `problem_id` | UUID | Problem ID |

### Response

```json
{
  "success": true,
  "message": "Problem added back to rotation",
  "progress": {
    "times_solved": 2,
    "is_mastered": true,
    "next_review_date": "2024-01-08",
    "show_again": false,
    "last_solved_at": "2024-01-05T10:00:00Z"
  }
}
```

### Behavior

When you click "Show Again":
- `show_again` flag is set to `false` (immediately)
- `next_review_date` is set to `today()`
- Problem appears in tomorrow's daily session
- Mastery status (`times_solved`, `is_mastered`) unchanged

### Example

```bash
curl -X POST -u admin:password \
  http://localhost:8000/api/mastered/abc123-uuid/show-again
```

## Data Models

### Daily Session Response

```typescript
{
  date: string;  // ISO 8601 date
  problems: Array<{
    id: string;
    title: string;
    slug: string;
    difficulty: "easy" | "medium" | "hard";
    pattern: string;
    sequence_number: number;
    type: "review" | "new";
    progress: {
      times_solved: number;
      next_review_date: string | null;
      is_mastered: boolean;
      last_solved_at: string;
    } | null;
  }>;
  stats: {
    reviews_due: number;
    new_available: boolean;
    total_mastered: number;
    total_in_review: number;
  };
}
```

### Progress Response

```typescript
{
  user_id: string;
  total_problems: number;
  problems_started: number;
  problems_mastered: number;
  problems_in_review: number;
  completion_percentage: number;
  mastery_percentage: number;
  problems: Array<{
    id: string;
    title: string;
    slug: string;
    difficulty: "easy" | "medium" | "hard";
    pattern: string;
    sequence_number: number;
    progress: {
      times_solved: number;
      is_mastered: boolean;
      last_solved_at: string;
      next_review_date: string | null;
    } | null;
  }>;
  by_difficulty: {
    [key: string]: {
      total: number;
      started: number;
      mastered: number;
    };
  };
  by_pattern: {
    [key: string]: {
      total: number;
      started: number;
      mastered: number;
    };
  };
}
```

## Frontend Integration

### Fetch Daily Session

```typescript
async function fetchDailySession() {
  const auth = localStorage.getItem('auth');

  const response = await fetch('/api/today', {
    headers: {
      'Authorization': `Basic ${auth}`
    }
  });

  return response.json();
}

// Usage
const session = await fetchDailySession();
const reviews = session.problems.filter(p => p.type === 'review');
const newProblems = session.problems.filter(p => p.type === 'new');

console.log(`${reviews.length} reviews, ${newProblems.length} new`);
```

### Fetch Overall Progress

```typescript
async function fetchProgress() {
  const auth = localStorage.getItem('auth');

  const response = await fetch('/api/progress', {
    headers: {
      'Authorization': `Basic ${auth}`
    }
  });

  return response.json();
}

// Usage
const progress = await fetchProgress();
console.log(`${progress.problems_mastered}/${progress.total_problems} mastered`);
console.log(`${progress.completion_percentage.toFixed(1)}% complete`);
```

### Show Again

```typescript
async function showAgain(problemId: string) {
  const auth = localStorage.getItem('auth');

  const response = await fetch(`/api/mastered/${problemId}/show-again`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${auth}`
    }
  });

  return response.json();
}

// Usage
await showAgain(problem.id);
console.log('Problem will appear in tomorrow\'s session');
```

### Display Progress Stats

```typescript
function displayProgress(progress) {
  const stats = {
    totalProblems: progress.total_problems,
    started: progress.problems_started,
    mastered: progress.problems_mastered,
    inReview: progress.problems_in_review,
    notStarted: progress.total_problems - progress.problems_started,
    completionPercent: progress.completion_percentage.toFixed(1),
    masteryPercent: progress.mastery_percentage.toFixed(1)
  };

  return stats;
}

// Example output:
// {
//   totalProblems: 100,
//   started: 15,
//   mastered: 5,
//   inReview: 10,
//   notStarted: 60,
//   completionPercent: "6.7",
//   masteryPercent: "33.3"
// }
```

### Filter by Difficulty

```typescript
function getProgressByDifficulty(progress, difficulty) {
  return {
    total: progress.by_difficulty[difficulty].total,
    started: progress.by_difficulty[difficulty].started,
    mastered: progress.by_difficulty[difficulty].mastered,
    percent: (
      (progress.by_difficulty[difficulty].mastered /
       progress.by_difficulty[difficulty].total) * 100
    ).toFixed(1)
  };
}

// Usage
const easyProgress = getProgressByDifficulty(progress, 'easy');
console.log(`Easy: ${easyProgress.mastered}/${easyProgress.total} (${easyProgress.percent}%)`);
```

### Filter by Pattern

```typescript
function getWeakPatterns(progress) {
  return Object.entries(progress.by_pattern)
    .map(([pattern, stats]) => ({
      pattern,
      ...stats,
      masteryRate: stats.total > 0 ? (stats.mastered / stats.total) * 100 : 0
    }))
    .filter(p => p.started > 0 && p.masteryRate < 50)
    .sort((a, b) => a.masteryRate - b.masteryRate);
}

// Usage
const weakPatterns = getWeakPatterns(progress);
console.log('Focus on these patterns:', weakPatterns.map(p => p.pattern));
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

### 404 Not Found

```json
{
  "success": false,
  "error": {
    "code": "PROBLEM_NOT_FOUND",
    "message": "Problem not found"
  }
}
```

### 422 Validation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Problem is not mastered"
  }
}
```

## Best Practices

### Client-Side

1. **Cache daily session:**
   ```typescript
   const cachedSession = sessionStorage.getItem('today');
   if (cachedSession) {
     return JSON.parse(cachedSession);
   }
   ```

2. **Show completion progress visually:**
   ```typescript
   <ProgressBar value={progress.completion_percentage} max={100} />
   ```

3. **Highlight reviews due:**
   ```typescript
   const isOverdue = new Date(problem.progress.next_review_date) < new Date();
   ```

### Server-Side

1. **Optimize query performance** (already implemented with indexes)
2. **Cache daily sessions** for performance
3. **Track analytics** on mastery rates per pattern

## Next Steps

- [Submissions API](/api/submissions) - Submit solutions
- [Problems API](/api/problems) - Get problem data
- [Authentication](/api/authentication) - Secure your requests
