
"""Learning Engine v3 adaptive recommendations."""

from __future__ import annotations


def build_adaptive_recommendations(regime: dict, scorecard: list[dict], risk: dict) -> list[str]:
    recs = []

    learning_regime = regime.get("learning_regime")
    risk_label = (risk.get("aggregate", {}) or {}).get("risk_label", "unknown")

    if learning_regime == "insufficient_history":
        recs.append("Accumulate more broker-authoritative MTM history before changing strategy weights.")
    elif learning_regime == "improving":
        recs.append("Maintain or cautiously increase exposure if Safety Governor remains permissive.")
    elif learning_regime == "deteriorating":
        recs.append("Reduce exposure and require stronger confirmation before new entries.")
    else:
        recs.append("Maintain current exposure while monitoring equity curve and attribution.")

    if risk_label in {"high_risk", "critical_risk"}:
        recs.append(f"Risk label is {risk_label}; override learning promotions and preserve capital.")
    elif risk_label == "moderate_risk":
        recs.append("Risk is moderate; cap position increases until drawdown and volatility improve.")

    promoted = [s["asset"] for s in scorecard if s.get("recommendation") == "promote"]
    reduced = [s["asset"] for s in scorecard if s.get("recommendation") == "reduce"]

    if promoted:
        recs.append("Asset confidence positive: " + ", ".join(promoted) + ".")
    if reduced:
        recs.append("Asset confidence weak: " + ", ".join(reduced) + ".")

    return recs


def aggregate_learning_confidence(regime: dict, scorecard: list[dict]) -> float:
    regime_conf = float(regime.get("confidence") or 0.0)

    if not scorecard:
        return round(regime_conf, 6)

    asset_conf = sum(float(s.get("asset_confidence") or 0.0) for s in scorecard) / len(scorecard)

    return round((regime_conf * 0.60) + (asset_conf * 0.40), 6)
