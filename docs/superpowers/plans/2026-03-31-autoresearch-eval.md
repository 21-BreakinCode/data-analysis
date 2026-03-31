# Autoresearch Eval System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-improving eval system that scores the data-analysis plugin's SKILL.md against 12 quality metrics, improves it to 36/36, and renders results in a static HTML dashboard.

**Architecture:** Standalone `autoresearch/` directory with 12 scorer agents (one per metric), an orchestrator that dispatches them in parallel and aggregates JSON reports, an improver agent that edits SKILL.md based on gaps, and a static Chart.js dashboard that reads report JSON files.

**Tech Stack:** Markdown agents (Claude Code subagents), Python + DuckDB (dataset generation), HTML + Chart.js (dashboard), JSON (reports/changelog)

---

### Task 1: Scaffold Directory Structure

**Files:**
- Create: `autoresearch/reports/.gitkeep`
- Create: `autoresearch/changelog.json`
- Create: `autoresearch/datasets/google-ads/.gitkeep`
- Create: `autoresearch/datasets/facebook-ads/.gitkeep`

- [ ] **Step 1: Create all directories**

```bash
mkdir -p autoresearch/agents/scorer
mkdir -p autoresearch/datasets/google-ads
mkdir -p autoresearch/datasets/facebook-ads
mkdir -p autoresearch/reports
mkdir -p autoresearch/dashboard
```

- [ ] **Step 2: Initialize changelog.json**

Write to `autoresearch/changelog.json`:

```json
{
  "iterations": []
}
```

- [ ] **Step 3: Add .gitkeep for empty directories**

```bash
touch autoresearch/reports/.gitkeep
```

- [ ] **Step 4: Commit scaffold**

```bash
git add autoresearch/
git commit -m "chore: scaffold autoresearch eval directory structure"
```

---

### Task 2: Generate Google Ads Dataset

**Files:**
- Create: `autoresearch/datasets/google-ads/generate.py`
- Create: `autoresearch/datasets/google-ads/data.csv`

This generates a realistic Google Ads campaign dataset with embedded patterns that stress-test the 12 eval metrics.

- [ ] **Step 1: Write the generator script**

Write to `autoresearch/datasets/google-ads/generate.py`:

```python
import duckdb

con = duckdb.connect()

con.execute("""
CREATE TABLE google_ads AS
WITH date_range AS (
    SELECT UNNEST(generate_series(DATE '2025-01-01', DATE '2026-03-31', INTERVAL '1 day')) AS day
),
campaigns AS (
    SELECT UNNEST(['Brand_Search', 'Generic_Search', 'Competitor_Search',
                   'Display_Retarget', 'Display_Prospecting', 'Video_Awareness',
                   'Shopping_Feed', 'Performance_Max']) AS campaign_name
),
ad_groups AS (
    SELECT
        campaign_name,
        CASE campaign_name
            WHEN 'Brand_Search' THEN UNNEST(['Brand_Exact', 'Brand_Broad', 'Brand_Product'])
            WHEN 'Generic_Search' THEN UNNEST(['Category_Terms', 'Problem_Terms', 'Comparison_Terms'])
            WHEN 'Competitor_Search' THEN UNNEST(['Competitor_A', 'Competitor_B', 'Competitor_C'])
            WHEN 'Display_Retarget' THEN UNNEST(['Cart_Abandon_7d', 'Product_View_14d', 'Past_Buyer_90d'])
            WHEN 'Display_Prospecting' THEN UNNEST(['Lookalike_1pct', 'Lookalike_5pct', 'Interest_Based'])
            WHEN 'Video_Awareness' THEN UNNEST(['YouTube_InStream', 'YouTube_Discovery', 'YouTube_Bumper'])
            WHEN 'Shopping_Feed' THEN UNNEST(['Electronics', 'Apparel', 'Home_Garden'])
            WHEN 'Performance_Max' THEN UNNEST(['PMax_AllProducts', 'PMax_HighMargin', 'PMax_NewArrivals'])
        END AS ad_group_name
    FROM campaigns
),
base AS (
    SELECT
        d.day AS date,
        ag.campaign_name,
        ag.ad_group_name,
        -- Deterministic seed from date + names
        hash(d.day::VARCHAR || ag.campaign_name || ag.ad_group_name) AS seed
    FROM date_range d
    CROSS JOIN ad_groups ag
)
SELECT
    date,
    campaign_name,
    ad_group_name,

    -- Campaign type derived
    CASE
        WHEN campaign_name LIKE '%Search%' THEN 'Search'
        WHEN campaign_name LIKE '%Display%' THEN 'Display'
        WHEN campaign_name LIKE '%Video%' THEN 'Video'
        WHEN campaign_name LIKE '%Shopping%' THEN 'Shopping'
        ELSE 'PMax'
    END AS campaign_type,

    -- Device split
    CASE (abs(seed) % 3)
        WHEN 0 THEN 'mobile'
        WHEN 1 THEN 'desktop'
        ELSE 'tablet'
    END AS device,

    -- Impressions: base varies by campaign type + seasonality
    GREATEST(10, (
        CASE
            WHEN campaign_name LIKE '%Brand%' THEN 500
            WHEN campaign_name LIKE '%Generic%' THEN 1200
            WHEN campaign_name LIKE '%Competitor%' THEN 300
            WHEN campaign_name LIKE '%Retarget%' THEN 800
            WHEN campaign_name LIKE '%Prospecting%' THEN 2000
            WHEN campaign_name LIKE '%Video%' THEN 5000
            WHEN campaign_name LIKE '%Shopping%' THEN 600
            ELSE 1000
        END
        -- Q4 holiday surge (Nov-Dec)
        * CASE WHEN EXTRACT(MONTH FROM date) IN (11, 12) THEN 1.8 ELSE 1.0 END
        -- Weekend dip
        * CASE WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 0.7 ELSE 1.0 END
        -- Random variance ±30%
        * (0.7 + (abs(seed % 60)) / 100.0)
    )::INT) AS impressions,

    -- CTR: varies by campaign type, DEGRADES for Generic_Search after 2025-09 (audience fatigue signal)
    ROUND(CASE
        WHEN campaign_name LIKE '%Brand%' THEN 0.08 + (abs(seed % 40)) / 1000.0
        WHEN campaign_name LIKE '%Generic%' AND date >= DATE '2025-09-01'
            THEN 0.025 - (EXTRACT(MONTH FROM date) - 8) * 0.002  -- fatigue decay
        WHEN campaign_name LIKE '%Generic%' THEN 0.04 + (abs(seed % 20)) / 1000.0
        WHEN campaign_name LIKE '%Competitor%' THEN 0.03 + (abs(seed % 15)) / 1000.0
        WHEN campaign_name LIKE '%Retarget%' THEN 0.06 + (abs(seed % 30)) / 1000.0
        WHEN campaign_name LIKE '%Prospecting%' THEN 0.01 + (abs(seed % 10)) / 1000.0
        WHEN campaign_name LIKE '%Video%' THEN 0.005 + (abs(seed % 5)) / 1000.0
        WHEN campaign_name LIKE '%Shopping%' THEN 0.05 + (abs(seed % 25)) / 1000.0
        ELSE 0.03 + (abs(seed % 20)) / 1000.0
    END, 4) AS ctr,

    -- Clicks derived from impressions * ctr (computed below in final select)
    -- CPC: varies by campaign, INCREASES for all Search after 2026-01 (CPA doubling signal)
    ROUND(CASE
        WHEN campaign_name LIKE '%Brand%' AND date >= DATE '2026-01-01'
            THEN 1.20 + (abs(seed % 80)) / 100.0  -- CPC spike
        WHEN campaign_name LIKE '%Brand%' THEN 0.60 + (abs(seed % 40)) / 100.0
        WHEN campaign_name LIKE '%Generic%' AND date >= DATE '2026-01-01'
            THEN 3.50 + (abs(seed % 200)) / 100.0  -- CPC spike
        WHEN campaign_name LIKE '%Generic%' THEN 1.80 + (abs(seed % 100)) / 100.0
        WHEN campaign_name LIKE '%Competitor%' AND date >= DATE '2026-01-01'
            THEN 4.00 + (abs(seed % 250)) / 100.0  -- CPC spike
        WHEN campaign_name LIKE '%Competitor%' THEN 2.50 + (abs(seed % 150)) / 100.0
        WHEN campaign_name LIKE '%Retarget%' THEN 0.80 + (abs(seed % 60)) / 100.0
        WHEN campaign_name LIKE '%Prospecting%' THEN 1.50 + (abs(seed % 100)) / 100.0
        WHEN campaign_name LIKE '%Video%' THEN 0.10 + (abs(seed % 10)) / 100.0
        WHEN campaign_name LIKE '%Shopping%' THEN 0.90 + (abs(seed % 70)) / 100.0
        ELSE 1.00 + (abs(seed % 80)) / 100.0
    END, 2) AS cpc,

    -- Conversion rate: drops for Search campaigns after 2026-01 (contributes to CPA doubling)
    ROUND(CASE
        WHEN campaign_name LIKE '%Brand%' AND date >= DATE '2026-01-01'
            THEN 0.06 - 0.02  -- conversion drop
        WHEN campaign_name LIKE '%Brand%' THEN 0.06 + (abs(seed % 20)) / 1000.0
        WHEN campaign_name LIKE '%Generic%' AND date >= DATE '2026-01-01'
            THEN 0.025 - 0.01  -- conversion drop
        WHEN campaign_name LIKE '%Generic%' THEN 0.025 + (abs(seed % 10)) / 1000.0
        WHEN campaign_name LIKE '%Retarget%' THEN 0.08 + (abs(seed % 30)) / 1000.0
        WHEN campaign_name LIKE '%Prospecting%' THEN 0.005 + (abs(seed % 5)) / 1000.0
        WHEN campaign_name LIKE '%Shopping%' THEN 0.04 + (abs(seed % 15)) / 1000.0
        WHEN campaign_name LIKE '%Video%' THEN 0.002 + (abs(seed % 3)) / 1000.0
        ELSE 0.02 + (abs(seed % 10)) / 1000.0
    END, 4) AS conversion_rate,

    -- Conversion value (revenue per conversion)
    ROUND(CASE
        WHEN campaign_name LIKE '%Brand%' THEN 85.0 + (abs(seed % 40))
        WHEN campaign_name LIKE '%Generic%' THEN 65.0 + (abs(seed % 50))
        WHEN campaign_name LIKE '%Retarget%' THEN 95.0 + (abs(seed % 60))
        WHEN campaign_name LIKE '%Prospecting%' THEN 45.0 + (abs(seed % 30))
        WHEN campaign_name LIKE '%Shopping%' THEN 75.0 + (abs(seed % 50))
        WHEN campaign_name LIKE '%Video%' THEN 35.0 + (abs(seed % 25))
        ELSE 55.0 + (abs(seed % 40))
    END, 2) AS avg_conversion_value,

    -- Quality score (1-10, only for Search)
    CASE
        WHEN campaign_name LIKE '%Search%' OR campaign_name LIKE '%Shopping%'
            THEN LEAST(10, GREATEST(1, 5 + (abs(seed % 6)) - 2))
        ELSE NULL
    END AS quality_score,

    -- Bounce rate for landing pages
    ROUND(CASE
        WHEN campaign_name LIKE '%Prospecting%' THEN 0.65 + (abs(seed % 20)) / 100.0
        WHEN campaign_name LIKE '%Brand%' THEN 0.25 + (abs(seed % 15)) / 100.0
        WHEN campaign_name LIKE '%Retarget%' THEN 0.30 + (abs(seed % 15)) / 100.0
        ELSE 0.45 + (abs(seed % 25)) / 100.0
    END, 2) AS bounce_rate,

    -- Some nulls in quality_score and bounce_rate for realism
    CASE WHEN abs(seed % 20) = 0 THEN NULL ELSE
        CASE WHEN campaign_name LIKE '%Search%' THEN 'text_ad'
             WHEN campaign_name LIKE '%Display%' THEN 'image_ad'
             WHEN campaign_name LIKE '%Video%' THEN 'video_ad'
             WHEN campaign_name LIKE '%Shopping%' THEN 'product_listing'
             ELSE 'responsive_ad'
        END
    END AS ad_format

FROM base
ORDER BY date, campaign_name, ad_group_name
""")

# Add computed columns
con.execute("""
CREATE TABLE google_ads_final AS
SELECT
    date,
    campaign_name,
    ad_group_name,
    campaign_type,
    device,
    impressions,
    ctr,
    GREATEST(1, (impressions * ctr)::INT) AS clicks,
    cpc,
    ROUND(GREATEST(1, (impressions * ctr)::INT) * cpc, 2) AS cost,
    conversion_rate,
    GREATEST(0, (GREATEST(1, (impressions * ctr)::INT) * conversion_rate)::INT) AS conversions,
    avg_conversion_value,
    ROUND(GREATEST(0, (GREATEST(1, (impressions * ctr)::INT) * conversion_rate)::INT) * avg_conversion_value, 2) AS conversion_value,
    CASE
        WHEN GREATEST(0, (GREATEST(1, (impressions * ctr)::INT) * conversion_rate)::INT) > 0
        THEN ROUND(GREATEST(1, (impressions * ctr)::INT) * cpc /
             GREATEST(1, (GREATEST(1, (impressions * ctr)::INT) * conversion_rate)::INT), 2)
        ELSE NULL
    END AS cpa,
    CASE
        WHEN GREATEST(1, (impressions * ctr)::INT) * cpc > 0
        THEN ROUND(GREATEST(0, (GREATEST(1, (impressions * ctr)::INT) * conversion_rate)::INT) * avg_conversion_value /
             (GREATEST(1, (impressions * ctr)::INT) * cpc), 2)
        ELSE NULL
    END AS roas,
    quality_score,
    bounce_rate,
    ad_format
FROM google_ads
""")

con.execute("COPY google_ads_final TO 'autoresearch/datasets/google-ads/data.csv' (HEADER, DELIMITER ',')")

row_count = con.execute("SELECT COUNT(*) FROM google_ads_final").fetchone()[0]
cols = con.execute("SELECT column_name FROM information_schema.columns WHERE table_name='google_ads_final'").fetchall()
print(f"Generated {row_count} rows, {len(cols)} columns")
print("Columns:", [c[0] for c in cols])

# Verify embedded patterns
print("\n--- Embedded Pattern Verification ---")
print("\nCPA trend (Search campaigns, monthly):")
con.execute("""
    SELECT date_trunc('month', date) AS month,
           ROUND(AVG(cpa), 2) AS avg_cpa
    FROM google_ads_final
    WHERE campaign_type = 'Search' AND cpa IS NOT NULL
    GROUP BY 1 ORDER BY 1
""").show()

print("\nCTR decay (Generic_Search, quarterly):")
con.execute("""
    SELECT date_trunc('quarter', date) AS quarter,
           ROUND(AVG(ctr), 4) AS avg_ctr
    FROM google_ads_final
    WHERE campaign_name = 'Generic_Search'
    GROUP BY 1 ORDER BY 1
""").show()
```

