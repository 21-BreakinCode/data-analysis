# Scorer: Uncertainty Quantification

## Purpose

Evaluate whether SKILL.md instructs the skill to quantify confidence, distinguish statistically significant findings from noise, and clearly state what the data can and cannot prove.

## Inputs

- `skills/data-analysis/SKILL.md` — the skill instructions under evaluation
- Relevant playbooks referenced within SKILL.md (e.g., `playbooks/google-ads.md`, `playbooks/fb-ads.md`)

---

## Scoring Rubric

### Score 3 — Explicit Uncertainty Quantification

- Instructs stating a confidence level per finding (e.g., "high confidence: N=2,400" vs "suggestive: N=47")
- Explicitly distinguishes statistical significance from practical significance vs noise
- Instructs computing confidence intervals or effect sizes where applicable
- ASSUME tags used for interpretations, paired with explicit hedging language ("might," "likely," "insufficient N to conclude")
- Notes sample size when drawing conclusions from segments

### Score 2 — FACT/ASSUME Captures Some Uncertainty

- FACT/ASSUME separation present and used consistently
- Black Hat mentions data limitations
- No explicit confidence quantification (no N counts, no effect size, no significance checks)
- Uncertainty conveyed implicitly through hedging language but not systematically

### Score 1 — ASSUME Tags Present, No Confidence Quantification

- ASSUME tags or hedging language exist
- No instruction to compute N, check significance, or report effect size
- Findings in FACT/ASSUME blocks but uncertainty not tied to evidence quality

### Score 0 — Findings Stated as Certainties

- Findings presented as definitive without qualification
- No FACT/ASSUME separation
- No acknowledgment that conclusions may not hold at all sample sizes

---

## Evaluation Checklist

Scan SKILL.md for the following:

- [ ] Instruction to compute sample sizes for each segment before drawing conclusions
- [ ] Explicit threshold for "sufficient N" (e.g., N < 30 = flag as suggestive only)
- [ ] Distinction between "statistically significant" and "directionally suggestive"
- [ ] Instruction to report confidence intervals or effect sizes for key metrics
- [ ] Hedging language required in ASSUME blocks ("might," "likely," "insufficient data to confirm")
- [ ] Instruction to state what the data cannot tell you (e.g., "this dataset does not capture view-through conversions")
- [ ] Black Hat phase explicitly flags segments with insufficient sample size

---

## Sample Validation

**Scenario 1:** Google Ads account with some ad groups having 3–5 conversions over the analysis period.

Apply SKILL.md mentally and ask:

1. Would the skill flag that a 40% CPA difference in an ad group with N=5 conversions is not statistically meaningful?
2. Would it distinguish "Campaign A has higher CPA (N=2,400, high confidence)" from "Ad Group B has higher CPA (N=5, insufficient data)"?

**Scenario 2:** Facebook Ads with `pixel_confidence` column ranging from 0.3 to 1.0.

Apply SKILL.md mentally and ask:

1. Would the skill quantify how much of the conversion volume comes from low-confidence pixels (e.g., "38% of conversions have pixel_confidence < 0.7")?
2. Would it attach uncertainty to conversion metrics derived from low-confidence pixels?
3. Would the Summary include a caveat like "conversion figures for Segment X are unreliable due to pixel_confidence averaging 0.4"?

---

## Output Format

```json
{
  "metric": "uncertainty",
  "score": 0,
  "max_score": 3,
  "evidence": [
    "SKILL.md line N: '<exact quote showing uncertainty handling>'",
    "SKILL.md line N: '<exact quote showing ASSUME usage or absence>'"
  ],
  "gaps": [
    "Missing: No instruction to compute sample sizes before drawing conclusions",
    "Missing: No threshold for minimum N to report a finding as reliable",
    "Missing: Confidence intervals or effect sizes not mentioned"
  ],
  "recommendation": "<specific edit to make to SKILL.md, referencing exact section and proposed text>"
}
```
