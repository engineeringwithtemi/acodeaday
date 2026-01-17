# Spaced Repetition

Learn how acodeaday uses the Anki SM-2 algorithm to help you master coding problems long-term.

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

acodeaday uses the **Anki SM-2 algorithm**, a proven spaced repetition algorithm with adaptive intervals based on how well you know each problem.

### The Rating System

After successfully solving a problem, you rate how difficult it was:

| Rating | Description | Effect on Interval |
|--------|-------------|-------------------|
| **Again** | I couldn't solve it / needed hints | Reset to 1 day, decrease ease |
| **Hard** | Solved but struggled | Slower growth (×1.2), decrease ease |
| **Good** | Solved with some effort | Normal growth (×ease factor) |
| **Mastered** | Solved easily, confident | Exit rotation immediately |

### Problem States

Every problem exists in one of three states:

1. **Unsolved** - You haven't attempted it yet
2. **In Review** - Solved at least once, scheduled for future review
3. **Mastered** - Reached 30+ day interval or rated "Mastered"

```
┌─────────────┐
│  Unsolved   │
│  (New)      │
└──────┬──────┘
       │
       │ Solve & rate
       ▼
┌─────────────┐
│  In Review  │◄─────────────────┐
│  (Scheduled)│                  │
└──────┬──────┘                  │
       │                         │
       │ Interval ≥30d      "Show Again"
       │ OR rate "Mastered"      │
       ▼                         │
┌─────────────┐                  │
│  Mastered   │──────────────────┘
│  (Done)     │
└─────────────┘
```

### The SM-2 Algorithm

The algorithm uses two key values:

1. **Ease Factor**: How easy the problem is for you (default: 2.5, minimum: 1.3)
2. **Interval**: Days until next review

#### How Intervals Grow

**First solve:**
- Rating "Hard": `interval = 1 day`
- Rating "Good": `interval = 3 days`

**Subsequent solves:**
```
new_interval = current_interval × ease_factor
```

**Ease factor adjustments:**
- "Again": `ease -= 0.2` (min 1.3)
- "Hard": `ease -= 0.15` (min 1.3), `interval × 1.2`
- "Good": `ease += 0.0` (unchanged), `interval × ease`
- "Mastered": Immediately exit rotation

#### Auto-Mastery

When a problem's interval reaches **30+ days**, it's automatically marked as mastered and removed from the rotation. This means you've demonstrated consistent recall over an extended period.

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
- Rate: "Good"
- Next review: Day 4 (3 days)

**Day 4:**
- Review "Two Sum"
- Rate: "Good" (ease = 2.5)
- Next review: Day 4 + (3 × 2.5) = Day 12 (8 days)

### Week 2

**Day 12:**
- Review "Two Sum"
- Rate: "Good"
- Next review: Day 12 + (8 × 2.5) = Day 32 (20 days)

### Week 5

**Day 32:**
- Review "Two Sum"
- Interval would be 50 days (≥30), auto-mastered!
- Two Sum is removed from rotation

### Rating "Hard" Example

**Day 1:**
- Solve "3Sum" (1st time)
- Rate: "Hard"
- Next review: Day 2 (1 day), ease drops to 2.35

**Day 2:**
- Review "3Sum"
- Rate: "Good"
- Next review: Day 2 + (1 × 2.35) = Day 4 (2 days)

**Day 4:**
- Review "3Sum"
- Rate: "Good"
- Next review: Day 4 + (2 × 2.35) = Day 9 (5 days)

Notice how "Hard" ratings create shorter intervals, giving you more practice.

## Database Tracking

### user_progress Table

The `user_progress` table tracks your journey:

```sql
CREATE TABLE user_progress (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  problem_id UUID NOT NULL,

  -- Mastery tracking
  times_solved INTEGER DEFAULT 0,
  is_mastered BOOLEAN DEFAULT FALSE,

  -- Anki SM-2 fields
  ease_factor FLOAT DEFAULT 2.5,      -- Range: 1.3 to 2.5+
  interval_days INTEGER DEFAULT 0,     -- Current interval
  review_count INTEGER DEFAULT 0,      -- Number of reviews

  -- Scheduling
  next_review_date DATE,
  last_solved_at TIMESTAMP,

  -- Re-entry flag
  show_again BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMP DEFAULT NOW()
);
```

