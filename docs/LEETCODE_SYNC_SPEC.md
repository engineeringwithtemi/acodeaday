# LeetCode Sync Extension - Technical Specification

## Overview

A Chrome extension that captures successful LeetCode submissions and syncs them to acodeaday for spaced repetition tracking. Problems are lazily enriched with generated test cases via a background workflow.

## Goals

1. Allow users to practice on LeetCode while tracking progress in acodeaday
2. Apply Anki-style spaced repetition to any LeetCode problem
3. Enable in-app practice for synced problems (after test case generation)
4. Maintain a single source of truth for all coding practice

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Flow                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. User solves problem on LeetCode                                         │
│  2. On successful submission → Extension detects & shows rating modal       │
│  3. User rates difficulty (Again/Hard/Good/Easy)                            │
│  4. Extension POSTs to acodeaday API                                        │
│  5. Problem appears in acodeaday dashboard for review                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           System Architecture                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────────────────┐  │
│  │   Chrome     │      │   acodeaday  │      │   Background Worker      │  │
│  │   Extension  │─────▶│   Backend    │─────▶│   (Supabase Edge Fn)     │  │
│  └──────────────┘      └──────────────┘      └──────────────────────────┘  │
│        │                      │                         │                   │
│        │                      ▼                         ▼                   │
│        │               ┌──────────────┐         ┌──────────────┐           │
│        │               │   Supabase   │         │   LLM API    │           │
│        │               │   Database   │         │   (OpenAI)   │           │
│        │               └──────────────┘         └──────────────┘           │
│        │                      │                         │                   │
│        │                      ▼                         │                   │
│        │               ┌──────────────┐                 │                   │
│        └──────────────▶│   Judge0     │◀────────────────┘                   │
│         (future)       │   (validate) │                                     │
│                        └──────────────┘                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Chrome Extension

### Directory Structure

```
extension/
├── manifest.json
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── content/
│   │   ├── leetcode-detector.ts    # Injected into LeetCode pages
│   │   └── styles.css              # Rating modal styles
│   ├── background/
│   │   └── service-worker.ts       # Background service worker
│   ├── popup/
│   │   ├── popup.html              # Extension popup (status/settings shortcut)
│   │   ├── popup.ts
│   │   └── popup.css
│   ├── options/
│   │   ├── options.html            # Settings page
│   │   ├── options.ts
│   │   └── options.css
│   ├── components/
│   │   └── RatingModal.ts          # Rating modal component
│   ├── lib/
│   │   ├── api.ts                  # acodeaday API client
│   │   ├── scraper.ts              # LeetCode page scraper
│   │   └── storage.ts              # Chrome storage wrapper
│   └── types/
│       └── index.ts                # Shared types
└── assets/
    ├── icon-16.png
    ├── icon-48.png
    └── icon-128.png
```

### manifest.json

```json
{
  "manifest_version": 3,
  "name": "acodeaday - LeetCode Sync",
  "version": "1.0.0",
  "description": "Sync your LeetCode practice with acodeaday for spaced repetition",
  "permissions": [
    "storage",
    "activeTab"
  ],
  "host_permissions": [
    "https://leetcode.com/*"
  ],
  "background": {
    "service_worker": "src/background/service-worker.ts",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["https://leetcode.com/problems/*"],
      "js": ["src/content/leetcode-detector.ts"],
      "css": ["src/content/styles.css"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "src/popup/popup.html",
    "default_icon": {
      "16": "assets/icon-16.png",
      "48": "assets/icon-48.png",
      "128": "assets/icon-128.png"
    }
  },
  "options_ui": {
    "page": "src/options/options.html",
    "open_in_tab": true
  },
  "icons": {
    "16": "assets/icon-16.png",
    "48": "assets/icon-48.png",
    "128": "assets/icon-128.png"
  }
}
```

### Content Script: LeetCode Detector

