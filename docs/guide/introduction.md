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

### Spaced Repetition

The app uses a simplified spaced repetition algorithm:

- **First solve**: Problem enters the review queue, due in 7 days
- **Second solve**: Problem is marked as "Mastered" and removed from rotation
- **"Show Again"**: You can manually re-add mastered problems to the rotation

```
                    ┌─────────────┐
                    │   Unsolved  │
                    └──────┬──────┘
                           │
                      Solve once
                           │
                           ▼
                    ┌─────────────┐
                    │  In Review  │◄─────────────┐
                    │  (due 7d)   │              │
                    └──────┬──────┘              │
                           │                     │
                      Solve twice          "Show Again"
                           │                     │
                           ▼                     │
                    ┌─────────────┐              │
                    │  Mastered   │──────────────┘
                    └─────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) with async SQLAlchemy 2.0 |
| Frontend | TanStack (React) |
| Code Editor | Monaco Editor |
| Code Execution | Judge0 CE (self-hosted) |
| Database | Supabase PostgreSQL |
| Auth | HTTP Basic Auth |
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

## MVP Scope

The current implementation focuses on:

- Python support (more languages coming)
- Spaced repetition with configurable intervals
- Monaco editor integration
- Self-hosted Judge0 for code execution

Future phases will add additional languages (JavaScript, Go, etc.) and more advanced spaced repetition features.

## Next Steps

Ready to get started? Head over to the [Quick Start](/guide/quick-start) guide to set up acodeaday locally.
