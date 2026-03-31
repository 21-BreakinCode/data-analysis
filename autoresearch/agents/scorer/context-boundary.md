# Scorer: Context Boundary

## Purpose

Evaluate whether SKILL.md maintains clear separation between phases and agents — each with a single purpose, no responsibilities leaking across boundaries.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Clean Phase Boundaries

- Each phase has a single, clearly stated purpose (could be split into an independent agent without ambiguity)
- No phase both collects data and interprets it (White Hat is data-only)
- Playbook is loaded once and referenced consistently; not re-loaded or duplicated mid-analysis
- Output format is defined per phase so downstream phases know what they receive
- Handoffs between phases are explicit (e.g., "Yellow Hat receives the output of White Hat and Black Hat")

### Score 2 — Phases Defined, Overlapping Responsibilities

- Phases are named and described
- Some overlap exists (e.g., White Hat includes mild interpretation, Yellow Hat re-runs data queries)
- Handoffs present but unstructured — no explicit description of what each phase receives
- Playbook loaded at the start but not consistently referenced

### Score 1 — Phases Named, Responsibilities Blur

- Phase names used but multiple responsibilities per phase
- Phases do not have explicit input/output contracts
- Analytical work mixed with data collection

### Score 0 — No Phase Separation

- Analysis is monolithic — no named phases or agents
- All work done in a single pass with no structural separation

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Each phase has a "Purpose:" line (or equivalent header) stating its single responsibility
- [ ] White Hat phase contains ZERO interpretation — only data retrieval and factual reporting
- [ ] Red Hat phase is deliberately brief — impressions only, no analysis
- [ ] Black Hat phase focuses on data quality and risk — not insights or recommendations
- [ ] Yellow Hat is the ONLY phase performing insight generation from data patterns
- [ ] Green Hat does not repeat Yellow Hat findings — it only proposes new angles
- [ ] Playbook is loaded exactly once and referenced by name in subsequent phases
- [ ] Each phase has a defined output format (JSON block, structured markdown, etc.)

---

## Sample Validation

**Scenario:** Multi-phase analysis of a Google Ads account.

Apply SKILL.md mentally and ask:

1. If White Hat is given data, would it avoid saying "this is surprisingly high"? (Interpretation belongs to Yellow Hat.)
2. Would Black Hat stick to "this data cannot be trusted because X" rather than "X is a problem therefore you should do Y"? (Recommendations belong to Yellow Hat/Summary.)
3. Would Green Hat say "here is a new angle to explore" rather than "Yellow Hat found X and that means Y"? (Yellow Hat owns the conclusion.)
4. Could each phase be extracted into its own agent file with clearly defined inputs and outputs?

A Score 3 skill would explicitly state at the top of each phase: "Input: [list], Output: [format], Constraint: [what this phase does NOT do]."

---

## Output Format

```json
{
  "metric": "context-boundary",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing phase definition>'",
    "SKILL.md line N: '<exact quote showing boundary violation or clean separation>'"
  ],
  "gaps": [
    "Missing: White Hat phase contains interpretive statements",
    "Missing: No explicit output format defined per phase",
    "Missing: Playbook loaded multiple times across phases"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
