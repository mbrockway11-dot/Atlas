# Decision Engine Report

Decision Engine selected LONG with confidence 0.923258 and target exposure 0.738606.

## Evidence

```json
{
  "long_evidence": 0.73,
  "short_evidence": 0.0,
  "flat_evidence": 0.07
}
```

## Conflict

```json
{
  "decision_bias": "LONG",
  "conflict_score": 0.0,
  "net_evidence": 0.73,
  "evidence_confidence": 0.9125
}
```

## Risk Adjusted Decision

```json
{
  "final_direction": "LONG",
  "final_confidence": 0.923258,
  "target_net_exposure": 0.738606,
  "target_cash_weight": 0.261394,
  "risk_label": "high_conviction_risk"
}
```

## Evidence Rows

- `sigil_v32` / `ENGINE_A_PULLBACK_CONTINUATION` asset=`SOL-USD` direction=`FLAT` strength=`0.035`
- `sigil_v32` / `ENGINE_B_FAILED_OPENING_EXPANSION` asset=`SOL-USD` direction=`FLAT` strength=`0.035`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`BTC-USD` direction=`LONG` strength=`0.127555`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`ETH-USD` direction=`LONG` strength=`0.108889`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`SOL-USD` direction=`LONG` strength=`0.043555`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`BTC-USD` direction=`LONG` strength=`0.205`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`ETH-USD` direction=`LONG` strength=`0.175`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`SOL-USD` direction=`LONG` strength=`0.07`
