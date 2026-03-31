"""
Google Ads synthetic dataset generator.

Generates ~10K+ rows of daily campaign performance data with embedded patterns:
  - Generic_Search CTR degrades after 2025-09 (audience fatigue)
  - All Search campaign CPC increases after 2026-01-01 (competitive pressure)
  - Search campaign conversion_rate drops after 2026-01-01 (creative decay)

These two forces combine to roughly double CPA for Search campaigns in 2026.

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
    ('Brand_Search',        'Search'),
    ('Generic_Search',      'Search'),
    ('Competitor_Search',   'Search'),
    ('Display_Retarget',    'Display'),
    ('Display_Prospecting', 'Display'),
    ('Video_Awareness',     'Video'),
    ('Shopping_Feed',       'Shopping'),
    ('Performance_Max',     'PMax')
) AS t(campaign_name, campaign_type);

CREATE OR REPLACE TABLE ad_groups AS
SELECT *
FROM (VALUES
    ('Brand_Search',        'Brand_Exact',              'Brand_Phrase',           'Brand_BMM'),
    ('Generic_Search',      'Generic_Exact',             'Generic_Phrase',          'Generic_BMM'),
    ('Competitor_Search',   'Competitor_Exact',          'Competitor_Phrase',       'Competitor_BMM'),
    ('Display_Retarget',    'Retarget_CartAbandoners',   'Retarget_PastBuyers',    'Retarget_SiteVisitors'),
    ('Display_Prospecting', 'Prospect_Lookalike',        'Prospect_Interest',       'Prospect_Demographic'),
    ('Video_Awareness',     'Video_InStream',            'Video_Bumper',            'Video_Discovery'),
    ('Shopping_Feed',       'Shopping_AllProducts',      'Shopping_BestSellers',    'Shopping_Clearance'),
    ('Performance_Max',     'PMax_AllSignals',           'PMax_StoreVisits',        'PMax_OnlineSales')
) AS t(campaign_name, ag1, ag2, ag3);

CREATE OR REPLACE TABLE ad_group_flat AS
SELECT campaign_name, ag1 AS ad_group_name FROM ad_groups
UNION ALL
SELECT campaign_name, ag2 FROM ad_groups
UNION ALL
SELECT campaign_name, ag3 FROM ad_groups;

-- -------------------------------------------------------------------------
-- 2. Date spine: 2025-01-01 through 2026-03-31
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE date_spine AS
SELECT CAST(range AS DATE) AS date
FROM range(DATE '2025-01-01', DATE '2026-04-01', INTERVAL '1 day');

-- -------------------------------------------------------------------------
-- 3. Devices
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE devices AS
SELECT unnest(['mobile', 'desktop', 'tablet']) AS device;

-- -------------------------------------------------------------------------
-- 4. Full skeleton (date × campaign × ad_group × device)
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE skeleton AS
SELECT
    d.date,
    c.campaign_name,
    ag.ad_group_name,
    c.campaign_type,
    dev.device
FROM date_spine d
CROSS JOIN campaigns c
JOIN ad_group_flat ag USING (campaign_name)
CROSS JOIN devices dev;

-- -------------------------------------------------------------------------
-- 5. Main dataset with all metrics
-- -------------------------------------------------------------------------
CREATE OR REPLACE TABLE google_ads AS
WITH base AS (
    SELECT
        date,
        campaign_name,
        ad_group_name,
        campaign_type,
        device,

        -- Deterministic hash seed per row
        hash(CAST(date AS VARCHAR) || '|' || campaign_name || '|' || ad_group_name || '|' || device) AS seed,

        -- Temporal flags
        EXTRACT(MONTH FROM date)  AS month_num,
        EXTRACT(DOW   FROM date)  AS dow,     -- 0=Sun, 6=Sat
        EXTRACT(YEAR  FROM date)  AS yr,
        EXTRACT(MONTH FROM date)
            + (EXTRACT(YEAR FROM date) - 2025) * 12 AS abs_month,  -- 1=Jan-25

        -- Q4 holiday surge: Nov (month 11) and Dec (month 12) → 1.8x
        CASE WHEN EXTRACT(MONTH FROM date) IN (11, 12) THEN 1.8 ELSE 1.0 END AS q4_factor,

        -- Weekend dip: Sat (6) / Sun (0) → 0.7x
        CASE WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN 0.7 ELSE 1.0 END AS weekend_factor

    FROM skeleton
),
metrics AS (
    SELECT
        date,
        campaign_name,
        ad_group_name,
        campaign_type,
        device,
        seed,
        abs_month,
        yr,

        -- ---------------------------------------------------------------
        -- IMPRESSIONS
        -- Base impressions by campaign type (daily per ad_group×device)
        -- ---------------------------------------------------------------
        CAST(
            GREATEST(10,
                ROUND(
                    CASE campaign_type
                        WHEN 'Search'   THEN 800.0
                        WHEN 'Display'  THEN 5000.0
                        WHEN 'Video'    THEN 8000.0
                        WHEN 'Shopping' THEN 1200.0
                        WHEN 'PMax'     THEN 3000.0
                    END
                    -- device weight
                    * CASE device
                        WHEN 'mobile'  THEN 0.55
                        WHEN 'desktop' THEN 0.35
                        WHEN 'tablet'  THEN 0.10
                      END
                    * q4_factor
                    * weekend_factor
                    -- ±30% random variance using hash
                    * (0.70 + (hash(seed + 1) % 10000) / 10000.0 * 0.60)
                )
            )
        AS BIGINT) AS impressions,

        -- ---------------------------------------------------------------
        -- CTR  (base varies by type; Generic_Search decays post-2025-09)
        -- ---------------------------------------------------------------
        GREATEST(0.001,
            CASE campaign_type
                WHEN 'Search'   THEN 0.045
                WHEN 'Display'  THEN 0.004
                WHEN 'Video'    THEN 0.006
                WHEN 'Shopping' THEN 0.020
                WHEN 'PMax'     THEN 0.012
            END
            -- Generic_Search fatigue: -0.002 per month after Sep-2025 (abs_month >= 10)
            - CASE
                WHEN campaign_name = 'Generic_Search' AND abs_month > 9
                THEN LEAST(0.030, (abs_month - 9) * 0.002)
                ELSE 0.0
              END
            -- ±20% random variance
            * (0.80 + (hash(seed + 2) % 10000) / 10000.0 * 0.40)
        ) AS ctr,

        -- ---------------------------------------------------------------
        -- CPC  (base by type; Search campaigns increase after 2026-01-01)
        -- ---------------------------------------------------------------
        GREATEST(0.01,
            CASE campaign_type
                WHEN 'Search'   THEN 1.80
                WHEN 'Display'  THEN 0.45
                WHEN 'Video'    THEN 0.25
                WHEN 'Shopping' THEN 0.90
                WHEN 'PMax'     THEN 1.10
            END
            -- Search CPC surge from 2026-01: +35% base increase,
            -- plus additional ramp each month
            * CASE
                WHEN campaign_type = 'Search' AND yr >= 2026
                THEN 1.35 + GREATEST(0, (abs_month - 12) * 0.04)
                ELSE 1.0
              END
            -- ±25% random variance
            * (0.75 + (hash(seed + 3) % 10000) / 10000.0 * 0.50)
        ) AS cpc,

        -- ---------------------------------------------------------------
        -- CONVERSION RATE (Search drops after 2026-01-01)
        -- ---------------------------------------------------------------
        GREATEST(0.001,
            CASE campaign_name
                WHEN 'Brand_Search'        THEN 0.080
                WHEN 'Generic_Search'      THEN 0.040
                WHEN 'Competitor_Search'   THEN 0.030
                WHEN 'Display_Retarget'    THEN 0.025
                WHEN 'Display_Prospecting' THEN 0.008
                WHEN 'Video_Awareness'     THEN 0.005
                WHEN 'Shopping_Feed'       THEN 0.055
                WHEN 'Performance_Max'     THEN 0.035
            END
            -- Search conv_rate drops after 2026-01: -25% base, further ramp per month
            * CASE
                WHEN campaign_type = 'Search' AND yr >= 2026
                THEN GREATEST(0.30, 0.75 - GREATEST(0, (abs_month - 12) * 0.05))
                ELSE 1.0
              END
            -- ±20% random variance
            * (0.80 + (hash(seed + 4) % 10000) / 10000.0 * 0.40)
        ) AS conversion_rate,

        -- ---------------------------------------------------------------
        -- AVG CONVERSION VALUE (revenue per conversion)
        -- ---------------------------------------------------------------
        ROUND(
            CASE campaign_name
                WHEN 'Brand_Search'        THEN 85.0
                WHEN 'Generic_Search'      THEN 65.0
                WHEN 'Competitor_Search'   THEN 55.0
                WHEN 'Display_Retarget'    THEN 70.0
                WHEN 'Display_Prospecting' THEN 45.0
                WHEN 'Video_Awareness'     THEN 30.0
                WHEN 'Shopping_Feed'       THEN 95.0
                WHEN 'Performance_Max'     THEN 75.0
            END
            * (0.85 + (hash(seed + 5) % 10000) / 10000.0 * 0.30)
        , 2) AS avg_conversion_value,

        -- ---------------------------------------------------------------
        -- QUALITY SCORE (Search + Shopping only, 1-10, else NULL)
        -- ---------------------------------------------------------------
        CASE
            WHEN campaign_type IN ('Search', 'Shopping')
            THEN CAST(1 + (hash(seed + 6) % 10) AS INTEGER)
            ELSE NULL
        END AS quality_score,

        -- ---------------------------------------------------------------
        -- BOUNCE RATE
        -- ---------------------------------------------------------------
        ROUND(
            CASE campaign_type
                WHEN 'Search'   THEN 0.42
                WHEN 'Display'  THEN 0.68
                WHEN 'Video'    THEN 0.75
                WHEN 'Shopping' THEN 0.35
                WHEN 'PMax'     THEN 0.50
            END
            * (0.85 + (hash(seed + 7) % 10000) / 10000.0 * 0.30)
        , 4) AS bounce_rate,

        -- ---------------------------------------------------------------
        -- AD FORMAT (5% NULL for realism)
        -- ---------------------------------------------------------------
        CASE
            WHEN (hash(seed + 8) % 100) < 5 THEN NULL
            ELSE
                CASE campaign_type
                    WHEN 'Search'   THEN 'text_ad'
                    WHEN 'Display'  THEN 'image_ad'
                    WHEN 'Video'    THEN 'video_ad'
                    WHEN 'Shopping' THEN 'product_listing'
                    WHEN 'PMax'     THEN 'responsive_ad'
                END
        END AS ad_format,

        q4_factor,
        weekend_factor

    FROM base
)
SELECT
    date,
    campaign_name,
    ad_group_name,
    campaign_type,
    device,

    impressions,
    ROUND(ctr, 6)                                                       AS ctr,
    CAST(GREATEST(0, ROUND(impressions * ctr)) AS BIGINT)               AS clicks,
    ROUND(cpc, 4)                                                       AS cpc,
    ROUND(GREATEST(0, ROUND(impressions * ctr)) * cpc, 2)               AS cost,

    ROUND(conversion_rate, 6)                                           AS conversion_rate,
    ROUND(GREATEST(0, ROUND(impressions * ctr)) * conversion_rate, 4)   AS conversions,

    avg_conversion_value,
    ROUND(GREATEST(0, ROUND(impressions * ctr)) * conversion_rate
          * avg_conversion_value, 2)                                    AS conversion_value,

    -- CPA: NULL when conversions = 0
    CASE
        WHEN ROUND(GREATEST(0, ROUND(impressions * ctr)) * conversion_rate, 4) = 0
        THEN NULL
        ELSE ROUND(
            GREATEST(0, ROUND(impressions * ctr)) * cpc
            / (ROUND(GREATEST(0, ROUND(impressions * ctr)) * conversion_rate, 4))
        , 2)
    END AS cpa,

    -- ROAS: NULL when cost = 0
    CASE
        WHEN ROUND(GREATEST(0, ROUND(impressions * ctr)) * cpc, 2) = 0
        THEN NULL
        ELSE ROUND(
            ROUND(GREATEST(0, ROUND(impressions * ctr)) * conversion_rate
                  * avg_conversion_value, 2)
            / ROUND(GREATEST(0, ROUND(impressions * ctr)) * cpc, 2)
        , 4)
    END AS roas,

    quality_score,
    bounce_rate,
    ad_format

FROM metrics
ORDER BY date, campaign_name, ad_group_name, device;
"""

