# Daily Investment Runbook

Daily Investment Runbook completed 14 step(s). Decision: LONG confidence=0.819455 target_exposure=0.491673. Simulated filled weight=0.41519 cash=0.508328 cost_drag=0.00083038.

## Final Snapshot

```json
{
  "market_direction": {
    "market_direction": "LONG",
    "direction_confidence": 0.939394,
    "target_net_exposure": 0.8,
    "target_cash_weight": 0.2,
    "exposure_label": "aggressive_long"
  },
  "decision": {
    "final_direction": "LONG",
    "final_confidence": 0.819455,
    "target_net_exposure": 0.491673,
    "target_cash_weight": 0.508327,
    "risk_label": "moderate_risk",
    "confirmation_adjustment": {
      "status": "execution_idle",
      "confidence_multiplier": 0.85,
      "exposure_multiplier": 0.75,
      "reason": "Intraday execution engines are idle; reduce confidence and exposure."
    }
  },
  "execution_orders": [
    {
      "asset": "BTC-USD",
      "side": "LONG",
      "planned_weight": 0.223984,
      "order_action": "BUY",
      "execution_gate": "OPEN",
      "priority": 1,
      "reason": "No execution adapter signal for asset."
    },
    {
      "asset": "ETH-USD",
      "side": "LONG",
      "planned_weight": 0.191206,
      "order_action": "BUY",
      "execution_gate": "OPEN",
      "priority": 2,
      "reason": "No execution adapter signal for asset."
    },
    {
      "asset": "SOL-USD",
      "side": "LONG",
      "planned_weight": 0.076482,
      "order_action": "WAIT",
      "execution_gate": "WAIT",
      "priority": 3,
      "reason": "Execution engines are idle; wait for structure confirmation."
    },
    {
      "asset": "CASH",
      "side": "CASH",
      "planned_weight": 0.508328,
      "order_action": "NO_ORDER",
      "execution_gate": "OPEN",
      "priority": 999,
      "reason": "Cash row."
    }
  ],
  "simulation_summary": {
    "filled_weight": 0.41519,
    "cash_weight": 0.508328,
    "waiting_weight": 0.076482,
    "total_cost_drag": 0.00083038,
    "filled_count": 2,
    "waiting_count": 1,
    "warning_count": 1,
    "warnings": [
      "0.076482 planned weight is waiting for confirmation."
    ]
  },
  "simulation_fills": [
    {
      "asset": "BTC-USD",
      "side": "LONG",
      "order_action": "BUY",
      "execution_gate": "OPEN",
      "planned_weight": 0.223984,
      "simulated_fill_weight": 0.223984,
      "fill_status": "FILLED_SIMULATED",
      "fee_drag": 0.00017919,
      "slippage_drag": 0.00026878,
      "total_cost_drag": 0.00044797,
      "reason": "No execution adapter signal for asset."
    },
    {
      "asset": "ETH-USD",
      "side": "LONG",
      "order_action": "BUY",
      "execution_gate": "OPEN",
      "planned_weight": 0.191206,
      "simulated_fill_weight": 0.191206,
      "fill_status": "FILLED_SIMULATED",
      "fee_drag": 0.00015296,
      "slippage_drag": 0.00022945,
      "total_cost_drag": 0.00038241,
      "reason": "No execution adapter signal for asset."
    },
    {
      "asset": "SOL-USD",
      "side": "LONG",
      "order_action": "WAIT",
      "execution_gate": "WAIT",
      "planned_weight": 0.076482,
      "simulated_fill_weight": 0.0,
      "fill_status": "WAITING_FOR_CONFIRMATION",
      "fee_drag": 0.0,
      "slippage_drag": 0.0,
      "total_cost_drag": 0.0,
      "reason": "Execution engines are idle; wait for structure confirmation."
    },
    {
      "asset": "CASH",
      "side": "CASH",
      "order_action": "NO_ORDER",
      "execution_gate": "OPEN",
      "planned_weight": 0.508328,
      "simulated_fill_weight": 0.508328,
      "fill_status": "NO_FILL",
      "fee_drag": 0.0,
      "slippage_drag": 0.0,
      "total_cost_drag": 0.0,
      "reason": "Cash row."
    }
  ]
}
```

## Steps

### market_features

- Success: `True`
- Return code: `0`

```text
True
Market Feature Engine built 6743 asset-feature row(s) and 2281 market-feature row(s) across 3 asset(s).
Asset rows: 6743
Market rows: 2281
Assets: ['BTC-USD', 'ETH-USD', 'SOL-USD']
```

