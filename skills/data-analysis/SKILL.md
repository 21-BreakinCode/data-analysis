---
name: data-analysis
description: "Analyze CSV, Parquet, and JSON datasets using DuckDB with Six Thinking Hats methodology and optional business-context playbooks."
---

# Data Analysis

Analyze datasets using DuckDB as the compute engine and Six Thinking Hats as the analysis framework. Every observation uses `<FACT>` and `<ASSUME>` tags to separate what the data shows from what it might mean.

## Prerequisites

- Python 3 with `duckdb` package
- If DuckDB is not installed, offer to install it (`pip install duckdb`) before proceeding

## Workflow

```
Wizard → Blue Hat (plan) → White Hat (profile) → Red Hat (impression)
       → Black Hat (quality) → Yellow Hat (findings) → Green Hat (creativity)
       → Summary
```

Each hat phase **pauses for user review** before proceeding to the next. This is not optional — the user is a co-pilot who may correct your assumptions at any step.

---

## Phase 0: Wizard Setup

Start an interactive setup. Ask **one question at a time**:

1. **Data file**: "What data file would you like to analyze? (CSV, Parquet, or JSON path)"
2. **Playbook**: Scan the plugin's `playbooks/` directory for available `.md` files. Present them: "Would you like to apply a business context playbook? Available: [list]. Or 'none' for generic analysis." If the user has their own playbook file elsewhere, accept that path too.
3. **Questions**: "What questions do you have about this data? Or type 'explore' for general profiling."

After collecting inputs, load the data into DuckDB:

```python
import duckdb
con = duckdb.connect()
con.execute("CREATE TABLE data AS SELECT * FROM 'path/to/file'")
row_count = con.execute("SELECT COUNT(*) FROM data").fetchone()[0]
columns = con.execute("DESCRIBE data").fetchall()
```

Confirm with the user: "Loaded [N] rows, [M] columns. Ready to begin analysis."

If loading fails (bad path, corrupt file, encoding issues), show the error clearly and help the user fix it before retrying.

---

## Phase 1: Blue Hat — Analysis Plan

**Purpose**: Define what we will examine and why.

Read the user's questions, the data schema, and the playbook context (if any). Based on data shape (column types, row count, cardinality), propose which analysis techniques to apply.

**Available techniques**:

| Technique | When to use |
|-----------|------------|
| Distribution analysis | Categorical or numeric columns — value counts, histograms, percentiles |
| Trend analysis | Date/time column present — patterns over time, seasonality |
| Correlation analysis | Multiple numeric columns — relationships, strength |
| Anomaly detection | Any column — outliers, unexpected nulls, distribution breaks |
| Group comparison | Category column present — segment-by-segment differences |
| Funnel analysis | Data represents sequential stages — drop-off or growth patterns |

**Output**:

```
## Blue Hat: Analysis Plan

<FACT>
- Dataset: [filename], [N] rows x [M] columns
- Column types: [list by type — numeric, categorical, datetime, text]
- User questions: [what they asked]
- Playbook applied: [name or 'none']
</FACT>

<ASSUME>
Based on the data shape and your questions, I recommend:
1. [Technique] — [why this fits]
2. [Technique] — [why this fits]
3. [Technique] — [why this fits]
</ASSUME>

Does this plan look right? Add, remove, or reorder anything?
```

**Wait for user confirmation.**

---

## Phase 2: White Hat — Data Profiling

**Purpose**: Neutral facts only. Zero interpretation.

Run profiling via DuckDB:

```python
# Full summary
con.execute("SUMMARIZE data").fetchdf()

# For large datasets (>1M rows), sample first
con.execute("CREATE TABLE data_sample AS SELECT * FROM data USING SAMPLE 10 PERCENT")
```

**Sampling strategy**:
- Under 100K rows: profile full dataset
- 100K–1M rows: full for profiling, sample for expensive operations
- Over 1M rows: sample 10% for initial profile, note this in output

**Output**:

```
## White Hat: Data Profile

<FACT>
**Shape**: [N] rows x [M] columns

| Column | Type | Non-null | Distinct | Min | Max | Mean |
|--------|------|----------|----------|-----|-----|------|
| ...    | ...  | ...      | ...      | ... | ... | ...  |

**Notable**:
- [Column X]: [N]% null values
- [Column Y]: [N] distinct values out of [M] rows
- Date range: [min] to [max]
- [If sampled]: "Profiled on 10% sample ([N] rows)"
</FACT>

<ASSUME>
None — just the facts.
</ASSUME>

Anything surprising here? Should I dig deeper into any column?
```

**Wait for user review.**

---

## Phase 3: Red Hat — Initial Impression

**Purpose**: Quick gut reaction. Deliberately brief and subjective — like a 30-second first impression.

```
## Red Hat: Initial Impression

<FACT>
[Reference 2-3 specific numbers from the profile that triggered the impression]
</FACT>

<ASSUME>
My quick read:
- [Data quality gut feel — does this look clean or messy?]
- [Any obvious patterns jumping out from the summary stats?]
- [Can this data actually answer the user's questions?]
</ASSUME>

Does this match your intuition? If not, tell me what I'm reading wrong — this is where your domain knowledge matters most.
```

**Wait for user reaction.** This phase calibrates interpretation. If the user corrects you here — e.g., a pattern you flagged as anomalous is actually normal in their domain — that correction should inform all subsequent phases.

