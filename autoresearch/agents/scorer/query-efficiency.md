# Scorer: Query Efficiency

## Purpose

Evaluate whether SKILL.md guides DuckDB queries to be efficient — avoiding redundant scans, using sampling where appropriate, and structuring intermediate results for reuse.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Full Efficiency Guidance

- Instructs creating a profiling summary once and reusing it across phases (no repeated full-table scans)
- Uses CTEs or temp tables for intermediate results referenced more than once
- Includes a sampling strategy based on data size (e.g., sample at 100K rows, full scan under 10K)
- All exploratory queries include LIMIT clauses
- Batches related queries rather than issuing many small separate queries

### Score 2 — Basic Patterns and Sampling, No Reuse

- Includes sampling thresholds or LIMIT clauses
- Basic SQL patterns shown
- No explicit guidance on query reuse across phases
- Phases may re-scan the same data independently

### Score 1 — SQL Examples, No Efficiency Guidance

- SQL examples present but no guidance on efficiency
- No LIMIT clauses, no sampling strategy
- Each phase likely re-scans the full dataset independently

### Score 0 — No Query Patterns or Efficiency Considerations

- No DuckDB query patterns
- No mention of scan cost, sampling, or result reuse
- Efficiency entirely up to the user

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Instruction to profile the dataset once and store/reference the summary across phases
- [ ] Sampling thresholds defined (e.g., sample if rows > 100K; use TABLESAMPLE or WHERE RANDOM() < 0.1)
- [ ] LIMIT clauses required on all exploratory queries
- [ ] SELECT * explicitly discouraged or prohibited
- [ ] CTEs or temp tables used for intermediate results
- [ ] Related queries batched into a single DuckDB call where possible

---

## Sample Validation

**Scenario:** Google Ads dataset with approximately 33,000 rows.

Apply SKILL.md mentally to this scenario and ask:

1. Would the skill compute a single profiling summary (row count, date range, column null rates) and reuse it in White Hat and Black Hat phases — or re-query separately in each?
2. Would GROUP BY queries for segment analysis include LIMIT 50 or similar bounds?
3. If the dataset were 500K rows, would the skill apply sampling before running distribution queries?
4. Would Yellow Hat analysis avoid re-reading the full table for each metric, instead working from the profiled summary?

A Score 3 skill would include an instruction like: "Before Phase 2, execute a single profiling query that captures row count, date range, null rates per column, and cardinality for key dimensions. Store this as `profile`. Reference `profile` in all subsequent phases rather than re-querying."

---

## Output Format

```json
{
  "metric": "query-efficiency",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing efficiency guidance>'",
    "SKILL.md line N: '<exact quote showing query pattern or absence>'"
  ],
  "gaps": [
    "Missing: No instruction to profile once and reuse across phases",
    "Missing: No sampling thresholds defined",
    "Missing: LIMIT clauses not required on exploratory queries"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
