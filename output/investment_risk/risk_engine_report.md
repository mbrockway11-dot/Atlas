# Risk Engine v2 Report

Risk Engine v2 classified portfolio as low_risk with score 0.028783.

## Aggregate

```json
{
  "aggregate_risk_score": 0.028783,
  "risk_label": "low_risk",
  "risk_breakdown": {
    "exposure": {
      "score": 0.0,
      "weight": 0.25,
      "weighted_score": 0.0
    },
    "concentration": {
      "score": 0.0,
      "weight": 0.2,
      "weighted_score": 0.0
    },
    "drawdown": {
      "score": 0.1,
      "weight": 0.2,
      "weighted_score": 0.02
    },
    "learning": {
      "score": 0.058555,
      "weight": 0.15,
      "weighted_score": 0.008783
    },
    "action": {
      "score": 0.0,
      "weight": 0.1,
      "weighted_score": 0.0
    },
    "rebalance": {
      "score": 0.0,
      "weight": 0.1,
      "weighted_score": 0.0
    }
  },
  "warnings": [
    "Paper PnL is slightly negative."
  ],
  "warning_count": 1
}
```

## Risk Blocks

- `exposure` score=`0.0` warnings=`0`
- `concentration` score=`0.0` warnings=`0`
- `drawdown` score=`0.1` warnings=`1`
- `learning` score=`0.058555` warnings=`0`
- `action` score=`0.0` warnings=`0`
- `rebalance` score=`0.0` warnings=`0`
