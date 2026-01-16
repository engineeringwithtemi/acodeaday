# Spaced Repetition

Learn how acodeaday uses spaced repetition to help you master coding problems long-term.

## What is Spaced Repetition?

Spaced repetition is a learning technique that involves reviewing information at increasing intervals. It's based on the psychological spacing effect, which shows that we learn better when study sessions are spaced out over time.

### The Forgetting Curve

Without review, we forget most of what we learn:

```
Memory
 100% │╲
      │ ╲
   75%│  ╲___
      │      ╲___
   50%│          ╲___
      │              ╲___
   25%│                  ╲___
      │                      ╲___
    0%└────────────────────────────▶ Time
      0d    7d    14d    30d    60d
```

With spaced repetition:

```
Memory
 100% │╲  ↗╲  ↗╲  ↗╲
      │ ╲↗  ╲↗  ╲↗  ╲
   75%│                ╲___
      │
   50%│
      │
   25%│
      │
    0%└────────────────────────────▶ Time
      0d    7d    14d    30d    60d
      ↑     ↑     ↑     ↑     ↑
    Review Review Review Review Review
```

Each review strengthens the memory and extends the time until the next review.

## How acodeaday Implements It

acodeaday uses a simplified spaced repetition algorithm optimized for coding practice.

### Problem States

Every problem exists in one of three states:

1. **Unsolved** - You haven't attempted it yet
2. **In Review** - Solved once, due for review in 7 days
3. **Mastered** - Solved twice, removed from rotation

```
┌─────────────┐
│  Unsolved   │
│  (New)      │
└──────┬──────┘
       │
       │ Solve 1st time
       ▼
┌─────────────┐
│  In Review  │◄─────────────────┐
│  (Due: 7d)  │                  │
└──────┬──────┘                  │
       │                         │
       │ Solve 2nd time    "Show Again"
       ▼                         │
┌─────────────┐                  │
│  Mastered   │──────────────────┘
│  (Done)     │
└─────────────┘
```

### Mastery Rules

| Event | State Change | Next Review |
|-------|-------------|-------------|
| Solve problem 1st time | Unsolved → In Review | Today + 7 days |
| Solve problem 2nd time | In Review → Mastered | None (removed from rotation) |
| Click "Show Again" on mastered | Mastered → In Review | Today |

### Daily Session Logic

Each day, acodeaday presents up to 3 problems in priority order:

```
┌─────────────────────────────────────────────┐
│  Daily Session (up to 3 problems)          │
├─────────────────────────────────────────────┤
│                                             │
│  1. REVIEW (oldest overdue)                 │
│     • next_review_date <= today             │
│     • is_mastered = false                   │
│     • Ordered by next_review_date ASC       │
│                                             │
│  2. REVIEW (second oldest overdue)          │
│     • Same criteria as #1                   │
│     • Next in queue after #1                │
│                                             │
│  3. NEW PROBLEM                             │
│     • times_solved = 0                      │
│     • Ordered by sequence_number ASC        │
│     • Next in problem sequence              │
│                                             │
└─────────────────────────────────────────────┘
```

**Priority:**
- Reviews always come before new problems
- Older reviews come before newer reviews
- If no reviews due, show up to 1 new problem

## Example Timeline

### Week 1

**Day 1:**
- Solve "Two Sum" (1st time)
- State: Unsolved → In Review
- Next review: Day 8

**Day 2:**
- Solve "Best Time to Buy Stock" (1st time)
- State: Unsolved → In Review
- Next review: Day 9

**Day 3-7:**
- Continue solving new problems

### Week 2

**Day 8:**
- Daily session shows:
  1. **Review:** Two Sum (due today)
  2. **New:** Next unsolved problem
- Solve Two Sum (2nd time)
- State: In Review → Mastered
- Two Sum is now removed from rotation

**Day 9:**
- Daily session shows:
  1. **Review:** Best Time to Buy Stock (due today)
  2. **New:** Next unsolved problem

### Week 3+

Continue the pattern:
- Review problems when due
- Work on new problems
- Build mastery over time

## Database Tracking

### user_progress Table

The `user_progress` table tracks your journey:

