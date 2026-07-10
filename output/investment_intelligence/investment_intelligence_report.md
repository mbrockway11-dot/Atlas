# Atlas Investment Intelligence v1

Investment Intelligence v1 assessed portfolio confidence as MODERATE (0.615), system health as HEALTHY_WITH_WARNINGS, and explained 2 asset(s) and 2 trade action(s).

## Executive Assessment

- Overall confidence: `0.61485`
- Confidence label: `MODERATE`
- System health: `HEALTHY_WITH_WARNINGS`
- Equity: `100000.0`
- Risky exposure: `0.7`
- Cash exposure: `0.3`
- Learning regime: `insufficient_history`
- Risk label: `low_risk`

## Portfolio Explanation

The portfolio is 70.00% invested with 30.00% held in cash. The learning regime is insufficient_history. Overall confidence is MODERATE at 0.615. 2 rebalance order(s) are required to move the portfolio toward adaptive targets.

## Recommendations

- Continue paper observations before promoting strategy weights or enabling live capital.

## Health Checks

- `PASS` **accounting_reconciliation** ? Broker Ledger is mathematically reconciled.
- `PASS` **mark_to_market** ? Mark-to-Market v4 is healthy.
- `PASS` **portfolio_state** ? Portfolio State is available.
- `PASS` **performance** ? Performance Engine is healthy.
- `PASS` **learning** ? Learning Engine is healthy.
- `PASS` **risk** ? Risk Engine is healthy.
- `WARN` **trade_safety** ? Safety Governor approved with warnings.
- `PASS` **atlas_core** ? Atlas Core completed successfully.

## Asset Explanations

### BTC-USD

BTC-USD has an ensemble conviction score of 0.585 and registry status MAINTAIN. Reduce exposure by approximately 8.76%.

- Ensemble score: `0.585`
- Current weight: `0.350055`
- Target weight: `0.2625`
- Registry status: `MAINTAIN`

### ETH-USD

ETH-USD has an ensemble conviction score of 0.585 and registry status MAINTAIN. Reduce exposure by approximately 8.74%.

- Ensemble score: `0.585`
- Current weight: `0.349945`
- Target weight: `0.2625`
- Registry status: `MAINTAIN`

## Trade Explanations

- **SELL BTC-USD** ? SELL BTC-USD because its current portfolio weight is 35.0055% and its adaptive target is 26.2500%. Required change: -8.7555%.
- **SELL ETH-USD** ? SELL ETH-USD because its current portfolio weight is 34.9945% and its adaptive target is 26.2500%. Required change: -8.7445%.

## Changes Since Prior Run

- This is the first Investment Intelligence snapshot.
