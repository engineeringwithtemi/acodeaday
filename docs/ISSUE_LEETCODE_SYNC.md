# Issue: LeetCode Sync Chrome Extension

## Summary

Build a Chrome extension that captures successful LeetCode submissions and syncs them to acodeaday for spaced repetition tracking. This allows users to practice on LeetCode while maintaining all progress in a single place.

## Motivation

Users often practice on LeetCode directly but want to track their progress using acodeaday's spaced repetition system. Currently, they must manually re-solve problems in acodeaday, duplicating effort. A sync extension eliminates this friction by automatically capturing LeetCode submissions.

**User Story**: "As a user, I want to solve problems on LeetCode and have them automatically tracked in acodeaday so I can benefit from spaced repetition without switching platforms."

## Technical Approach

### Architecture Overview

```
Chrome Extension → Backend API → Supabase DB
                                      ↓
                         Background Worker (Edge Function)
                                      ↓
                            LLM (test case generation)
                                      ↓
                           Judge0 (validation)
```

### Extension Components

1. **Content Script** - Injected into `leetcode.com/problems/*` pages
   - Detects successful submissions via DOM observation
   - Scrapes problem metadata (title, slug, difficulty, tags, description)
   - Captures user's code from Monaco editor
   - Shows rating modal on successful submission

2. **Rating Modal** - Overlay UI shown after successful submission
   - Four rating buttons: Again, Hard, Good, Easy (Anki-style)
   - Skip option for problems user doesn't want to track
   - Styled to match LeetCode's design language

3. **Options Page** - Extension settings
   - API URL configuration
   - API key input
   - Test connection button
   - Auto-sync toggle

4. **Service Worker** - Background coordination
   - Message passing between content script and popup
   - Offline queue management (future)

### Backend Changes

1. **Database Schema Updates**
   - Add to `problems` table: `source`, `external_id`, `external_url`, `generation_status`
   - New table: `generation_queue` for async test case generation
   - New table: `api_keys` for extension authentication

2. **New API Endpoints**
   - `POST /api/external/sync` - Receive synced problems from extension
   - `POST /api/external/api-keys` - Create API key
   - `GET /api/external/api-keys` - List user's API keys
   - `DELETE /api/external/api-keys/{id}` - Revoke API key

3. **Auth Updates**
   - Support Bearer token authentication (API keys)
   - Hash API keys with SHA-256 for storage

### Test Case Generation

**Lazy Generation Strategy**:
1. Problem synced without test cases initially (`generation_status: pending`)
2. Background worker polls `generation_queue` every 5 minutes
3. Uses GPT-4 to generate 8 test cases from problem description
4. Validates generated tests against user's submitted code via Judge0
5. Only saves test cases that pass validation

**Supabase Edge Function**: Runs as cron job, processes pending problems in batches.

### Frontend Changes

1. **Settings Page** - Add API Keys section
   - Generate new keys
   - List existing keys with last used date
   - Revoke keys

2. **Dashboard** - Handle external problems
   - Show "pending generation" badge for problems without test cases
   - Link to external source URL
   - Filter by source (acodeaday vs leetcode)

## Tasks

### Phase 1: Backend Foundation

- [ ] **1.1** Add migration for `problems` table fields (`source`, `external_id`, `external_url`, `generation_status`)
- [ ] **1.2** Add migration for `generation_queue` table
- [ ] **1.3** Add migration for `api_keys` table
- [ ] **1.4** Update `Problem` SQLAlchemy model with new fields
- [ ] **1.5** Create `GenerationQueue` SQLAlchemy model
- [ ] **1.6** Create `APIKey` SQLAlchemy model
- [ ] **1.7** Implement API key authentication in middleware
- [ ] **1.8** Create `/api/external/api-keys` endpoints (create, list, revoke)
- [ ] **1.9** Create `/api/external/sync` endpoint
- [ ] **1.10** Write tests for new endpoints

### Phase 2: Chrome Extension

- [ ] **2.1** Initialize extension project structure in `extension/` directory
- [ ] **2.2** Configure manifest.json (Manifest V3)
- [ ] **2.3** Set up Vite build for TypeScript
- [ ] **2.4** Implement LeetCode problem scraper (title, slug, difficulty, tags, description)
- [ ] **2.5** Implement submission detector (MutationObserver on result panel)
- [ ] **2.6** Implement code capture from Monaco editor
- [ ] **2.7** Create rating modal component with Anki-style buttons
- [ ] **2.8** Create options page with API URL/key configuration
- [ ] **2.9** Create popup page with sync status
- [ ] **2.10** Implement API client for backend communication
- [ ] **2.11** Add Chrome storage wrapper for settings
- [ ] **2.12** Create extension icons (16x16, 48x48, 128x128)
- [ ] **2.13** Test extension manually on various LeetCode problems

