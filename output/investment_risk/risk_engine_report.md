# Risk Engine v3 Report

Risk Engine v3 classified MTM portfolio as low_risk with score 0.113.

## Aggregate

```json
{
  "aggregate_risk_score": 0.113,
  "risk_label": "low_risk",
  "risk_breakdown": {
    "exposure": {
      "score": 0.25,
      "weight": 0.22,
      "weighted_score": 0.055
    },
    "concentration": {
      "score": 0.25,
      "weight": 0.16,
      "weighted_score": 0.04
    },
    "drawdown": {
      "score": 0.0,
      "weight": 0.22,
      "weighted_score": 0.0
    },
    "mtm_position": {
      "score": 0.0,
      "weight": 0.14,
      "weighted_score": 0.0
    },
    "learning": {
      "score": 0.15,
      "weight": 0.12,
      "weighted_score": 0.018
    },
    "action": {
      "score": 0.0,
      "weight": 0.07,
      "weighted_score": 0.0
    },
    "rebalance": {
      "score": 0.0,
      "weight": 0.07,
      "weighted_score": 0.0
    }
  },
  "warnings": [
    "MTM gross exposure above 65%.",
    "Largest MTM position above 30%.",
    "Learning regime is flat."
  ],
  "warning_count": 3,
  "source": "risk_engine_v3_mtm"
}
```

## Risk Blocks

- `exposure` score=`0.25` warnings=`1`
- `concentration` score=`0.25` warnings=`1`
- `drawdown` score=`0.0` warnings=`0`
- `mtm_position` score=`0.0` warnings=`0`
- `learning` score=`0.15` warnings=`1`
- `action` score=`0.0` warnings=`0`
- `rebalance` score=`0.0` warnings=`0`
