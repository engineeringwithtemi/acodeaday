"""Pydantic AI agent definitions for the problem import pipeline.

Agents are created lazily via get_*() functions to avoid requiring API keys
at import time (which breaks tests and CLI tools).
"""

from functools import lru_cache

from pydantic_ai import Agent

from app.config.settings import settings
from app.schemas.import_schemas import (
    GeneratedProblem,
    GeneratedTestCases,
    ImportPlan,
    VerificationResult,
)


# ─── 1. INTENT PARSER ─────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_intent_parser_agent() -> Agent:
    return Agent(
        settings.import_intent_parser_model or settings.import_agent_model,
        output_type=ImportPlan,
        system_prompt="""\
You parse user requests for importing coding problems into a practice app.
Determine if the user wants:
- A batch of problems by pattern (e.g., "10 sliding window problems") → intent: "pattern"
- A specific LeetCode problem by name or number (e.g., "LeetCode 4") → intent: "specific"

Extract:
- intent: "pattern" or "specific"
- pattern: kebab-case tag like "sliding-window", "two-pointers", "dynamic-programming"
- problem_name: the problem title if mentioned (e.g., "Median of Two Sorted Arrays")
- leetcode_number: the LeetCode number if mentioned
- count: how many problems (default 1)
- difficulty: "easy", "medium", or "hard" if specified, else null

For pattern names, use kebab-case: "sliding-window", "two-pointers", "binary-search",
"dynamic-programming", "graph", "tree", "stack", "queue", "heap", "greedy",
"backtracking", "hash-map", "linked-list", "array", "string", "math", "bit-manipulation".
""",
    )


# ─── 2. PROBLEM GENERATOR ─────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_problem_generator_agent() -> Agent:
    return Agent(
        settings.import_problem_generator_model or settings.import_agent_model,
        output_type=GeneratedProblem,
        system_prompt="""\
You generate LeetCode-style coding problems. You must generate REAL LeetCode problems
with their correct leetcode_no. Do not invent fictional problems.

Requirements:
- title: The exact LeetCode problem title (e.g., "Sliding Window Maximum")
- difficulty: "easy", "medium", or "hard" — matching the actual LeetCode difficulty
- pattern: Array of kebab-case tags describing the algorithmic pattern
- description: Clear markdown problem statement. Include examples inline with
  **bold** for emphasis and `code` formatting where appropriate.
- constraints: Realistic bounds matching the problem (e.g., "1 <= nums.length <= 10^5")
- examples: 2-3 examples with input (as string), output (as string), and explanation
- leetcode_no: The REAL LeetCode problem number. This must be accurate.
- comparison_strategy: null for most problems. Use "unordered_array" only when the
  problem says "return in any order" or output order is explicitly undefined.
  NEVER use "in_place_only" or "in_place_with_length".

Language-specific requirements (Python only for now):
- starter_code: class Solution with the correct method signature and `pass` body
- reference_solution: Complete, correct, efficient Python solution inside class Solution
- function_signature: JSON with name, params (array of {name, type}), and return_type

The solution MUST use the `class Solution` pattern:
    class Solution:
        def methodName(self, param1: type1, param2: type2) -> return_type:

IMPORTANT: Generate problems DIFFERENT from the excluded list provided in the prompt.
""",
    )


# ─── 3. PROBLEM VERIFIER ──────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_problem_verifier_agent() -> Agent:
    return Agent(
        settings.import_problem_verifier_model or settings.import_agent_model,
        output_type=VerificationResult,
        system_prompt="""\
You verify the quality and correctness of coding problems. Check ALL of the following:

1. The title matches a real LeetCode problem
2. The leetcode_no is correct for the given title
3. The description is clear, unambiguous, and matches the real LeetCode problem
4. The reference solution is correct and would pass on LeetCode
5. The function signature matches the solution's method name and parameters
6. The starter code has the correct method signature with `pass` as the body
7. Constraints are realistic and match the actual LeetCode problem
8. Examples are correct — the output matches what the reference solution would return
9. The difficulty matches the actual LeetCode difficulty
10. comparison_strategy is appropriate (null for exact, "unordered_array" only if
    the problem explicitly allows any order)

Be strict. Flag anything that would confuse a solver or cause incorrect test results.
Set valid=true only if ALL checks pass. List specific issues in the issues array.
""",
    )


# ─── 4. TEST CASE GENERATOR ───────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_test_case_generator_agent() -> Agent:
    return Agent(
        settings.import_test_case_generator_model or settings.import_agent_model,
        output_type=GeneratedTestCases,
        system_prompt="""\
You generate comprehensive test cases for coding problems.

For each problem, generate 10-15 test cases covering:
- Basic cases from the examples in the problem description
- Edge cases: empty input, single element, minimum constraint values
- Boundary cases: values near maximum constraint bounds (but keep inputs small enough
  to be readable — no arrays longer than ~20 elements)
- Corner cases specific to the algorithm
- Cases that commonly trip up incorrect solutions

Format:
- input: Array of function arguments in the order the function expects them.
  Example: for twoSum(nums, target), input would be [[2,7,11,15], 9]
- expected: The return value the correct solution would produce.
  Example: [0,1]

IMPORTANT: Mentally trace through the reference solution for EVERY test case to verify
each expected value is correct. An incorrect expected value will cause correct user
solutions to fail.
""",
    )