- [ ] **Step 2: Run the generator**

```bash
cd /Users/williamhung/Projects/cc-plugins/data-analysis && python3 autoresearch/datasets/google-ads/generate.py
```

Expected: prints row count (~10K+), column list, and pattern verification tables showing CPA increase in 2026 Q1 and CTR decay for Generic_Search.

- [ ] **Step 3: Commit dataset**

```bash
git add autoresearch/datasets/google-ads/
git commit -m "feat: add synthetic Google Ads dataset with embedded CPA/CTR patterns"
```

---

### Task 3: Generate Facebook Ads Dataset

**Files:**
- Create: `autoresearch/datasets/facebook-ads/generate.py`
- Create: `autoresearch/datasets/facebook-ads/data.csv`

- [ ] **Step 1: Write the generator script**

Write to `autoresearch/datasets/facebook-ads/generate.py`:

```python
import duckdb

con = duckdb.connect()

con.execute("""
CREATE TABLE fb_ads AS
WITH date_range AS (
    SELECT UNNEST(generate_series(DATE '2025-01-01', DATE '2026-03-31', INTERVAL '1 day')) AS day
),
campaigns AS (
    SELECT UNNEST(['Retargeting_DPA', 'Lookalike_1pct', 'Lookalike_5pct',
                   'Interest_Fitness', 'Interest_Tech', 'Interest_Fashion',
                   'Broad_CBO', 'Video_Views', 'Lead_Gen']) AS campaign_name
),
audiences AS (
    SELECT
        campaign_name,
        CASE
            WHEN campaign_name LIKE 'Retargeting%' THEN UNNEST(['Cart_Abandon', 'Product_View', 'Past_Purchase'])
            WHEN campaign_name LIKE 'Lookalike_1%' THEN UNNEST(['LA1_HighLTV', 'LA1_Purchasers', 'LA1_Engaged'])
            WHEN campaign_name LIKE 'Lookalike_5%' THEN UNNEST(['LA5_HighLTV', 'LA5_Purchasers', 'LA5_Engaged'])
            WHEN campaign_name LIKE 'Interest_Fitness%' THEN UNNEST(['Gym_Goers', 'Runners', 'Yoga'])
            WHEN campaign_name LIKE 'Interest_Tech%' THEN UNNEST(['Early_Adopters', 'Gadget_Buyers', 'SaaS_Users'])
            WHEN campaign_name LIKE 'Interest_Fashion%' THEN UNNEST(['Luxury', 'Streetwear', 'Sustainable'])
            WHEN campaign_name LIKE 'Broad%' THEN UNNEST(['Age_18_24', 'Age_25_34', 'Age_35_54'])
            WHEN campaign_name LIKE 'Video%' THEN UNNEST(['Short_Form', 'Long_Form', 'Stories'])
            ELSE UNNEST(['Form_Simple', 'Form_Multi', 'Form_Quiz'])
        END AS audience_segment
    FROM campaigns
),
base AS (
    SELECT
        d.day AS date,
        a.campaign_name,
        a.audience_segment,
        hash(d.day::VARCHAR || a.campaign_name || a.audience_segment) AS seed
    FROM date_range d
    CROSS JOIN audiences a
)
SELECT
    date,
    campaign_name,
    audience_segment,

    CASE
        WHEN campaign_name LIKE 'Retargeting%' THEN 'Retargeting'
        WHEN campaign_name LIKE 'Lookalike%' THEN 'Lookalike'
        WHEN campaign_name LIKE 'Interest%' THEN 'Interest'
        WHEN campaign_name LIKE 'Broad%' THEN 'Broad'
        WHEN campaign_name LIKE 'Video%' THEN 'Video'
        ELSE 'Lead_Gen'
    END AS campaign_objective,

    CASE (abs(seed) % 4)
        WHEN 0 THEN 'feed'
        WHEN 1 THEN 'stories'
        WHEN 2 THEN 'reels'
        ELSE 'right_column'
    END AS placement,

    -- Reach
    GREATEST(100, (
        CASE
            WHEN campaign_name LIKE 'Retargeting%' THEN 2000
            WHEN campaign_name LIKE 'Lookalike_1%' THEN 5000
            WHEN campaign_name LIKE 'Lookalike_5%' THEN 8000
            WHEN campaign_name LIKE 'Interest%' THEN 6000
            WHEN campaign_name LIKE 'Broad%' THEN 15000
            WHEN campaign_name LIKE 'Video%' THEN 20000
            ELSE 3000
        END
        * (0.7 + (abs(seed % 60)) / 100.0)
        * CASE WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 1.15 ELSE 1.0 END
    )::INT) AS reach,

    -- Impressions (frequency * reach)
    GREATEST(100, (
        CASE
            WHEN campaign_name LIKE 'Retargeting%' THEN 2000 * 3.5  -- high frequency
            WHEN campaign_name LIKE 'Lookalike_1%' THEN 5000 * 1.8
            WHEN campaign_name LIKE 'Broad%' THEN 15000 * 1.2
            ELSE 5000 * 1.5
        END
        * (0.7 + (abs(seed % 60)) / 100.0)
    )::INT) AS impressions,

    -- CPM (cost per 1000 impressions)
    ROUND(CASE
        WHEN campaign_name LIKE 'Retargeting%' THEN 12.0 + (abs(seed % 80)) / 10.0
        WHEN campaign_name LIKE 'Lookalike_1%' THEN 15.0 + (abs(seed % 100)) / 10.0
        WHEN campaign_name LIKE 'Lookalike_5%' THEN 10.0 + (abs(seed % 60)) / 10.0
        WHEN campaign_name LIKE 'Interest%' THEN 8.0 + (abs(seed % 50)) / 10.0
        WHEN campaign_name LIKE 'Broad%' THEN 5.0 + (abs(seed % 40)) / 10.0
        WHEN campaign_name LIKE 'Video%' THEN 6.0 + (abs(seed % 30)) / 10.0
        ELSE 9.0 + (abs(seed % 50)) / 10.0
    END, 2) AS cpm,

    -- Link CTR
    ROUND(CASE
        WHEN campaign_name LIKE 'Retargeting%' THEN 0.035 + (abs(seed % 20)) / 1000.0
        WHEN campaign_name LIKE 'Lookalike_1%' THEN 0.02 + (abs(seed % 15)) / 1000.0
        WHEN campaign_name LIKE 'Lookalike_5%' THEN 0.015 + (abs(seed % 10)) / 1000.0
        -- Interest_Fashion DECLINES after 2025-10 (audience to cut)
        WHEN campaign_name = 'Interest_Fashion' AND date >= DATE '2025-10-01'
            THEN 0.008 - (EXTRACT(MONTH FROM date) - 9) * 0.001
        WHEN campaign_name LIKE 'Interest%' THEN 0.018 + (abs(seed % 12)) / 1000.0
        WHEN campaign_name LIKE 'Broad%' THEN 0.01 + (abs(seed % 8)) / 1000.0
        WHEN campaign_name LIKE 'Video%' THEN 0.008 + (abs(seed % 5)) / 1000.0
        ELSE 0.012 + (abs(seed % 8)) / 1000.0
    END, 4) AS link_ctr,

    -- Purchase conversion rate
    ROUND(CASE
        WHEN campaign_name LIKE 'Retargeting%' THEN 0.045 + (abs(seed % 20)) / 1000.0
        -- LA1_HighLTV is the SCALE winner (high conv rate, good LTV)
        WHEN audience_segment = 'LA1_HighLTV' THEN 0.035 + (abs(seed % 15)) / 1000.0
        WHEN campaign_name LIKE 'Lookalike_1%' THEN 0.025 + (abs(seed % 12)) / 1000.0
        WHEN campaign_name LIKE 'Lookalike_5%' THEN 0.015 + (abs(seed % 8)) / 1000.0
        WHEN campaign_name LIKE 'Interest%' THEN 0.012 + (abs(seed % 8)) / 1000.0
        -- Broad_CBO Age_18_24 has LOW conversion but HIGH volume (segment to cut)
        WHEN audience_segment = 'Age_18_24' THEN 0.003 + (abs(seed % 3)) / 1000.0
        WHEN campaign_name LIKE 'Broad%' THEN 0.008 + (abs(seed % 5)) / 1000.0
        WHEN campaign_name LIKE 'Video%' THEN 0.002 + (abs(seed % 2)) / 1000.0
        ELSE 0.01 + (abs(seed % 5)) / 1000.0
    END, 4) AS purchase_conv_rate,

    -- Average order value
    ROUND(CASE
        -- LA1_HighLTV has highest AOV (scale signal)
        WHEN audience_segment = 'LA1_HighLTV' THEN 120.0 + (abs(seed % 80))
        WHEN campaign_name LIKE 'Retargeting%' THEN 95.0 + (abs(seed % 60))
        WHEN campaign_name LIKE 'Lookalike_1%' THEN 85.0 + (abs(seed % 50))
        WHEN campaign_name LIKE 'Lookalike_5%' THEN 70.0 + (abs(seed % 40))
        WHEN campaign_name LIKE 'Interest%' THEN 60.0 + (abs(seed % 35))
        -- Age_18_24 has lowest AOV (cut signal)
        WHEN audience_segment = 'Age_18_24' THEN 25.0 + (abs(seed % 15))
        WHEN campaign_name LIKE 'Broad%' THEN 55.0 + (abs(seed % 30))
        ELSE 50.0 + (abs(seed % 30))
    END, 2) AS avg_order_value,

    -- 30-day repeat purchase rate (proxy for LTV)
    ROUND(CASE
        WHEN audience_segment = 'LA1_HighLTV' THEN 0.35 + (abs(seed % 15)) / 100.0
        WHEN campaign_name LIKE 'Retargeting%' AND audience_segment = 'Past_Purchase'
            THEN 0.40 + (abs(seed % 20)) / 100.0
        WHEN campaign_name LIKE 'Retargeting%' THEN 0.25 + (abs(seed % 15)) / 100.0
        WHEN campaign_name LIKE 'Lookalike_1%' THEN 0.20 + (abs(seed % 12)) / 100.0
        WHEN campaign_name LIKE 'Lookalike_5%' THEN 0.12 + (abs(seed % 8)) / 100.0
        WHEN audience_segment = 'Age_18_24' THEN 0.05 + (abs(seed % 5)) / 100.0
        WHEN campaign_name LIKE 'Interest%' THEN 0.10 + (abs(seed % 8)) / 100.0
        ELSE 0.08 + (abs(seed % 6)) / 100.0
    END, 2) AS repeat_purchase_rate_30d,

    -- Pixel attribution confidence (data quality signal)
    CASE
        WHEN campaign_name LIKE 'Retargeting%' THEN 'high'
        WHEN campaign_name LIKE 'Lookalike_1%' THEN 'high'
        WHEN campaign_name LIKE 'Lookalike_5%' THEN 'medium'
        WHEN campaign_name LIKE 'Interest%' THEN 'medium'
        WHEN campaign_name LIKE 'Broad%' THEN 'low'
        WHEN campaign_name LIKE 'Video%' THEN 'low'
        ELSE 'medium'
    END AS pixel_confidence,

    -- Some nulls for realism (5% of rows missing placement data)
    CASE WHEN abs(seed % 20) = 0 THEN NULL ELSE
        CASE (abs(seed) % 3)
            WHEN 0 THEN 'single_image'
            WHEN 1 THEN 'carousel'
            ELSE 'video'
        END
    END AS creative_type

FROM base
ORDER BY date, campaign_name, audience_segment
""")

# Compute final metrics
con.execute("""
CREATE TABLE fb_ads_final AS
SELECT
    date,
    campaign_name,
    audience_segment,
    campaign_objective,
    placement,
    creative_type,
    reach,
    impressions,
    ROUND(impressions::FLOAT / GREATEST(1, reach), 2) AS frequency,
    cpm,
    ROUND(impressions * cpm / 1000.0, 2) AS spend,
    link_ctr,
    GREATEST(0, (impressions * link_ctr)::INT) AS link_clicks,
    CASE WHEN GREATEST(0, (impressions * link_ctr)::INT) > 0
        THEN ROUND(impressions * cpm / 1000.0 / GREATEST(1, (impressions * link_ctr)::INT), 2)
        ELSE NULL
    END AS cpc,
    purchase_conv_rate,
    GREATEST(0, (GREATEST(0, (impressions * link_ctr)::INT) * purchase_conv_rate)::INT) AS purchases,
    avg_order_value,
    ROUND(GREATEST(0, (GREATEST(0, (impressions * link_ctr)::INT) * purchase_conv_rate)::INT) * avg_order_value, 2) AS revenue,
    CASE WHEN GREATEST(0, (GREATEST(0, (impressions * link_ctr)::INT) * purchase_conv_rate)::INT) > 0
        THEN ROUND(impressions * cpm / 1000.0 / GREATEST(1, (GREATEST(0, (impressions * link_ctr)::INT) * purchase_conv_rate)::INT), 2)
        ELSE NULL
    END AS cost_per_purchase,
    CASE WHEN impressions * cpm / 1000.0 > 0
        THEN ROUND(GREATEST(0, (GREATEST(0, (impressions * link_ctr)::INT) * purchase_conv_rate)::INT) * avg_order_value / (impressions * cpm / 1000.0), 2)
        ELSE NULL
    END AS roas,
    repeat_purchase_rate_30d,
    pixel_confidence
FROM fb_ads
""")

con.execute("COPY fb_ads_final TO 'autoresearch/datasets/facebook-ads/data.csv' (HEADER, DELIMITER ',')")

row_count = con.execute("SELECT COUNT(*) FROM fb_ads_final").fetchone()[0]
cols = con.execute("SELECT column_name FROM information_schema.columns WHERE table_name='fb_ads_final'").fetchall()
print(f"Generated {row_count} rows, {len(cols)} columns")
print("Columns:", [c[0] for c in cols])

# Verify embedded patterns
print("\n--- Embedded Pattern Verification ---")
print("\nBest segments to SCALE (ROAS + repeat rate):")
con.execute("""
    SELECT audience_segment,
           ROUND(AVG(roas), 2) AS avg_roas,
           ROUND(AVG(repeat_purchase_rate_30d), 2) AS avg_repeat,
           ROUND(AVG(cost_per_purchase), 2) AS avg_cpp
    FROM fb_ads_final
    WHERE roas IS NOT NULL
    GROUP BY 1
    ORDER BY avg_roas DESC
    LIMIT 10
""").show()

print("\nSegments to CUT (low ROAS, low repeat):")
con.execute("""
    SELECT audience_segment,
           ROUND(AVG(roas), 2) AS avg_roas,
           ROUND(AVG(repeat_purchase_rate_30d), 2) AS avg_repeat,
           ROUND(AVG(cost_per_purchase), 2) AS avg_cpp
    FROM fb_ads_final
    WHERE roas IS NOT NULL
    GROUP BY 1
    ORDER BY avg_roas ASC
    LIMIT 5
""").show()

print("\nInterest_Fashion CTR decay:")
con.execute("""
    SELECT date_trunc('quarter', date) AS quarter,
           ROUND(AVG(link_ctr), 4) AS avg_ctr
    FROM fb_ads_final
    WHERE campaign_name = 'Interest_Fashion'
    GROUP BY 1 ORDER BY 1
""").show()
```

