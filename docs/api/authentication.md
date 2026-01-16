# Authentication

acodeaday uses HTTP Basic Authentication for simplicity and security.

## Authentication Flow

```
┌──────────┐           ┌──────────┐           ┌──────────┐
│  Client  │           │ Backend  │           │ Database │
└────┬─────┘           └────┬─────┘           └────┬─────┘
     │                      │                      │
     │ POST /api/login      │                      │
     │ {username, password} │                      │
     ├─────────────────────>│                      │
     │                      │                      │
     │                      │ Validate credentials │
     │                      ├─────────────────────>│
     │                      │                      │
     │                      │ User data            │
     │                      │<─────────────────────┤
     │                      │                      │
     │ 200 OK               │                      │
     │ {user, token}        │                      │
     │<─────────────────────┤                      │
     │                      │                      │
     │ GET /api/today       │                      │
     │ Authorization: Basic │                      │
     ├─────────────────────>│                      │
     │                      │                      │
     │ 200 OK               │                      │
     │ {problems}           │                      │
     │<─────────────────────┤                      │
     │                      │                      │
```

## Login

### Endpoint

```http
POST /api/login
```

### Request

```json
{
  "username": "admin",
  "password": "your-password"
}
```

### Response (Success)

```json
{
  "success": true,
  "user": {
    "id": "admin",
    "username": "admin",
    "email": "admin@example.com"
  },
  "token": "base64-encoded-credentials"
}
```

### Response (Error)

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

## Using Authentication

### HTTP Basic Auth

Include username and password in every authenticated request.

**Format:**
```
Authorization: Basic base64(username:password)
```

**Example:**
```bash
# Encode credentials
echo -n "admin:password" | base64
# Output: YWRtaW46cGFzc3dvcmQ=

# Use in request
curl -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" \
  http://localhost:8000/api/today
```

### Using curl with -u Flag

Easier method:
```bash
curl -u admin:password http://localhost:8000/api/today
```

curl automatically encodes credentials and adds the header.

### Using JavaScript (Frontend)

```javascript
// Store credentials after login
const credentials = btoa(`${username}:${password}`);
localStorage.setItem('auth', credentials);

// Use in API requests
const response = await fetch('http://localhost:8000/api/today', {
  headers: {
    'Authorization': `Basic ${credentials}`
  }
});
```

### Using Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  auth: {
    username: 'admin',
    password: 'password'
  }
});

// All requests now include auth
const { data } = await api.get('/api/today');
```

## Protected Endpoints

Endpoints requiring authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/today` | GET | Daily session |
| `/api/submit` | POST | Submit solution |
| `/api/progress` | GET | User progress |
| `/api/mastered` | GET | Mastered problems |
| `/api/mastered/:id/show-again` | POST | Re-add problem |
| `/api/submissions/:problem_id` | GET | Submission history |

## Public Endpoints

No authentication required:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/problems` | GET | List problems |
| `/api/problems/:slug` | GET | Problem details |
| `/api/run` | POST | Run code (testing only) |

## Error Responses

### 401 Unauthorized

Missing or invalid authentication:

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required"
  }
}
```

**Cause:**
- No Authorization header
- Invalid credentials
- Malformed header

**Resolution:**
- Include Authorization header
- Verify username and password
- Check header format

### 403 Forbidden

Authenticated but not authorized:

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to access this resource"
  }
}
```

## Security Best Practices

### Client-Side

1. **Store credentials securely:**
   ```javascript
   // Use sessionStorage for single-session
   sessionStorage.setItem('auth', credentials);

   // Or localStorage for "remember me"
   localStorage.setItem('auth', credentials);
   ```

2. **Clear credentials on logout:**
   ```javascript
   localStorage.removeItem('auth');
   sessionStorage.clear();
   ```

3. **Never log credentials:**
   ```javascript
   // ❌ DON'T
   console.log('Auth:', credentials);

   // ✅ DO
   console.log('User authenticated');
   ```

4. **Use HTTPS in production:**
   ```javascript
   const API_URL = process.env.NODE_ENV === 'production'
     ? 'https://api.yourapp.com'
     : 'http://localhost:8000';
   ```

### Server-Side

1. **Hash passwords** (already implemented with Supabase)

2. **Rate limit login attempts:**
   ```python
   # Limit to 5 login attempts per minute
   @app.post("/api/login")
   @limiter.limit("5/minute")
   async def login(credentials: LoginRequest):
       ...
   ```

3. **Use HTTPS only in production:**
   ```python
   if settings.ENVIRONMENT == "production":
       app.add_middleware(
           HTTPSRedirectMiddleware
       )
   ```

4. **Set secure headers:**
   ```python
   @app.middleware("http")
   async def add_security_headers(request, call_next):
       response = await call_next(request)
       response.headers["X-Content-Type-Options"] = "nosniff"
       response.headers["X-Frame-Options"] = "DENY"
       return response
   ```

## Session Management

Currently, authentication is stateless (credentials sent with each request).

Future enhancements may include:
- JWT tokens
- Session-based auth
- Refresh tokens
- OAuth integration

## Default Credentials

The backend creates a default user on startup using environment variables:

```bash
# In backend/.env
AUTH_USERNAME=admin
AUTH_PASSWORD=changeme
DEFAULT_USER_EMAIL=admin@example.com
DEFAULT_USER_PASSWORD=changeme
```

**IMPORTANT:** Change these in production!

## Multi-User Support

Currently single-user (default admin account).

To add more users:

1. Use Supabase Auth dashboard to create users
2. Or extend backend to support user registration

## Testing Authentication

### Test Login

```bash
# Valid credentials
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Should return: {"success": true, ...}
```

### Test Protected Endpoint

```bash
# Without auth (should fail)
curl http://localhost:8000/api/today
# Returns: 401 Unauthorized

# With auth (should succeed)
curl -u admin:password http://localhost:8000/api/today
# Returns: 200 OK with data
```

### Test Invalid Credentials

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "wrong"}'

# Returns: {"success": false, "error": {...}}
```

## Frontend Integration Example

```typescript
// auth.ts
export class AuthService {
  private credentials: string | null = null;

  async login(username: string, password: string) {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const { token } = await response.json();
      this.credentials = token;
      localStorage.setItem('auth', token);
      return true;
    }
    return false;
  }

  logout() {
    this.credentials = null;
    localStorage.removeItem('auth');
  }

  getAuthHeader() {
    const creds = this.credentials || localStorage.getItem('auth');
    return creds ? `Basic ${creds}` : null;
  }

  isAuthenticated() {
    return !!this.getAuthHeader();
  }
}

// api.ts
export async function apiRequest(url: string, options = {}) {
  const auth = new AuthService();
  const authHeader = auth.getAuthHeader();

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      ...(authHeader && { 'Authorization': authHeader })
    }
  });

  if (response.status === 401) {
    // Redirect to login
    window.location.href = '/login';
  }

  return response;
}
```

## Next Steps

- [Problems API](/api/problems) - Fetch problem data
- [Submissions API](/api/submissions) - Submit solutions
- [Progress API](/api/progress) - Track user progress
