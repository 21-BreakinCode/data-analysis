# Scorer: Follow-Up Generation

## Purpose

Evaluate whether SKILL.md anticipates the user's next questions and generates structured follow-up paths — deeper dives, open hypotheses, and data gaps to fill.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Structured Follow-Up Generation

- Each analytical phase generates at least one specific next question (not "anything else?")
- Green Hat proposes specific unexplored analytical angles that could change conclusions
- Summary includes a structured list of open questions and unresolved hypotheses
- At least one phase notes "what additional data would we need to confirm this finding?"
- Wizard handles "explore further" mode with a defined protocol for deepening analysis

### Score 2 — Phases Pause for Input, No Structured Follow-Up

- Phases pause and check in with the user before proceeding
- Green Hat suggests alternative approaches
- No structured list of follow-up questions generated
- Open hypotheses not captured or surfaced

### Score 1 — Generic Prompts Only

- Phases end with generic "Is there anything else you'd like to explore?" prompts
- No specific follow-up questions tied to findings
- Analysis is essentially one-shot with a weak check-in mechanism

### Score 0 — One-Shot Report, No Follow-Up

- Analysis produces a report and stops
- No mechanism for follow-up, iteration, or deepening

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Each phase ends with at least one specific question tied to the phase's output (not generic)
- [ ] Green Hat phase proposes specific unexplored analytical angles (e.g., "we haven't checked time-of-day patterns")
- [ ] Summary phase includes a dedicated "Open Questions" or "Next Steps" section
- [ ] Yellow Hat instructs suggesting specific drill-down analyses for anomalies found
- [ ] At least one instruction notes what additional data (columns, time range, external data) would improve conclusions
- [ ] Wizard phase has explicit "explore mode" instructions for iterative deepening

---

## Sample Validation

**Scenario:** Analysis of Google Ads performance showing `Brand_Search` campaigns are efficient but `Display` is underperforming.

Apply SKILL.md mentally and ask:

1. After identifying `Display` underperformance, would the skill generate a specific follow-up question like "Is the Display underperformance driven by placements, audiences, or creatives?" — not just "would you like to explore Display further?"
2. Would Green Hat propose "we haven't analyzed conversion lag for Display (view-through vs click-through)" as a specific unexplored angle?
3. Would the Summary include: "Open question: Is Display underperformance consistent across devices, or driven by mobile?" as a structured next step?
4. Would the skill note "to confirm this hypothesis we would need impression share data, which is not in the current dataset"?

A Score 3 skill would include: "At the end of Yellow Hat, generate a 'Follow-Up Queue' of 3-5 specific questions that arose from the analysis but were not answered. Each question should reference a specific finding and suggest the analysis needed to resolve it."

---

## Output Format

```json
{
  "metric": "followup",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing follow-up generation mechanism>'",
    "SKILL.md line N: '<exact quote showing open questions handling or absence>'"
  ],
  "gaps": [
    "Missing: Phases end with generic prompts, not specific follow-up questions",
    "Missing: No structured Open Questions section in Summary",
    "Missing: No instruction to note what additional data would strengthen conclusions"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
