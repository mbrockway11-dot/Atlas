# Decision Engine Report

Decision Engine selected LONG with confidence 0.819455 and target exposure 0.491673.

## Evidence

```json
{
  "long_evidence": 0.492138,
  "short_evidence": 0.0,
  "flat_evidence": 0.009782,
  "family_weights": {
    "portfolio_allocation": 0.213973,
    "cross_sectional_ranking": 0.213973,
    "intraday_execution": 0.048908,
    "momentum": 0.117484,
    "breadth": 0.119484,
    "leadership": 0.125699,
    "topology": 0.160479
  }
}
```

## Conflict

```json
{
  "decision_bias": "LONG",
  "conflict_score": 0.0,
  "net_evidence": 0.492138,
  "evidence_confidence": 0.980511
}
```

## Risk Adjusted Decision

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

## Evidence Rows

- `sigil_v32` / `ENGINE_A_PULLBACK_CONTINUATION` asset=`SOL-USD` direction=`FLAT` strength=`0.004891`
- `sigil_v32` / `ENGINE_B_FAILED_OPENING_EXPANSION` asset=`SOL-USD` direction=`FLAT` strength=`0.004891`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`BTC-USD` direction=`LONG` strength=`0.077981`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`ETH-USD` direction=`LONG` strength=`0.066569`
- `atlas_alpha` / `alpha_portfolio_construction` asset=`SOL-USD` direction=`LONG` strength=`0.026628`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`BTC-USD` direction=`LONG` strength=`0.146215`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`ETH-USD` direction=`LONG` strength=`0.124818`
- `atlas_alpha` / `cross_sectional_alpha_ranker` asset=`SOL-USD` direction=`LONG` strength=`0.049927`
