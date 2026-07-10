# Investment Intelligence v2.1

Investment Intelligence v2.1 assessed 10 research asset(s), identified market state HIGH_DISPERSION_SELECTION, measured segmented-data coverage at 100.0%, and reconciled portfolio state with 4 canonical action(s).

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
      "asset": "SOL-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 1.0
    },
    {
      "asset": "AAVE-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 1.0
    },
    {
      "asset": "BTC-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 1.0
    }
  ],
  "laggards": [
    {
      "asset": "SOL-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 1.0
    },
    {
      "asset": "AAVE-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 1.0
    },
    {
      "asset": "BTC-USD",
      "score": 0.0,
      "score_field": "final_alpha_score",
      "rank": 1.0
    }
  ],
  "rank_concentration": {
    "top_two_score_share": 0.0,
    "label": "UNDIFFERENTIATED"
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
  "generated_at": "2026-07-10T11:14:30.100823+00:00",
  "snapshot_fingerprint": "3a989d2b891739cd5d12f0fd8d5893ad98f3c41d8e668a17467d8098c7a28a71",
  "state_consistent": false,
  "stale_rebalance_detected": true,
  "tolerance": 0.0005,
  "summary": "Reconciled 4 risky asset(s); generated 4 canonical trade action(s); detected 8 source inconsistency/inconsistencies.",
  "portfolio": {
    "current_risky_weight": 0.7,
    "target_risky_weight": 0.6,
    "current_cash_weight": 0.3,
    "target_cash_weight": 0.4
  },
  "asset_reconciliation": [
    {
      "asset": "BNB-USD",
      "current_weight": 0.0,
      "canonical_target_weight": 0.299397,
      "adaptive_weight": 0.299397,
      "rebalance_target_weight": 0.080607,
      "canonical_delta": 0.299397,
      "rebalance_delta": 0.080607,
      "rebalance_action": "BUY",
      "target_matches_adaptive": true,
      "rebalance_target_current": false,
      "rebalance_delta_current": false,
      "canonical_current_source": "mark_to_market_v4",
      "canonical_target_source": "alpha_portfolio_v3"
    },
    {
      "asset": "BTC-USD",
      "current_weight": 0.350055,
      "canonical_target_weight": 0.0,
      "adaptive_weight": null,
      "rebalance_target_weight": 0.255809,
      "canonical_delta": -0.350055,
      "rebalance_delta": -0.094246,
      "rebalance_action": "SELL",
      "target_matches_adaptive": true,
      "rebalance_target_current": false,
      "rebalance_delta_current": false,
      "canonical_current_source": "portfolio_state_v4",
      "canonical_target_source": "alpha_portfolio_v3"
    },
    {
      "asset": "ETH-USD",
      "current_weight": 0.349945,
      "canonical_target_weight": 0.0,
      "adaptive_weight": null,
      "rebalance_target_weight": 0.255729,
      "canonical_delta": -0.349945,
      "rebalance_delta": -0.094216,
      "rebalance_action": "SELL",
      "target_matches_adaptive": true,
      "rebalance_target_current": false,
      "rebalance_delta_current": false,
      "canonical_current_source": "portfolio_state_v4",
      "canonical_target_source": "alpha_portfolio_v3"
    },
    {
      "asset": "LINK-USD",
      "current_weight": 0.0,
      "canonical_target_weight": 0.300603,
      "adaptive_weight": 0.300603,
      "rebalance_target_weight": 0.080932,
      "canonical_delta": 0.300603,
      "rebalance_delta": 0.080932,
      "rebalance_action": "BUY",
      "target_matches_adaptive": true,
      "rebalance_target_current": false,
      "rebalance_delta_current": false,
      "canonical_current_source": "mark_to_market_v4",
      "canonical_target_source": "alpha_portfolio_v3"
    }
  ],
  "canonical_trades": [
    {
      "asset": "BTC-USD",
      "action": "SELL",
      "current_weight": 0.350055,
      "target_weight": 0.0,
      "signed_delta": -0.350055,
      "weight_delta": 0.350055,
      "priority": 1,
      "reason": "Reconciled current broker/MTM state against the latest Alpha Portfolio target.",
      "source": "investment_intelligence_v2_1_reconciliation",
      "authoritative": true,
      "execution_instruction": false,
      "explanation": "SELL BTC-USD because the reconciled current weight is 35.0055% and the current canonical target is 0.0000%. Required change: -35.0055%."
    },
    {
      "asset": "ETH-USD",
      "action": "SELL",
      "current_weight": 0.349945,
      "target_weight": 0.0,
      "signed_delta": -0.349945,
      "weight_delta": 0.349945,
      "priority": 2,
      "reason": "Reconciled current broker/MTM state against the latest Alpha Portfolio target.",
      "source": "investment_intelligence_v2_1_reconciliation",
      "authoritative": true,
      "execution_instruction": false,
      "explanation": "SELL ETH-USD because the reconciled current weight is 34.9945% and the current canonical target is 0.0000%. Required change: -34.9945%."
    },
    {
      "asset": "LINK-USD",
      "action": "BUY",
      "current_weight": 0.0,
      "target_weight": 0.300603,
      "signed_delta": 0.300603,
      "weight_delta": 0.300603,
      "priority": 3,
      "reason": "Reconciled current broker/MTM state against the latest Alpha Portfolio target.",
      "source": "investment_intelligence_v2_1_reconciliation",
      "authoritative": true,
      "execution_instruction": false,
      "explanation": "BUY LINK-USD because the reconciled current weight is 0.0000% and the current canonical target is 30.0603%. Required change: 30.0603%."
    },
    {
      "asset": "BNB-USD",
      "action": "BUY",
      "current_weight": 0.0,
      "target_weight": 0.299397,
      "signed_delta": 0.299397,
      "weight_delta": 0.299397,
      "priority": 4,
      "reason": "Reconciled current broker/MTM state against the latest Alpha Portfolio target.",
      "source": "investment_intelligence_v2_1_reconciliation",
      "authoritative": true,
      "execution_instruction": false,
      "explanation": "BUY BNB-USD because the reconciled current weight is 0.0000% and the current canonical target is 29.9397%. Required change: 29.9397%."
    }
  ],
  "issues": [
    {
      "asset": "BNB-USD",
      "issue": "STALE_REBALANCE_TARGET",
      "canonical_target": 0.299397,
      "rebalance_target": 0.080607,
      "difference": 0.21879
    },
    {
      "asset": "BNB-USD",
      "issue": "STALE_REBALANCE_DELTA",
      "canonical_delta": 0.299397,
      "rebalance_delta": 0.080607,
      "difference": 0.21879
    },
    {
      "asset": "BTC-USD",
      "issue": "STALE_REBALANCE_TARGET",
      "canonical_target": 0.0,
      "rebalance_target": 0.255809,
      "difference": -0.255809
    },
    {
      "asset": "BTC-USD",
      "issue": "STALE_REBALANCE_DELTA",
      "canonical_delta": -0.350055,
      "rebalance_delta": -0.094246,
      "difference": -0.255809
    },
    {
      "asset": "ETH-USD",
      "issue": "STALE_REBALANCE_TARGET",
      "canonical_target": 0.0,
      "rebalance_target": 0.255729,
      "difference": -0.255729
    },
    {
      "asset": "ETH-USD",
      "issue": "STALE_REBALANCE_DELTA",
      "canonical_delta": -0.349945,
      "rebalance_delta": -0.094216,
      "difference": -0.255729
    },
    {
      "asset": "LINK-USD",
      "issue": "STALE_REBALANCE_TARGET",
      "canonical_target": 0.300603,
      "rebalance_target": 0.080932,
      "difference": 0.219671
    },
    {
      "asset": "LINK-USD",
      "issue": "STALE_REBALANCE_DELTA",
      "canonical_delta": 0.300603,
      "rebalance_delta": 0.080932,
      "difference": 0.219671
    }
  ],
  "source_manifest": [
    {
      "source": "portfolio_state",
      "path": "output\\investment_portfolio_state\\portfolio_state.json",
      "exists": true,
      "size_bytes": 2144,
      "modified_at": "2026-07-10T11:14:16.634633+00:00"
    },
    {
      "source": "portfolio_holdings",
      "path": "output\\investment_portfolio_state\\portfolio_holdings.csv",
      "exists": true,
      "size_bytes": 366,
      "modified_at": "2026-07-10T11:14:16.634633+00:00"
    },
    {
      "source": "mtm_report",
      "path": "output\\investment_mark_to_market\\mark_to_market_report.json",
      "exists": true,
      "size_bytes": 2393,
      "modified_at": "2026-07-10T11:14:06.222558+00:00"
    },
    {
      "source": "mtm_positions",
      "path": "output\\investment_mark_to_market\\positions.csv",
      "exists": true,
      "size_bytes": 390,
      "modified_at": "2026-07-10T11:14:06.214213+00:00"
    },
    {
      "source": "alpha_portfolio_report",
      "path": "output\\investment_alpha\\alpha_portfolio_report.json",
      "exists": true,
      "size_bytes": 701,
      "modified_at": "2026-07-10T11:14:12.286568+00:00"
    },
    {
      "source": "alpha_portfolio",
      "path": "output\\investment_alpha\\alpha_portfolio.csv",
      "exists": true,
      "size_bytes": 446,
      "modified_at": "2026-07-10T11:07:49.883309+00:00"
    },
    {
      "source": "adaptive_weighting_report",
      "path": "output\\investment_adaptive_weighting\\adaptive_weighting_report.json",
      "exists": true,
      "size_bytes": 2786,
      "modified_at": "2026-07-10T11:14:09.582640+00:00"
    },
    {
      "source": "adaptive_weights",
      "path": "output\\investment_adaptive_weighting\\adaptive_weights.csv",
      "exists": true,
      "size_bytes": 430,
      "modified_at": "2026-07-10T11:14:09.582640+00:00"
    },
    {
      "source": "rebalance_report",
      "path": "output\\investment_rebalance\\rebalance_report.json",
      "exists": true,
      "size_bytes": 4571,
      "modified_at": "2026-07-10T11:14:26.009866+00:00"
    },
    {
      "source": "rebalance_orders",
      "path": "output\\investment_rebalance\\rebalance_orders.csv",
      "exists": true,
      "size_bytes": 919,
      "modified_at": "2026-07-10T11:14:26.009866+00:00"
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

- Continue paper observation across all approved assets and timeframes.
