# Scorer: Data Quality Assessment

## Purpose

Evaluate whether SKILL.md instructs thorough data quality checks — nulls, outliers, sampling bias, data freshness, and how quality issues affect analytical conclusions.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Comprehensive Quality Checks Linked to Analytical Risk

- Black Hat runs specific DuckDB queries to check nulls, duplicates, and outliers (not just mentions them conceptually)
- Checks data freshness (date range gaps, missing recent periods)
- Explicitly links each quality issue to its analytical risk ("5% null creative_type means campaign breakdown is unreliable")
- Validates data against playbook expectations (e.g., playbook says field X should be non-null)
- Re-checks quality after any filtering or transformation steps

### Score 2 — Basic Checks Without Risk Linkage

- Black Hat checks nulls, duplicates, and obvious outliers
- No connection between quality issues and which conclusions they invalidate
- No freshness check
- No post-filtering quality re-check

### Score 1 — Quality Mentioned, No Specific Checks

- Data quality discussed in general terms
- No specific queries or thresholds provided
- Black Hat exists but is vague ("check for issues")

### Score 0 — No Data Quality Assessment

- No phase or instruction dedicated to data quality
- Analysis proceeds on raw data without validation

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Black Hat includes specific DuckDB queries for null counts per column
- [ ] Black Hat includes specific DuckDB queries for duplicate row detection
- [ ] Black Hat includes outlier detection (e.g., values > 3 IQR from median)
- [ ] Date gap detection — checks for missing days or unexpected date ranges
- [ ] Each quality issue is connected to the analytical conclusion it affects
- [ ] Playbook field expectations validated against actual data (schema consistency check)
- [ ] Handling strategy defined for each quality issue (exclude, impute, flag, or note in Summary)
- [ ] Summary includes data quality caveats for any findings that depend on incomplete or unreliable fields

---

## Sample Validation

**Scenario:** Facebook Ads dataset with `pixel_confidence`, `creative_type`, and `repeat_purchase_rate` columns.

Apply SKILL.md mentally to this scenario and ask:

1. Would the skill detect that `pixel_confidence` = low affects conversion count accuracy, and flag which analyses are unreliable as a result?
2. Would it catch a 5% NULL rate in `creative_type` and note that creative-level analysis is incomplete for that share of spend?
3. Would it flag that `repeat_purchase_rate` computed over a 30-day window introduces survivorship bias for recent campaigns (insufficient lookback)?
4. After filtering to `pixel_confidence > 0.7`, would it re-check whether the filtered dataset is still representative (no systematic bias in what was removed)?

A Score 3 skill would include a query like:
```sql
SELECT
  COUNT(*) AS total_rows,
  SUM(CASE WHEN creative_type IS NULL THEN 1 ELSE 0 END) AS null_creative_type,
  SUM(CASE WHEN pixel_confidence < 0.7 THEN 1 ELSE 0 END) AS low_confidence_rows
FROM ads_data;
```
And the instruction: "For each null or low-quality flag, state which downstream analyses are affected and whether results should be qualified."

---

## Output Format

```json
{
  "metric": "data-quality",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing data quality check>'",
    "SKILL.md line N: '<exact quote showing quality-to-risk linkage or absence>'"
  ],
  "gaps": [
    "Missing: No specific DuckDB queries for null detection",
    "Missing: Quality issues not connected to which conclusions they invalidate",
    "Missing: No post-filtering quality re-check"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