### alpha_hypotheses

- Success: `True`
- Return code: `0`

```text
True
Alpha Hypothesis Generator produced 36 candidate rule(s).
Families: {'momentum': 9, 'breadth': 15, 'leadership': 9, 'topology': 3}
JSON: output\investment_alpha\alpha_hypotheses.json
Markdown: output\investment_alpha\alpha_hypotheses.md
```

### alpha_backtests

- Success: `True`
- Return code: `0`

```text
True
Alpha Backtesting Engine evaluated 36 hypothesis/hypotheses. Top hypothesis: topology_low_density_leader_72.
JSON: output\investment_alpha\alpha_backtests.json
Rankings: output\investment_alpha\alpha_rankings.csv
Trades: output\investment_alpha\alpha_backtest_trades.csv
Markdown: output\investment_alpha\alpha_backtest_report.md
topology_low_density_leader_72 score= 5.893153 raw_trades= 633 raw_avg= 0.59543661 non_trades= 224 non_avg= 0.60674584 non_pf= 7.223237 concentration= 0.663507
leader_persistence_288_8 score= 4.13712 raw_trades= 1540 raw_avg= 1.09262675 non_trades= 136 non_avg= 1.23231271 non_pf= 8.9952 concentration= 0.570779
momentum_top_rank_72_q75 score= 4.06169 raw_trades= 871 raw_avg= 0.43058575 non_trades= 310 non_avg= 0.43469049 non_pf= 5.646926 concentration= 0.659013
momentum_top_rank_72_q50 score= 3.35111 raw_trades= 1344 raw_avg= 0.37929796 non_trades= 490 non_avg= 0.37945142 non_pf= 4.598652 concentration= 0.576637
breadth_positive_72_0_66 score= 3.070836 raw_trades= 1277 raw_avg= 0.3542796 non_trades= 475 non_avg= 0.34891834 non_pf= 4.234433 concentration= 0.581832
```

### alpha_validation

- Success: `True`
- Return code: `0`

```text
True
Promoted 9 alpha strategy/strategies. Rejected 16.
Validated: 25
Promoted: 9
Rejected: 16
```

### alpha_ensemble

- Success: `True`
- Return code: `0`

```text
True
Alpha Ensemble built 2971 historical signal row(s) from 9 promoted strategy/strategies.
Promoted strategies: 9
Signals: 2971
Votes: 11375
Latest: {'date': Timestamp('2026-03-04 00:00:00'), 'asset': 'SOL-USD', 'long_weight': 0.22065389115969808, 'short_weight': 0.0, 'total_weight': 0.22065389115969808, 'net_long_score': 0.22065389115969808, 'strategy_count': 2, 'active_strategies': ['breadth_positive_24_0_8', 'breadth_positive_24_1_0'], 'ensemble_confidence': 0.82, 'consensus_score': 1.0, 'breadth_score': 0.4, 'confidence_label': 'moderate_ensemble_signal'}
Outputs: {'signals_csv': 'output\\investment_alpha\\alpha_ensemble_signals.csv', 'weights_csv': 'output\\investment_alpha\\alpha_ensemble_weights.csv', 'json': 'output\\investment_alpha\\alpha_ensemble_report.json', 'markdown': 'output\\investment_alpha\\alpha_ensemble_report.md'}
```

### cross_sectional_ranker

- Success: `True`
- Return code: `0`

```text
True
Cross-Sectional Alpha Ranker scored 6743 asset-date row(s) across 3 asset(s). Latest date: 2026-03-31 00:00:00.
BTC-USD rank= 1.0 score= 0.6833333333333332 ensemble= 0.0 label= highest_conviction
ETH-USD rank= 2.0 score= 0.5833333333333334 ensemble= 0.0 label= portfolio_candidate
SOL-USD rank= 3.0 score= 0.23333333333333334 ensemble= 0.0 label= portfolio_candidate
Outputs: {'rankings_csv': 'output\\investment_alpha\\cross_sectional_alpha_rankings.csv', 'latest_csv': 'output\\investment_alpha\\cross_sectional_alpha_latest.csv', 'json': 'output\\investment_alpha\\cross_sectional_alpha_ranker_report.json', 'markdown': 'output\\investment_alpha\\cross_sectional_alpha_ranker_report.md'}
```

### alpha_portfolio

- Success: `True`
- Return code: `0`

