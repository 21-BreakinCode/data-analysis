"""
Facebook/Meta Ads synthetic dataset generator.

Generates ~12K+ rows of daily audience segment performance data with embedded patterns:
  - LA1_HighLTV (Lookalike_1pct) is the SCALE winner: highest conversion rate, AOV, repeat rate
  - Age_18_24 (Interest_Fashion) is the CUT candidate: lowest conversion, AOV, repeat rate
  - Interest_Fashion CTR declines after 2025-10 (audience exhaustion, -0.001/month)
  - pixel_confidence = 'low' for Broad/Video campaigns (conversions likely undercounted)
  - Weekend boost: ~15% higher reach on Sat/Sun

Uses DuckDB with hash-based deterministic randomness so the output is
reproducible without a fixed random seed.
"""

import os
import duckdb

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "data.csv")

# ---------------------------------------------------------------------------
# SQL – all generation logic lives here so DuckDB does the heavy lifting
# ---------------------------------------------------------------------------

GENERATE_SQL = """
-- -------------------------------------------------------------------------
-- 1. Reference tables
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE campaigns AS
SELECT *
FROM (VALUES
    ('Retargeting_DPA',  'Retargeting'),
    ('Lookalike_1pct',   'Lookalike'),
    ('Lookalike_5pct',   'Lookalike'),
    ('Interest_Fitness', 'Interest'),
    ('Interest_Tech',    'Interest'),
    ('Interest_Fashion', 'Interest'),
    ('Broad_CBO',        'Broad'),
    ('Video_Views',      'Video'),
    ('Lead_Gen',         'Lead_Gen')
) AS t(campaign_name, campaign_objective);

-- 3 audience segments per campaign (27 total)
CREATE OR REPLACE TABLE audience_segments AS
SELECT *
FROM (VALUES
    ('Retargeting_DPA',  'Cart_Abandoners',    'Past_Purchasers_90d',  'Site_Visitors_30d'),
    ('Lookalike_1pct',   'LA1_HighLTV',        'LA1_AllCustomers',     'LA1_EmailList'),
    ('Lookalike_5pct',   'LA5_HighLTV',        'LA5_AllCustomers',     'LA5_EmailList'),
    ('Interest_Fitness', 'Fitness_Enthusiasts','Health_Wellness',      'Sports_Active'),
    ('Interest_Tech',    'Tech_EarlyAdopters', 'Consumer_Electronics', 'Mobile_Gamers'),
    ('Interest_Fashion', 'Age_18_24',          'Fashion_Shoppers',     'Luxury_Apparel'),
    ('Broad_CBO',        'Broad_US_18plus',    'Broad_US_25_54',       'Broad_US_35plus'),
    ('Video_Views',      'Video_Engaged_3s',   'Video_Engaged_25pct',  'Video_Engaged_50pct'),
    ('Lead_Gen',         'LeadForm_Openers',   'LeadForm_Submitters',  'LeadForm_Qualified')
) AS t(campaign_name, seg1, seg2, seg3);

CREATE OR REPLACE TABLE audience_segment_flat AS
SELECT campaign_name, seg1 AS audience_segment FROM audience_segments
UNION ALL
SELECT campaign_name, seg2 FROM audience_segments
UNION ALL
SELECT campaign_name, seg3 FROM audience_segments;

-- -------------------------------------------------------------------------
-- 2. Date spine: 2025-01-01 through 2026-03-31
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE date_spine AS
SELECT CAST(range AS DATE) AS date
FROM range(DATE '2025-01-01', DATE '2026-04-01', INTERVAL '1 day');

-- -------------------------------------------------------------------------
-- 3. Placements
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE placements AS
SELECT unnest(['feed', 'stories', 'reels', 'right_column']) AS placement;

-- -------------------------------------------------------------------------
-- 4. Full skeleton (date × campaign × audience_segment × placement)
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE skeleton AS
SELECT
    d.date,
    c.campaign_name,
    ag.audience_segment,
    c.campaign_objective,
    p.placement
FROM date_spine d
CROSS JOIN campaigns c
JOIN audience_segment_flat ag USING (campaign_name)
CROSS JOIN placements p;

-- -------------------------------------------------------------------------
-- 5. Main dataset with all metrics
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE facebook_ads AS
WITH base AS (
    SELECT
        date,
        campaign_name,
        audience_segment,
        campaign_objective,
        placement,

        -- Deterministic hash seed per row
        hash(CAST(date AS VARCHAR) || '|' || campaign_name || '|' || audience_segment || '|' || placement) AS seed,

        -- Temporal flags
        EXTRACT(MONTH FROM date)  AS month_num,
        EXTRACT(DOW   FROM date)  AS dow,     -- 0=Sun, 6=Sat
        EXTRACT(YEAR  FROM date)  AS yr,
        EXTRACT(MONTH FROM date)
            + (EXTRACT(YEAR FROM date) - 2025) * 12 AS abs_month,  -- 1=Jan-25

        -- Weekend boost: Sat (6) / Sun (0) → 1.15x reach
        CASE WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 1.15 ELSE 1.0 END AS weekend_factor,

        -- Q4 holiday surge for relevant campaigns
        CASE WHEN EXTRACT(MONTH FROM date) IN (11, 12) THEN 1.5 ELSE 1.0 END AS q4_factor

    FROM skeleton
),
metrics AS (
    SELECT
        date,
        campaign_name,
        audience_segment,
        campaign_objective,
        placement,
        seed,
        abs_month,
        yr,

        -- ---------------------------------------------------------------
        -- REACH (daily unique users reached)
        -- Base varies by campaign type and placement
        -- ---------------------------------------------------------------
        CAST(
            GREATEST(100,
                ROUND(
                    CASE campaign_objective
                        WHEN 'Retargeting' THEN 3000.0
                        WHEN 'Lookalike'   THEN 8000.0
                        WHEN 'Interest'    THEN 12000.0
                        WHEN 'Broad'       THEN 25000.0
                        WHEN 'Video'       THEN 20000.0
                        WHEN 'Lead_Gen'    THEN 6000.0
                    END
                    -- placement weight
                    * CASE placement
                        WHEN 'feed'         THEN 0.55
                        WHEN 'stories'      THEN 0.25
                        WHEN 'reels'        THEN 0.15
                        WHEN 'right_column' THEN 0.05
                      END
                    * weekend_factor
                    * q4_factor
                    -- ±30% random variance using hash
                    * (0.70 + (hash(seed + 1) % 10000) / 10000.0 * 0.60)
                )
            )
        AS BIGINT) AS reach,

        -- ---------------------------------------------------------------
        -- FREQUENCY (impressions per person, 1.1 to 2.5)
        -- ---------------------------------------------------------------
        ROUND(
            1.1 + (hash(seed + 2) % 10000) / 10000.0 * 1.4
        , 2) AS frequency,

        -- ---------------------------------------------------------------
        -- CPM (cost per 1000 impressions, by campaign objective)
        -- ---------------------------------------------------------------
        GREATEST(1.0,
            ROUND(
                CASE campaign_objective
                    WHEN 'Retargeting' THEN 18.0
                    WHEN 'Lookalike'   THEN 12.0
                    WHEN 'Interest'    THEN 10.0
                    WHEN 'Broad'       THEN 7.0
                    WHEN 'Video'       THEN 5.0
                    WHEN 'Lead_Gen'    THEN 14.0
                END
                -- placement premium
                * CASE placement
                    WHEN 'feed'         THEN 1.20
                    WHEN 'stories'      THEN 1.10
                    WHEN 'reels'        THEN 1.05
                    WHEN 'right_column' THEN 0.60
                  END
                -- ±25% random variance
                * (0.75 + (hash(seed + 3) % 10000) / 10000.0 * 0.50)
            , 2)
        ) AS cpm,

        -- ---------------------------------------------------------------
        -- LINK CTR  (Interest_Fashion decays after Oct-2025, abs_month > 10)
        -- ---------------------------------------------------------------
        GREATEST(0.0005,
            CASE
                -- Segment-specific overrides first
                WHEN audience_segment = 'LA1_HighLTV'       THEN 0.022
                WHEN audience_segment = 'Age_18_24'         THEN 0.010
                WHEN audience_segment = 'Cart_Abandoners'   THEN 0.030
                WHEN audience_segment = 'Past_Purchasers_90d' THEN 0.025
                ELSE
                    CASE campaign_objective
                        WHEN 'Retargeting' THEN 0.020
                        WHEN 'Lookalike'   THEN 0.015
                        WHEN 'Interest'    THEN 0.012
                        WHEN 'Broad'       THEN 0.008
                        WHEN 'Video'       THEN 0.004
                        WHEN 'Lead_Gen'    THEN 0.016
                    END
            END
            -- Interest_Fashion audience exhaustion: -0.001/month after Oct-2025
            - CASE
                WHEN campaign_name = 'Interest_Fashion' AND abs_month > 10
                THEN LEAST(0.008, (abs_month - 10) * 0.001)
                ELSE 0.0
              END
            -- ±20% random variance
            * (0.80 + (hash(seed + 4) % 10000) / 10000.0 * 0.40)
        ) AS link_ctr,

        -- ---------------------------------------------------------------
        -- PURCHASE CONVERSION RATE (varies heavily by segment)
        -- ---------------------------------------------------------------
        GREATEST(0.0005,
            CASE audience_segment
                -- SCALE WINNER: LA1_HighLTV
                WHEN 'LA1_HighLTV'              THEN 0.035
                WHEN 'LA1_AllCustomers'         THEN 0.020
                WHEN 'LA1_EmailList'            THEN 0.025
                -- Retargeting strong performers
                WHEN 'Cart_Abandoners'          THEN 0.028
                WHEN 'Past_Purchasers_90d'      THEN 0.022
                WHEN 'Site_Visitors_30d'        THEN 0.015
                -- LA5 moderate
                WHEN 'LA5_HighLTV'              THEN 0.018
                WHEN 'LA5_AllCustomers'         THEN 0.012
                WHEN 'LA5_EmailList'            THEN 0.014
                -- Interest moderate
                WHEN 'Fitness_Enthusiasts'      THEN 0.010
                WHEN 'Health_Wellness'          THEN 0.009
                WHEN 'Sports_Active'            THEN 0.008
                WHEN 'Tech_EarlyAdopters'       THEN 0.012
                WHEN 'Consumer_Electronics'     THEN 0.010
                WHEN 'Mobile_Gamers'            THEN 0.007
                WHEN 'Fashion_Shoppers'         THEN 0.008
                WHEN 'Luxury_Apparel'           THEN 0.011
                -- CUT CANDIDATE: Age_18_24
                WHEN 'Age_18_24'               THEN 0.003
                -- Broad/Video low (undercount due to pixel)
                WHEN 'Broad_US_18plus'          THEN 0.005
                WHEN 'Broad_US_25_54'           THEN 0.007
                WHEN 'Broad_US_35plus'          THEN 0.008
                WHEN 'Video_Engaged_3s'         THEN 0.003
                WHEN 'Video_Engaged_25pct'      THEN 0.005
                WHEN 'Video_Engaged_50pct'      THEN 0.008
                -- Lead gen
                WHEN 'LeadForm_Openers'         THEN 0.006
                WHEN 'LeadForm_Submitters'      THEN 0.015
                WHEN 'LeadForm_Qualified'       THEN 0.022
                ELSE 0.008
            END
            -- ±25% random variance
            * (0.75 + (hash(seed + 5) % 10000) / 10000.0 * 0.50)
        ) AS purchase_conv_rate,

        -- ---------------------------------------------------------------
        -- AVERAGE ORDER VALUE
        -- ---------------------------------------------------------------
        GREATEST(5.0,
            ROUND(
                CASE audience_segment
                    -- SCALE WINNER high AOV
                    WHEN 'LA1_HighLTV'              THEN 125.0
                    WHEN 'LA1_AllCustomers'         THEN 90.0
                    WHEN 'LA1_EmailList'            THEN 95.0
                    WHEN 'Cart_Abandoners'          THEN 85.0
                    WHEN 'Past_Purchasers_90d'      THEN 95.0
                    WHEN 'Site_Visitors_30d'        THEN 70.0
                    WHEN 'LA5_HighLTV'              THEN 105.0
                    WHEN 'LA5_AllCustomers'         THEN 75.0
                    WHEN 'LA5_EmailList'            THEN 80.0
                    WHEN 'Fitness_Enthusiasts'      THEN 65.0
                    WHEN 'Health_Wellness'          THEN 60.0
                    WHEN 'Sports_Active'            THEN 55.0
                    WHEN 'Tech_EarlyAdopters'       THEN 110.0
                    WHEN 'Consumer_Electronics'     THEN 100.0
                    WHEN 'Mobile_Gamers'            THEN 40.0
                    WHEN 'Fashion_Shoppers'         THEN 70.0
                    WHEN 'Luxury_Apparel'           THEN 130.0
                    -- CUT CANDIDATE low AOV
                    WHEN 'Age_18_24'               THEN 25.0
                    WHEN 'Broad_US_18plus'          THEN 45.0
                    WHEN 'Broad_US_25_54'           THEN 60.0
                    WHEN 'Broad_US_35plus'          THEN 72.0
                    WHEN 'Video_Engaged_3s'         THEN 35.0
                    WHEN 'Video_Engaged_25pct'      THEN 48.0
                    WHEN 'Video_Engaged_50pct'      THEN 62.0
                    WHEN 'LeadForm_Openers'         THEN 55.0
                    WHEN 'LeadForm_Submitters'      THEN 75.0
                    WHEN 'LeadForm_Qualified'       THEN 95.0
                    ELSE 60.0
                END
                * (0.85 + (hash(seed + 6) % 10000) / 10000.0 * 0.30)
            , 2)
        ) AS avg_order_value,

        -- ---------------------------------------------------------------
        -- REPEAT PURCHASE RATE 30D (LTV proxy)
        -- ---------------------------------------------------------------
        GREATEST(0.01,
            LEAST(0.60,
                CASE audience_segment
                    -- SCALE WINNER high repeat
                    WHEN 'LA1_HighLTV'              THEN 0.35
                    WHEN 'LA1_AllCustomers'         THEN 0.22
                    WHEN 'LA1_EmailList'            THEN 0.28
                    WHEN 'Cart_Abandoners'          THEN 0.20
                    WHEN 'Past_Purchasers_90d'      THEN 0.30
                    WHEN 'Site_Visitors_30d'        THEN 0.12
                    WHEN 'LA5_HighLTV'              THEN 0.25
                    WHEN 'LA5_AllCustomers'         THEN 0.15
                    WHEN 'LA5_EmailList'            THEN 0.18
                    WHEN 'Fitness_Enthusiasts'      THEN 0.14
                    WHEN 'Health_Wellness'          THEN 0.13
                    WHEN 'Sports_Active'            THEN 0.11
                    WHEN 'Tech_EarlyAdopters'       THEN 0.16
                    WHEN 'Consumer_Electronics'     THEN 0.14
                    WHEN 'Mobile_Gamers'            THEN 0.08
                    WHEN 'Fashion_Shoppers'         THEN 0.13
                    WHEN 'Luxury_Apparel'           THEN 0.20
                    -- CUT CANDIDATE low repeat
                    WHEN 'Age_18_24'               THEN 0.05
                    WHEN 'Broad_US_18plus'          THEN 0.08
                    WHEN 'Broad_US_25_54'           THEN 0.10
                    WHEN 'Broad_US_35plus'          THEN 0.13
                    WHEN 'Video_Engaged_3s'         THEN 0.06
                    WHEN 'Video_Engaged_25pct'      THEN 0.09
                    WHEN 'Video_Engaged_50pct'      THEN 0.12
                    WHEN 'LeadForm_Openers'         THEN 0.07
                    WHEN 'LeadForm_Submitters'      THEN 0.14
                    WHEN 'LeadForm_Qualified'       THEN 0.20
                    ELSE 0.10
                END
                -- ±15% random variance
                * (0.85 + (hash(seed + 7) % 10000) / 10000.0 * 0.30)
            )
        ) AS repeat_purchase_rate_30d,

        -- ---------------------------------------------------------------
        -- CREATIVE TYPE (5% NULL for tracking gaps)
        -- ---------------------------------------------------------------
        CASE
            WHEN (hash(seed + 8) % 100) < 5 THEN NULL
            ELSE
                CASE (hash(seed + 9) % 3)
                    WHEN 0 THEN 'single_image'
                    WHEN 1 THEN 'carousel'
                    ELSE        'video'
                END
        END AS creative_type,

        -- ---------------------------------------------------------------
        -- PIXEL CONFIDENCE (low for Broad/Video)
        -- ---------------------------------------------------------------
        CASE campaign_objective
            WHEN 'Broad'   THEN 'low'
            WHEN 'Video'   THEN 'low'
            WHEN 'Lead_Gen' THEN 'medium'
            WHEN 'Interest' THEN 'medium'
            ELSE 'high'
        END AS pixel_confidence

    FROM base
),
computed AS (
    SELECT
        date,
        campaign_name,
        audience_segment,
        campaign_objective,
        placement,
        creative_type,
        pixel_confidence,

        reach,
        frequency,
        -- impressions = reach * frequency
        CAST(ROUND(reach * frequency) AS BIGINT)          AS impressions,
        cpm,

        link_ctr,
        purchase_conv_rate,
        avg_order_value,
        repeat_purchase_rate_30d

    FROM metrics
)
SELECT
    date,
    campaign_name,
    audience_segment,
    campaign_objective,
    placement,
    creative_type,
    pixel_confidence,

    reach,
    impressions,
    ROUND(frequency, 2)                                         AS frequency,

    ROUND(cpm, 2)                                               AS cpm,
    -- spend = impressions * cpm / 1000
    ROUND(impressions * cpm / 1000.0, 2)                        AS spend,

    ROUND(link_ctr, 6)                                          AS link_ctr,
    -- link_clicks = impressions * link_ctr
    CAST(GREATEST(0, ROUND(impressions * link_ctr)) AS BIGINT)  AS link_clicks,

    -- cpc = spend / link_clicks (NULL when no clicks)
    CASE
        WHEN ROUND(impressions * link_ctr) = 0 THEN NULL
        ELSE ROUND(
            (impressions * cpm / 1000.0)
            / GREATEST(1, ROUND(impressions * link_ctr))
        , 4)
    END AS cpc,

    ROUND(purchase_conv_rate, 6)                                AS purchase_conv_rate,
    -- purchases = link_clicks * purchase_conv_rate
    CAST(GREATEST(0, ROUND(
        GREATEST(0, ROUND(impressions * link_ctr)) * purchase_conv_rate
    )) AS BIGINT)                                               AS purchases,

    ROUND(avg_order_value, 2)                                   AS avg_order_value,
    -- revenue = purchases * avg_order_value
    ROUND(
        CAST(GREATEST(0, ROUND(
            GREATEST(0, ROUND(impressions * link_ctr)) * purchase_conv_rate
        )) AS BIGINT) * avg_order_value
    , 2)                                                        AS revenue,

    -- cost_per_purchase = spend / purchases (NULL when 0)
    CASE
        WHEN ROUND(
            GREATEST(0, ROUND(impressions * link_ctr)) * purchase_conv_rate
        ) = 0
        THEN NULL
        ELSE ROUND(
            (impressions * cpm / 1000.0)
            / GREATEST(1, ROUND(
                GREATEST(0, ROUND(impressions * link_ctr)) * purchase_conv_rate
            ))
        , 2)
    END AS cost_per_purchase,

    -- roas = revenue / spend (NULL when spend = 0)
    CASE
        WHEN ROUND(impressions * cpm / 1000.0, 2) = 0 THEN NULL
        ELSE ROUND(
            CAST(GREATEST(0, ROUND(
                GREATEST(0, ROUND(impressions * link_ctr)) * purchase_conv_rate
            )) AS BIGINT) * avg_order_value
            / ROUND(impressions * cpm / 1000.0, 2)
        , 4)
    END AS roas,

    ROUND(repeat_purchase_rate_30d, 4)                          AS repeat_purchase_rate_30d

FROM computed
ORDER BY date, campaign_name, audience_segment, placement;
"""