- [ ] **Step 2: Run the generator**

```bash
cd /Users/williamhung/Projects/cc-plugins/data-analysis && python3 autoresearch/datasets/facebook-ads/generate.py
```

Expected: prints row count (~12K+), columns, and verification tables showing LA1_HighLTV as scale winner and Age_18_24 as cut candidate.

- [ ] **Step 3: Commit dataset**

```bash
git add autoresearch/datasets/facebook-ads/
git commit -m "feat: add synthetic Facebook Ads dataset with segment scale/cut patterns"
```

---

### Task 4: Write Ads Playbooks

**Files:**
- Create: `autoresearch/datasets/google-ads/playbook.md`
- Create: `autoresearch/datasets/facebook-ads/playbook.md`

- [ ] **Step 1: Write Google Ads playbook**

Write to `autoresearch/datasets/google-ads/playbook.md`:

```markdown
---
name: google-ads-performance
domain: digital-advertising
description: Google Ads campaign performance analysis across Search, Display, Video, Shopping, and Performance Max campaigns
---

## Context

- `date`: daily granularity, UTC
- `campaign_name`: 8 campaigns (Brand_Search, Generic_Search, Competitor_Search, Display_Retarget, Display_Prospecting, Video_Awareness, Shopping_Feed, Performance_Max)
- `ad_group_name`: 3 ad groups per campaign (24 total)
- `campaign_type`: derived — Search, Display, Video, Shopping, PMax
- `device`: mobile, desktop, tablet
- `impressions`: ad views
- `ctr`: click-through rate (clicks / impressions)
- `clicks`: derived from impressions * ctr
- `cpc`: cost per click in USD
- `cost`: total spend (clicks * cpc)
- `conversion_rate`: purchases / clicks
- `conversions`: purchase count
- `avg_conversion_value`: revenue per conversion in USD
- `conversion_value`: total revenue (conversions * avg_conversion_value)
- `cpa`: cost per acquisition (cost / conversions)
- `roas`: return on ad spend (conversion_value / cost)
- `quality_score`: 1-10, Google's relevance metric (Search/Shopping only, NULL for others)
- `bounce_rate`: landing page bounce rate
- `ad_format`: text_ad, image_ad, video_ad, product_listing, responsive_ad (5% NULL)

Data source: Google Ads API daily export, one row per campaign × ad_group × device × day.

## Expected Patterns

- Brand_Search: highest CTR (6-10%), lowest CPC ($0.50-1.00), highest conversion rate (~6%)
- Generic_Search: moderate CTR (3-5%), higher CPC ($1.50-2.50), moderate conversion rate (2-3%)
- Competitor_Search: lower CTR (2-4%), highest CPC ($2.50-4.00), lower conversion rate
- Display_Retarget: high conversion rate (~8%) but lower CTR than Search
- Display_Prospecting: high impressions, low CTR (<1.5%), low conversion rate (<1%)
- Video_Awareness: very high impressions, very low CTR (<1%), minimal conversions
- Shopping_Feed: moderate performance across metrics
- Weekend dip: 30% impression reduction on Sat/Sun
- Q4 holiday surge: 1.5-2x volume in Nov-Dec
- quality_score NULL for Display/Video/PMax campaigns (expected)

## Key Metrics

- **CPA target**: < $40 for Search, < $25 for Retargeting, < $60 for Prospecting
- **ROAS target**: > 3.0 for Search, > 5.0 for Retargeting, > 1.5 for Prospecting
- **CTR benchmark**: > 5% Brand, > 3% Generic, > 2% Shopping
- **Bounce rate healthy**: < 40% Brand, < 50% Generic, < 70% Prospecting
- **Blended CPA**: Should stay under $35 month-over-month
- **Quality Score**: > 6 is healthy, < 4 needs attention

## Steps

1. Check data freshness and completeness — any gaps in dates? NULL patterns?
2. Compute blended CPA trend month-over-month — is it increasing?
3. Break down CPA change by campaign_type — which campaigns drive the increase?
4. For problematic campaigns: decompose CPA = CPC / conversion_rate — is it a CPC problem (auction pressure) or conversion problem (landing page/creative)?
5. Check CTR trends — is audience fatigue (declining CTR over time) a factor?
6. Segment by device — any device-specific performance shifts?
7. Compare quality_scores over time — declining quality affects CPC
8. Recommend: bid adjustments, budget reallocation, creative refresh, audience exclusions
```

