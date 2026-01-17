# Introduction

## What is acodeaday?

acodeaday is a daily coding practice app that uses **spaced repetition** to help you master coding interview problems. Instead of cramming, you solve one new problem per day plus review problems at optimal intervals for long-term retention.

## Core Philosophy

> "An apple a day keeps the doctor away"
> **"A code a day keeps rejection away"**

The app is designed around the principle of **understanding through consistent practice**, not cramming. By spacing out your practice and reviewing problems at scientifically-proven intervals, you build lasting knowledge of coding patterns and problem-solving techniques.

## How It Works

### Daily Session

Each day, you'll see up to 3 problems:

1. **Review #1**: Your oldest overdue problem (if any)
2. **Review #2**: Your second oldest overdue problem (if any)
3. **New Problem**: The next unsolved problem in sequence

### Spaced Repetition (Anki SM-2)

The app uses the Anki SM-2 algorithm with adaptive intervals based on difficulty ratings:

After solving a problem, you rate how difficult it was:
- **Again**: Reset to 1 day (struggled/needed hints)
- **Hard**: Slower growth (×1.2), decrease ease factor
- **Good**: Normal growth (×ease factor)
- **Mastered**: Exit rotation immediately

```
                    ┌─────────────┐
                    │   Unsolved  │
                    └──────┬──────┘
                           │
                      Solve & rate
                           │
                           ▼
                    ┌─────────────┐
                    │  In Review  │◄─────────────┐
                    │ (scheduled) │              │
                    └──────┬──────┘              │
                           │                     │
                    Interval ≥30d          "Show Again"
                    or "Mastered"                │
                           │                     │
                           ▼                     │
                    ┌─────────────┐              │
                    │  Mastered   │──────────────┘
                    └─────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.13+) with async SQLAlchemy 2.0 |
| Frontend | TanStack (React 19) with TanStack Router/Query |
| Code Editor | Monaco Editor |
| Code Execution | Judge0 CE (self-hosted) |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth (JWT Bearer tokens) |
| AI Chat | litellm (Gemini, OpenAI, Anthropic) |
| Package Manager | uv (Python), npm (JavaScript) |

## Key Features

- **LeetCode-style interface**: Familiar split-pane layout with problem description and code editor
- **Secure code execution**: All code runs in Judge0 sandboxed environment
- **Progress tracking**: See your mastery progress across all problems
- **Submission history**: Review your past attempts and solutions
- **AI-powered assistance**: Get hints and explanations from AI tutors when you're stuck
- **Multiple test modes**: Run code against example tests, or submit against all tests

## Architecture

```
┌──────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Client  │──────▶│  FastAPI        │──────▶│ Judge0 (Docker) │
│ (React)  │       │  Backend        │       │                 │
└──────────┘       └─────────────────┘       └─────────────────┘
                           │
                           ▼
                   ┌─────────────────┐
                   │ Supabase        │
                   │ PostgreSQL      │
                   └─────────────────┘
```

## Current Features

The implementation includes:

- **16 Blind 75 problems** seeded and ready to practice
- **Python support** with JavaScript coming soon
- **Anki SM-2 spaced repetition** with difficulty ratings
- **Monaco editor** with auto-save
- **Self-hosted Judge0** for secure code execution
- **AI Chat assistant** for hints and explanations (Socratic or direct mode)
- **Submission history** to review past attempts

## Next Steps

Ready to get started? Head over to the [Quick Start](/guide/quick-start) guide to set up acodeaday locally.
