# Trade Safety Governor Report

Trade Safety Governor status: REJECTED. Decision: BLOCK_EXECUTION. Reason: Single asset planned weight 0.508328 exceeds limit 0.3..

## Checks

- `PASS` `order_count` ? Actionable order count 2 <= 5.
- `PASS` `shorts_disabled` ? No short orders present.
- `REJECT` `single_asset_exposure` ? Single asset planned weight 0.508328 exceeds limit 0.3.
- `PASS` `total_exposure` ? Filled exposure 0.415190 within limit.
- `PASS` `cash_reserve` ? Cash reserve 0.508328 above minimum.
- `PASS` `waiting_weight` ? Waiting weight 0.076482 within limit.
- `PASS` `cost_drag` ? Cost drag 0.00083038 within limit.
- `PASS` `paper_drawdown` ? Paper PnL acceptable: -0.000830.
- `PASS` `learning_regime` ? Learning regime acceptable: improving.
- `WARN` `execution_confirmation` ? Execution layer is idle; exposure should remain reduced.
