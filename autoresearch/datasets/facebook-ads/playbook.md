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
- `impressions`: total ad views (reach x frequency)
- `frequency`: avg impressions per user (high frequency = potential fatigue)
- `cpm`: cost per 1000 impressions in USD
- `spend`: total cost
- `link_ctr`: click-through rate on link clicks
- `link_clicks`: outbound clicks
- `cpc`: cost per link click
- `purchase_conv_rate`: purchases / link_clicks
- `purchases`: purchase events
- `avg_order_value`: revenue per purchase in USD
- `revenue`: total revenue (purchases x avg_order_value)
- `cost_per_purchase`: CPA (spend / purchases)
- `roas`: return on ad spend (revenue / spend)
- `repeat_purchase_rate_30d`: % of purchasers who buy again within 30 days (LTV proxy)
- `pixel_confidence`: high/medium/low — Meta pixel attribution reliability

Data source: Meta Ads API daily export, one row per campaign x audience_segment x placement x day.

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