```sql
CREATE TABLE user_progress (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  problem_id UUID NOT NULL,

  -- Mastery tracking
  times_solved INTEGER DEFAULT 0,        -- 0 → 1 → 2
  is_mastered BOOLEAN DEFAULT FALSE,     -- True after 2 solves

  -- Scheduling
  next_review_date DATE,                 -- When to review next
  last_solved_at TIMESTAMP,              -- Last successful solve

  -- Re-entry flag
  show_again BOOLEAN DEFAULT FALSE,      -- User wants to review

  created_at TIMESTAMP DEFAULT NOW()
);
```

### State Transitions

**First Solve (Unsolved → In Review):**
```python
times_solved = 1
last_solved_at = now()
next_review_date = today() + 7 days
is_mastered = False
```

**Second Solve (In Review → Mastered):**
```python
times_solved = 2
last_solved_at = now()
next_review_date = None
is_mastered = True
```

**Show Again (Mastered → In Review):**
```python
show_again = False  # Reset flag
next_review_date = today()
# Keep times_solved and is_mastered unchanged
```

## Why This Works

### 1. Active Recall

You're forced to retrieve the solution from memory, not just recognize it. This strengthens neural pathways.

### 2. Optimal Timing

7 days is:
- Long enough to forget surface details
- Short enough to still have some memory
- The sweet spot for reinforcement

### 3. Mastery Focus

Two successful solves ensures:
- You understand the pattern, not just memorized the answer
- You can apply the technique to variations
- You're ready for similar problems in interviews

### 4. Efficient Learning

By removing mastered problems, you:
- Focus time on weak areas
- Avoid over-practicing known patterns
- Make consistent progress through problem set

## Future Enhancements

### Adaptive Intervals (Planned)

Instead of fixed 7-day intervals, use performance-based scheduling:

```
| Performance | Next Interval |
|-------------|---------------|
| Struggled   | 3 days        |
| Solved OK   | 7 days        |
| Solved Fast | 14 days       |
```

### Difficulty Multipliers (Planned)

Harder problems get longer intervals:

```
| Difficulty | Base Interval |
|------------|---------------|
| Easy       | 7 days        |
| Medium     | 10 days       |
| Hard       | 14 days       |
```

### Lapse Handling (Planned)

If you fail a review:
- Reset to shorter interval (3 days)
- Track lapse count for analytics

## Tips for Success

### 1. Solve Daily

Consistency is key. Even 20 minutes a day is better than 3 hours on weekends.

### 2. Don't Skip Reviews

Reviews are more important than new problems. They cement your knowledge.

### 3. Struggle Before Looking

Try for at least 15 minutes before checking hints or solutions. The struggle strengthens learning.

### 4. Use "Show Again"

If you barely remembered a solution, use "Show Again" to practice it more.

### 5. Track Patterns

Notice which patterns you struggle with (arrays, trees, DP). Focus on those.

### 6. Implement from Memory

Don't copy-paste solutions. Type them out from memory to reinforce muscle memory.

## Analytics (Coming Soon)

Future versions will show:
- **Mastery Rate**: % of problems mastered per pattern
- **Retention Rate**: % of reviews solved successfully
- **Weak Patterns**: Patterns with low retention
- **Study Streak**: Consecutive days practiced
- **Projected Completion**: When you'll master all problems

## Research Background

Spaced repetition is backed by decades of cognitive science research:

- **Ebbinghaus (1885)**: First documented the forgetting curve
- **Pimsleur (1967)**: Developed graduated interval recall
- **Leitner (1972)**: Created the Leitner system (flashcard boxes)
- **SuperMemo (1987)**: Implemented algorithmic spaced repetition
- **Anki (2006)**: Popularized SRS for general learning

acodeaday applies these proven techniques to coding interview preparation.

## Comparison with Other Methods

### Traditional Practice (LeetCode)
- ❌ No systematic review
- ❌ Easy to forget problems
- ❌ Overwhelming problem count
- ✅ Large problem variety

### acodeaday Spaced Repetition
- ✅ Systematic review schedule
- ✅ Long-term retention
- ✅ Manageable daily sessions
- ✅ Curated problem sets

### Cramming (Before Interview)
- ❌ Short-term memory only
- ❌ High stress
- ❌ Forget after interview
- ❌ Surface-level understanding

### Daily Practice with SRS
- ✅ Long-term mastery
- ✅ Low stress, sustainable
- ✅ Interview-ready anytime
- ✅ Deep pattern understanding

## Next Steps

- [Quick Start](/guide/quick-start) - Start your daily practice
- [Adding Problems](/guide/adding-problems) - Customize your problem set
- [API Reference](/api/progress) - Build custom analytics
