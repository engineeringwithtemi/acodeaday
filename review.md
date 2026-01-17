# Documentation & Code Audit Review

> **Instructions**: Review each item below and add your thoughts/decisions in the `[ ] Your Decision:` sections. Once complete, we'll proceed with implementation based on your feedback.

---

## Part 1: Documentation Fixes (No Code Changes)

### 1.1 Environment Variables Location

**Issue**: Docs say `backend/.env` but project uses root `.env`

**Current behavior**:
- `settings.py` line 63: `env_file=("../.env", ".env")` - checks parent dir first, then current
- Frontend `vite.config.ts`: `envDir: path.resolve(__dirname, '..')` - reads parent dir

**Options**:
- A) Move `.env` to `backend/` and update vite config. 
- B) Keep root `.env`, update docs to reflect this

**My recommendation**: Option B (simpler, shared config)

- [] Your Decision: Option A. Seems frontend can't use the root .env 

---

### 1.2 Non-Existent Environment Variables

These are documented but NOT in `settings.py`:

| Variable | Documented In | Actually Used? |
|----------|---------------|----------------|
| `SUPABASE_SERVICE_KEY` | env-variables.md:33-34 | NO |
| `JUDGE0_API_KEY` | env-variables.md:55 | NO |
| `CORS_ORIGINS` | env-variables.md:78-79 | NO |
| `SECRET_KEY` | env-variables.md:103 | NO |
| `REDIS_URL` | env-variables.md:106 | NO |
| `SENTRY_DSN` | env-variables.md:109 | NO |
| `VITE_SENTRY_DSN` | env-variables.md:144 | NO |
| `VITE_GA_ID` | env-variables.md:147 | NO |
| `VITE_ENV` | env-variables.md:150 | NO |

**Options**:
- A) Remove all from docs (they don't work)
- B) Remove now, add back when implemented
- C) Keep as "planned/optional" with note they're not implemented

**My recommendation**: Option A (remove - docs should reflect reality)

- [ ] Your Decision: remove all

---

### 1.3 Judge0 Authentication

**Issue**: Docs mention `JUDGE0_AUTHENTICATION_ENABLED` and `JUDGE0_AUTHENTICATION_TOKEN`

**Reality**:
- `JUDGE0_AUTHENTICATION_ENABLED` is NOT a valid Judge0 env var (doesn't exist in Judge0)
- Our `judge0.py` has NO authentication support - just plain HTTP calls
- The `docker-compose.yml` line 47-48 has it commented out: `# - AUTHENTICATION_TOKEN=your-secret-token`

**Options**:
- A) Remove auth docs entirely (we don't support it)
- B) Add auth support to `judge0.py` AND update docs
- C) Just fix the env var name to `AUTHN_TOKEN` (correct Judge0 var) and add support

**My recommendation**: Option A (simplify - local Judge0 doesn't need auth)

- [ ] Your Decision: option a is the one to do now. but we should have a coming soon to non local judge0 integration 

---

### 1.4 Judge0 Directory Path

**Issue**: `judge0-setup.md:24-28` says "Navigate to `backend/judge0`"

**Reality**: Judge0 is configured in root `docker-compose.yml`

**Fix**: Update docs to say:
```bash
# From project root
docker compose up -d judge0-server judge0-workers judge0-db judge0-redis
```

- [ ] Your Decision: Approve this fix? (Y/N)Y

---

### 1.5 Backend Validation Claim

**Issue**: `env-variables.md:313-326` says "The backend validates env vars on startup"

**Reality**: No startup validation exists. Pydantic just uses defaults if missing.

**Options**:
- A) Remove this claim from docs
- B) Add actual startup validation to backend

**My recommendation**: Option A 

- [ ] Your Decision:depends, if we have default vars then there's no need to validate else

---

### 1.6 Loading Environment Variables Code Example

**Issue**: `env-variables.md:364-376` shows old `load_dotenv()` pattern