### State Transitions

**First Solve (rate "Good"):**
```python
times_solved = 1
ease_factor = 2.5
interval_days = 3
next_review_date = today() + 3 days
last_solved_at = now()
is_mastered = False
```

**Review (rate "Good"):**
```python
review_count += 1
interval_days = interval_days * ease_factor
next_review_date = today() + interval_days
last_solved_at = now()
if interval_days >= 30:
    is_mastered = True
```

**Review (rate "Hard"):**
```python
review_count += 1
ease_factor = max(1.3, ease_factor - 0.15)
interval_days = interval_days * 1.2
next_review_date = today() + interval_days
```

**Review (rate "Again"):**
```python
review_count += 1
ease_factor = max(1.3, ease_factor - 0.2)
interval_days = 1
next_review_date = today() + 1
```

**Show Again (Mastered → In Review):**
```python
show_again = False
ease_factor = 2.5  # Reset ease
interval_days = 0
next_review_date = today()
is_mastered = False
# times_solved unchanged
```

## Why This Works

### 1. Active Recall

You're forced to retrieve the solution from memory, not just recognize it. This strengthens neural pathways.

### 2. Adaptive Intervals

Unlike fixed intervals, SM-2 adapts to your performance:
- Easy problems grow faster (high ease factor)
- Hard problems repeat more often (low ease factor)

### 3. Difficulty Feedback

By rating difficulty, you give the algorithm feedback:
- "Again" = need more practice soon
- "Hard" = need more practice, but not immediately
- "Good" = on track for mastery
- "Mastered" = confident, exit rotation

### 4. Efficient Learning

By removing mastered problems, you:
- Focus time on weak areas
- Avoid over-practicing known patterns
- Make consistent progress through problem set

## Tips for Success

### 1. Be Honest with Ratings

- Use "Again" if you needed hints or couldn't solve it
- Use "Hard" if you solved it but struggled
- Use "Good" for normal solves
- Only use "Mastered" if you're truly confident

### 2. Solve Daily

Consistency is key. Even 20 minutes a day is better than 3 hours on weekends.

### 3. Don't Skip Reviews

Reviews are more important than new problems. They cement your knowledge.

### 4. Struggle Before Looking

Try for at least 15 minutes before checking hints or solutions. The struggle strengthens learning.

### 5. Use "Show Again"

If you barely remembered a solution, rate "Hard" or "Again". If you mastered a problem but want to refresh it, use "Show Again".

### 6. Track Patterns

Notice which patterns you struggle with (arrays, trees, DP). Focus on those.

## Research Background

Spaced repetition is backed by decades of cognitive science research:

- **Ebbinghaus (1885)**: First documented the forgetting curve
- **Pimsleur (1967)**: Developed graduated interval recall
- **Leitner (1972)**: Created the Leitner system (flashcard boxes)
- **SuperMemo (1987)**: Implemented algorithmic spaced repetition
- **Anki (2006)**: Popularized SRS for general learning

acodeaday applies the proven Anki SM-2 algorithm specifically to coding interview preparation.

## Comparison with Other Methods

### Traditional Practice (LeetCode)
- ❌ No systematic review
- ❌ Easy to forget problems
- ❌ Overwhelming problem count
- ✅ Large problem variety

### acodeaday Anki SM-2
- ✅ Adaptive review schedule
- ✅ Long-term retention
- ✅ Manageable daily sessions
- ✅ Difficulty-based intervals

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

## API Reference

### Rate Submission Endpoint

After a successful submission, rate the difficulty:

```http
POST /api/rate-submission
```

```json
{
  "submission_id": "uuid",
  "rating": "good"
}
```

Rating options: `"again"`, `"hard"`, `"good"`, `"mastered"`

Response includes updated progress:

```json
{
  "times_solved": 2,
  "is_mastered": false,
  "ease_factor": 2.5,
  "interval_days": 8,
  "next_review_date": "2024-01-15"
}
```

## Next Steps

- [Quick Start](/guide/quick-start) - Start your daily practice
- [Adding Problems](/guide/adding-problems) - Customize your problem set
- [API Reference](/api/progress) - Build custom analytics