- [ ] **Step 2: Write Facebook Ads playbook**

Write to `autoresearch/datasets/facebook-ads/playbook.md`:

```markdown
---
name: facebook-ads-performance
domain: digital-advertising
description: Meta/Facebook Ads performance analysis with audience segmentation, ROAS optimization, and LTV-aware budget allocation
---

## Context

- `date`: daily granularity, UTC
- `campaign_name`: 9 campaigns across Retargeting, Lookalike, Interest, Broad, Video, Lead_Gen
- `audience_segment`: 3 segments per campaign (27 total) — these are the key analysis dimension
- `campaign_objective`: derived — Retargeting, Lookalike, Interest, Broad, Video, Lead_Gen
- `placement`: feed, stories, reels, right_column
- `creative_type`: single_image, carousel, video (5% NULL — tracking gaps)
- `reach`: unique users shown the ad
- `impressions`: total ad views (reach × frequency)
- `frequency`: avg impressions per user (high frequency = potential fatigue)
- `cpm`: cost per 1000 impressions in USD
- `spend`: total cost
- `link_ctr`: click-through rate on link clicks
- `link_clicks`: outbound clicks
- `cpc`: cost per link click
- `purchase_conv_rate`: purchases / link_clicks
- `purchases`: purchase events
- `avg_order_value`: revenue per purchase in USD
- `revenue`: total revenue (purchases × avg_order_value)
- `cost_per_purchase`: CPA (spend / purchases)
- `roas`: return on ad spend (revenue / spend)
- `repeat_purchase_rate_30d`: % of purchasers who buy again within 30 days (LTV proxy)
- `pixel_confidence`: high/medium/low — Meta pixel attribution reliability

Data source: Meta Ads API daily export, one row per campaign × audience_segment × day.

## Expected Patterns

- Retargeting: highest conversion rates (4-6%), highest frequency (3-4x), highest CPM ($12-20)
- Lookalike_1pct: best balance of scale + quality — especially LA1_HighLTV segment
- Lookalike_5pct: more reach, lower quality than 1%
- Interest campaigns: moderate performance, watch for CTR decay (audience exhaustion)
- Broad_CBO: high reach, low efficiency — Age_18_24 particularly weak (low AOV, low repeat)
- Video: awareness-focused, low direct conversions
- Weekend boost: ~15% higher reach on Sat/Sun (opposite of B2B/Search)
- pixel_confidence = 'low' on Broad/Video campaigns — conversions likely undercounted
- creative_type NULL for ~5% of rows — Meta tracking gaps, not errors
- Frequency > 4 on Retargeting is a fatigue signal

## Key Metrics

- **ROAS target**: > 4.0 for Retargeting, > 3.0 for Lookalike_1pct, > 1.5 for Interest, > 1.0 for Broad
- **Cost per purchase**: < $20 Retargeting, < $30 Lookalike, < $50 Interest, < $60 Broad
- **Repeat purchase rate**: > 25% is strong LTV signal, < 10% suggests one-time buyers
- **Frequency cap warning**: > 4.0 for any segment — creative fatigue likely
- **Link CTR benchmark**: > 2% Retargeting, > 1.5% Lookalike, > 1% Interest
- **Pixel confidence impact**: low-confidence segments may have 20-40% more conversions than reported

## Steps

1. Check pixel_confidence distribution — how much data has low attribution confidence?
2. Compute ROAS by audience_segment — which segments are profitable?
3. Layer in repeat_purchase_rate_30d — a segment with mediocre ROAS but high repeat rate has hidden LTV
4. Identify SCALE segments: high ROAS + high repeat rate + not yet saturated (frequency < 3)
5. Identify CUT segments: low ROAS + low repeat rate + high spend
6. Check for audience fatigue: CTR trend over time per segment — declining CTR = time to refresh creative
7. Account for pixel_confidence: adjust low-confidence segment performance upward by 20-30% before making cut decisions
8. Recommend: budget shifts, audience exclusions, creative refresh schedule, LTV-adjusted bidding
```

- [ ] **Step 3: Commit playbooks**