**Reality**: We use `pydantic-settings`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"))
```

**Fix**: Update code example to show actual pattern

- [ ] Your Decision: Approve this fix? (Y/N)y

---

### 1.7 Authentication Documentation

**Issue**: Some docs may reference `AUTH_USERNAME`/`AUTH_PASSWORD`

**Reality**:
- Backend uses `DEFAULT_USER_EMAIL` (default: `admin@acodeaday.local`)
- Backend uses `DEFAULT_USER_PASSWORD` (default: `changeme123`)
- Uses Supabase JWT Bearer tokens, NOT HTTP Basic Auth

**Fix**: Update all auth references to correct variable names

- [ ] Your Decision: Approve this fix? (Y/N)y

---

### 1.8 Signup Flow Documentation

**Issue**: Docs may describe signup flow

**Reality**:
- NO signup route exists in frontend
- Only `/login` route
- Default user created on backend startup via Supabase Auth
- Users must use pre-configured credentials OR create user in Supabase dashboard

**Fix**: Remove signup docs, clarify login-only flow

- [ ] Your Decision: Approve this fix? (Y/N)y

---

### 1.9 VITE_SUPABASE_ANON_KEY vs VITE_SUPABASE_KEY

**Issue**: Docs say `VITE_SUPABASE_ANON_KEY`

**Reality**: Frontend uses `VITE_SUPABASE_KEY` (see `frontend/src/lib/supabase.ts`)

**Fix**: Update docs to use correct variable name

- [ ] Your Decision: Approve this fix? (Y/N)y

---

### 1.10 Pattern Type

**Issue**: You mentioned docs say pattern is string

**Reality**: Migration `b7c09ca0d8a9_change_pattern_to_array.py` confirms it's ARRAY

**Fix**: Verify and update any docs mentioning pattern type

- [ ] Your Decision: Approve this fix? (Y/N)y

---

### 1.11 About Page Photo

**Issue**: Add your photo to about.md

**Proposed change**:
```markdown
## Built By

<div style="text-align: center; margin: 2rem 0;">
  <img src="/temi.jpg" alt="Temiloluwa Ojo" style="width: 150px; height: 150px; border-radius: 50%; object-fit: cover;" />
  <h3>Temiloluwa Ojo</h3>
  <p>Software Engineer</p>
</div>
```

- [ ] Your Decision: Approve this addition? (Y/N)y

---

## Part 2: Code Changes Required

### 2.1 Create verify_solutions.py Script

**Purpose**: Verify problem solutions using Judge0

**Features**:
- Load problem YAML files
- Get reference_solution for specified language
- Generate wrapper using existing `generate_python_wrapper()`
- Submit to Judge0
- Report pass/fail for each problem

**Usage**:
```bash
# Verify all problems (all languages with solutions)
uv run python scripts/verify_solutions.py

# Verify specific problem
uv run python scripts/verify_solutions.py two-sum

# Verify specific language only
uv run python scripts/verify_solutions.py --lang python
uv run python scripts/verify_solutions.py two-sum --lang python
```

- [ ] Your Decision: Approve creating this script? (Y/N) y
- [ ] Any additional features needed?

---

### 2.2 Add get_wrapper_for_language Function

**File**: `backend/app/services/wrapper.py`

**Purpose**: Dispatcher to get correct wrapper generator for a language

```python
def get_wrapper_for_language(language: str):
    """Get the appropriate wrapper generator for a language."""
    wrappers = {
        "python": generate_python_wrapper,
        # "javascript": generate_javascript_wrapper,  # When implemented
    }

    if language not in wrappers:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(wrappers.keys())}")

    return wrappers[language]