COPY_SQL = f"COPY facebook_ads TO '{OUTPUT_CSV}' (HEADER, DELIMITER ',');"

# ---------------------------------------------------------------------------
# Verification queries
# ---------------------------------------------------------------------------

SCALE_SEGMENTS_SQL = """
SELECT
    audience_segment,
    campaign_name,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)          AS roas,
    ROUND(AVG(repeat_purchase_rate_30d), 4)                  AS avg_repeat_rate,
    SUM(purchases)                                            AS total_purchases
FROM facebook_ads
GROUP BY audience_segment, campaign_name
HAVING SUM(spend) > 0
ORDER BY roas DESC, avg_repeat_rate DESC
LIMIT 8;
"""

CUT_SEGMENTS_SQL = """
SELECT
    audience_segment,
    campaign_name,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)          AS roas,
    ROUND(AVG(repeat_purchase_rate_30d), 4)                  AS avg_repeat_rate,
    SUM(purchases)                                            AS total_purchases
FROM facebook_ads
GROUP BY audience_segment, campaign_name
HAVING SUM(spend) > 0
ORDER BY roas ASC, avg_repeat_rate ASC
LIMIT 8;
"""

FASHION_CTR_DECAY_SQL = """
SELECT
    CASE
        WHEN EXTRACT(MONTH FROM date) BETWEEN 1 AND 3  THEN STRFTIME(date, '%Y') || '-Q1'
        WHEN EXTRACT(MONTH FROM date) BETWEEN 4 AND 6  THEN STRFTIME(date, '%Y') || '-Q2'
        WHEN EXTRACT(MONTH FROM date) BETWEEN 7 AND 9  THEN STRFTIME(date, '%Y') || '-Q3'
        ELSE                                                 STRFTIME(date, '%Y') || '-Q4'
    END AS quarter,
    ROUND(SUM(link_clicks)::DOUBLE / NULLIF(SUM(impressions), 0), 6) AS avg_link_ctr
FROM facebook_ads
WHERE campaign_name = 'Interest_Fashion'
GROUP BY 1
ORDER BY 1;
"""


