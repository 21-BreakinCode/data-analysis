# Scorer: Direction Quality

## Purpose

Evaluate whether SKILL.md starts analysis with a clear business question and frames it causally rather than descriptively.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Full Causal Direction

- Wizard explicitly asks "what DECISION depends on this analysis?"
- Blue Hat explicitly distinguishes correlation from causation
- Skill proposes hypothesis-driven analysis (not just "explore the data")
- Analysis framing connects to a specific business outcome

### Score 2 — Partial Direction, No Causal Framing

- Wizard asks clarifying questions about goals
- Blue Hat proposes analytical techniques
- No explicit causal framing or hypothesis testing structure
- Direction is present but correlation/causation conflated

### Score 1 — Questions Asked, Descriptive Execution

- Wizard collects user questions
- Proceeds as descriptive profiling (what happened, not why)
- No mechanism to move from observation to causal inference

### Score 0 — No Direction Mechanism

- No structured intake of business question
- Analysis begins with data exploration without stated purpose
- No connection between data patterns and business decisions

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Wizard phase asks "what decision will this analysis inform?" or equivalent
- [ ] Blue Hat phase explicitly distinguishes correlation from causation
- [ ] Skill proposes or references hypothesis testing (not just description)
- [ ] Playbook reference includes causal hypotheses (e.g., "CPA rose because X, not just that CPA rose")
- [ ] Summary phase connects findings back to the original business question

---

## Sample Validation

**Scenario:** Google Ads account where CPA doubled last month.

Apply SKILL.md mentally to this scenario and ask:

1. Would the skill ask WHY CPA doubled (causal) or just SHOW that it doubled (descriptive)?
2. Would it decompose `CPA = CPC / conversion_rate` and test each lever separately?
3. Would it propose hypotheses (e.g., "bid strategy change caused CPC increase" vs "landing page issue caused conversion drop") before querying?
4. Would the Summary distinguish "CPA increased" (fact) from "bid strategy change drove CPA increase" (causal claim)?

A Score 3 skill would surface a hypothesis like: "Test whether the CPA increase is driven by CPC (supply/auction side) or CVR (demand/creative/landing page side) before querying the full dataset."

---

## Output Format

```json
{
  "metric": "direction-quality",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing direction mechanism>'",
    "SKILL.md line N: '<exact quote showing causal framing or absence>'"
  ],
  "gaps": [
    "Missing: Wizard does not ask what decision the analysis will inform",
    "Missing: Blue Hat does not distinguish correlation from causation",
    "Missing: No hypothesis-driven analysis structure"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
