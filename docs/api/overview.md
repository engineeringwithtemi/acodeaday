# API Overview

The acodeaday API is a RESTful API built with FastAPI. This reference covers all available endpoints, request/response formats, and authentication.

## Base URL

**Local Development:**
```
http://localhost:8000
```

**Production:**
```
https://api.yourapp.com
```

All API endpoints are prefixed with `/api`.

## Authentication

acodeaday uses Supabase Auth with JWT Bearer tokens.

### Login Flow

1. User authenticates with Supabase (email/password)
2. Supabase returns JWT access token
3. Client includes token in subsequent requests to backend
4. Backend validates token with Supabase

### JWT Bearer Token Header

```http
Authorization: Bearer <access_token>
```

Example:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." http://localhost:8000/api/today
```

See [Authentication](/api/authentication) for details.

## Request Format

### Content Type

All requests with body must use:
```
Content-Type: application/json
```

### Example Request

```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" \
  -d '{
    "problem_slug": "two-sum",
    "language": "python",
    "code": "class Solution:\n    def twoSum(self, nums, target):\n        ..."
  }'
```

## Response Format

All responses are JSON with consistent structure.

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data here
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Problem not found",
    "details": {}
  }
}
```

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

## Pagination

List endpoints support pagination:

```http
GET /api/problems?limit=10&offset=0
```

**Query Parameters:**
- `limit` - Number of items per page (default: 20, max: 100)
- `offset` - Number of items to skip (default: 0)

**Response:**
```json
{
  "items": [...],
  "total": 100,
  "limit": 10,
  "offset": 0,
  "has_more": true
}
```

## Rate Limiting

Currently no rate limiting is implemented, but recommended for production:

- 100 requests per minute per IP
- 1000 requests per hour per user

## CORS

CORS is configured to allow requests from:
- Local development: `http://localhost:5173`
- Production: Your frontend domain

Allowed methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

## Endpoints Summary

### Problems

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/problems` | No | List all problems |
| GET | `/api/problems/:slug` | No | Get problem details |

### Code Execution

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/run` | No | Run code against example tests |
| POST | `/api/submit` | Yes | Submit solution against all tests |
| POST | `/api/rate-submission` | Yes | Rate submission difficulty (Anki SM-2) |

### Code Persistence

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/code/save` | Yes | Save code (auto-save) |
| POST | `/api/code/reset` | Yes | Reset to starter code |
| POST | `/api/code/load-submission` | Yes | Load past submission |

### User Progress

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/today` | Yes | Get daily session problems |
| GET | `/api/progress` | Yes | Get overall progress |
| GET | `/api/mastered` | Yes | Get mastered problems |
| POST | `/api/mastered/:id/show-again` | Yes | Re-add problem to rotation |

### Submissions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/submissions/:problem_id` | Yes | Get submission history |

### AI Chat

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/chat/models` | No | List available LLM models |
| POST | `/api/chat/sessions` | Yes | Create chat session |
| GET | `/api/chat/sessions/:slug` | Yes | List sessions for problem |
| GET | `/api/chat/session/:id` | Yes | Get session with messages |
| POST | `/api/chat/session/:id/message` | Yes | Send message to AI |

## Interactive Documentation

FastAPI provides interactive API documentation:

**Swagger UI:**
```
http://localhost:8000/docs
```

**ReDoc:**
```
http://localhost:8000/redoc
```

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Test endpoints directly in browser
- Download OpenAPI spec

## OpenAPI Specification

Download the OpenAPI 3.0 spec:

```
http://localhost:8000/openapi.json
```

Use with tools like:
- Postman (import OpenAPI spec)
- Insomnia
- curl
- HTTPie

## Error Codes Reference

| Code | Description | Resolution |
|------|-------------|------------|
| `VALIDATION_ERROR` | Invalid request data | Check request body format |
| `AUTHENTICATION_REQUIRED` | Missing auth | Include Authorization header |
| `INVALID_CREDENTIALS` | Wrong username/password | Verify credentials |
| `PROBLEM_NOT_FOUND` | Problem doesn't exist | Check problem slug |
| `JUDGE0_ERROR` | Code execution failed | Check Judge0 status |
| `DATABASE_ERROR` | Database operation failed | Contact support |

## Data Types

### Problem

```typescript
{
  id: string;              // UUID
  title: string;
  slug: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  pattern: string;
  sequence_number: number;
  constraints: string[];
  examples: Array<{
    input: string;
    output: string;
    explanation?: string;
  }>;
}
```

### Test Case

```typescript
{
  id: string;
  input: any[];           // Array of function arguments
  expected: any;          // Expected output
  sequence: number;
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
  submitted_at: string;   // ISO 8601 timestamp
}
```

### User Progress

```typescript
{
  id: string;
  user_id: string;
  problem_id: string;
  times_solved: number;
  is_mastered: boolean;
  ease_factor: number;           // Anki SM-2: default 2.5, min 1.3
  interval_days: number;         // Days until next review
  review_count: number;          // Number of reviews completed
  next_review_date: string | null; // ISO 8601 date
  last_solved_at: string;         // ISO 8601 timestamp
}
```

## Versioning

Currently API is v1 (implicit). Future versions will use URL versioning:

```
/api/v1/problems
/api/v2/problems
```

## Next Steps

Explore specific endpoint documentation:

- [Authentication](/api/authentication)
- [Problems](/api/problems)
- [Submissions](/api/submissions)
- [Progress](/api/progress)
