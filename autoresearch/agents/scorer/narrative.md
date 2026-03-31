# Scorer: Narrative Coherence

## Purpose

Evaluate whether SKILL.md produces an analysis that tells a coherent story — phases building on each other, findings connecting to form a through-line from question to insight to action.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Phases Build on Each Other, Clear Narrative Arc

- Blue Hat sets the narrative frame that all phases return to
- Phases explicitly reference the outputs of previous phases (not isolated)
- Summary weaves all phase findings into a coherent story, not a list
- FACT/ASSUME rhythm creates readable prose flow throughout the analysis
- Red Hat initial impression is revisited in Summary to show whether it held or was revised by data

### Score 2 — Logical Order, Implicit Narrative

- Phases appear in logical order
- Summary exists and synthesizes findings
- Phases do not reference each other explicitly — narrative is implicit
- Summary reads as a structured list rather than a story

### Score 1 — Sequential but Disconnected

- Phases follow a sequence but each stands alone
- Summary is a bullet list of phase outputs
- No through-line connecting the original question to final conclusions

### Score 0 — Collection of Unrelated Observations

- Analysis is a flat set of observations with no structure
- No arc from question to insight
- Reader must construct the story themselves

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Blue Hat phase sets a narrative frame that defines what the analysis is trying to resolve
- [ ] Red Hat initial impression is explicitly revisited or updated in the Summary
- [ ] Black Hat quality findings are referenced in Yellow Hat (e.g., "excluding low-confidence rows per Black Hat findings...")
- [ ] Yellow Hat explicitly builds on White Hat findings (e.g., "White Hat found X; Yellow Hat now investigates whether X explains Y")
- [ ] Green Hat explicitly references Yellow Hat conclusions when proposing new angles
- [ ] Summary connects final conclusions back to the original questions posed in Wizard/Blue Hat
- [ ] FACT/ASSUME rhythm throughout creates readable, structured prose

---

## Sample Validation

**Scenario:** Google Ads analysis starting with "CPA has increased."

Apply SKILL.md mentally and trace the narrative arc:

1. **Blue Hat** sets frame: "We are investigating whether CPA increase is supply-side (CPC) or demand-side (CVR)."
2. **White Hat** surfaces: CPC +18%, CVR -8%.
3. **Red Hat** impression: "Feels like a bid strategy issue."
4. **Black Hat** flags: "3 ad groups have N < 20 conversions; exclude from CVR analysis."
5. **Yellow Hat** builds on this: "After excluding small-N ad groups per Black Hat, CVR drop is concentrated in mobile. CPC increase is campaign-wide."
6. **Green Hat**: "Yellow Hat found mobile CVR drop — we haven't checked whether mobile landing page speed changed during this period."
7. **Summary** closes the loop: "Red Hat impression (bid strategy) was partially correct for CPC increase, but mobile CVR drop (not bid-related) is the larger driver. Original question resolved: CPA increase is primarily demand-side, concentrated in mobile."

A Score 3 skill would explicitly instruct each phase to reference the prior phase's key output, and the Summary to evaluate whether the Blue Hat frame was resolved.

---

## Output Format

```json
{
  "metric": "narrative",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing phase cross-referencing>'",
    "SKILL.md line N: '<exact quote showing Summary arc or absence>'"
  ],
  "gaps": [
    "Missing: Phases do not reference outputs of previous phases",
    "Missing: Summary does not revisit Red Hat impression",
    "Missing: No instruction to connect Summary back to Blue Hat frame"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
