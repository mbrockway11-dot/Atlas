# Execution Planner Report

Execution Planner built 4 planned position row(s) and 4 order intent row(s).

## Decision

```json
{
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
}
```

## Order Intents

- `BTC-USD` action=`BUY` side=`LONG` weight=`0.223984` gate=`OPEN`
- `ETH-USD` action=`BUY` side=`LONG` weight=`0.191206` gate=`OPEN`
- `SOL-USD` action=`WAIT` side=`LONG` weight=`0.076482` gate=`WAIT`
- `CASH` action=`NO_ORDER` side=`CASH` weight=`0.508328` gate=`OPEN`
