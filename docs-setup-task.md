# Task: Set Up VitePress Documentation for acodeaday

## Objective
Create a documentation site using VitePress for the acodeaday project, covering local setup, cloud deployment, and usage guides.

## Project Context
- **Project**: acodeaday - Daily coding practice app with spaced repetition
- **Tech Stack**: FastAPI (Python) backend, TanStack (React) frontend, Supabase PostgreSQL, Judge0 for code execution
- **Location**: `/Users/to/tee/acodeaday/`

## Steps

### 1. Initialize VitePress in `/docs` folder

```bash
cd /Users/to/tee/acodeaday
mkdir docs && cd docs
npm init -y
npm add -D vitepress
npx vitepress init
```

When prompted:
- Where to put VitePress config: `./`
- Site title: `acodeaday`
- Description: `Daily coding practice with spaced repetition`
- Theme: Default
- TypeScript: No (keep it simple)

### 2. Configure VitePress

Create/update `.vitepress/config.js`:

```js
export default {
  title: 'acodeaday',
  description: 'Daily coding practice with spaced repetition',
  themeConfig: {
    logo: '/logo.svg',
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'API Reference', link: '/api/overview' },
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Introduction', link: '/guide/introduction' },
            { text: 'Quick Start', link: '/guide/quick-start' },
          ]
        },
        {
          text: 'Local Development',
          items: [
            { text: 'Prerequisites', link: '/guide/prerequisites' },
            { text: 'Backend Setup', link: '/guide/backend-setup' },
            { text: 'Frontend Setup', link: '/guide/frontend-setup' },
            { text: 'Judge0 Setup', link: '/guide/judge0-setup' },
            { text: 'Database Setup', link: '/guide/database-setup' },
          ]
        },
        {
          text: 'Deployment',
          items: [
            { text: 'Overview', link: '/guide/deployment-overview' },
            { text: 'Deploy Backend', link: '/guide/deploy-backend' },
            { text: 'Deploy Frontend', link: '/guide/deploy-frontend' },
            { text: 'Environment Variables', link: '/guide/environment-variables' },
          ]
        },
        {
          text: 'Configuration',
          items: [
            { text: 'Adding Problems', link: '/guide/adding-problems' },
            { text: 'Spaced Repetition', link: '/guide/spaced-repetition' },
          ]
        }
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Overview', link: '/api/overview' },
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Problems', link: '/api/problems' },
            { text: 'Submissions', link: '/api/submissions' },
            { text: 'Progress', link: '/api/progress' },
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/your-repo/acodeaday' }
    ],
    search: {
      provider: 'local'
    }
  }
}
```

### 3. Create Documentation Pages

Create the following markdown files with content derived from the existing docs (CLAUDE.md, TASKS.md, README.md, spec.md):

#### `/docs/index.md` (Homepage)
```md
---
layout: home
hero:
  name: acodeaday
  text: Daily Coding Practice
  tagline: Master the Blind 75 with spaced repetition
  actions:
    - theme: brand
      text: Get Started
      link: /guide/introduction
    - theme: alt
      text: View on GitHub
      link: https://github.com/your-repo/acodeaday
features:
  - title: Spaced Repetition
    details: Scientifically-proven memory technique to retain coding patterns
  - title: Daily Practice
    details: One new problem + review problems each day
  - title: Judge0 Integration
    details: Run code in a secure sandbox environment
---
```

#### `/docs/guide/introduction.md`
- What is acodeaday
- Core philosophy ("A code a day keeps rejection away")
- How spaced repetition works
- Tech stack overview

#### `/docs/guide/quick-start.md`
- Minimal steps to get running locally
- Docker Compose option for fastest setup

#### `/docs/guide/prerequisites.md`
- Node.js 22+
- Python 3.12+ with uv
- Docker (for Judge0)
- Supabase account (or local Supabase)

#### `/docs/guide/backend-setup.md`
Content from existing docs:
- Clone repo
- `cd backend && uv sync`
- Set up `.env` file
- Run migrations: `uv run alembic upgrade head`
- Seed problems: `uv run python scripts/seed_problems.py seed`
- Start server: `uv run uvicorn app.main:app --reload`

#### `/docs/guide/frontend-setup.md`
- `cd frontend && npm install`
- Configure `.env` with API URL
- `npm run dev`

#### `/docs/guide/judge0-setup.md`
- Docker Compose setup for Judge0
- Configuration options
- Testing the connection

#### `/docs/guide/database-setup.md`
- Supabase project creation
- Local Supabase with Docker
- Running migrations
- Seeding initial data

#### `/docs/guide/deployment-overview.md`
- Architecture diagram
- Recommended hosting options (Vercel, Railway, Fly.io)

#### `/docs/guide/environment-variables.md`
Document all env vars:
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `JUDGE0_URL`
- `DEFAULT_USER_EMAIL`
- `DEFAULT_USER_PASSWORD`
- etc.

#### `/docs/guide/adding-problems.md`
- YAML format for problems
- Using the seeder CLI
- Test case format

#### `/docs/guide/spaced-repetition.md`
- How the algorithm works
- First solve → 7 days → mastered
- Show again feature

#### `/docs/api/overview.md`
- Base URL
- Authentication method
- Response format

#### `/docs/api/authentication.md`
- Supabase Auth flow
- JWT tokens
- Example requests

#### `/docs/api/problems.md`
- `GET /api/problems/`
- `GET /api/problems/:slug`
- `GET /api/today`

#### `/docs/api/submissions.md`
- `POST /api/run`
- `POST /api/submit`
- `GET /api/submissions/:problem_id`

#### `/docs/api/progress.md`
- `GET /api/progress`
- `GET /api/mastered`
- `POST /api/rate`

### 4. Add npm scripts to docs/package.json

```json
{
  "scripts": {
    "dev": "vitepress dev",
    "build": "vitepress build",
    "preview": "vitepress preview"
  }
}
```

### 5. Test Locally

```bash
cd /Users/to/tee/acodeaday/docs
npm run dev
```

Verify:
- Homepage loads
- Navigation works
- All pages render correctly
- Search works

### 6. Add to .gitignore

Add to `/Users/to/tee/acodeaday/.gitignore`:
```
docs/.vitepress/cache
docs/.vitepress/dist
docs/node_modules
```

## Source Files to Reference

Pull content from these existing files:
- `/Users/to/tee/acodeaday/.claude/CLAUDE.md` - Project overview, architecture
- `/Users/to/tee/acodeaday/backend/README.md` - Backend setup
- `/Users/to/tee/acodeaday/backend/data/problems/README.md` - Problem YAML format
- `/Users/to/tee/acodeaday/backend/.env.example` - Environment variables
- `/Users/to/tee/acodeaday/spec.md` - Detailed specification

## Deliverables

1. Working VitePress site in `/docs` folder
2. All documentation pages created with relevant content
3. Site builds without errors (`npm run build`)
4. Local dev server runs (`npm run dev`)
