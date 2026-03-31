# Autoresearch Eval System for Data-Analysis Plugin

## Overview

A self-improving evaluation system inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) that scores the data-analysis plugin's SKILL.md against 12 data analysis quality metrics. Eval agents score structurally, an improver agent applies fixes, and the loop repeats until 36/36 (all metrics scoring 3).

## Architecture

```
autoresearch/
├── agents/
│   ├── scorer/                  # 12 metric scoring agents
│   │   ├── direction-quality.md
│   │   ├── insight-novelty.md
│   │   ├── query-efficiency.md
│   │   ├── context-boundary.md
│   │   ├── uncertainty.md
│   │   ├── data-quality.md
│   │   ├── segmentation.md
│   │   ├── actionability.md
│   │   ├── followup.md
│   │   ├── simplicity.md
│   │   ├── narrative.md
│   │   └── success-metrics.md
│   ├── orchestrator.md          # Dispatches scorers, aggregates results
│   └── improver.md              # Reads scores, edits SKILL.md
├── datasets/
│   ├── google-ads/
│   │   ├── data.csv
│   │   └── playbook.md
│   └── facebook-ads/
│       ├── data.csv
│       └── playbook.md
├── reports/
│   └── run-YYYY-MM-DD-HHmmss.json
├── changelog.json
├── dashboard/
│   └── index.html
└── run.md
```

## Scoring System

### Scale: 0-3 per metric

- **0** — Not addressed at all
- **1** — Mentioned but weak/incomplete
- **2** — Adequately addressed
- **3** — Strongly addressed with specific mechanisms

### Target: 36/36 (all 12 metrics scoring 3)

### Scorer Output Format

```json
{
  "metric": "metric-name",
  "score": 2,
  "max_score": 3,
  "evidence": ["SKILL.md line X: ..."],
  "gaps": ["Missing: ..."],
  "recommendation": "Specific change to make"
}
```

### Aggregated Report Format

```json
{
  "run_id": "2026-03-31-143022",
  "timestamp": "2026-03-31T14:30:22Z",
  "skill_hash": "abc123",
  "total_score": 28,
  "max_score": 36,
  "pass": false,
  "target": 36,
  "metrics": [],
  "summary": "..."
}
```

## 12 Evaluation Metrics

| # | Metric | What it checks |
|---|--------|---------------|
| 1 | Direction Quality | Clear business question? Causation not just correlation? |
| 2 | Insight Novelty | Helpful for finding new/unexpected results? |
| 3 | Query Efficiency | DuckDB queries efficient? No redundant scans? |
| 4 | Context Boundary | Clear agent/phase separation? Right tool for right task? |
| 5 | Uncertainty | Quantifies confidence? States what data can/cannot prove? |
| 6 | Data Quality | Accounts for nulls, outliers, sampling bias, limitations? |
| 7 | Segmentation | Meaningful grouping vs just averaging? |
| 8 | Actionability | Includes specific, actionable recommendations? |
| 9 | Follow-up | Anticipates next questions? Suggests deeper dives? |
| 10 | Simplicity | Uses simplest appropriate method? No over-engineering? |
| 11 | Narrative | Tells coherent story from data to insight to action? |
| 12 | Success Metrics | Defines and validates metrics before measuring? |

## Agent Design

### Scorer Agents (12 total)

Each scorer:
1. Reads SKILL.md completely
2. Reads the relevant ads playbook for context
3. Structural analysis — scans for keywords, patterns, instructions addressing the metric
4. Sample validation — runs targeted DuckDB queries against ads dataset
5. Scores 0-3 with evidence + gaps + recommendation

### Orchestrator Agent

- Dispatches all 12 scorers as parallel subagents
- Collects JSON results
- Computes aggregate score
- Writes report to `reports/run-{timestamp}.json`
- Updates `changelog.json`
- Returns pass/fail against target (36/36)

### Improver Agent

- Reads latest report
- Identifies metrics scoring < 3
- Proposes specific SKILL.md edits for each gap
- Applies changes
- Triggers re-score via orchestrator

### Iteration Flow

```
Orchestrator → [12 Scorers in parallel] → Aggregate Report
     ↓
  36/36? → Yes → Done (publish final dashboard)
     ↓ No
  Improver → Edit SKILL.md → Re-trigger Orchestrator
     ↓
  Max 5 iterations → Stop, report best score
```

## Ads Datasets & Scenarios

### Dataset 1: Google Ads Campaign Performance

- **Scenario:** "Our CPA doubled last month. Is it a channel mix issue, audience fatigue, or creative decay?"
- **Stress-tests:** Causation framing (M1), segmentation by campaign/ad group (M7), uncertainty in attribution (M5), actionable bid/budget recommendations (M8)

### Dataset 2: Facebook/Meta Ads Performance

- **Scenario:** "Which audience segments should we scale spend on, and which should we cut?"
- **Stress-tests:** Meaningful segmentation (M7), data quality of pixel tracking (M6), follow-up questions about LTV vs CPA tradeoff (M9), success metric definition (M12)

## Dashboard

Static `index.html` with Chart.js CDN. Three sections:

1. **Scorecard** — Radar chart (12 metrics), color-coded (green/yellow/red), total score badge
2. **Iteration Timeline** — Line chart of total score across iterations, per-metric sparklines
3. **Change Log** — Per-iteration: what changed, why, score delta, SKILL.md diff snippets

Reads from `reports/*.json` and `changelog.json`. No server required.

## Execution

### How to run

1. Download ads datasets to `autoresearch/datasets/`
2. Run orchestrator: dispatches 12 scorers in parallel
3. Review report + dashboard
4. If < 36/36: run improver, then re-score
5. Repeat until 36/36 or max 5 iterations