```typescript
// src/content/leetcode-detector.ts

interface ProblemData {
  title: string
  slug: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  tags: string[]
  description: string
  externalId: string
  externalUrl: string
}

interface SubmissionData {
  code: string
  language: string
  runtime: string
  memory: string
  passed: boolean
}

class LeetCodeDetector {
  private problemData: ProblemData | null = null
  private observer: MutationObserver | null = null

  constructor() {
    this.init()
  }

  private async init() {
    // Wait for page to load
    await this.waitForElement('[data-cy="question-title"]')

    // Scrape problem data
    this.problemData = this.scrapeProblemData()

    // Watch for submission results
    this.observeSubmissions()
  }

  private scrapeProblemData(): ProblemData {
    const title = document.querySelector('[data-cy="question-title"]')?.textContent || ''
    const slug = window.location.pathname.split('/')[2]
    const difficultyEl = document.querySelector('[diff]')
    const difficulty = difficultyEl?.textContent as 'Easy' | 'Medium' | 'Hard'

    // Get tags
    const tagElements = document.querySelectorAll('[class*="topic-tag"]')
    const tags = Array.from(tagElements).map(el => el.textContent || '')

    // Get description
    const descriptionEl = document.querySelector('[data-cy="question-content"]')
    const description = descriptionEl?.innerHTML || ''

    // Extract problem ID from URL or page
    const externalId = this.extractProblemId()

    return {
      title,
      slug,
      difficulty,
      tags,
      description,
      externalId,
      externalUrl: window.location.href
    }
  }

  private extractProblemId(): string {
    // LeetCode problem IDs can be found in various places
    // Try to extract from the page
    const match = document.body.innerHTML.match(/"questionId":"(\d+)"/)
    return match ? match[1] : ''
  }

  private observeSubmissions() {
    // Watch for submission result panel
    this.observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList') {
          this.checkForSubmissionResult()
        }
      }
    })

    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    })
  }

  private checkForSubmissionResult() {
    // Look for "Accepted" result
    const acceptedEl = document.querySelector('[data-e2e-locator="submission-result"]')
    if (acceptedEl?.textContent?.includes('Accepted')) {
      this.handleSuccessfulSubmission()
    }
  }

  private async handleSuccessfulSubmission() {
    // Prevent duplicate triggers
    if (document.querySelector('#acodeaday-rating-modal')) return

    // Scrape submission data
    const submissionData = this.scrapeSubmissionData()

    if (submissionData.passed && this.problemData) {
      // Show rating modal
      this.showRatingModal(this.problemData, submissionData)
    }
  }

  private scrapeSubmissionData(): SubmissionData {
    // Get the submitted code from Monaco editor or submission details
    const codeEl = document.querySelector('.monaco-editor .view-lines')
    const code = this.getCodeFromEditor()

    // Get language
    const languageEl = document.querySelector('[data-cy="lang-select"]')
    const language = languageEl?.textContent?.toLowerCase() || 'python'

    // Get runtime/memory
    const runtime = document.querySelector('[data-e2e-locator="submission-runtime"]')?.textContent || ''
    const memory = document.querySelector('[data-e2e-locator="submission-memory"]')?.textContent || ''

    return {
      code,
      language,
      runtime,
      memory,
      passed: true
    }
  }

  private getCodeFromEditor(): string {
    // Get code from Monaco editor
    // This may need adjustment based on LeetCode's implementation
    const lines = document.querySelectorAll('.monaco-editor .view-line')
    return Array.from(lines).map(line => line.textContent || '').join('\n')
  }

  private showRatingModal(problem: ProblemData, submission: SubmissionData) {
    // Create and show rating modal
    const modal = new RatingModal({
      problem,
      submission,
      onRate: async (rating) => {
        await this.syncToAcodeaday(problem, submission, rating)
      },
      onSkip: () => {
        // User chose not to sync
      }
    })

    modal.show()
  }

  private async syncToAcodeaday(
    problem: ProblemData,
    submission: SubmissionData,
    rating: 'again' | 'hard' | 'good' | 'easy'
  ) {
    const api = new AcodeadayAPI()

    try {
      await api.syncProblem({
        source: 'leetcode',
        external_id: problem.externalId,
        external_url: problem.externalUrl,
        title: problem.title,
        slug: problem.slug,
        difficulty: problem.difficulty.toLowerCase(),
        tags: problem.tags,
        description: problem.description,
        code: submission.code,
        language: submission.language,
        rating
      })

      this.showSuccessNotification()
    } catch (error) {
      this.showErrorNotification(error)
    }
  }

  private waitForElement(selector: string): Promise<Element> {
    return new Promise((resolve) => {
      const el = document.querySelector(selector)
      if (el) {
        resolve(el)
        return
      }

      const observer = new MutationObserver(() => {
        const el = document.querySelector(selector)
        if (el) {
          observer.disconnect()
          resolve(el)
        }
      })

      observer.observe(document.body, {
        childList: true,
        subtree: true
      })
    })
  }
}

// Initialize
new LeetCodeDetector()
```