---

## Phase 4: Black Hat — Data Quality & Caveats

**Purpose**: Critical evaluation. What's wrong, missing, or risky?

Run quality checks:

```python
# Null rates per column
con.execute("""
    SELECT column_name, null_percentage
    FROM (SUMMARIZE data)
    WHERE null_percentage > 0
    ORDER BY null_percentage DESC
""")

# Duplicate rows
con.execute("""
    SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM data)) as dupes
    FROM data
""")

# Outliers (IQR method — run per numeric column)
for col_name in numeric_columns:
    con.execute(f"""
        SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY "{col_name}") as q1,
               percentile_cont(0.75) WITHIN GROUP (ORDER BY "{col_name}") as q3
        FROM data
    """)
```

**If a playbook is loaded**, check data against expected patterns:
- Does the shape match what the playbook says is normal?
- Are expected columns present?
- Do value ranges match business expectations?
- Are there patterns the playbook says are normal that you would otherwise flag?

**Output**:

```
## Black Hat: Data Quality & Caveats

<FACT>
**Nulls**:
| Column | Null count | Null % |
|--------|-----------|--------|
| ...    | ...       | ...    |

**Duplicates**: [N] duplicate rows
**Outliers**: [Column X] has [N] values beyond 1.5x IQR
[If playbook]: **Playbook check**: [which expected patterns match/don't match]
</FACT>

<ASSUME>
- [Are nulls random or systematic?]
- [Are duplicates expected (denormalized) or problematic?]
- [Are outliers real extremes or data errors?]
- [Playbook-specific interpretation of any issues]
</ASSUME>

<SUGGEST>
- [How to handle each issue, if needed]
</SUGGEST>

How would you like to handle these? Proceed as-is, or apply cleaning?
```

**Wait for user decision.**

---

## Phase 5: Yellow Hat — Key Findings

**Purpose**: What does the data reveal? What opportunities exist?

Execute the techniques selected in the Blue Hat plan. This is the main analytical phase — run DuckDB queries for each technique and present results.

For each technique, run the relevant queries using standard approaches:

- **Distribution**: `SELECT col, COUNT(*) FROM data GROUP BY col ORDER BY COUNT(*) DESC LIMIT 20`
- **Trend**: `SELECT date_trunc('month', date_col), COUNT(*), AVG(metric) FROM data GROUP BY 1 ORDER BY 1`
- **Correlation**: compute pairwise correlations between numeric columns
- **Anomaly**: Z-score or IQR-based detection
- **Group comparison**: `SELECT category, COUNT(*), AVG(metric), MEDIAN(metric) FROM data GROUP BY category`
- **Funnel**: `SELECT stage, COUNT(*) FROM data GROUP BY stage ORDER BY stage_order`

**Keep result sets under 50 rows** in conversation. Summarize larger results. For tables exceeding this, show top/bottom N and aggregate the middle.

**Output**:

```
## Yellow Hat: Key Findings

<FACT>
**[Technique 1 name]**:
[Query results as markdown tables or bullet points]

**[Technique 2 name]**:
[Results]

**[Technique 3 name]**:
[Results]
</FACT>

<ASSUME>
Key insights:
1. [What finding #1 might mean for the business]
2. [What finding #2 suggests]
3. [Pattern or opportunity spotted]
[If playbook loaded: interpret through business context — use the playbook's definitions and thresholds]
</ASSUME>

Which findings matter most to you? Want to drill deeper into any of these?
```

**Wait for user feedback.** They may want to zoom into specific findings — if so, run additional queries and present in the same FACT/ASSUME format.

---

## Phase 6: Green Hat — Alternative Perspectives

**Purpose**: Creative angles. What haven't we tried? What might we be missing?

```
## Green Hat: Alternative Perspectives

<FACT>
[What we've analyzed so far and what remains unexplored]
</FACT>

<ASSUME>
Alternative angles worth exploring:
1. [A different way to slice the data we haven't tried]
2. [A hypothesis that contradicts our Yellow Hat findings]
3. [An unexpected derived metric worth computing]
4. [Cross-referencing suggestion — "what if we joined with X?"]
</ASSUME>

Want me to pursue any of these? Or are you satisfied with the analysis?
```

**Wait for user decision.** If they want more, loop back with additional DuckDB queries in FACT/ASSUME format. If satisfied, proceed to summary.

---

## Summary

After all phases complete (or user says they're satisfied):

```
## Analysis Complete

**Key facts discovered:**
- [Top 3-5 FACT highlights across all phases]

**Main interpretations:**
- [Top 3-5 ASSUME highlights]

**Open questions:**
- [Anything unresolved or worth investigating with more data]

**Data quality notes:**
- [Key caveats to keep in mind when acting on these findings]
```

---

## Important Rules

1. **Never modify source data** — all DuckDB operations are read-only
2. **Show your queries** — the user should see what SQL is being run (use code blocks)
3. **FACT before ASSUME** — always lead with observable evidence
4. **Pause between phases** — wait for user review at each hat transition, no exceptions
5. **Respect playbook context** — if a playbook says a pattern is normal, do not flag it as anomalous
6. **Sample large data** — never dump full large tables into conversation context
7. **One question at a time** — during wizard and phase reviews
8. **Correct course when told** — if the user says your assumption is wrong, update your mental model for all subsequent phases