```bash
git add autoresearch/datasets/
git commit -m "feat: add Google and Facebook Ads playbooks for eval scenarios"
```

---

### Task 5: Write 12 Scorer Agent Files

**Files:**
- Create: `autoresearch/agents/scorer/direction-quality.md`
- Create: `autoresearch/agents/scorer/insight-novelty.md`
- Create: `autoresearch/agents/scorer/query-efficiency.md`
- Create: `autoresearch/agents/scorer/context-boundary.md`
- Create: `autoresearch/agents/scorer/uncertainty.md`
- Create: `autoresearch/agents/scorer/data-quality.md`
- Create: `autoresearch/agents/scorer/segmentation.md`
- Create: `autoresearch/agents/scorer/actionability.md`
- Create: `autoresearch/agents/scorer/followup.md`
- Create: `autoresearch/agents/scorer/simplicity.md`
- Create: `autoresearch/agents/scorer/narrative.md`
- Create: `autoresearch/agents/scorer/success-metrics.md`

Each scorer agent follows the same structure. All 12 are defined below with their specific evaluation criteria.

- [ ] **Step 1: Write direction-quality.md**

Write to `autoresearch/agents/scorer/direction-quality.md`:

```markdown
# Direction Quality Scorer

You are an eval agent. Score SKILL.md on whether it guides analysis toward clear business questions and causal reasoning.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided (Google or Facebook)

## Scoring Rubric (0-3)

- **3**: Skill explicitly instructs framing analysis around a business decision. Wizard asks what decision depends on the analysis. Blue Hat distinguishes "what correlates" from "what causes." Playbook context drives causal hypotheses.
- **2**: Wizard asks for user questions and Blue Hat proposes techniques, but no explicit causal framing or decision-anchoring step.
- **1**: Wizard collects questions but analysis proceeds as descriptive profiling without connecting to decisions or causation.
- **0**: No mechanism to establish analysis direction or connect to business questions.

## Evaluation Checklist

Scan SKILL.md for:
- [ ] Phase 0 (Wizard): Does it ask what DECISION the analysis will inform? (not just "what questions do you have")
- [ ] Phase 1 (Blue Hat): Does it instruct distinguishing correlation from causation?
- [ ] Phase 1 (Blue Hat): Does it propose hypothesis-driven analysis (e.g., "test whether X causes Y") vs descriptive only?
- [ ] Any phase: Does it reference the playbook's business context to generate causal hypotheses?
- [ ] Summary: Does it connect findings back to the original business question/decision?

## Sample Validation

Using the Google Ads dataset with scenario "Our CPA doubled last month":
- Would the skill's instructions lead to asking WHY CPA doubled (causal) or just SHOWING that CPA doubled (descriptive)?
- Would it decompose CPA = CPC / conversion_rate to isolate the causal factor?
- Would it test channel mix vs audience fatigue vs creative decay as competing hypotheses?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "direction-quality",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 2: Write insight-novelty.md**

Write to `autoresearch/agents/scorer/insight-novelty.md`:

```markdown
# Insight Novelty Scorer

You are an eval agent. Score SKILL.md on whether it guides analysis toward discovering NEW and non-obvious insights.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill explicitly instructs looking beyond obvious patterns. Green Hat proposes contrarian hypotheses. Yellow Hat cross-references unexpected dimensions. Has specific instructions for "what would surprise the user?"
- **2**: Green Hat suggests alternative perspectives but without structured novelty-seeking. Yellow Hat interprets findings but doesn't push beyond the obvious.
- **1**: Analysis follows a standard profiling template. Green Hat exists but is generic ("what else could we look at?").
- **0**: No mechanism for discovering non-obvious insights.

## Evaluation Checklist

- [ ] Green Hat: Does it instruct proposing hypotheses that CONTRADICT Yellow Hat findings?
- [ ] Yellow Hat: Does it instruct cross-referencing unexpected dimension combinations?
- [ ] Any phase: Does it instruct looking at the data from the perspective of different stakeholders?
- [ ] Any phase: Does it instruct computing derived metrics not in the raw data?
- [ ] Any phase: Does it instruct comparing segments that "shouldn't" differ to find surprising differences?

## Sample Validation

Using Facebook Ads dataset:
- Would the skill discover that LA1_HighLTV has hidden value via repeat_purchase_rate (not obvious from ROAS alone)?
- Would it suggest looking at LTV-adjusted ROAS vs raw ROAS?
- Would it notice that low pixel_confidence segments might be UNDERVALUED?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "insight-novelty",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 3: Write query-efficiency.md**

Write to `autoresearch/agents/scorer/query-efficiency.md`:

```markdown
# Query Efficiency Scorer

You are an eval agent. Score SKILL.md on whether it guides efficient DuckDB query patterns.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill shows query patterns that avoid redundant full-table scans. Uses CTEs or temp tables for reuse. Instructs sampling strategy by data size. Shows indexing/partitioning hints for large data. Limits result sets explicitly.
- **2**: Skill shows basic query patterns and sampling strategy but doesn't address query reuse or redundant scans.
- **1**: Skill shows SQL examples but no efficiency guidance. Multiple phases may re-scan the same data unnecessarily.
- **0**: No query patterns shown or efficiency considerations.

## Evaluation Checklist

- [ ] Does it instruct creating a profiling summary table once and reusing it across phases?
- [ ] Does it show sampling strategy with explicit thresholds (100K, 1M)?
- [ ] Does it instruct LIMIT clauses on exploratory queries?
- [ ] Does it avoid SELECT * patterns?
- [ ] Does it instruct using CTEs or temp tables for intermediate results shared across analyses?
- [ ] Does it instruct batching related queries rather than running them one-at-a-time?

## Sample Validation

For Google Ads dataset (~10K rows):
- Would the skill run SUMMARIZE once and reuse, or re-profile in multiple phases?
- Would the Group BY queries in Yellow Hat use appropriate limits?
- Are correlation computations done efficiently (not N² separate queries)?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "query-efficiency",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 4: Write context-boundary.md**

Write to `autoresearch/agents/scorer/context-boundary.md`:

```markdown
# Context Boundary Scorer

You are an eval agent. Score SKILL.md on whether analysis phases have clear responsibilities and boundaries.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Each hat phase has a single clear purpose. No phase leaks into another's responsibility. Playbook context is loaded once and referenced consistently. Phase handoffs are explicit with defined inputs/outputs. Could split each phase into an independent agent.
- **2**: Phases have defined purposes but some overlap (e.g., Black Hat does interpretation that belongs in Yellow Hat). Handoffs exist but aren't structured.
- **1**: Phases are named but responsibilities blur. One phase does work another should handle.
- **0**: No clear phase separation or everything happens in one monolithic step.

## Evaluation Checklist

- [ ] Each phase has a stated "Purpose" line
- [ ] White Hat contains ZERO interpretation (pure facts)
- [ ] Red Hat is deliberately brief (gut reaction only, not analysis)
- [ ] Black Hat focuses on data quality, not business insights
- [ ] Yellow Hat is the ONLY phase that runs analytical queries for findings
- [ ] Green Hat doesn't repeat Yellow Hat — it suggests NEW angles
- [ ] Playbook context is loaded in Phase 0 and referenced by name in later phases
- [ ] Each phase's output format is defined (not freeform)

## Sample Validation

Using the Six Hats framework with ads data:
- Would a data engineer (White Hat) and business analyst (Yellow Hat) produce different outputs, or would they overlap?
- Is there a clear handoff: White Hat profile → Black Hat quality check → Yellow Hat analysis?
- Could you assign each phase to a different specialist?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "context-boundary",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 5: Write uncertainty.md**

Write to `autoresearch/agents/scorer/uncertainty.md`:

```markdown
# Uncertainty Quantification Scorer

You are an eval agent. Score SKILL.md on whether it instructs quantifying confidence and stating data limitations.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill explicitly instructs stating confidence levels for each finding. Distinguishes statistically significant differences from noise. Instructs computing confidence intervals or effect sizes. ASSUME tags include hedging language ("likely," "suggests," "insufficient data to conclude"). Instructs noting sample size behind each metric.
- **2**: FACT/ASSUME separation implicitly captures some uncertainty. Black Hat mentions data limitations. But no explicit confidence quantification or statistical significance testing.
- **1**: ASSUME tags exist but no instruction to quantify confidence or note when data is insufficient.
- **0**: No uncertainty quantification. Findings stated as certainties.

## Evaluation Checklist

- [ ] Does it instruct computing sample sizes behind findings?
- [ ] Does it instruct distinguishing "statistically significant" from "directionally suggestive"?
- [ ] Does it instruct noting when a finding is based on small N?
- [ ] Does it instruct confidence intervals or margin of error for key metrics?
- [ ] Does ASSUME language instruct hedging ("likely," "suggests") vs certainty?
- [ ] Does it instruct noting what the data CANNOT tell you?
- [ ] Does Black Hat flag when sample is too small for reliable conclusions?

## Sample Validation

Using Google Ads dataset:
- If CPA doubled based on 15 conversions in a small ad group, would the skill flag the small sample?
- Would it distinguish "CPA increased significantly (p<0.05)" from "CPA appears higher but based on limited data"?
- For the pixel_confidence = 'low' segments in Facebook data, would it quantify the uncertainty?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "uncertainty",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 6: Write data-quality.md**

Write to `autoresearch/agents/scorer/data-quality.md`:

```markdown
# Data Quality & Limitations Scorer