### Rating Modal Component

```typescript
// src/components/RatingModal.ts

interface RatingModalProps {
  problem: ProblemData
  submission: SubmissionData
  onRate: (rating: 'again' | 'hard' | 'good' | 'easy') => Promise<void>
  onSkip: () => void
}

class RatingModal {
  private props: RatingModalProps
  private element: HTMLElement | null = null

  constructor(props: RatingModalProps) {
    this.props = props
  }

  show() {
    this.element = document.createElement('div')
    this.element.id = 'acodeaday-rating-modal'
    this.element.innerHTML = this.render()
    document.body.appendChild(this.element)

    this.attachEventListeners()
  }

  private render(): string {
    return `
      <div class="acodeaday-overlay">
        <div class="acodeaday-modal">
          <div class="acodeaday-header">
            <img src="${chrome.runtime.getURL('assets/icon-48.png')}" alt="acodeaday" />
            <h2>Sync to acodeaday</h2>
          </div>

          <div class="acodeaday-content">
            <p class="acodeaday-problem-title">${this.props.problem.title}</p>
            <p class="acodeaday-prompt">How well did you understand this problem?</p>

            <div class="acodeaday-ratings">
              <button data-rating="again" class="rating-btn rating-again">
                <span class="rating-emoji">😰</span>
                <span class="rating-label">Again</span>
                <span class="rating-desc">Couldn't solve / looked at solution</span>
              </button>

              <button data-rating="hard" class="rating-btn rating-hard">
                <span class="rating-emoji">🤔</span>
                <span class="rating-label">Hard</span>
                <span class="rating-desc">Solved but struggled</span>
              </button>

              <button data-rating="good" class="rating-btn rating-good">
                <span class="rating-emoji">😊</span>
                <span class="rating-label">Good</span>
                <span class="rating-desc">Solved with some effort</span>
              </button>

              <button data-rating="easy" class="rating-btn rating-easy">
                <span class="rating-emoji">😎</span>
                <span class="rating-label">Easy</span>
                <span class="rating-desc">Solved quickly</span>
              </button>
            </div>
          </div>

          <div class="acodeaday-footer">
            <button class="acodeaday-skip">Skip (don't sync)</button>
          </div>
        </div>
      </div>
    `
  }

  private attachEventListeners() {
    // Rating buttons
    this.element?.querySelectorAll('.rating-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const rating = (e.currentTarget as HTMLElement).dataset.rating as 'again' | 'hard' | 'good' | 'easy'
        this.setLoading(true)
        try {
          await this.props.onRate(rating)
          this.close()
        } catch (error) {
          this.showError(error)
        } finally {
          this.setLoading(false)
        }
      })
    })

    // Skip button
    this.element?.querySelector('.acodeaday-skip')?.addEventListener('click', () => {
      this.props.onSkip()
      this.close()
    })

    // Close on overlay click
    this.element?.querySelector('.acodeaday-overlay')?.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.props.onSkip()
        this.close()
      }
    })
  }

  private setLoading(loading: boolean) {
    this.element?.classList.toggle('loading', loading)
  }

  private showError(error: any) {
    // Show error message in modal
  }

  private close() {
    this.element?.remove()
  }
}
```

### Options Page

```typescript
// src/options/options.ts

interface Settings {
  apiUrl: string
  apiKey: string
  autoSync: boolean
  showNotifications: boolean
}

class OptionsPage {
  private form: HTMLFormElement

  constructor() {
    this.form = document.getElementById('settings-form') as HTMLFormElement
    this.init()
  }

  private async init() {
    // Load saved settings
    const settings = await this.loadSettings()
    this.populateForm(settings)

    // Attach event listeners
    this.form.addEventListener('submit', (e) => this.handleSubmit(e))
    document.getElementById('test-connection')?.addEventListener('click', () => this.testConnection())
  }

  private async loadSettings(): Promise<Settings> {
    return new Promise((resolve) => {
      chrome.storage.sync.get({
        apiUrl: '',
        apiKey: '',
        autoSync: true,
        showNotifications: true
      }, (settings) => {
        resolve(settings as Settings)
      })
    })
  }

  private populateForm(settings: Settings) {
    (document.getElementById('api-url') as HTMLInputElement).value = settings.apiUrl
    ;(document.getElementById('api-key') as HTMLInputElement).value = settings.apiKey
    ;(document.getElementById('auto-sync') as HTMLInputElement).checked = settings.autoSync
    ;(document.getElementById('show-notifications') as HTMLInputElement).checked = settings.showNotifications
  }

  private async handleSubmit(e: Event) {
    e.preventDefault()

    const settings: Settings = {
      apiUrl: (document.getElementById('api-url') as HTMLInputElement).value,
      apiKey: (document.getElementById('api-key') as HTMLInputElement).value,
      autoSync: (document.getElementById('auto-sync') as HTMLInputElement).checked,
      showNotifications: (document.getElementById('show-notifications') as HTMLInputElement).checked
    }

    await this.saveSettings(settings)
    this.showSuccess('Settings saved!')
  }

  private async saveSettings(settings: Settings): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.sync.set(settings, () => {
        resolve()
      })
    })
  }

  private async testConnection() {
    const apiUrl = (document.getElementById('api-url') as HTMLInputElement).value
    const apiKey = (document.getElementById('api-key') as HTMLInputElement).value

    try {
      const response = await fetch(`${apiUrl}/api/health`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`
        }
      })

      if (response.ok) {
        this.showSuccess('Connection successful!')
      } else {
        this.showError('Connection failed: ' + response.statusText)
      }
    } catch (error) {
      this.showError('Connection failed: ' + (error as Error).message)
    }
  }

  private showSuccess(message: string) {
    // Show success toast
  }

  private showError(message: string) {
    // Show error toast
  }
}