```text
True
Alpha Portfolio constructed 4 row(s). Risk label: aggressive.
BTC-USD weight= 0.364444 rank= 1.0 label= highest_conviction
ETH-USD weight= 0.311111 rank= 2.0 label= portfolio_candidate
SOL-USD weight= 0.124444 rank= 3.0 label= portfolio_candidate
CASH weight= 0.2 rank= nan label= cash_buffer
Risk: {'success': True, 'asset_count': 3, 'total_risky_weight': 0.799999, 'cash_weight': 0.2, 'max_asset_weight': 0.364444, 'diversification_score': 0.531334, 'risk_label': 'aggressive'}
Outputs: {'portfolio_csv': 'output\\investment_alpha\\alpha_portfolio_latest.csv', 'json': 'output\\investment_alpha\\alpha_portfolio_report.json', 'markdown': 'output\\investment_alpha\\alpha_portfolio_report.md'}
```

### sigil_v32_adapter

- Success: `True`
- Return code: `0`

```text
True
Sigil V32 adapter translated 2 engine state row(s) from C:\Projects\sigil-engine-git.
{'source': 'sigil_v32', 'engine': 'ENGINE_A_PULLBACK_CONTINUATION', 'asset': 'SOL', 'timestamp': '2024-12-31 23:45:00+00:00', 'signal_state': 'IDLE', 'action': 'NO_ACTION', 'direction': 'FLAT', 'target_exposure': 0.0, 'entry_ready': False, 'setup_active': False, 'notes': 'No valid Engine A setup on the latest bar.'}
{'source': 'sigil_v32', 'engine': 'ENGINE_B_FAILED_OPENING_EXPANSION', 'asset': 'SOL', 'timestamp': '2024-12-31 23:45:00+00:00', 'signal_state': 'IDLE', 'action': 'NO_ACTION', 'direction': 'FLAT', 'target_exposure': 0.0, 'entry_ready': False, 'setup_active': False, 'notes': 'No valid Engine B setup on the latest bar.'}
Outputs: {'signals_csv': 'output\\investment_adapters\\sigil_v32\\sigil_v32_strategy_signals.csv', 'json': 'output\\investment_adapters\\sigil_v32\\sigil_v32_adapter_report.json', 'markdown': 'output\\investment_adapters\\sigil_v32\\sigil_v32_adapter_report.md'}
```

### strategy_registry

- Success: `True`
- Return code: `0`

```text
ntraday_execution': 2}, 'action_counts': {'ALLOCATE': 3, 'WATCH': 3, 'NO_ACTION': 2}, 'asset_counts': {'SOL-USD': 4, 'BTC-USD': 2, 'ETH-USD': 2}, 'unique_assets': ['BTC-USD', 'ETH-USD', 'SOL-USD']}
{'source': 'sigil_v32', 'strategy_id': 'ENGINE_A_PULLBACK_CONTINUATION', 'strategy_family': 'intraday_execution', 'asset': 'SOL-USD', 'timestamp': '2024-12-31 23:45:00+00:00', 'action': 'NO_ACTION', 'direction': 'FLAT', 'confidence': 0.0, 'target_exposure': 0.0, 'rank': None, 'notes': 'No valid Engine A setup on the latest bar.'}
{'source': 'sigil_v32', 'strategy_id': 'ENGINE_B_FAILED_OPENING_EXPANSION', 'strategy_family': 'intraday_execution', 'asset': 'SOL-USD', 'timestamp': '2024-12-31 23:45:00+00:00', 'action': 'NO_ACTION', 'direction': 'FLAT', 'confidence': 0.0, 'target_exposure': 0.0, 'rank': None, 'notes': 'No valid Engine B setup on the latest bar.'}
{'source': 'atlas_alpha', 'strategy_id': 'alpha_portfolio_construction', 'strategy_family': 'portfolio_allocation', 'asset': 'BTC-USD', 'timestamp': None, 'action': 'ALLOCATE', 'direction': 'LONG', 'confidence': 0.0, 'target_exposure': 0.364444, 'rank': 1.0, 'notes': 'Allocated by cross-sectional alpha score with max-asset cap.'}
{'source': 'atlas_alpha', 'strategy_id': 'alpha_portfolio_construction', 'strategy_family': 'portfolio_allocation', 'asset': 'ETH-USD', 'timestamp': None, 'action': 'ALLOCATE', 'direction': 'LONG', 'confidence': 0.0, 'target_exposure': 0.311111, 'rank': 2.0, 'notes': 'Allocated by cross-sectional alpha score with max-asset cap.'}
{'source': 'atlas_alpha', 'strategy_id': 'alpha_portfolio_construction', 'strategy_family': 'portfolio_allocation', 'asset': 'SOL-USD', 'timestamp': None, 'action': 'ALLOCATE', 'direction': 'LONG', 'confidence': 0.0, 'target_exposure': 0.124444, 'rank': 3.0, 'notes': 'Allocated by cross-sectional alpha score with max-asset cap.'}
{'source': 'atlas_alpha', 'strategy_id': 'cross_sectional_alpha_ranker', 'strategy_family': 'cross_sectional_ranking', 'asset': 'BTC-USD', 'timestamp': '2026-03-31', 'action': 'WATCH', 'direction': 'LONG', 'confidence': 0.6833333333333332, 'target_exposure': 0.0, 'rank': 1.0, 'notes': 'highest_conviction'}
{'source': 'atlas_alpha', 'strategy_id': 'cross_sectional_alpha_ranker', 'strategy_family': 'cross_sectional_ranking', 'asset': 'ETH-USD', 'timestamp': '2026-03-31', 'action': 'WATCH', 'direction': 'LONG', 'confidence': 0.5833333333333334, 'target_exposure': 0.0, 'rank': 2.0, 'notes': 'portfolio_candidate'}
{'source': 'atlas_alpha', 'strategy_id': 'cross_sectional_alpha_ranker', 'strategy_family': 'cross_sectional_ranking', 'asset': 'SOL-USD', 'timestamp': '2026-03-31', 'action': 'WATCH', 'direction': 'LONG', 'confidence': 0.2333333333333333, 'target_exposure': 0.0, 'rank': 3.0, 'notes': 'portfolio_candidate'}
Outputs:
 - output/investment_strategy_registry/strategy_registry_signals.csv
 - output/investment_strategy_registry/strategy_registry_report.json
 - output/investment_strategy_registry/strategy_registry_report.md
```