def main() -> None:
    con = duckdb.connect()

    print("Generating Facebook Ads dataset …")
    con.execute(GENERATE_SQL)
    con.execute(COPY_SQL)

    # -------------------------------------------------------------------
    # 1. Row + column summary
    # -------------------------------------------------------------------
    result = con.execute("SELECT COUNT(*) FROM facebook_ads").fetchone()
    row_count = result[0] if result else 0
    cols = [r[0] for r in con.execute("DESCRIBE facebook_ads").fetchall()]
    print(f"\nRow count : {row_count:,}")
    print(f"Columns   : {len(cols)}")
    print(f"  {', '.join(cols)}")

    # -------------------------------------------------------------------
    # 2. Best segments to SCALE (ROAS + repeat rate)
    # -------------------------------------------------------------------
    print("\n--- Best segments to SCALE (top ROAS + repeat rate) ---")
    print(f"{'Segment':<30}  {'Campaign':<18}  {'ROAS':>8}  {'Repeat%':>8}  {'Purchases':>10}")
    print("-" * 82)
    for seg, camp, roas, repeat, purch in con.execute(SCALE_SEGMENTS_SQL).fetchall():
        marker = " ← SCALE WINNER" if seg == "LA1_HighLTV" else ""
        roas_str = str(roas) if roas is not None else "N/A"
        print(f"{seg:<30}  {camp:<18}  {roas_str:>8}  {repeat:>8.4f}  {purch:>10,}{marker}")

    # -------------------------------------------------------------------
    # 3. Segments to CUT (low ROAS + low repeat)
    # -------------------------------------------------------------------
    print("\n--- Segments to CUT (lowest ROAS + repeat rate) ---")
    print(f"{'Segment':<30}  {'Campaign':<18}  {'ROAS':>8}  {'Repeat%':>8}  {'Purchases':>10}")
    print("-" * 82)
    for seg, camp, roas, repeat, purch in con.execute(CUT_SEGMENTS_SQL).fetchall():
        marker = " ← CUT CANDIDATE" if seg == "Age_18_24" else ""
        roas_str = str(roas) if roas is not None else "N/A"
        print(f"{seg:<30}  {camp:<18}  {roas_str:>8}  {repeat:>8.4f}  {purch:>10,}{marker}")

    # -------------------------------------------------------------------
    # 4. Interest_Fashion CTR decay by quarter
    # -------------------------------------------------------------------
    print("\n--- Interest_Fashion CTR decay by quarter ---")
    print(f"{'Quarter':<10}  {'Avg Link CTR':>14}")
    print("-" * 28)
    for quarter, ctr in con.execute(FASHION_CTR_DECAY_SQL).fetchall():
        marker = " ← exhaustion" if quarter >= "2025-Q4" else ""
        print(f"{quarter:<10}  {str(ctr):>14}{marker}")

    print(f"\nCSV written to: {OUTPUT_CSV}")
    con.close()


if __name__ == "__main__":
    main()