new OptionsPage()
```

---

## Backend Changes

### New Database Tables

```sql
-- Add source tracking to problems table
ALTER TABLE problems ADD COLUMN source VARCHAR(50) DEFAULT 'acodeaday';
ALTER TABLE problems ADD COLUMN external_id VARCHAR(100);
ALTER TABLE problems ADD COLUMN external_url TEXT;
ALTER TABLE problems ADD COLUMN generation_status VARCHAR(20) DEFAULT 'ready';
-- 'ready' | 'pending' | 'generating' | 'failed'

-- Create index for external lookups
CREATE UNIQUE INDEX idx_problems_source_external
ON problems(source, external_id)
WHERE external_id IS NOT NULL;

-- Generation queue table
CREATE TABLE generation_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    -- 'pending' | 'processing' | 'completed' | 'failed'
    attempts INT DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_generation_queue_status ON generation_queue(status);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash of the key
    name VARCHAR(100),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

### Updated Problem Model

```python
# backend/app/db/tables.py

class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)
    pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    constraints: Mapped[list] = mapped_column(ARRAY(String), default=[])
    examples: Mapped[dict] = mapped_column(JSONB, default={})

    # Source tracking (new fields)
    source: Mapped[str] = mapped_column(String(50), default="acodeaday")
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_status: Mapped[str] = mapped_column(String(20), default="ready")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    languages: Mapped[list["ProblemLanguage"]] = relationship(back_populates="problem", lazy="selectin")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="problem", lazy="selectin")


class GenerationQueue(Base):
    __tablename__ = "generation_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    problem: Mapped["Problem"] = relationship()


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"))
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### New API Endpoints

```python
# backend/app/routes/external.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/external", tags=["external"])