COPY_SQL = f"COPY google_ads TO '{OUTPUT_CSV}' (HEADER, DELIMITER ',');"

# ---------------------------------------------------------------------------
# Verification queries
# ---------------------------------------------------------------------------

CPA_TREND_SQL = """
SELECT
    STRFTIME(date, '%Y-%m')           AS month,
    ROUND(SUM(cost) / NULLIF(SUM(conversions), 0), 2) AS avg_cpa
FROM google_ads
WHERE campaign_type = 'Search'
GROUP BY 1
ORDER BY 1;
"""

CTR_DECAY_SQL = """
SELECT
    CASE
        WHEN EXTRACT(MONTH FROM date) BETWEEN 1 AND 3  THEN STRFTIME(date, '%Y') || '-Q1'
        WHEN EXTRACT(MONTH FROM date) BETWEEN 4 AND 6  THEN STRFTIME(date, '%Y') || '-Q2'
        WHEN EXTRACT(MONTH FROM date) BETWEEN 7 AND 9  THEN STRFTIME(date, '%Y') || '-Q3'
        ELSE                                                 STRFTIME(date, '%Y') || '-Q4'
    END AS quarter,
    ROUND(SUM(clicks)::DOUBLE / NULLIF(SUM(impressions), 0), 6) AS avg_ctr
FROM google_ads
WHERE campaign_name = 'Generic_Search'
GROUP BY 1
ORDER BY 1;
"""


