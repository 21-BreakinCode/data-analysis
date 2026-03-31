# Scorer: Actionability

## Purpose

Evaluate whether SKILL.md produces specific, actionable recommendations tied to findings — not just observations. A high score means the skill would tell the user what to do, where, and why.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Specific Actions with Expected Impact

- SUGGEST tags used with concrete, specific actions (e.g., "shift $X budget from Campaign A to Campaign B", "lower bid on Device Y by 15%")
- Each recommendation includes what to do, where (specific campaign/segment/ad group), and expected impact
- Yellow Hat findings are paired with associated recommended actions
- Summary includes a prioritized list of recommendations with effort or impact estimates
- Playbook Steps drive the recommendation structure (not generic best practices)

### Score 2 — SUGGEST Used, Recommendations Generic

- SUGGEST tags present in Black Hat or Summary
- Recommendations are generic ("optimize underperforming campaigns", "review creative performance")
- Not tied to specific data points or segments identified in the analysis
- No prioritization or impact estimation

### Score 1 — Findings Without Recommendation Mechanism

- Findings clearly presented
- No structured mechanism to convert findings into recommendations
- User must infer actions from observations

### Score 0 — Purely Descriptive

- Only reports what happened
- No recommendations, actions, or next steps of any kind

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] SUGGEST tags (or equivalent) used with specific actions, not general guidance
- [ ] Each recommendation includes: what action, which specific entity (campaign/ad group/segment), expected impact
- [ ] Yellow Hat phase explicitly pairs each finding with an associated action
- [ ] Summary phase produces a prioritized list of recommended actions
- [ ] Recommendations reference specific data findings (not generic best practices)
- [ ] Playbook Steps section drives the recommendation structure for the domain

---

## Sample Validation

**Scenario:** Google Ads analysis identifies that `Brand_Search` campaign has CPA of $12 (below $18 target) while `Competitor_Keywords` has CPA of $34 (above target).

Apply SKILL.md mentally and ask:

1. Would the skill recommend specifically: "Increase `Brand_Search` budget by 20-30%; reduce `Competitor_Keywords` bids by 15%" — or just "Brand_Search is efficient; Competitor_Keywords needs attention"?
2. Would the Summary rank this recommendation as "high priority" based on spend volume and gap from target?
3. Would the recommendation reference the specific CPA figures from the analysis (not just say "CPA is high")?
4. Would the Yellow Hat finding "CPA in Competitor_Keywords is 89% above target" automatically trigger a SUGGEST for a specific bid or budget action?

A Score 3 skill would include: "For each finding where a metric exceeds or falls below the playbook threshold, generate a SUGGEST with: (1) specific action type (bid change, budget shift, pause, test), (2) specific entity name, (3) magnitude if quantifiable, (4) expected directional outcome."

---

## Output Format

```json
{
  "metric": "actionability",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing SUGGEST usage or recommendation mechanism>'",
    "SKILL.md line N: '<exact quote showing generic vs specific recommendation>'"
  ],
  "gaps": [
    "Missing: SUGGEST tags not used with specific actions",
    "Missing: Recommendations not tied to specific entities from the data",
    "Missing: Summary does not prioritize recommendations"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
