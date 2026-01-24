# Plan: Backend Comparison Strategy for Test Results

## Summary

Move test result comparison logic from Judge0 wrappers to the backend. This enables flexible comparison strategies (exact, unordered, in-place mutations) without duplicating logic across language wrappers.

---

## Current Architecture

```
User Code → Wrapper (comparison inside) → Judge0 → Returns {passed: bool}
                                                          ↓
                                               Backend trusts this value
```

**Problems:**
1. Comparison logic embedded in wrapper string templates
2. Must duplicate for each language (Python, JavaScript, etc.)
3. Hard to unit test
4. Sorting/comparison adds to measured runtime
5. Can't easily handle complex strategies (in-place mutations)

---

## Proposed Architecture

```
User Code → Wrapper (no comparison) → Judge0 → Returns {output, mutated_input?}
                                                          ↓
                                               Backend compares using strategy
```

---

## Implementation Steps

### Step 1: Create Comparison Service

**New file:** `backend/app/services/comparison.py`

```python
from typing import Any

STRATEGIES = ["exact", "unordered_array", "in_place_only", "in_place_with_length"]

def compare(output: Any, expected: Any, strategy: str = "exact") -> bool:
    """
    Compare test output against expected value using specified strategy.

    Strategies:
    - exact: Direct equality (default)
    - unordered_array: Sort before comparing (for problems like Two Sum)
    - in_place_only: Compare mutated input, ignore return value
    - in_place_with_length: Compare return value AND first k elements of mutated input
    """
    if strategy == "exact" or strategy is None:
        return output == expected

    if strategy == "unordered_array":
        return _compare_unordered(output, expected)

    if strategy == "in_place_only":
        return output.get("mutated_input") == expected.get("mutated_input")

    if strategy == "in_place_with_length":
        return _compare_in_place_with_length(output, expected)

    # Unknown strategy falls back to exact
    return output == expected


def _compare_unordered(output: Any, expected: Any) -> bool:
    """Compare arrays/lists ignoring order."""
    try:
        # Handle nested structures by converting to sorted tuples
        return sorted(_normalize(output)) == sorted(_normalize(expected))
    except TypeError:
        # If not sortable, fall back to exact
        return output == expected


def _normalize(value: Any) -> Any:
    """Normalize value for sorting (handle nested lists/dicts)."""
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return tuple(sorted((k, _normalize(v)) for k, v in value.items()))
    return value


def _compare_in_place_with_length(output: Any, expected: Any) -> bool:
    """Compare return value AND first k elements of mutated input."""
    k_output = output.get("return_value")
    k_expected = expected.get("return_value")

    if k_output != k_expected:
        return False

    mutated_output = output.get("mutated_input", [])
    mutated_expected = expected.get("mutated_input", [])

    return mutated_output[:k_output] == mutated_expected[:k_expected]
```

### Step 2: Add Database Field

**Migration:** Add `comparison_strategy` to `problems` table (not test_cases - strategy is per-problem)

```python
# alembic migration
def upgrade():
    op.add_column(
        'problems',
        sa.Column('comparison_strategy', sa.String(50), nullable=True)
    )

def downgrade():
    op.drop_column('problems', 'comparison_strategy')
```

**Update model:** `backend/app/db/tables.py`

```python
class Problem(Base):
    # ... existing fields ...
    comparison_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
```

### Step 3: Simplify Wrapper

**Modify:** `backend/app/services/wrapper.py`

Remove comparison logic, capture output and optionally mutated input:

```python
# Before
passed = result == test["expected"]
results.append({"passed": passed, ...})

# After
results.append({
    "test_number": i + 1,
    "output": result,
    "expected": test["expected"],
    # For in-place problems, wrapper also captures mutated input
    # This is controlled by a flag passed to the wrapper generator
})
```

### Step 4: Update Execution Route

**Modify:** `backend/app/routes/execution.py`

In `_parse_execution_results`, apply comparison strategy:

```python
from app.services.comparison import compare

def _parse_execution_results(judge0_result: dict, test_cases: list[TestCase], comparison_strategy: str = None) -> dict:
    # ... existing parsing ...

    for i, result_data in enumerate(results_data):
        # Apply comparison strategy instead of trusting "passed" from wrapper
        output = result_data.get("output")
        expected = result_data.get("expected")
        passed = compare(output, expected, comparison_strategy)

        test_results.append(
            TestResult(
                test_number=result_data.get("test_number", i + 1),
                passed=passed,  # Computed here, not from Judge0
                output=output,
                expected=expected,
                # ...
            )
        )
```

### Step 5: Update Problem Seeder

**Modify:** Problem YAML files to include `comparison_strategy` where needed:

```yaml
# problems/001-two-sum.yaml
title: Two Sum
slug: two-sum
comparison_strategy: unordered_array  # New field
# ...
```

---

## Data Flow Comparison

### Before (Current)
```
1. Backend generates wrapper with comparison logic
2. Judge0 runs wrapper, comparison happens inside
3. Judge0 returns {"passed": true/false}
4. Backend trusts and returns this value
```

### After (Proposed)
```
1. Backend generates simple wrapper (no comparison)
2. Judge0 runs wrapper
3. Judge0 returns {"output": [...], "expected": [...]}
4. Backend compares using problem's comparison_strategy
5. Backend returns result
```

---

## Affected Files

| File | Change |
|------|--------|
| `backend/app/services/comparison.py` | NEW - comparison logic |
| `backend/app/services/wrapper.py` | Simplify - remove comparison |
| `backend/app/routes/execution.py` | Add comparison call |
| `backend/app/db/tables.py` | Add comparison_strategy field |
| `alembic/versions/xxx_add_comparison.py` | NEW - migration |
| `backend/scripts/seed_problems.py` | Handle new field |
| `problems/*.yaml` | Add comparison_strategy where needed |

---

## Testing Plan

1. **Unit tests for comparison.py**
   - Test each strategy with various inputs
   - Test edge cases (empty arrays, nested structures)
   - Test fallback to exact for unknown strategies

2. **Integration tests**
   - Two Sum with reversed output should pass
   - Existing problems should work unchanged (exact default)
   - In-place problems work correctly

3. **Regression tests**
   - All existing test cases still pass
   - Runtime/memory measurements unchanged
   - No breaking changes to API responses

---

## Rollback Plan

If issues arise:
1. Revert migration (drop column)
2. Restore old wrapper.py with comparison logic
3. Remove comparison.py

The change is additive - existing behavior preserved when `comparison_strategy` is NULL.

---

## Security Considerations

1. **Strategy validation**: Only allow known strategies, reject unknown values
2. **Input sanitization**: comparison.py receives data from Judge0 stdout - ensure JSON parsing is safe
3. **DoS via complex comparison**: Large arrays with unordered comparison could be slow - consider size limits

---

## Open Questions

1. Should `comparison_strategy` be on `problems` or `test_cases` table?
   - Recommendation: `problems` - simpler, strategy applies to whole problem

2. How to handle in-place problems in wrapper?
   - Need flag to tell wrapper to capture mutated input
   - Could add `capture_mutated_input: bool` to problem config

3. What about problems with multiple valid outputs (not just ordering)?
   - Future strategy: `any_valid` with custom validator?
   - Out of scope for initial implementation
