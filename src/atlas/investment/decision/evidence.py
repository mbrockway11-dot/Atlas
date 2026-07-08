
"""Decision evidence scoring."""

from __future__ import annotations

import pandas as pd


FAMILY_WEIGHTS = {
    "portfolio_allocation": 0.35,
    "cross_sectional_ranking": 0.30,
    "intraday_execution": 0.35,
}


def build_evidence_scores(registry: pd.DataFrame) -> dict:
    if registry.empty:
        return {
            "long_evidence": 0.0,
            "short_evidence": 0.0,
            "flat_evidence": 0.0,
            "evidence_rows": [],
        }

    df = registry.copy()
    df["direction"] = df["direction"].fillna("FLAT").astype(str).str.upper()
    df["action"] = df["action"].fillna("NO_ACTION").astype(str).str.upper()
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)
    df["target_exposure"] = pd.to_numeric(df["target_exposure"], errors="coerce").fillna(0.0)

    rows = []
    long_evidence = 0.0
    short_evidence = 0.0
    flat_evidence = 0.0

    for _, row in df.iterrows():
        family = row.get("strategy_family")
        weight = FAMILY_WEIGHTS.get(family, 0.10)

        exposure_component = abs(float(row.get("target_exposure") or 0.0))
        confidence_component = float(row.get("confidence") or 0.0)

        strength = weight * max(exposure_component, confidence_component, 0.10)

        direction = str(row.get("direction") or "FLAT").upper()
        action = str(row.get("action") or "NO_ACTION").upper()

        if direction == "LONG" or action in {"ALLOCATE", "WATCH", "BUY", "LONG"}:
            long_evidence += strength
            evidence_direction = "LONG"
        elif direction == "SHORT" or action in {"SELL", "SHORT"}:
            short_evidence += strength
            evidence_direction = "SHORT"
        else:
            flat_evidence += strength
            evidence_direction = "FLAT"

        rows.append({
            "source": row.get("source"),
            "strategy_id": row.get("strategy_id"),
            "strategy_family": family,
            "asset": row.get("asset"),
            "direction": evidence_direction,
            "raw_direction": direction,
            "action": action,
            "weight": round(weight, 6),
            "strength": round(float(strength), 6),
            "confidence": confidence_component,
            "target_exposure": exposure_component,
            "notes": row.get("notes"),
        })

    return {
        "long_evidence": round(float(long_evidence), 6),
        "short_evidence": round(float(short_evidence), 6),
        "flat_evidence": round(float(flat_evidence), 6),
        "evidence_rows": rows,
    }
