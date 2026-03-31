# Scorer: Insight Novelty

## Purpose

Evaluate whether SKILL.md is structured to surface new, unexpected, or non-obvious insights — not just confirm what the user already suspects.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Structured Novelty Seeking

- Green Hat explicitly proposes contrarian hypotheses (challenges the user's assumptions)
- Yellow Hat cross-references unexpected or non-obvious dimension combinations
- Skill includes instruction equivalent to "what would surprise the user?" as a prompt
- Derived metrics (e.g., LTV-adjusted ROAS, repeat purchase rate) computed alongside standard ones

### Score 2 — Alternatives Suggested, No Novelty Structure

- Green Hat suggests alternative interpretations or approaches
- No structured process for seeking what is unexpected
- Cross-dimensional analysis happens but is not guided by surprise-seeking intent

### Score 1 — Standard Profiling, Generic Green Hat

- Green Hat present but used only to suggest "try X technique"
- Analysis follows a fixed template; no mechanism to discover what breaks the template
- Non-obvious segments or metrics not prompted

### Score 0 — No Novelty Mechanism

- No phase or instruction that prompts for non-obvious insights
- Skill produces a standard descriptive summary only

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Green Hat explicitly proposes hypotheses that contradict the user's stated assumption
- [ ] Yellow Hat or Green Hat cross-references unexpected dimension combinations (e.g., audience × device × time-of-day)
- [ ] Skill instructs looking at data from multiple stakeholder perspectives (finance, creative, media buyer)
- [ ] Derived metrics are computed rather than only raw metrics reported
- [ ] Skill includes at least one instruction to compare segments that "shouldn't" differ to find anomalies

---

## Sample Validation

**Scenario:** Facebook Ads account with standard audience and campaign structure.

Apply SKILL.md mentally to this scenario and ask:

1. Would the skill surface `LA1_HighLTV` audience's hidden value via `repeat_purchase_rate` (non-obvious) rather than just top-line ROAS?
2. Would it compute LTV-adjusted ROAS instead of just reported ROAS?
3. Would it flag that low `pixel_confidence` segments might be UNDERVALUED (inverse of the obvious concern) because they show fewer conversions but their actual purchase rate is higher?
4. Would Green Hat propose "what if the worst-performing segment is undervalued, not bad?"

A Score 3 skill would include an instruction like: "For each segment labeled 'underperforming', test whether the signal quality (pixel confidence, match rate) is causing underreporting before concluding the segment is weak."

---

## Output Format

```json
{
  "metric": "insight-novelty",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing novelty mechanism>'",
    "SKILL.md line N: '<exact quote showing Green Hat behavior>'"
  ],
  "gaps": [
    "Missing: Green Hat does not propose contrarian hypotheses",
    "Missing: No instruction to seek what would surprise the user",
    "Missing: Derived metrics not computed alongside standard ones"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
