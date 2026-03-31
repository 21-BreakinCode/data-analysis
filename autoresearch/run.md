# Running the Autoresearch Eval

## Prerequisites

- Python 3 with `duckdb` package
- Claude Code CLI

## Quick Start

### 1. Generate datasets (one-time)

```bash
python3 autoresearch/datasets/google-ads/generate.py
python3 autoresearch/datasets/facebook-ads/generate.py
```

### 2. Run the eval orchestrator

Tell Claude Code:

> "Read autoresearch/agents/orchestrator.md and follow its instructions to score the data-analysis SKILL.md"

This dispatches 12 scorer agents in parallel, aggregates results, and writes a report to `autoresearch/reports/`.

### 3. View results

```bash
open autoresearch/dashboard/index.html
```

### 4. Improve (if score < 36/36)

Tell Claude Code:

> "Read autoresearch/agents/improver.md and follow its instructions to improve SKILL.md based on the latest eval report"

### 5. Re-score

Repeat step 2. The dashboard auto-loads all reports and shows the improvement timeline.

### 6. Iterate

Repeat steps 4-5 until 36/36 or max 5 iterations.

## File Reference

| File | Purpose |
|------|---------|
| `agents/scorer/*.md` | 12 metric scoring agents |
| `agents/orchestrator.md` | Dispatches scorers, aggregates reports |
| `agents/improver.md` | Reads gaps, edits SKILL.md |
| `datasets/*/data.csv` | Ads datasets for validation |
| `datasets/*/playbook.md` | Business context for scoring |
| `reports/run-*.json` | Score reports (one per eval run) |
| `changelog.json` | Iteration history |
| `dashboard/index.html` | Visual dashboard |
