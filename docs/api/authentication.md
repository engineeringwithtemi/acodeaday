# Authentication

acodeaday uses Supabase Auth with JWT Bearer tokens for authentication.

## Authentication Flow

```
┌──────────┐           ┌──────────┐           ┌──────────┐
│  Client  │           │ Supabase │           │ Backend  │
└────┬─────┘           └────┬─────┘           └────┬─────┘
     │                      │                      │
     │ POST /auth/login     │                      │
     │ {email, password}    │                      │
     ├─────────────────────>│                      │
     │                      │                      │
     │ 200 OK               │                      │
     │ {access_token, user} │                      │
     │<─────────────────────┤                      │
     │                      │                      │
     │ GET /api/today       │                      │
     │ Authorization: Bearer│                      │
     ├──────────────────────┼─────────────────────>│
     │                      │                      │
     │                      │ Validate JWT token   │
     │                      │<─────────────────────┤
     │                      │                      │
     │                      │ User data            │
     │                      ├─────────────────────>│
     │                      │                      │
     │ 200 OK               │                      │
     │ {problems}           │                      │
     │<─────────────────────┼──────────────────────┤
     │                      │                      │
```

## Login

Authentication is handled by Supabase Auth on the frontend.

### Using Supabase JS Client

```javascript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
});

if (data.session) {
  // access_token is in data.session.access_token
  console.log('Logged in:', data.user.email);
}
```

### Response (Success)

```json
{
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "...",
    "expires_in": 3600,
    "token_type": "bearer"
  },
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Response (Error)

```json
{
  "error": {
    "message": "Invalid login credentials"
  }
}
```

## Using Authentication

### JWT Bearer Token

Include the access token in every authenticated request.

**Format:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/api/today
```

### Using JavaScript (Frontend)

```javascript
// Get current session
const { data: { session } } = await supabase.auth.getSession();

// Use in API requests
const response = await fetch('http://localhost:8000/api/today', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
});
```

### Using React Query

```typescript
import { useQuery } from '@tanstack/react-query';

function useTodaySession() {
  return useQuery({
    queryKey: ['today'],
    queryFn: async () => {
      const { data: { session } } = await supabase.auth.getSession();

      const response = await fetch('/api/today', {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        }
      });

      return response.json();
    }
  });
}
```

## Protected Endpoints

Endpoints requiring authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/today` | GET | Daily session |
| `/api/submit` | POST | Submit solution |
| `/api/rate-submission` | POST | Rate submission difficulty |
| `/api/progress` | GET | User progress |
| `/api/mastered` | GET | Mastered problems |
| `/api/mastered/:id/show-again` | POST | Re-add problem |
| `/api/submissions/:problem_id` | GET | Submission history |
| `/api/code/save` | POST | Save code |
| `/api/code/reset` | POST | Reset to starter code |
| `/api/code/load-submission` | POST | Load past submission |
| `/api/chat/sessions` | POST | Create chat session |
| `/api/chat/session/:id/message` | POST | Send chat message |

## Public Endpoints

No authentication required:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/problems` | GET | List problems |
| `/api/problems/:slug` | GET | Problem details |
| `/api/run` | POST | Run code (testing only) |
| `/api/chat/models` | GET | Available LLM models |

## Error Responses

### 401 Unauthorized

Missing or invalid authentication:

```json
{
  "detail": "Not authenticated"
}
```

**Cause:**
- No Authorization header
- Invalid or expired JWT token
- Malformed token

**Resolution:**
- Include Authorization header with valid Bearer token
- Refresh the token if expired
- Re-authenticate with Supabase

### 403 Forbidden

Authenticated but not authorized:

```json
{
  "detail": "Forbidden"
}
```

## Token Refresh

Supabase tokens expire after 1 hour. The Supabase JS client handles refresh automatically.

```javascript
// Automatic refresh happens on API calls
// Or manually refresh:
const { data, error } = await supabase.auth.refreshSession();
```

### Listen for Auth State Changes

```javascript
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    console.log('User signed in:', session.user.email);
  }
  if (event === 'SIGNED_OUT') {
    console.log('User signed out');
  }
  if (event === 'TOKEN_REFRESHED') {
    console.log('Token refreshed');
  }
});
```

## Security Best Practices

### Client-Side

1. **Never store tokens in localStorage for sensitive apps:**
   ```javascript
   // Supabase handles storage automatically
   // Default: localStorage (persists across sessions)
   // For more security, configure session storage
   ```

2. **Clear session on logout:**
   ```javascript
   await supabase.auth.signOut();
   ```

3. **Handle token expiration:**
   ```javascript
   const { data: { session } } = await supabase.auth.getSession();
   if (!session) {
     // Redirect to login
     window.location.href = '/login';
   }
   ```

4. **Use HTTPS in production:**
   - Supabase URLs are always HTTPS
   - Ensure your backend uses HTTPS

### Server-Side

1. **Validate JWT on every request** (already implemented):
   ```python
   # backend/app/middleware/auth.py
   async def get_current_user(token: str):
       user = supabase.auth.get_user(token)
       return user.user.id
   ```

2. **Use Supabase service key only on backend:**
   - Never expose service key to frontend
   - Use anon key for client-side

## Default Credentials

A default user is created on backend startup using environment variables:

```bash
# In backend/.env
DEFAULT_USER_EMAIL=admin@acodeaday.local
DEFAULT_USER_PASSWORD=changeme123
```

**IMPORTANT:** Change these in production!

## Multi-User Support

Supabase Auth supports multiple users out of the box:

1. Users can sign up via Supabase Auth dashboard
2. Or enable email signup in Supabase settings
3. Each user gets isolated progress data

## Testing Authentication

### Test Login

```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'admin@acodeaday.local',
  password: 'changeme123'
});

if (error) {
  console.error('Login failed:', error.message);
} else {
  console.log('Logged in successfully');
}
```

### Test Protected Endpoint

```bash
# Without auth (should fail)
curl http://localhost:8000/api/today
# Returns: 401 Unauthorized

# With auth (should succeed)
curl -H "Authorization: Bearer <your-token>" http://localhost:8000/api/today
# Returns: 200 OK with data
```

## Frontend Integration Example

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

// lib/api.ts
export async function apiRequest(url: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.status === 401) {
    // Token expired, try refresh
    const { data: { session: newSession } } = await supabase.auth.refreshSession();
    if (!newSession) {
      window.location.href = '/login';
      throw new Error('Session expired');
    }
    // Retry with new token
    return apiRequest(url, options);
  }

  return response;
}

// hooks/useAuth.ts
export function useAuth() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // Listen for changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  return {
    session,
    loading,
    user: session?.user,
    signIn: (email, password) => supabase.auth.signInWithPassword({ email, password }),
    signOut: () => supabase.auth.signOut()
  };
}
```

## Next Steps

- [Problems API](/api/problems) - Fetch problem data
- [Submissions API](/api/submissions) - Submit solutions
- [Progress API](/api/progress) - Track user progress
