# Scorer: Success Metrics Definition

## Purpose

Evaluate whether SKILL.md instructs defining and validating success criteria before measuring — ensuring metrics are compared against thresholds, not just computed in isolation.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Define Good Before Measuring

- Blue Hat or Wizard explicitly asks "what does good look like?" before any analysis begins
- Playbook includes Key Metrics with specific thresholds (not just metric names)
- Yellow Hat compares findings against those thresholds — not just reports numbers
- Skill validates that the metric measures what it claims to measure (metric validity check)
- Summary evaluates performance against the pre-defined criteria, not just trends

### Score 2 — Playbook Metrics Referenced, No Pre-Definition Step

- Playbook includes Key Metrics and they are referenced in analysis
- No explicit step to define "what good looks like" before querying
- Metrics compared to playbook values but without explicit pre-analysis criteria-setting ritual

### Score 1 — Metrics Computed, Compared to Nothing

- Metrics computed and reported accurately
- No comparison against benchmarks, targets, or thresholds
- User must judge whether numbers are good or bad

### Score 0 — Numbers Without Context

- Raw numbers reported
- No targets, no benchmarks, no thresholds
- "CPA is $24" with no context for whether $24 is good, bad, or expected

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Blue Hat or Wizard includes an explicit step: "establish success criteria before querying" (or equivalent)
- [ ] Playbook Key Metrics section includes numeric thresholds (e.g., "target CPA: $18", "minimum ROAS: 2.5x")
- [ ] Yellow Hat compares findings against those thresholds, not just reports them
- [ ] Skill asks: "what does a good outcome look like for this analysis?" at the intake step
- [ ] Metric validity check: does the metric actually measure what we think? (e.g., "reported ROAS may exclude view-through conversions")
- [ ] Summary evaluates "did we meet the criteria?" — not just "here is what we found"

---

## Sample Validation

**Scenario 1:** Google Ads — target CPA is $18, current CPA is $24.

Apply SKILL.md mentally and ask:

1. Would the skill establish "target CPA = $18" as a criterion before querying — or discover the $24 figure and ask the user if that is high?
2. Would the Summary say "CPA of $24 is 33% above the $18 target" — or just "CPA is $24"?
3. Would Yellow Hat flag every segment where CPA > $18 and rank them by severity?

**Scenario 2:** Facebook Ads — ROAS reported by platform.

Apply SKILL.md mentally and ask:

1. Would the skill validate whether reported ROAS includes or excludes view-through and offline conversions before comparing to target?
2. Would the analysis note "reported ROAS of 3.2x may overstate true ROAS if view-through attribution is broad" as a metric validity concern?
3. Would Blue Hat ask "what ROAS threshold counts as success for this campaign?" before proceeding?

A Score 3 skill would include an intake step like: "Before analysis: confirm with the user (or from playbook) the target values for each Key Metric. These become the evaluation threshold for the entire analysis. Every finding is expressed relative to these targets."

---

## Output Format

```json
{
  "metric": "success-metrics",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing success criteria definition step>'",
    "SKILL.md line N: '<exact quote showing threshold comparison or absence>'"
  ],
  "gaps": [
    "Missing: No step to define 'what good looks like' before querying",
    "Missing: Playbook Key Metrics lack numeric thresholds",
    "Missing: Summary does not evaluate performance against pre-defined criteria"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
