# Investment Intelligence v2.1

Investment Intelligence v2.1 assessed 10 research asset(s), identified market state HIGH_DISPERSION_SELECTION, measured segmented-data coverage at 100.0%, and reconciled portfolio state with 0 canonical action(s).

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

## Reconciliation

```json
{
  "version": "investment_intelligence_reconciliation_v2_1",
  "generated_at": "2026-07-10T07:46:28.205707+00:00",
  "snapshot_fingerprint": "f2a387911331a666d49ae758b43c4fb99bb5bdd5151b9ea3815eab6905d0f42a",
  "state_consistent": true,
  "stale_rebalance_detected": false,
  "tolerance": 0.0005,
  "summary": "Reconciled 2 risky asset(s); generated 0 canonical trade action(s); detected 0 source inconsistency/inconsistencies.",
  "portfolio": {
    "current_risky_weight": 0.7,
    "target_risky_weight": 0.7,
    "current_cash_weight": 0.3,
    "target_cash_weight": 0.3
  },
  "asset_reconciliation": [
    {
      "asset": "BTC-USD",
      "current_weight": 0.350055,
      "canonical_target_weight": 0.35,
      "adaptive_weight": 0.35,
      "rebalance_target_weight": null,
      "canonical_delta": -5.5e-05,
      "rebalance_delta": null,
      "rebalance_action": null,
      "target_matches_adaptive": true,
      "rebalance_target_current": true,
      "rebalance_delta_current": true,
      "canonical_current_source": "portfolio_state_v4",
      "canonical_target_source": "alpha_portfolio_v3"
    },
    {
      "asset": "ETH-USD",
      "current_weight": 0.349945,
      "canonical_target_weight": 0.35,
      "adaptive_weight": 0.35,
      "rebalance_target_weight": null,
      "canonical_delta": 5.5e-05,
      "rebalance_delta": null,
      "rebalance_action": null,
      "target_matches_adaptive": true,
      "rebalance_target_current": true,
      "rebalance_delta_current": true,
      "canonical_current_source": "portfolio_state_v4",
      "canonical_target_source": "alpha_portfolio_v3"
    }
  ],
  "canonical_trades": [],
  "issues": [],
  "source_manifest": [
    {
      "source": "portfolio_state",
      "path": "output\\investment_portfolio_state\\portfolio_state.json",
      "exists": true,
      "size_bytes": 2143,
      "modified_at": "2026-07-10T07:46:15.106157+00:00"
    },
    {
      "source": "portfolio_holdings",
      "path": "output\\investment_portfolio_state\\portfolio_holdings.csv",
      "exists": true,
      "size_bytes": 366,
      "modified_at": "2026-07-10T07:46:15.106157+00:00"
    },
    {
      "source": "mtm_report",
      "path": "output\\investment_mark_to_market\\mark_to_market_report.json",
      "exists": true,
      "size_bytes": 2393,
      "modified_at": "2026-07-10T07:46:04.102839+00:00"
    },
    {
      "source": "mtm_positions",
      "path": "output\\investment_mark_to_market\\positions.csv",
      "exists": true,
      "size_bytes": 390,
      "modified_at": "2026-07-10T07:46:04.091384+00:00"
    },
    {
      "source": "alpha_portfolio_report",
      "path": "output\\investment_alpha\\alpha_portfolio_report.json",
      "exists": true,
      "size_bytes": 1393,
      "modified_at": "2026-07-10T07:46:10.539523+00:00"
    },
    {
      "source": "alpha_portfolio",
      "path": "output\\investment_alpha\\alpha_portfolio.csv",
      "exists": true,
      "size_bytes": 393,
      "modified_at": "2026-07-10T07:45:03.395540+00:00"
    },
    {
      "source": "adaptive_weighting_report",
      "path": "output\\investment_adaptive_weighting\\adaptive_weighting_report.json",
      "exists": true,
      "size_bytes": 1662,
      "modified_at": "2026-07-10T07:46:07.768848+00:00"
    },
    {
      "source": "adaptive_weights",
      "path": "output\\investment_adaptive_weighting\\adaptive_weights.csv",
      "exists": true,
      "size_bytes": 271,
      "modified_at": "2026-07-10T07:46:07.768848+00:00"
    },
    {
      "source": "rebalance_report",
      "path": "output\\investment_rebalance\\rebalance_report.json",
      "exists": true,
      "size_bytes": 1901,
      "modified_at": "2026-07-10T07:46:24.363659+00:00"
    },
    {
      "source": "rebalance_orders",
      "path": "output\\investment_rebalance\\rebalance_orders.csv",
      "exists": true,
      "size_bytes": 2,
      "modified_at": "2026-07-10T07:46:24.363659+00:00"
    },
    {
      "source": "broker_ledger_report",
      "path": "output\\investment_broker_ledger\\broker_ledger_report.json",
      "exists": true,
      "size_bytes": 2781,
      "modified_at": "2026-07-10T01:50:20.589123+00:00"
    }
  ],
  "authority": {
    "current_positions": "portfolio_state_v4_then_mtm_v4",
    "target_portfolio": "alpha_portfolio_v3",
    "adaptive_cross_check": "adaptive_weighting_v4",
    "rebalance_role": "audit_only",
    "execution_influence": false
  }
}
```

## V2.1 Recommendations

- Leadership is concentrated; avoid treating the full universe as equally supported.
