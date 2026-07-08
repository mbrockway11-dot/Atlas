# Investment Pipeline Expansion Plan

Expansion plan prepared for 11 target asset(s). Current: 3. Missing: 8.

## Target Asset Universe

```python
ASSETS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
    "LINK-USD",
    "AVAX-USD",
    "TRX-USD",
    "SUI-USD",
]
```

## Missing Assets

- `BNB-USD`
- `XRP-USD`
- `ADA-USD`
- `DOGE-USD`
- `LINK-USD`
- `AVAX-USD`
- `TRX-USD`
- `SUI-USD`

## Likely Sigil-Engine Files to Inspect

- `fetch_prices.py`
- `src/data/fetch_prices.py`
- `src/strategy/fetch_prices.py`
- `daily_runner_v5.py`
- `weekly_diagnostics_v5.py`
- `build_forward_outcomes.py`
- `pre_signal.py`
- `build_pre_signal_candidates.py`
- `build_pre_signal_candidates_v5.py`
- `backfill_live_signals_v5.py`
- `equity_curve_sim_v5.py`
- `equity_compare_runner_v5.py`

## Expansion Steps

### 1. Update asset universe

Find the asset list in sigil-engine and replace BTC/ETH/SOL with the expanded target universe.

### 2. Re-fetch price data

Run the sigil-engine price fetcher so output/price_data.csv contains all target assets.

- Expected output: `output/price_data.csv`

### 3. Rebuild leader-laggard summary

Run the leader-laggard pipeline against the expanded universe.

- Expected output: `output/leader_laggard_summary.csv`

### 4. Rebuild forward outcomes

Recalculate forward outcomes across the expanded asset set.

- Expected output: `output/forward_outcomes.csv`

### 5. Rebuild pre-signal candidates

Rebuild raw and filtered pre-signal candidates for the expanded universe.

- Expected outputs:
  - `output/pre_signal_raw.csv`
  - `output/pre_signal_candidates.csv`
  - `output/pre_signal_candidates_v5.csv`
  - `output/pre_signal_candidates_excess.csv`

### 6. Backfill live signals

Run the backfill process and compare trade count, win rate, and returns versus the old 3-asset sample.

- Expected output: `output/backfilled_live_signals_v5.csv`

### 7. Rerun equity simulations

Run equity curve and comparison scripts with asset caps adjusted for the expanded universe.

- Expected outputs:
  - `output/equity_curve_v5.csv`
  - `output/equity_compare_summary_v5.csv`
  - `output/equity_compare_trades_v5.csv`

### 8. Audit in Atlas

Rerun Investment Validation, Investment Regime Validation, and Asset Universe reports from Atlas.

## Atlas Validation Commands

```powershell
python scripts\investment_asset_universe_report.py --root "C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"
```
```powershell
python scripts\investment_system_audit.py --root "C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"
```
```powershell
python scripts\investment_regime_validation.py --root "C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"
```
```powershell
pytest
```
```powershell
python scripts\audit_dashboard_modernization.py
```