class ExternalSyncRequest(BaseModel):
    source: str  # "leetcode"
    external_id: str
    external_url: str
    title: str
    slug: str
    difficulty: str
    tags: list[str]
    description: str
    code: str
    language: str
    rating: str  # "again" | "hard" | "good" | "easy"


class ExternalSyncResponse(BaseModel):
    success: bool
    problem_id: str
    is_new: bool
    generation_status: str
    next_review_date: str | None
    interval_days: int


@router.post("/sync", response_model=ExternalSyncResponse)
async def sync_external_problem(
    request: ExternalSyncRequest,
    user: dict = Depends(get_current_user),  # Supports both Supabase JWT and API key
    db: AsyncSession = Depends(get_db),
):
    """
    Sync a problem from external source (e.g., LeetCode).

    1. Find or create problem record
    2. Queue for test case generation if new
    3. Record submission
    4. Apply rating
    """
    user_id = user["id"]

    # Check if problem exists
    existing = await find_problem_by_external(
        db,
        source=request.source,
        external_id=request.external_id
    )

    if existing:
        problem = existing
        is_new = False
    else:
        # Create new problem (minimal data, pending generation)
        problem = Problem(
            title=request.title,
            slug=generate_unique_slug(request.slug, request.source),
            description=request.description,
            difficulty=Difficulty(request.difficulty.lower()),
            pattern=infer_pattern_from_tags(request.tags),
            sequence_number=await get_next_sequence_number(db),
            source=request.source,
            external_id=request.external_id,
            external_url=request.external_url,
            generation_status="pending",
        )
        db.add(problem)
        await db.flush()  # Get problem.id

        # Queue for test case generation
        queue_item = GenerationQueue(problem_id=problem.id)
        db.add(queue_item)

        is_new = True

    # Record submission (user's code becomes reference solution candidate)
    submission = Submission(
        user_id=user_id,
        problem_id=problem.id,
        code=request.code,
        language=Language(request.language),
        passed=True,
        runtime_ms=None,
        memory_kb=None,
    )
    db.add(submission)

    # Ensure user progress exists
    await ensure_user_progress(db, user_id, problem.id)

    # Apply rating
    rating_result = await apply_rating(db, user_id, problem.id, request.rating)

    await db.commit()

    return ExternalSyncResponse(
        success=True,
        problem_id=str(problem.id),
        is_new=is_new,
        generation_status=problem.generation_status,
        next_review_date=rating_result.get("next_review_date"),
        interval_days=rating_result.get("interval_days", 0),
    )


# API Key management endpoints

class CreateAPIKeyRequest(BaseModel):
    name: str | None = None
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    id: str
    name: str | None
    key: str  # Only returned on creation
    created_at: str
    expires_at: str | None


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new API key for the extension."""
    import secrets
    import hashlib

    # Generate secure random key
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    api_key = APIKey(
        user_id=user["id"],
        key_hash=key_hash,
        name=request.name,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()

    return APIKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        key=raw_key,  # Only time we return the actual key
        created_at=api_key.created_at.isoformat(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


@router.get("/api-keys")
async def list_api_keys(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's API keys (without the actual key values)."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == user["id"])
        .where(APIKey.revoked_at.is_(None))
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        {
            "id": str(k.id),
            "name": k.name,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id)
        .where(APIKey.user_id == user["id"])
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.revoked_at = datetime.utcnow()
    await db.commit()

    return {"success": True}
```

### Auth Middleware Update

```python
# backend/app/middleware/auth.py

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Authenticate user via Supabase JWT or API key.
    """
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Try Supabase JWT first
        try:
            user = await verify_supabase_token(token)
            return user
        except:
            pass

        # Try API key
        import hashlib
        key_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await db.execute(
            select(APIKey)
            .where(APIKey.key_hash == key_hash)
            .where(APIKey.revoked_at.is_(None))
        )
        api_key = result.scalar_one_or_none()

        if api_key:
            # Check expiry
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="API key expired")

            # Update last used
            api_key.last_used_at = datetime.utcnow()

            return {"id": str(api_key.user_id), "auth_type": "api_key"}

    raise HTTPException(status_code=401, detail="Invalid authentication")
