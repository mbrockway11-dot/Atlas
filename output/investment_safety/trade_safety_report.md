# Trade Safety Governor Report

Trade Safety Governor status: APPROVED_WITH_WARNINGS. Decision: ALLOW_PAPER_EXECUTION. Reason: All hard safety checks passed with warnings..

## Checks

- `PASS` `order_count` ? Actionable order count 0 <= 5.
- `PASS` `shorts_disabled` ? No short orders present.
- `PASS` `single_asset_exposure` ? Max non-cash asset planned weight 0.094246 within limit.
- `PASS` `total_exposure` ? Filled exposure 0.161539 within limit.
- `PASS` `waiting_weight` ? Waiting weight 0.000000 within limit.
- `PASS` `cost_drag` ? Cost drag 0.00032307 within limit.
- `PASS` `paper_drawdown` ? Paper PnL acceptable: 0.000000.
- `PASS` `learning_regime` ? Learning regime acceptable: flat.
- `WARN` `execution_confirmation` ? Execution layer is idle; exposure should remain reduced.
- `PASS` `risk_engine_score` ? Risk Engine acceptable: score=0.113000, label=low_risk.
- `PASS` `mtm_gross_exposure` ? MTM gross exposure 0.700000 within limit.
- `PASS` `mtm_cash_reserve` ? MTM cash reserve 0.300000 above minimum.
- `PASS` `mtm_drawdown` ? MTM drawdown 0.000000 within limit.
