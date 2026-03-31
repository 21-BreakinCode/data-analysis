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

Data source: Google Ads API daily export, one row per campaign x ad_group x device x day.

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
