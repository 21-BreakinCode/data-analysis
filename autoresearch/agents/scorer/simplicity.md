# Scorer: Simplicity

## Purpose

Evaluate whether SKILL.md prioritizes the simplest appropriate analytical method — avoiding over-engineering where standard SQL or basic statistics suffice.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Simplicity as Explicit Principle

- Blue Hat explicitly starts with simple methods and escalates only if data complexity requires it
- Technique selection is driven by data shape (row count, column types, question type) — not by what is impressive
- Standard SQL (GROUP BY, aggregates, window functions) used before advanced methods
- Anomaly detection uses IQR or percentile thresholds — not ML or complex models
- Complexity is only introduced when the simple approach demonstrably fails

### Score 2 — Appropriate Techniques, No Simplicity Principle

- Techniques chosen are generally appropriate for the analysis
- No explicit principle of simplicity stated
- Complexity level varies without clear justification
- Advanced methods sometimes introduced without establishing simpler baseline first

### Score 1 — Over-Engineered Approaches

- More complex techniques used where simple ones would suffice (e.g., clustering where GROUP BY works, regression where correlation suffices)
- Analysis steps introduced without checking if simpler alternatives would answer the question
- Complexity treated as a positive feature

### Score 0 — Complex Methods Where Simple Ones Suffice

- Analysis consistently introduces unnecessary complexity
- SQL is bypassed in favor of in-memory dataframe operations for simple aggregation tasks
- Statistical tests applied where descriptive statistics would answer the question

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Blue Hat explicitly states: "start with the simplest technique; escalate only if needed"
- [ ] Technique selection criteria tied to data shape, not sophistication (e.g., "for N < 10K, use direct GROUP BY; for N > 1M, add sampling")
- [ ] Standard SQL (GROUP BY, window functions, CTEs) used as the default before advanced methods
- [ ] Anomaly detection uses IQR or fixed percentile thresholds — not ML or clustering
- [ ] Correlation analysis uses straightforward Pearson or Spearman before multivariate methods
- [ ] No unnecessary statistical significance tests where the business question is directional
- [ ] Sampling uses simple threshold-based logic (e.g., TABLESAMPLE or WHERE RANDOM() < rate) — not complex reservoir sampling

---

## Sample Validation

**Scenario 1:** Google Ads — identify which campaigns have anomalously high CPA.

Apply SKILL.md mentally and ask:

1. Would the skill use `CPA > percentile_90` or `CPA > median + 2*IQR` — or would it propose clustering algorithms or machine learning anomaly detection?
2. Would the answer come from a single GROUP BY query — or would it require a multi-step pipeline?

**Scenario 2:** Facebook Ads — identify whether CTR correlates with conversion rate.

Apply SKILL.md mentally and ask:

1. Would the skill compute a basic scatter or Spearman correlation with a simple SELECT — or propose multivariate regression with control variables?
2. If the simple correlation answers the question, would the skill stop there — or continue to more complex methods anyway?

A Score 3 skill would include: "Choose the simplest method that answers the question. Reserve advanced techniques (regression, clustering, time-series decomposition) for cases where the business question cannot be answered by aggregation, filtering, or ranking alone."

---

## Output Format

```json
{
  "metric": "simplicity",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing technique selection guidance>'",
    "SKILL.md line N: '<exact quote showing simplicity principle or over-engineering>'"
  ],
  "gaps": [
    "Missing: No explicit simplicity principle stated",
    "Missing: Technique selection not tied to data shape or question complexity",
    "Missing: Anomaly detection method more complex than IQR/percentile"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