You are an eval agent. Score SKILL.md on how thoroughly it addresses data quality issues and their impact on conclusions.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Dedicated quality phase (Black Hat) checks nulls, duplicates, outliers with specific DuckDB queries. Instructs checking data freshness/completeness. Links quality issues to specific analytical risks ("30% null in channel means channel analysis unreliable"). Instructs playbook validation of expected vs actual patterns. Instructs re-checking quality after filtering/transformations.
- **2**: Black Hat checks nulls, duplicates, outliers but doesn't connect quality issues to analytical risks. Playbook validation exists but is surface-level.
- **1**: Quality mentioned but no specific checks or queries shown.
- **0**: No data quality assessment.

## Evaluation Checklist

- [ ] Black Hat: specific DuckDB queries for null rates, duplicates, outliers (IQR method)
- [ ] Black Hat: checks data freshness (date gaps)
- [ ] Black Hat: connects each quality issue to its analytical impact
- [ ] Black Hat: playbook consistency check (expected vs actual column values/ranges)
- [ ] Any phase: instructs noting when a conclusion is affected by data quality
- [ ] Any phase: instructs handling strategy for each quality issue (drop, impute, flag)
- [ ] Summary: includes data quality caveats for key findings

## Sample Validation

Using Facebook Ads dataset:
- Would it flag pixel_confidence = 'low' as affecting conversion counts?
- Would it flag 5% NULL creative_type and assess impact?
- Would it check that audience_segment values match playbook expectations?
- Would it note that repeat_purchase_rate_30d is a 30-day window (recency bias)?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "data-quality",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 7: Write segmentation.md**

Write to `autoresearch/agents/scorer/segmentation.md`:

```markdown
# Meaningful Segmentation Scorer

You are an eval agent. Score SKILL.md on whether it instructs meaningful grouping rather than just averaging.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill explicitly warns against global averages. Instructs GROUP BY analysis as default. Shows multi-dimensional segmentation (e.g., campaign × device × time). Instructs looking for Simpson's paradox. Instructs identifying which segments drive aggregate changes. Playbook defines meaningful segments.
- **2**: Group comparison technique listed and used in Yellow Hat. But no explicit warning about averaging or multi-dimensional analysis.
- **1**: GROUP BY queries shown but segmentation is single-dimensional only.
- **0**: Analysis operates on aggregates with no segmentation.

## Evaluation Checklist

- [ ] Blue Hat: lists Group Comparison as a technique with clear "when to use"
- [ ] Yellow Hat: shows GROUP BY queries with multiple dimensions
- [ ] Any phase: warns against interpreting global averages without segmentation
- [ ] Any phase: instructs decomposing aggregate changes into segment contributions
- [ ] Any phase: instructs checking if a trend holds across all segments (Simpson's paradox check)
- [ ] Playbook: defines meaningful business segments to analyze

## Sample Validation

Using Google Ads dataset:
- Would it segment CPA increase by campaign_type to find which campaigns drive it?
- Would it further segment by device within problematic campaigns?
- Would it check if CPA increase is uniform or driven by 1-2 segments?

Using Facebook Ads dataset:
- Would it segment by audience_segment (not just campaign_name)?
- Would it identify that Age_18_24 drags down Broad_CBO performance?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "segmentation",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 8: Write actionability.md**

Write to `autoresearch/agents/scorer/actionability.md`:

```markdown
# Actionable Recommendations Scorer

You are an eval agent. Score SKILL.md on whether it produces specific, implementable recommendations.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill instructs SUGGEST tags with specific actions (exact budget shifts, bid changes, segments to exclude). Recommendations include expected impact, effort estimate, and priority. Yellow Hat and Summary both produce actionable outputs. Playbook's Steps section drives specific recommendations.
- **2**: SUGGEST tags used in Black Hat. Summary includes recommendations but they're generic ("consider optimizing X").
- **1**: Findings presented but no explicit recommendation mechanism.
- **0**: No actionable output — purely descriptive.

## Evaluation Checklist

- [ ] SUGGEST tags used with specific actions (not just "consider X")
- [ ] Recommendations include: what to do, where to do it, expected impact
- [ ] Yellow Hat findings each have an associated action
- [ ] Summary includes prioritized action items
- [ ] Recommendations reference specific data (e.g., "shift 20% of Broad budget to Lookalike_1pct based on 3x ROAS difference")
- [ ] Playbook Steps section drives domain-specific recommendations

## Sample Validation

Using Google Ads dataset with CPA doubling scenario:
- Would it recommend specific bid adjustments for the campaigns driving CPA increase?
- Would it suggest budget reallocation with specific percentages?
- Would it recommend creative refresh for campaigns with CTR decay?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "actionability",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 9: Write followup.md**

Write to `autoresearch/agents/scorer/followup.md`:

```markdown
# Follow-up Anticipation Scorer

You are an eval agent. Score SKILL.md on whether it anticipates and surfaces follow-up questions.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Each phase explicitly asks the user what to explore next. Green Hat proposes specific unexplored angles. Summary lists open questions. Skill instructs noting "what would we need to confirm this?" for each assumption. Instructs proactive drill-down suggestions.
- **2**: Phases pause for user input. Green Hat suggests alternatives. But no structured follow-up question generation.
- **1**: Phases pause but prompts are generic ("anything else?").
- **0**: No follow-up mechanism — analysis is a one-shot report.

## Evaluation Checklist

- [ ] Each phase ends with a specific question (not generic "anything else?")
- [ ] Green Hat proposes specific alternative analyses with rationale
- [ ] Summary includes "Open questions" section
- [ ] Yellow Hat suggests drill-down paths for interesting findings
- [ ] Any phase: instructs noting what additional data would strengthen a conclusion
- [ ] Wizard: handles "explore" mode with progressive question generation

## Sample Validation

Using Facebook Ads dataset:
- After identifying LA1_HighLTV as a scale segment, would it suggest: "What's the creative performing best in this segment?"
- After finding Age_18_24 underperforms, would it ask: "Is this segment important for brand awareness even if ROAS is low?"
- Would it suggest joining with CRM data to validate repeat_purchase_rate?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "followup",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 10: Write simplicity.md**

Write to `autoresearch/agents/scorer/simplicity.md`:

```markdown
# Simplicity Scorer

You are an eval agent. Score SKILL.md on whether it favors the simplest appropriate analytical method.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill explicitly prioritizes simple methods first (counts, averages, distributions) before complex ones. Technique selection in Blue Hat is data-shape-driven, not methodology-driven. No unnecessary statistical machinery. DuckDB queries use straightforward SQL. Complexity justified only when simple methods are insufficient.
- **2**: Techniques are appropriate but no explicit simplicity principle. Some queries could be simpler.
- **1**: Over-engineered analytical approaches for data that doesn't warrant them.
- **0**: Uses complex methods where simple ones suffice, or methods are inappropriate for data shape.

## Evaluation Checklist

- [ ] Blue Hat: technique selection starts simple and escalates only if needed
- [ ] Yellow Hat: query patterns use standard SQL (GROUP BY, aggregates) before advanced features
- [ ] Anomaly detection: uses IQR (simple) rather than complex ML methods
- [ ] Correlation: uses straightforward pairwise computation, not overcomplicated approaches
- [ ] No unnecessary statistical tests for exploratory analysis
- [ ] Sampling strategy is simple and threshold-based (not adaptive/complex)

## Sample Validation

For ads data analysis:
- Would it start with "CPA by month" (simple) before "multivariate regression of CPA drivers" (complex)?
- Would trend analysis use date_trunc + GROUP BY (simple) rather than time series decomposition?
- Would segmentation use GROUP BY (simple) rather than clustering algorithms?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "simplicity",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 11: Write narrative.md**

Write to `autoresearch/agents/scorer/narrative.md`:

```markdown
# Coherent Narrative Scorer

You are an eval agent. Score SKILL.md on whether it produces a coherent story from data to insight to action.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Six Hats phases build on each other in a clear narrative arc: Plan → Facts → Impression → Quality check → Findings → Creative angles → Summary. Each phase references previous phases' outputs. Summary weaves findings into a coherent story. FACT/ASSUME flow creates a natural "here's what we see → here's what it means" rhythm.
- **2**: Phases follow a logical order. Summary exists. But phases don't explicitly reference each other's outputs. Narrative is implicit rather than structured.
- **1**: Phases are sequential but feel disconnected. Summary is a list, not a narrative.
- **0**: No narrative structure. Analysis is a collection of unrelated observations.

## Evaluation Checklist

- [ ] Blue Hat references user's questions and sets up the narrative
- [ ] Red Hat's gut reaction is revisited in Summary (was initial impression confirmed or overturned?)
- [ ] Black Hat quality issues are referenced in Yellow Hat when they affect findings
- [ ] Yellow Hat findings build on White Hat profile (not repeating profiling)
- [ ] Green Hat references Yellow Hat findings to propose contrarian angles
- [ ] Summary connects back to original questions with a clear answer arc
- [ ] FACT/ASSUME rhythm creates a readable flow

## Sample Validation

Using Google Ads CPA doubling scenario:
- Would the narrative arc be: "CPA doubled → let's profile the data → initial read suggests Search campaigns → quality looks OK → decomposition shows CPC increase + conversion drop in Generic/Competitor → CTR decay suggests audience fatigue → recommendation: refresh creatives, reallocate budget"?
- Or would it be: "Here are some stats. Here are some more stats. Here's a summary."?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "narrative",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 12: Write success-metrics.md**

Write to `autoresearch/agents/scorer/success-metrics.md`:

```markdown
# Success Metrics Definition Scorer

You are an eval agent. Score SKILL.md on whether it instructs defining and validating success metrics BEFORE measuring them.

## Inputs

1. Read: `skills/data-analysis/SKILL.md`
2. Read: the ads playbook provided

## Scoring Rubric (0-3)

