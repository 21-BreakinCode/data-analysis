# Scorer: Segmentation Quality

## Purpose

Evaluate whether SKILL.md guides analysis to use meaningful groupings rather than global averages — including multi-dimensional segmentation and checks for aggregation artifacts like Simpson's paradox.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Multi-Dimensional Segmentation with Averaging Warnings

- Explicitly warns against interpreting global averages without segment breakdown
- GROUP BY as the default analytical posture (not averages then drill-down)
- Guides multi-dimensional segmentation (e.g., campaign_type × device × time)
- Includes Simpson's paradox check (aggregate trend may reverse at segment level)
- Identifies which segments are driving changes in aggregate metrics

### Score 2 — Group Comparison Used, No Averaging Warning

- Segment comparisons present in Yellow Hat
- No explicit warning against global averages
- Single-dimensional segmentation only
- No multi-dimensional cross-tabs or paradox checks

### Score 1 — GROUP BY Present, Single-Dimensional Only

- GROUP BY queries appear in examples
- Operates dimension by dimension, never crossing dimensions
- No check for how segments contribute to aggregate changes

### Score 0 — Aggregate-Level Analysis Only

- Analysis operates on means, totals, or overall aggregates
- No segmentation guidance
- User must request segments explicitly

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Blue Hat or Yellow Hat explicitly warns: "global averages mask segment differences"
- [ ] Yellow Hat instructs multi-dimensional GROUP BY (at least two dimensions combined)
- [ ] Instruction to identify which segment(s) drive a change in an aggregate metric
- [ ] Instruction or check for Simpson's paradox (aggregate trend reverses when segmented)
- [ ] Playbook defines primary segments for the domain (e.g., campaign_type, device, audience)
- [ ] Analysis decomposes changes (e.g., "CPA increased: is it across all campaigns or driven by one?")

---

## Sample Validation

**Scenario 1:** Google Ads account where overall CPA increased 20%.

Apply SKILL.md mentally and ask:

1. Would the skill immediately segment by `campaign_type` before concluding "CPA increased"?
2. Would it further segment by `device` within each campaign type?
3. Would it check: "Is the CPA increase uniform across campaigns, or is one campaign driving the aggregate?"
4. Would it flag if a new high-spend, high-CPA campaign entered the mix and made overall CPA look worse even though existing campaigns improved?

**Scenario 2:** Facebook Ads where `Age_18_24` is a large segment.

Apply SKILL.md mentally and ask:

1. Would the skill check whether `Age_18_24` is dragging down `Broad_CBO` campaign averages even though other age groups in the same campaign are efficient?
2. Would it segment `Broad_CBO` by age bracket before drawing conclusions about campaign performance?

A Score 3 skill would include: "Default to GROUP BY before reporting any metric. Before stating an average, ask: 'Which segments make up this average, and do they behave consistently?'"

---

## Output Format

```json
{
  "metric": "segmentation",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing segmentation guidance>'",
    "SKILL.md line N: '<exact quote showing averaging warning or absence>'"
  ],
  "gaps": [
    "Missing: No warning against interpreting global averages",
    "Missing: No multi-dimensional segmentation guidance",
    "Missing: No Simpson's paradox check"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