```

**Note**: Docs reference this function but it doesn't exist

- [ ] Your Decision: Approve adding this function? (Y/N)Y

---

### 2.3 Add JavaScript Wrapper Function

**File**: `backend/app/services/wrapper.py`

**Purpose**: Enable JavaScript code execution (infrastructure already exists in Judge0)

**Note**: The docs already have a complete implementation example. Should we add it?

- [ ] Your Decision: Add JavaScript wrapper now? (Y/N / Later) Later

---

### 2.4 Create LanguageSelector Component

**File**: `frontend/src/components/LanguageSelector.tsx`

**Current state**: Language is hardcoded to `'python'` in `problem.$slug.tsx`:
```typescript
const [language] = useState<'python' | 'javascript'>('python')
```

**Proposed**: Create dropdown component to switch between available languages

- [ ] Your Decision: Create LanguageSelector component? (Y/N / Later)Y, we should have an endpoint that provides supported languages from the wrapper 

---

### 2.5 npm test / Frontend Tests

**Current state**:
- `vitest` is configured in package.json
- `npm test` runs `vitest run`
- But NO test files exist

**Options**:
- A) Remove test script / update docs to say "no tests yet" 
- B) Add basic tests
- C) Keep as-is with note in docs

**My recommendation**: Option A (remove claim from docs, keep script for future)

- [ ] Your Decision:A

---

### 2.6 npm run preview

**Issue**: You said docs mention it but we don't support it

**Reality**: `package.json` line 8: `"preview": "vite preview"` - IT EXISTS

**Fix**: None needed, docs are correct

- [ ] Your Decision: Confirmed (no fix needed)? (Y/N)Y

---

### 2.7 seed_problems.py Clarifications

**Current behavior**:
- `new` command takes `slug` as argument (not title)
- `--lang` flag EXISTS and WORKS (defaults to `['python']`)
- Slug is NOT auto-generated from title

**Your concern**: "isn't slug determined from the title?"

**Current implementation**: NO - user provides slug directly

**Options**:
- A) Keep as-is (slug provided manually)
- B) Change to accept title and auto-generate slug

**My recommendation**: Option A (simpler, more control)

- [ ] Your Decision: i need more clarification on this, what i expect is title should determine slug so if it's two-sum-ii, slug should be that. I hope that clarifies the point below. 

---

### 2.8 Slug Conflict Handling

**Your concern**: "the function to get slug from title should be able to automatically handle conflicts"

**Current implementation**:
- Database has UNIQUE constraint on `slug`
- `upsert_problem` uses `ON CONFLICT (slug) DO UPDATE`
- So conflicts are handled by UPDATE, not by generating new slug

**Options**:
- A) Keep as-is (conflicts update existing)
- B) Add auto-suffix on conflict (e.g., `two-sum-2`)

**My recommendation**: Option A (conflicts should update, not create duplicates)

- [ ] Your Decision:

---

### 2.9 Hosted Judge0 Section

**Issue**: Docs mention RapidAPI hosted Judge0 with `JUDGE0_API_KEY`

**Reality**: We don't support this

**Options**:
- A) Remove section entirely
- B) Add support for API key header in `judge0.py`

**My recommendation**: Option A (self-hosted is the focus)

- [ ] Your Decision: B, let's accept an env that if it's provided, the judge0 service should use it 

---

### 2.10 "In Python" vs "In General" Language

**Your concern**: Adding-languages.md speaks about Python alone

**Fix**: Add "For example, in Python..." prefix to language-specific sections

- [ ] Your Decision: Approve this fix? (Y/N)y

---

## Part 3: Summary of Changes

### Documentation Files to Modify:
1. `docs/guide/environment-variables.md` - Major rewrite
2. `docs/guide/judge0-setup.md` - Fix directory paths, remove auth
3. `docs/guide/adding-languages.md` - Update for actual implementation
4. `docs/about.md` - Add photo
5. `docs/guide/introduction.md` - Fix auth description (if needed)
6. `docs/guide/backend-setup.md` - Fix auth vars
7. `docs/guide/frontend-setup.md` - Fix auth vars

### Backend Files to Create/Modify:
1. `backend/scripts/verify_solutions.py` - NEW
    let's use the verify_solutions.py file, let's have a default arg of mood with judge0. if not we use python
2. `backend/app/services/wrapper.py` - Add functions

### Frontend Files to Create/Modify:
1. `frontend/src/components/LanguageSelector.tsx` - NEW (if approved)
2. `frontend/src/routes/problem.$slug.tsx` - Use LanguageSelector (if approved)

---

## Your Overall Feedback

Please add any additional thoughts, corrections, or priorities here:

```
[Your feedback here]
```

---

## Next Steps

Once you've reviewed this document:
1. Fill in your decisions above
2. Add any additional feedback
3. Let me know and I'll proceed with implementation based on your input