```

---

## Background Worker: Test Case Generation

### Supabase Edge Function

```typescript
// supabase/functions/generate-test-cases/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const BATCH_SIZE = 5
const MAX_ATTEMPTS = 3

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  )

  // Get pending items from queue
  const { data: queueItems, error } = await supabase
    .from("generation_queue")
    .select("*, problem:problems(*)")
    .eq("status", "pending")
    .lt("attempts", MAX_ATTEMPTS)
    .order("created_at", { ascending: true })
    .limit(BATCH_SIZE)

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  const results = []

  for (const item of queueItems) {
    try {
      // Mark as processing
      await supabase
        .from("generation_queue")
        .update({ status: "processing", updated_at: new Date().toISOString() })
        .eq("id", item.id)

      // Generate test cases using LLM
      const testCases = await generateTestCases(item.problem)

      // Get user's submitted code as reference solution
      const { data: submission } = await supabase
        .from("submissions")
        .select("code, language")
        .eq("problem_id", item.problem_id)
        .eq("passed", true)
        .order("submitted_at", { ascending: false })
        .limit(1)
        .single()

      if (submission) {
        // Validate test cases against user's code
        const validationResult = await validateTestCases(
          submission.code,
          submission.language,
          testCases
        )

        if (validationResult.success) {
          // Save test cases
          await supabase.from("test_cases").insert(
            testCases.map((tc, idx) => ({
              problem_id: item.problem_id,
              sequence: idx + 1,
              input: tc.input,
              expected: tc.expected,
              is_hidden: idx >= 3, // First 3 visible, rest hidden
            }))
          )

          // Save reference solution
          await supabase.from("problem_languages").insert({
            problem_id: item.problem_id,
            language: submission.language,
            starter_code: generateStarterCode(item.problem),
            reference_solution: submission.code,
            function_signature: testCases[0].function_signature,
          })

          // Mark as complete
          await supabase
            .from("generation_queue")
            .update({
              status: "completed",
              completed_at: new Date().toISOString(),
            })
            .eq("id", item.id)

          await supabase
            .from("problems")
            .update({ generation_status: "ready" })
            .eq("id", item.problem_id)

          results.push({ problem_id: item.problem_id, success: true })
        } else {
          throw new Error(`Validation failed: ${validationResult.errors.join(", ")}`)
        }
      }
    } catch (error) {
      // Mark as failed, increment attempts
      await supabase
        .from("generation_queue")
        .update({
          status: item.attempts + 1 >= MAX_ATTEMPTS ? "failed" : "pending",
          attempts: item.attempts + 1,
          last_error: error.message,
          updated_at: new Date().toISOString(),
        })
        .eq("id", item.id)

      if (item.attempts + 1 >= MAX_ATTEMPTS) {
        await supabase
          .from("problems")
          .update({ generation_status: "failed" })
          .eq("id", item.problem_id)
      }

      results.push({ problem_id: item.problem_id, success: false, error: error.message })
    }
  }

  return new Response(JSON.stringify({ processed: results.length, results }), {
    headers: { "Content-Type": "application/json" },
  })
})


async function generateTestCases(problem: any) {
  const openai = new OpenAI({ apiKey: Deno.env.get("OPENAI_API_KEY") })

  const prompt = `
Given this coding problem:

Title: ${problem.title}
Difficulty: ${problem.difficulty}
Description: ${problem.description}

Generate 8 test cases for this problem. Include:
1. 2 simple/edge cases (empty input, single element, etc.)
2. 4 normal cases with varying inputs
3. 2 complex/larger cases

Return as JSON:
{
  "function_signature": {
    "name": "functionName",
    "params": [{"name": "param1", "type": "List[int]"}],
    "return_type": "int"
  },
  "test_cases": [
    {"input": [[2,7,11,15], 9], "expected": [0,1]},
    ...
  ]
}
`

  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [{ role: "user", content: prompt }],
    response_format: { type: "json_object" },
  })

  return JSON.parse(response.choices[0].message.content)
}