### adaptive_weighting

- Success: `True`
- Return code: `0`

```text
True
Adaptive Weighting produced 7 family weight(s).
portfolio_allocation 0.213973
cross_sectional_ranking 0.213973
intraday_execution 0.048908
momentum 0.117484
breadth 0.119484
leadership 0.125699
topology 0.160479
Outputs: {'json': 'output\\investment_adaptive\\adaptive_family_weights.json', 'csv': 'output\\investment_adaptive\\adaptive_family_weights.csv', 'markdown': 'output\\investment_adaptive\\adaptive_weighting_report.md'}
```

### market_direction

- Success: `True`
- Return code: `0`

```text
True
Market Direction Engine classified market as LONG with confidence 0.939394.
Vote: {'success': True, 'direction': 'LONG', 'confidence': 0.939394, 'long_score': 1.549999, 'short_score': 0.0, 'flat_score': 0.1, 'total_score': 1.649999, 'long_count': 6, 'short_count': 0, 'flat_count': 2}
Exposure: {'market_direction': 'LONG', 'direction_confidence': 0.939394, 'target_net_exposure': 0.8, 'target_cash_weight': 0.2, 'exposure_label': 'aggressive_long'}
Outputs: {'json': 'output\\investment_direction\\market_direction_report.json', 'markdown': 'output\\investment_direction\\market_direction_report.md', 'input_signals_csv': 'output\\investment_direction\\market_direction_input_signals.csv'}
```

### decision_engine

- Success: `True`
- Return code: `0`

```text
True
Decision Engine selected LONG with confidence 0.819455 and target exposure 0.491673.
Evidence: {'long_evidence': 0.492138, 'short_evidence': 0.0, 'flat_evidence': 0.009782, 'family_weights': {'portfolio_allocation': 0.213973, 'cross_sectional_ranking': 0.213973, 'intraday_execution': 0.048908, 'momentum': 0.117484, 'breadth': 0.119484, 'leadership': 0.125699, 'topology': 0.160479}}
Conflict: {'decision_bias': 'LONG', 'conflict_score': 0.0, 'net_evidence': 0.492138, 'evidence_confidence': 0.980511}
Decision: {'final_direction': 'LONG', 'final_confidence': 0.819455, 'target_net_exposure': 0.491673, 'target_cash_weight': 0.508327, 'risk_label': 'moderate_risk', 'confirmation_adjustment': {'status': 'execution_idle', 'confidence_multiplier': 0.85, 'exposure_multiplier': 0.75, 'reason': 'Intraday execution engines are idle; reduce confidence and exposure.'}}
Outputs: {'json': 'output\\investment_decision\\decision_engine_report.json', 'markdown': 'output\\investment_decision\\decision_engine_report.md', 'evidence_csv': 'output\\investment_decision\\decision_evidence.csv'}
```

