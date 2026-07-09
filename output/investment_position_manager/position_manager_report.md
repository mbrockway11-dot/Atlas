# Position Manager Report

Position Manager produced 8 position action(s). Rebalance action: BALANCED.

## Rebalance

```json
{
  "manager_action": "BALANCED",
  "reason": "Portfolio allocation is within operating band.",
  "risky_weight": 0.41436,
  "reserved_cash_weight": 0.076482,
  "cash_weight": 0.508328
}
```

## Actions

- `BTC-USD` action=`QUEUE_ENTRY` state=`APPROVED` reason=`Decision confidence supports entry.`
- `ETH-USD` action=`QUEUE_ENTRY` state=`APPROVED` reason=`Decision confidence supports entry.`
- `BTC-USD` action=`HOLD_SIZE` state=`OPEN` reason=`Portfolio exposure is within target band.`
- `ETH-USD` action=`HOLD_SIZE` state=`OPEN` reason=`Portfolio exposure is within target band.`
- `BTC-USD` action=`HOLD` state=`OPEN` reason=`No exit condition triggered.`
- `ETH-USD` action=`HOLD` state=`OPEN` reason=`No exit condition triggered.`
- `BTC-USD` action=`TRAILING_STOP_PENDING` state=`None` reason=`Trailing stop calculation will activate after price/cost-basis tracking is added.`
- `ETH-USD` action=`TRAILING_STOP_PENDING` state=`None` reason=`Trailing stop calculation will activate after price/cost-basis tracking is added.`