def main() -> None:
    con = duckdb.connect()

    print("Generating Google Ads dataset …")
    con.execute(GENERATE_SQL)
    con.execute(COPY_SQL)

    # -------------------------------------------------------------------
    # 1. Row + column summary
    # -------------------------------------------------------------------
    result = con.execute("SELECT COUNT(*) FROM google_ads").fetchone()
    row_count = result[0] if result else 0
    cols = [r[0] for r in con.execute("DESCRIBE google_ads").fetchall()]
    print(f"\nRow count : {row_count:,}")
    print(f"Columns   : {len(cols)}")
    print(f"  {', '.join(cols)}")

    # -------------------------------------------------------------------
    # 2. CPA trend for Search campaigns (should show increase in 2026)
    # -------------------------------------------------------------------
    print("\n--- CPA trend: Search campaigns by month ---")
    print(f"{'Month':<10}  {'Avg CPA':>10}")
    print("-" * 24)
    for month, cpa in con.execute(CPA_TREND_SQL).fetchall():
        marker = " ← 2026 surge" if month.startswith("2026") else ""
        print(f"{month:<10}  {str(cpa):>10}{marker}")

    # -------------------------------------------------------------------
    # 3. CTR decay for Generic_Search by quarter
    # -------------------------------------------------------------------
    print("\n--- CTR decay: Generic_Search by quarter ---")
    print(f"{'Quarter':<10}  {'Avg CTR':>10}")
    print("-" * 24)
    for quarter, ctr in con.execute(CTR_DECAY_SQL).fetchall():
        marker = " ← fatigue" if quarter >= "2025-Q4" else ""
        print(f"{quarter:<10}  {str(ctr):>10}{marker}")

    print(f"\nCSV written to: {OUTPUT_CSV}")
    con.close()


if __name__ == "__main__":
    main()