async function validateTestCases(
  code: string,
  language: string,
  testCases: any[]
): Promise<{ success: boolean; errors: string[] }> {
  // Call Judge0 to validate
  const judge0Url = Deno.env.get("JUDGE0_URL")

  // ... validation logic using Judge0

  return { success: true, errors: [] }
}


function generateStarterCode(problem: any): string {
  // Generate language-specific starter code template
  return `class Solution:
    def ${problem.function_name}(self, ${problem.params}):
        # Your code here
        pass
`
}
```

### Cron Job Setup

```sql
-- Supabase cron job to trigger generation
SELECT cron.schedule(
  'generate-test-cases',
  '*/5 * * * *',  -- Every 5 minutes
  $$
  SELECT net.http_post(
    url := 'https://your-project.supabase.co/functions/v1/generate-test-cases',
    headers := '{"Authorization": "Bearer ' || current_setting('app.service_role_key') || '"}'::jsonb
  );
  $$
);
```

---

## Frontend Changes

### API Keys Settings Page

Add a new settings section in the frontend for managing API keys:

```typescript
// frontend/src/routes/settings.tsx

function APIKeysSection() {
  const [keys, setKeys] = useState<APIKey[]>([])
  const [newKeyName, setNewKeyName] = useState('')
  const [generatedKey, setGeneratedKey] = useState<string | null>(null)

  const createKey = async () => {
    const response = await apiPost('/api/external/api-keys', { name: newKeyName })
    setGeneratedKey(response.key)
    // Refresh list
    fetchKeys()
  }

  const revokeKey = async (keyId: string) => {
    await apiDelete(`/api/external/api-keys/${keyId}`)
    fetchKeys()
  }

  return (
    <div>
      <h2>API Keys</h2>
      <p>Use API keys to connect the Chrome extension to your account.</p>

      {generatedKey && (
        <div className="bg-yellow-500/20 p-4 rounded-lg mb-4">
          <p className="font-bold">Your new API key (copy it now, it won't be shown again):</p>
          <code className="block p-2 bg-gray-800 rounded mt-2">{generatedKey}</code>
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Key name (optional)"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
        />
        <button onClick={createKey}>Generate New Key</button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Created</th>
            <th>Last Used</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key.id}>
              <td>{key.name || 'Unnamed'}</td>
              <td>{formatDate(key.created_at)}</td>
              <td>{key.last_used_at ? formatDate(key.last_used_at) : 'Never'}</td>
              <td>
                <button onClick={() => revokeKey(key.id)}>Revoke</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## Implementation Phases

### Phase 1: Extension MVP (Week 1-2)
- [ ] Scaffold extension structure
- [ ] Implement LeetCode problem detection
- [ ] Implement submission detection
- [ ] Create rating modal UI
- [ ] Implement options page with API URL/key config
- [ ] Basic API client

### Phase 2: Backend API (Week 2-3)
- [ ] Add source tracking fields to Problem model
- [ ] Create migration
- [ ] Implement `/api/external/sync` endpoint
- [ ] Implement API key generation/management
- [ ] Update auth middleware for API key support

### Phase 3: Test Case Generation (Week 3-4)
- [ ] Create generation_queue table
- [ ] Implement Supabase Edge Function
- [ ] Implement LLM prompt for test case generation
- [ ] Implement validation against user's code
- [ ] Set up cron job

### Phase 4: Frontend Integration (Week 4)
- [ ] Add API keys management UI
- [ ] Show external problems in dashboard
- [ ] Handle "pending generation" status
- [ ] Link to external source

### Phase 5: Testing & Polish (Week 5)
- [ ] End-to-end testing
- [ ] Error handling improvements
- [ ] Chrome Web Store submission
- [ ] Documentation

---

## Open Questions

1. **NeetCode support?** - Should we also support NeetCode.io? Similar scraping approach.

2. **Problem deduplication** - How to handle if user syncs same problem from different sources?

3. **Code comparison** - Should we show diff between user's solutions over time?

4. **Offline support** - Should extension queue syncs when offline?

5. **Rate limiting** - How to prevent abuse of the sync endpoint?
