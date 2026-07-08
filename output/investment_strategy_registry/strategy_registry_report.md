# Strategy Registry Report

Strategy Registry collected 8 signal row(s) from 2 source(s).

## Summary

```json
{
  "signal_count": 8,
  "source_counts": {
    "atlas_alpha": 6,
    "sigil_v32": 2
  },
  "family_counts": {
    "portfolio_allocation": 3,
    "cross_sectional_ranking": 3,
    "intraday_execution": 2
  },
  "action_counts": {
    "ALLOCATE": 3,
    "WATCH": 3,
    "NO_ACTION": 2
  },
  "asset_counts": {
    "SOL-USD": 4,
    "BTC-USD": 2,
    "ETH-USD": 2
  },
  "unique_assets": [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD"
  ]
}
```

## Signals

- `sigil_v32` / `ENGINE_A_PULLBACK_CONTINUATION` asset=`SOL-USD` action=`NO_ACTION` direction=`FLAT` exposure=`0.0`
- `sigil_v32` / `ENGINE_B_FAILED_OPENING_EXPANSION` asset=`SOL-USD` action=`NO_ACTION` direction=`FLAT` exposure=`0.0`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`BTC-USD` action=`ALLOCATE` direction=`LONG` exposure=`0.364444`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`ETH-USD` action=`ALLOCATE` direction=`LONG` exposure=`0.311111`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`SOL-USD` action=`ALLOCATE` direction=`LONG` exposure=`0.124444`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`BTC-USD` action=`WATCH` direction=`LONG` exposure=`0.0`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`ETH-USD` action=`WATCH` direction=`LONG` exposure=`0.0`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`SOL-USD` action=`WATCH` direction=`LONG` exposure=`0.0`