### Phase 3: Test Case Generation

- [ ] **3.1** Create Supabase Edge Function for test case generation
- [ ] **3.2** Implement LLM prompt for generating test cases from problem description
- [ ] **3.3** Implement function signature inference from description
- [ ] **3.4** Implement starter code generation
- [ ] **3.5** Implement test case validation via Judge0
- [ ] **3.6** Handle generation failures and retries (max 3 attempts)
- [ ] **3.7** Set up pg_cron job to trigger edge function every 5 minutes
- [ ] **3.8** Add monitoring/logging for generation pipeline

### Phase 4: Frontend Integration

- [ ] **4.1** Create API keys management component
- [ ] **4.2** Add settings route for API keys
- [ ] **4.3** Update dashboard to show external problems
- [ ] **4.4** Add "pending generation" badge/indicator
- [ ] **4.5** Add source filter to problem lists
- [ ] **4.6** Add external link icon that opens original LeetCode problem

### Phase 5: Polish & Release

- [ ] **5.1** End-to-end testing of full flow
- [ ] **5.2** Error handling improvements (network failures, invalid responses)
- [ ] **5.3** Add offline queue for extension (sync when back online)
- [ ] **5.4** Write user documentation (README for extension setup)
- [ ] **5.5** Create Chrome Web Store listing assets
- [ ] **5.6** Submit to Chrome Web Store for review

## Data Captured from LeetCode

The extension captures the following on successful submission:

| Field | Source | Notes |
|-------|--------|-------|
| `title` | `[data-cy="question-title"]` | Problem title |
| `slug` | URL path segment | e.g., "two-sum" from URL |
| `difficulty` | `[diff]` element | Easy/Medium/Hard |
| `tags` | `[class*="topic-tag"]` elements | Array of topic tags |
| `description` | `[data-cy="question-content"]` | HTML content |
| `external_id` | Page source regex | LeetCode's internal problem ID |
| `external_url` | `window.location.href` | Full URL |
| `code` | Monaco editor lines | User's submitted code |
| `language` | `[data-cy="lang-select"]` | Selected language |

## API Schema

### POST /api/external/sync

**Request:**
```json
{
  "source": "leetcode",
  "external_id": "1",
  "external_url": "https://leetcode.com/problems/two-sum/",
  "title": "Two Sum",
  "slug": "two-sum",
  "difficulty": "easy",
  "tags": ["Array", "Hash Table"],
  "description": "<p>Given an array of integers...</p>",
  "code": "class Solution:\n    def twoSum(self, nums, target):\n        ...",
  "language": "python",
  "rating": "good"
}
```

**Response:**
```json
{
  "success": true,
  "problem_id": "uuid-here",
  "is_new": true,
  "generation_status": "pending",
  "next_review_date": "2025-01-25",
  "interval_days": 3
}
```

## Edge Cases & Error Handling

1. **Duplicate sync** - Same problem synced multiple times → Update existing, apply rating
2. **Network failure** - Extension shows error toast, user can retry
3. **API key expired** - Extension prompts to re-authenticate in options
4. **Generation failure** - Problem marked with failed status, user notified
5. **LeetCode DOM changes** - Extension may need selector updates, version bump

## Dependencies

- **Extension**: TypeScript, Vite, Chrome Extensions API (Manifest V3)
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Generation**: OpenAI GPT-4 API, Judge0 CE
- **Database**: Supabase PostgreSQL with pg_cron

## Security Considerations

1. **API keys** - Hashed before storage, only shown once on creation
2. **CORS** - Backend must allow requests from extension context
3. **Rate limiting** - Implement per-user rate limits on sync endpoint
4. **Input validation** - Sanitize HTML description before storage

## Out of Scope (Future)

- NeetCode.io support (similar scraping approach)
- Firefox extension
- Problem deduplication across sources
- Solution diff/comparison over time
- Offline queue with background sync

## References

- [Technical Spec](/docs/LEETCODE_SYNC_SPEC.md) - Detailed implementation spec with code examples
- [Chrome Extension Docs](https://developer.chrome.com/docs/extensions/mv3/)
- [Manifest V3 Migration](https://developer.chrome.com/docs/extensions/mv3/intro/)