- **3**: Skill instructs defining what "good" looks like before running analysis. Blue Hat or Wizard establishes success criteria. Playbook Key Metrics section defines thresholds. Analysis compares findings against pre-defined benchmarks. Instructs validating that chosen metrics actually measure what they claim (metric validity).
- **2**: Playbook Key Metrics exist and are referenced. But no explicit "define before measure" instruction in the skill itself.
- **1**: Metrics are computed but compared to nothing — no benchmarks or success criteria.
- **0**: No success metric definition. Analysis presents numbers without context for what good/bad means.

## Evaluation Checklist

- [ ] Blue Hat or Wizard: instructs establishing success criteria before analysis
- [ ] Playbook: Key Metrics section with specific thresholds
- [ ] Yellow Hat: compares findings against playbook benchmarks (not just raw numbers)
- [ ] Any phase: instructs asking "what does good look like?" for each metric
- [ ] Any phase: instructs validating that a metric measures what it claims (e.g., ROAS doesn't capture LTV)
- [ ] Summary: evaluates findings against pre-established criteria

## Sample Validation

Using Google Ads playbook:
- Would it reference CPA target < $40 before computing CPA?
- Would it compare actual ROAS against the > 3.0 benchmark?
- Would it flag if a metric definition is misleading (e.g., last-click CPA ignores assist conversions)?

Using Facebook Ads playbook:
- Would it define what "scale" means (ROAS + repeat_rate + headroom) before identifying scale segments?
- Would it question whether ROAS alone is sufficient or if LTV matters?

## Output Format

Return ONLY valid JSON:

```json
{
  "metric": "success-metrics",
  "score": <0-3>,
  "max_score": 3,
  "evidence": ["SKILL.md line N: <quote>", ...],
  "gaps": ["Missing: <specific gap>", ...],
  "recommendation": "<specific edit to make to SKILL.md>"
}
```
```

- [ ] **Step 13: Commit all scorer agents**

```bash
git add autoresearch/agents/scorer/
git commit -m "feat: add 12 scorer agents for autoresearch eval metrics"
```

---

### Task 6: Write Orchestrator Agent

**Files:**
- Create: `autoresearch/agents/orchestrator.md`

- [ ] **Step 1: Write orchestrator.md**

Write to `autoresearch/agents/orchestrator.md`:

```markdown
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
```

- [ ] **Step 2: Commit orchestrator**

```bash
git add autoresearch/agents/orchestrator.md
git commit -m "feat: add orchestrator agent for eval dispatch and aggregation"
```

---

### Task 7: Write Improver Agent

**Files:**
- Create: `autoresearch/agents/improver.md`

- [ ] **Step 1: Write improver.md**

Write to `autoresearch/agents/improver.md`:

```markdown
# SKILL.md Improver

You improve the data-analysis SKILL.md based on eval scorer feedback.

## Process

### Step 1: Read Latest Report

Find the most recent file in `autoresearch/reports/` (sort by filename, take last).
Read it and identify all metrics with score < 3.

### Step 2: Read Current SKILL.md

Read `skills/data-analysis/SKILL.md` completely.

### Step 3: Plan Improvements

For each metric scoring < 3, read its recommendation from the report.
Plan specific edits to SKILL.md that address each gap.

**Rules:**
- Make the MINIMUM change needed to address each gap
- Do NOT remove existing functionality
- Do NOT restructure the Six Hats framework
- Preserve all existing FACT/ASSUME patterns
- Add new instructions at the appropriate phase (e.g., uncertainty guidance goes in Yellow Hat and Summary)
- Keep the skill readable — no walls of text
- Each edit should be independently valuable (if one edit is reverted, others still work)

### Step 4: Apply Edits

Use the Edit tool to make each change to `skills/data-analysis/SKILL.md`.
After each edit, briefly note what was changed and which metric it addresses.

### Step 5: Document Changes

Create a change summary:

```json
{
  "changes": [
    {
      "metric": "<metric name>",
      "previous_score": <N>,
      "change_description": "<what was added/modified>",
      "skill_section": "<which phase/section was edited>",
      "diff_summary": "<before → after, 1-2 lines>"
    }
  ]
}
```

Print this summary so the orchestrator can log it in changelog.json.

### Step 6: Verify

Read the modified SKILL.md and confirm:
- It still follows the Six Hats structure
- No phases were removed or reordered
- FACT/ASSUME pattern is preserved
- New instructions are clear and concise
- No contradictions introduced

State: "SKILL.md improved. {N} changes applied targeting {list of metrics}. Ready for re-scoring."
```

- [ ] **Step 2: Commit improver**

```bash
git add autoresearch/agents/improver.md
git commit -m "feat: add improver agent for SKILL.md gap-driven improvements"
```

---

### Task 8: Build Static Dashboard

**Files:**
- Create: `autoresearch/dashboard/index.html`

- [ ] **Step 1: Write the dashboard**

Write to `autoresearch/dashboard/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autoresearch Eval Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #0f1117;
            color: #e1e4e8;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
        h1 { font-size: 28px; margin-bottom: 8px; }
        .subtitle { color: #8b949e; margin-bottom: 32px; }

        /* Score badge */
        .score-badge {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 16px 24px;
            margin-bottom: 32px;
        }
        .score-number {
            font-size: 48px;
            font-weight: 700;
        }
        .score-label { color: #8b949e; font-size: 14px; }
        .score-pass { color: #3fb950; }
        .score-fail { color: #f85149; }

        /* Sections */
        .section {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .section h2 {
            font-size: 18px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #30363d;
        }

        /* Charts */
        .chart-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        .chart-container {
            position: relative;
            height: 350px;
        }

        /* Metric table */
        table { width: 100%; border-collapse: collapse; }
        th, td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #30363d;
        }
        th { color: #8b949e; font-weight: 500; font-size: 13px; text-transform: uppercase; }
        .score-cell { font-weight: 600; font-size: 16px; }
        .score-3 { color: #3fb950; }
        .score-2 { color: #d29922; }
        .score-1 { color: #f85149; }
        .score-0 { color: #f85149; }

        /* Changelog */
        .change-entry {
            border-left: 3px solid #30363d;
            padding: 12px 16px;
            margin-bottom: 16px;
        }
        .change-entry.improved { border-color: #3fb950; }
        .change-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .change-score { font-weight: 600; }
        .change-time { color: #8b949e; font-size: 13px; }
        .change-desc { color: #c9d1d9; font-size: 14px; }
        .change-gaps { color: #f85149; font-size: 13px; margin-top: 4px; }
        .change-diff {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
            margin-top: 8px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 13px;
            white-space: pre-wrap;
        }

        /* Iteration selector */
        .iter-selector {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .iter-btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }
        .iter-btn:hover { background: #30363d; }
        .iter-btn.active { background: #388bfd; border-color: #388bfd; color: #fff; }

        /* Loading / Empty */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #8b949e;
        }
        .empty-state h3 { margin-bottom: 8px; color: #c9d1d9; }

        /* Evidence list */
        .evidence-list { list-style: none; padding: 0; }
        .evidence-list li {
            padding: 4px 0;
            font-size: 13px;
            color: #8b949e;
        }
        .evidence-list li::before { content: '  '; }
        .gap-item { color: #f85149; }
        .evidence-item { color: #3fb950; }

        @media (max-width: 768px) {
            .chart-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Autoresearch Eval Dashboard</h1>
        <p class="subtitle">Data-Analysis Plugin Quality Metrics</p>

        <div id="score-badge" class="score-badge" style="display:none;">
            <div>
                <span id="score-num" class="score-number">0</span>
                <span class="score-number" style="color:#8b949e">/36</span>
            </div>
            <div>
                <div id="score-status" class="score-label">Loading...</div>
                <div id="score-iter" class="score-label"></div>
            </div>
        </div>

        <!-- Iteration selector -->
        <div id="iter-selector" class="iter-selector"></div>

        <!-- Scorecard -->
        <div class="section">
            <h2>Metric Scorecard</h2>
            <div class="chart-row">
                <div class="chart-container">
                    <canvas id="radarChart"></canvas>
                </div>
                <div>
                    <table id="metrics-table">
                        <thead>
                            <tr><th>Metric</th><th>Score</th><th>Status</th></tr>
                        </thead>
                        <tbody id="metrics-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Iteration Timeline -->
        <div class="section">
            <h2>Score Timeline</h2>
            <div class="chart-container" style="height:250px;">
                <canvas id="timelineChart"></canvas>
            </div>
        </div>

        <!-- Metric Details (expandable) -->
        <div id="metric-details" class="section" style="display:none;">
            <h2 id="detail-title">Metric Details</h2>
            <div id="detail-content"></div>
        </div>

        <!-- Changelog -->
        <div class="section">
            <h2>Iteration Change Log</h2>
            <div id="changelog"></div>
        </div>

        <div id="empty-state" class="empty-state">
            <h3>No eval reports yet</h3>
            <p>Run the orchestrator agent to generate the first eval report.</p>
        </div>
    </div>

    <script>
    const METRIC_LABELS = [
        'Direction Quality', 'Insight Novelty', 'Query Efficiency',
        'Context Boundary', 'Uncertainty', 'Data Quality',
        'Segmentation', 'Actionability', 'Follow-up',
        'Simplicity', 'Narrative', 'Success Metrics'
    ];

    const METRIC_KEYS = [
        'direction-quality', 'insight-novelty', 'query-efficiency',
        'context-boundary', 'uncertainty', 'data-quality',
        'segmentation', 'actionability', 'followup',
        'simplicity', 'narrative', 'success-metrics'
    ];

    let reports = [];
    let changelog = { iterations: [] };
    let radarChart = null;
    let timelineChart = null;
    let selectedReport = null;

    async function loadData() {
        // Load all report files listed in changelog
        try {
            const clRes = await fetch('../changelog.json');
            if (clRes.ok) changelog = await clRes.json();
        } catch (e) { console.log('No changelog.json yet'); }

        // Try loading reports referenced in changelog
        for (const iter of changelog.iterations) {
            try {
                const res = await fetch(`../reports/run-${iter.run_id}.json`);
                if (res.ok) {
                    const report = await res.json();
                    reports.push(report);
                }
            } catch (e) { console.log(`Could not load report ${iter.run_id}`); }
        }

        if (reports.length === 0) {
            document.getElementById('empty-state').style.display = 'block';
            return;
        }

        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('score-badge').style.display = 'flex';

        renderIterSelector();
        selectReport(reports.length - 1);
        renderTimeline();
        renderChangelog();
    }

    function renderIterSelector() {
        const container = document.getElementById('iter-selector');
        container.innerHTML = '';
        reports.forEach((r, i) => {
            const btn = document.createElement('button');
            btn.className = 'iter-btn';
            btn.textContent = `Run ${i + 1} (${r.total_score}/36)`;
            btn.onclick = () => selectReport(i);
            container.appendChild(btn);
        });
    }

    function selectReport(index) {
        selectedReport = reports[index];

        // Update selector buttons
        document.querySelectorAll('.iter-btn').forEach((btn, i) => {
            btn.classList.toggle('active', i === index);
        });

        // Update score badge
        const scoreNum = document.getElementById('score-num');
        const scoreStatus = document.getElementById('score-status');
        const scoreIter = document.getElementById('score-iter');
        scoreNum.textContent = selectedReport.total_score;
        scoreNum.className = 'score-number ' + (selectedReport.pass ? 'score-pass' : 'score-fail');
        scoreStatus.textContent = selectedReport.pass ? 'ALL METRICS PASS' : 'GAPS REMAINING';
        scoreStatus.className = 'score-label ' + (selectedReport.pass ? 'score-pass' : 'score-fail');
        scoreIter.textContent = `Run ${index + 1} · ${selectedReport.timestamp || selectedReport.run_id}`;

        renderRadar();
        renderMetricsTable();
    }

    function getScoreForMetric(report, key) {
        const m = report.metrics.find(m => m.metric === key);
        return m ? m.score : 0;
    }

    function renderRadar() {
        const scores = METRIC_KEYS.map(k => getScoreForMetric(selectedReport, k));
        const ctx = document.getElementById('radarChart').getContext('2d');

        if (radarChart) radarChart.destroy();

        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: METRIC_LABELS,
                datasets: [{
                    label: 'Score',
                    data: scores,
                    backgroundColor: 'rgba(56, 139, 253, 0.15)',
                    borderColor: '#388bfd',
                    borderWidth: 2,
                    pointBackgroundColor: scores.map(s =>
                        s === 3 ? '#3fb950' : s === 2 ? '#d29922' : '#f85149'
                    ),
                    pointRadius: 5
                }, {
                    label: 'Target',
                    data: Array(12).fill(3),
                    backgroundColor: 'transparent',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 3,
                        ticks: {
                            stepSize: 1,
                            color: '#8b949e',
                            backdropColor: 'transparent'
                        },
                        grid: { color: '#21262d' },
                        angleLines: { color: '#21262d' },
                        pointLabels: { color: '#c9d1d9', font: { size: 11 } }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    function renderMetricsTable() {
        const tbody = document.getElementById('metrics-body');
        tbody.innerHTML = '';

        METRIC_KEYS.forEach((key, i) => {
            const metric = selectedReport.metrics.find(m => m.metric === key);
            const score = metric ? metric.score : 0;
            const status = score === 3 ? 'PASS' : 'GAP';
            const tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.onclick = () => showMetricDetail(key);
            tr.innerHTML = `
                <td>${METRIC_LABELS[i]}</td>
                <td class="score-cell score-${score}">${score}/3</td>
                <td class="score-${score}">${status}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function showMetricDetail(key) {
        const metric = selectedReport.metrics.find(m => m.metric === key);
        if (!metric) return;

        const section = document.getElementById('metric-details');
        const title = document.getElementById('detail-title');
        const content = document.getElementById('detail-content');

        section.style.display = 'block';
        title.textContent = METRIC_LABELS[METRIC_KEYS.indexOf(key)] + ` (${metric.score}/3)`;

        let html = '';
        if (metric.evidence && metric.evidence.length) {
            html += '<h4 style="color:#3fb950;margin:12px 0 8px">Evidence</h4><ul class="evidence-list">';
            metric.evidence.forEach(e => html += `<li class="evidence-item">${escHtml(e)}</li>`);
            html += '</ul>';
        }
        if (metric.gaps && metric.gaps.length) {
            html += '<h4 style="color:#f85149;margin:12px 0 8px">Gaps</h4><ul class="evidence-list">';
            metric.gaps.forEach(g => html += `<li class="gap-item">${escHtml(g)}</li>`);
            html += '</ul>';
        }
        if (metric.recommendation) {
            html += `<h4 style="color:#d29922;margin:12px 0 8px">Recommendation</h4><p style="font-size:14px">${escHtml(metric.recommendation)}</p>`;
        }

        content.innerHTML = html;
        section.scrollIntoView({ behavior: 'smooth' });
    }

    function renderTimeline() {
        const ctx = document.getElementById('timelineChart').getContext('2d');
        const labels = reports.map((r, i) => `Run ${i + 1}`);
        const scores = reports.map(r => r.total_score);

        if (timelineChart) timelineChart.destroy();

        timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Total Score',
                    data: scores,
                    borderColor: '#388bfd',
                    backgroundColor: 'rgba(56, 139, 253, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 6,
                    pointBackgroundColor: scores.map(s =>
                        s === 36 ? '#3fb950' : s >= 30 ? '#d29922' : '#f85149'
                    )
                }, {
                    label: 'Target (36)',
                    data: Array(reports.length).fill(36),
                    borderColor: '#3fb950',
                    borderDash: [5, 5],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 36,
                        ticks: { color: '#8b949e', stepSize: 6 },
                        grid: { color: '#21262d' }
                    },
                    x: {
                        ticks: { color: '#8b949e' },
                        grid: { color: '#21262d' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#c9d1d9' } }
                }
            }
        });
    }

    function renderChangelog() {
        const container = document.getElementById('changelog');
        if (!changelog.iterations.length) {
            container.innerHTML = '<p style="color:#8b949e">No iterations recorded yet.</p>';
            return;
        }

        container.innerHTML = '';
        // Reverse to show latest first
        [...changelog.iterations].reverse().forEach((iter, i) => {
            const isImproved = i < changelog.iterations.length - 1;
            const div = document.createElement('div');
            div.className = 'change-entry' + (isImproved ? ' improved' : '');
            div.innerHTML = `
                <div class="change-header">
                    <span class="change-score score-${iter.pass ? '3' : iter.total_score >= 30 ? '2' : '1'}">${iter.total_score}/36</span>
                    <span class="change-time">${iter.timestamp || iter.run_id}</span>
                </div>
                <div class="change-desc">${escHtml(iter.changes_made || 'Initial baseline')}</div>
                ${iter.gaps && iter.gaps.length ?
                    `<div class="change-gaps">Gaps: ${iter.gaps.join(', ')}</div>` : ''}
                ${iter.diff_snippets ?
                    `<div class="change-diff">${escHtml(iter.diff_snippets)}</div>` : ''}
            `;
            container.appendChild(div);
        });
    }

    function escHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    loadData();
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit dashboard**

```bash
git add autoresearch/dashboard/
git commit -m "feat: add static HTML eval dashboard with radar chart and timeline"
```

---

### Task 9: Write Run Instructions

**Files:**
- Create: `autoresearch/run.md`

- [ ] **Step 1: Write run.md**

Write to `autoresearch/run.md`:

```markdown
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
```

- [ ] **Step 2: Commit run instructions**

```bash
git add autoresearch/run.md
git commit -m "docs: add autoresearch run instructions"
```

---

### Task 10: Run Initial Eval and Iterate to 36/36

This task uses the autoresearch system we just built.

- [ ] **Step 1: Generate both datasets**

```bash
cd /Users/williamhung/Projects/cc-plugins/data-analysis
python3 autoresearch/datasets/google-ads/generate.py
python3 autoresearch/datasets/facebook-ads/generate.py
```

Verify both print row counts and pattern verification.

- [ ] **Step 2: Run orchestrator (baseline score)**

Follow `autoresearch/agents/orchestrator.md`:
1. Hash current SKILL.md
2. Dispatch all 12 scorers as parallel subagents
3. Aggregate into report JSON
4. Write to `autoresearch/reports/run-{timestamp}.json`
5. Update `autoresearch/changelog.json`
6. Print summary table

- [ ] **Step 3: Review baseline report**

Open dashboard: `open autoresearch/dashboard/index.html`
Note which metrics score < 3.

- [ ] **Step 4: Run improver (iteration 1)**

Follow `autoresearch/agents/improver.md`:
1. Read latest report
2. Identify gaps (score < 3)
3. Edit SKILL.md with minimum changes
4. Document changes

- [ ] **Step 5: Re-score (iteration 1)**

Repeat Step 2 with updated SKILL.md.

- [ ] **Step 6: Continue iterating**

If still < 36/36, repeat Steps 4-5 up to max 5 iterations.

- [ ] **Step 7: Commit final SKILL.md and all reports**

```bash
git add skills/data-analysis/SKILL.md autoresearch/reports/ autoresearch/changelog.json
git commit -m "feat: improve SKILL.md to 36/36 via autoresearch eval loop"
```

- [ ] **Step 8: Verify dashboard shows full history**

```bash
open autoresearch/dashboard/index.html
```

Confirm: radar chart shows all green, timeline shows improvement curve, changelog shows all iteration diffs.
