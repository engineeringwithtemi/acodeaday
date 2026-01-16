# Future Improvements

## Automated Problem Generation Pipeline

**Status:** Planned - needs thorough design

**Summary:** Automatically generate original coding problems using LLM (Google Gemini) via Supabase Edge Functions.

**Detailed Plan:** See `/Users/to/.claude/plans/parallel-popping-manatee.md`

### Key Features
- 3-stage pipeline: Problem Generation → Test Case Generation → Validation
- Uses Google Gemini Batch API for cost-effective batch processing
- Generates 100+ test cases per problem (like LeetCode)
- Validates by running reference solution against test cases via Judge0
- Threshold-based fault detection to distinguish bad tests from bad solutions

### Open Questions
1. How to reliably distinguish faulty test cases from buggy reference solutions
2. Whether to require human review for all generated problems or auto-publish
3. Cost implications of generating 100+ test cases per problem
4. How to handle edge cases in LLM output (malformed JSON, duplicate problems)

### Files to Create
- `supabase/functions/` - 5 edge functions
- `backend/app/routes/validation.py` - validation endpoint
- Database migration for `generation_jobs` table

---

*Add more future improvements below as they come up*
