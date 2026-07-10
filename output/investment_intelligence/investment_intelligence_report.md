# Investment Intelligence v2

Investment Intelligence v2 assessed 10 research asset(s), identified market state HIGH_DISPERSION_SELECTION, and measured segmented-data coverage at 100.0%.

## Market Context

```json
{
  "asset_count": 10,
  "breadth": {
    "positive_1d_ratio": 1.0,
    "positive_7d_ratio": 0.7,
    "positive_30d_ratio": 0.7
  },
  "median_returns": {
    "return_1d": 0.0199,
    "return_7d": 0.025712,
    "return_30d": 0.017938
  },
  "dispersion": {
    "return_30d_std": 0.166607,
    "volatility_30d_std": 0.176161,
    "label": "HIGH"
  },
  "leaders": [
    {
      "asset": "BTC-USD",
      "score": 0.105625,
      "score_field": "final_alpha_score",
      "rank": 1.0
    },
    {
      "asset": "ETH-USD",
      "score": 0.105625,
      "score_field": "final_alpha_score",
      "rank": 1.0
    },
    {
      "asset": "SOL-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 3.0
    }
  ],
  "laggards": [
    {
      "asset": "SOL-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 3.0
    },
    {
      "asset": "AAVE-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 3.0
    },
    {
      "asset": "LINK-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 3.0
    }
  ],
  "rank_concentration": {
    "top_two_score_share": 1.0,
    "label": "HIGHLY_CONCENTRATED"
  },
  "market_state": "HIGH_DISPERSION_SELECTION"
}
```

## Price Repository

```json
{
  "coverage_ratio": 1.0,
  "coverage_label": "EXCELLENT",
  "segment_count": 30,
  "healthy_segment_count": 30,
  "unhealthy_segments": [],
  "provider": "yfinance"
}
```

## V2 Recommendations

- Leadership is concentrated; avoid treating the full universe as equally supported.