### execution_planner

- Success: `True`
- Return code: `0`

```text
True
Execution Planner built 4 planned position row(s) and 4 order intent row(s).
Decision: {'final_direction': 'LONG', 'final_confidence': 0.819455, 'target_net_exposure': 0.491673, 'target_cash_weight': 0.508327, 'risk_label': 'moderate_risk', 'confirmation_adjustment': {'status': 'execution_idle', 'confidence_multiplier': 0.85, 'exposure_multiplier': 0.75, 'reason': 'Intraday execution engines are idle; reduce confidence and exposure.'}}
{'asset': 'BTC-USD', 'side': 'LONG', 'planned_weight': 0.223984, 'order_action': 'BUY', 'execution_gate': 'OPEN', 'priority': 1, 'reason': 'No execution adapter signal for asset.'}
{'asset': 'ETH-USD', 'side': 'LONG', 'planned_weight': 0.191206, 'order_action': 'BUY', 'execution_gate': 'OPEN', 'priority': 2, 'reason': 'No execution adapter signal for asset.'}
{'asset': 'SOL-USD', 'side': 'LONG', 'planned_weight': 0.076482, 'order_action': 'WAIT', 'execution_gate': 'WAIT', 'priority': 3, 'reason': 'Execution engines are idle; wait for structure confirmation.'}
{'asset': 'CASH', 'side': 'CASH', 'planned_weight': 0.508328, 'order_action': 'NO_ORDER', 'execution_gate': 'OPEN', 'priority': 999, 'reason': 'Cash row.'}
Outputs: {'plan_csv': 'output\\investment_execution\\execution_plan.csv', 'orders_csv': 'output\\investment_execution\\execution_order_intents.csv', 'json': 'output\\investment_execution\\execution_planner_report.json', 'markdown': 'output\\investment_execution\\execution_planner_report.md'}
```

### execution_simulator

- Success: `True`
- Return code: `0`

```text
True
Execution Simulator filled 2 order(s), waiting on 1, with estimated cost drag 0.00083038.
Summary: {'filled_weight': 0.41519, 'cash_weight': 0.508328, 'waiting_weight': 0.076482, 'total_cost_drag': 0.00083038, 'filled_count': 2, 'waiting_count': 1, 'warning_count': 1, 'warnings': ['0.076482 planned weight is waiting for confirmation.']}
{'asset': 'BTC-USD', 'side': 'LONG', 'order_action': 'BUY', 'execution_gate': 'OPEN', 'planned_weight': 0.223984, 'simulated_fill_weight': 0.223984, 'fill_status': 'FILLED_SIMULATED', 'fee_drag': 0.00017919, 'slippage_drag': 0.00026878, 'total_cost_drag': 0.00044797, 'reason': 'No execution adapter signal for asset.'}
{'asset': 'ETH-USD', 'side': 'LONG', 'order_action': 'BUY', 'execution_gate': 'OPEN', 'planned_weight': 0.191206, 'simulated_fill_weight': 0.191206, 'fill_status': 'FILLED_SIMULATED', 'fee_drag': 0.00015296, 'slippage_drag': 0.00022945, 'total_cost_drag': 0.00038241, 'reason': 'No execution adapter signal for asset.'}
{'asset': 'SOL-USD', 'side': 'LONG', 'order_action': 'WAIT', 'execution_gate': 'WAIT', 'planned_weight': 0.076482, 'simulated_fill_weight': 0.0, 'fill_status': 'WAITING_FOR_CONFIRMATION', 'fee_drag': 0.0, 'slippage_drag': 0.0, 'total_cost_drag': 0.0, 'reason': 'Execution engines are idle; wait for structure confirmation.'}
{'asset': 'CASH', 'side': 'CASH', 'order_action': 'NO_ORDER', 'execution_gate': 'OPEN', 'planned_weight': 0.508328, 'simulated_fill_weight': 0.508328, 'fill_status': 'NO_FILL', 'fee_drag': 0.0, 'slippage_drag': 0.0, 'total_cost_drag': 0.0, 'reason': 'Cash row.'}
Outputs: {'fills_csv': 'output\\investment_execution_simulator\\simulated_fills.csv', 'json': 'output\\investment_execution_simulator\\execution_simulator_report.json', 'markdown': 'output\\investment_execution_simulator\\execution_simulator_report.md'}
```
