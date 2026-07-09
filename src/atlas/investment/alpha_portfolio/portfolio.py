
"""Alpha Portfolio v3 construction."""

from __future__ import annotations

import pandas as pd


def build_alpha_portfolio(inputs: dict) -> dict:
    weights = inputs.get("adaptive_weights")

    rows = []

    if weights is not None and not weights.empty:
        for _, row in weights.iterrows():
            asset = str(row.get("asset"))
            target_weight = float(row.get("adaptive_weight") or 0.0)

            rows.append({
                "asset": asset,
                "target_weight": round(target_weight, 6),
                "paper_weight": round(target_weight, 6),
                "weight": round(target_weight, 6),
                "allocation": round(target_weight, 6),
                "target_exposure": round(target_weight, 6),
                "source": "adaptive_weighting_v3",
                "base_weight": round(float(row.get("base_weight") or 0.0), 6),
                "registry_multiplier": round(float(row.get("registry_multiplier") or 1.0), 6),
                "regime_multiplier": round(float(row.get("regime_multiplier") or 1.0), 6),
            })

    if not rows:
        rows = [{"asset": "CASH", "target_weight": 1.0, "paper_weight": 1.0, "weight": 1.0, "allocation": 1.0, "target_exposure": 1.0, "source": "fallback_cash"}]

    risky = sum(r["target_weight"] for r in rows if r["asset"] != "CASH")
    cash = next((r["target_weight"] for r in rows if r["asset"] == "CASH"), max(0.0, 1.0 - risky))

    return {
        "rows": rows,
        "summary": {
            "asset_count": len(rows),
            "risky_weight": round(risky, 6),
            "cash_weight": round(cash, 6),
            "gross_exposure": round(risky, 6),
            "source": "adaptive_weighting_v3",
        },
    }
