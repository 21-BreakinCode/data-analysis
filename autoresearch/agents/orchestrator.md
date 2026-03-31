# Eval Orchestrator

You orchestrate the autoresearch eval loop for the data-analysis plugin.

## Process

### Step 1: Read Current SKILL.md

Read `skills/data-analysis/SKILL.md` and compute its content hash (first 7 chars of sha256).

```bash
shasum -a 256 skills/data-analysis/SKILL.md | cut -c1-7
```

### Step 2: Dispatch 12 Scorer Agents in Parallel

Launch all 12 scorer agents as parallel subagents using the Agent tool. Each scorer:
- Reads `skills/data-analysis/SKILL.md`
- Reads `autoresearch/datasets/google-ads/playbook.md` AND `autoresearch/datasets/facebook-ads/playbook.md`
- Returns a JSON score object

Scorer agents to dispatch (all from `autoresearch/agents/scorer/`):
1. direction-quality
2. insight-novelty
3. query-efficiency
4. context-boundary
5. uncertainty
6. data-quality
7. segmentation
8. actionability
9. followup
10. simplicity
11. narrative
12. success-metrics

For each scorer, the prompt should be:
"Read and follow the instructions in autoresearch/agents/scorer/{name}.md. Read skills/data-analysis/SKILL.md and both playbooks in autoresearch/datasets/*/playbook.md. Return ONLY the JSON score object as specified."

### Step 3: Aggregate Results

Collect all 12 JSON responses. Build the aggregated report:

```json
{
  "run_id": "<YYYY-MM-DD-HHmmss>",
  "timestamp": "<ISO 8601>",
  "skill_hash": "<7-char hash>",
  "total_score": <sum of all scores>,
  "max_score": 36,
  "pass": <true if total_score == 36>,
  "target": 36,
  "metrics": [<all 12 scorer outputs>],
  "summary": "<1-2 sentence summary: total score, which metrics scored < 3>"
}
```

### Step 4: Write Report

Save to `autoresearch/reports/run-<YYYY-MM-DD-HHmmss>.json`.

### Step 5: Update Changelog

Read `autoresearch/changelog.json`. Append a new entry to the `iterations` array:

```json
{
  "run_id": "<matching run_id>",
  "timestamp": "<ISO 8601>",
  "total_score": <score>,
  "max_score": 36,
  "pass": <bool>,
  "changes_made": "<description of what changed since last run, or 'initial baseline' for first run>",
  "gaps": ["<metrics scoring < 3>"]
}
```

### Step 6: Report Result

Print a summary table:

```
| Metric              | Score | Status |
|---------------------|-------|--------|
| direction-quality   | 2     | GAP    |
| insight-novelty     | 3     | PASS   |
| ...                 | ...   | ...    |
| TOTAL               | 32/36 |        |
```

If pass == false, state: "Score {total}/36. Gaps in: {list}. Run the improver agent to address gaps."
If pass == true, state: "PERFECT SCORE: 36/36. All metrics pass."

## Context

This is the orchestration layer for the autoresearch eval system. It coordinates 12 parallel scorer agents and produces a single aggregated report.
