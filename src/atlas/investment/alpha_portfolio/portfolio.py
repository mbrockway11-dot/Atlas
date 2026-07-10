
"""Alpha Portfolio v3.1 construction.

Adaptive Weighting v4 is already risk-adjusted and normalized. Alpha
Portfolio must preserve those weights exactly rather than applying another
risk or cash multiplier.
"""

from __future__ import annotations

import math

import pandas as pd


TOLERANCE = 0.000001


def build_alpha_portfolio(inputs: dict) -> dict:
    weights = inputs.get("adaptive_weights")

    if (
        weights is None
        or weights.empty
        or "asset" not in weights.columns
        or "adaptive_weight" not in weights.columns
    ):
        return fallback_cash_portfolio(
            "Adaptive Weighting v4 output unavailable."
        )

    frame = weights.copy()
    frame["asset"] = frame["asset"].astype(str)
    frame["adaptive_weight"] = pd.to_numeric(
        frame["adaptive_weight"],
        errors="coerce",
    ).fillna(0.0)

    frame = frame.drop_duplicates(
        subset=["asset"],
        keep="last",
    )

    rows = []

    for _, row in frame.iterrows():
        asset = str(row.get("asset", "")).strip()
        target_weight = finite_number(
            row.get("adaptive_weight")
        )

        if not asset:
            continue

        rows.append({
            "asset": asset,
            "target_weight": round(target_weight, 6),
            "paper_weight": round(target_weight, 6),
            "weight": round(target_weight, 6),
            "allocation": round(target_weight, 6),
            "target_exposure": round(target_weight, 6),
            "adaptive_weight": round(target_weight, 6),
            "source": "adaptive_weighting_v4_passthrough",
            "base_weight": round(
                finite_number(row.get("base_weight")),
                6,
            ),
            "registry_multiplier": round(
                finite_number(
                    row.get("registry_multiplier"),
                    default=1.0,
                ),
                6,
            ),
            "regime_multiplier": round(
                finite_number(
                    row.get("regime_multiplier"),
                    default=1.0,
                ),
                6,
            ),
        })

    if not rows:
        return fallback_cash_portfolio(
            "Adaptive Weighting contained no usable rows."
        )

    risky = sum(
        row["target_weight"]
        for row in rows
        if row["asset"].upper() != "CASH"
    )

    cash_rows = [
        row
        for row in rows
        if row["asset"].upper() == "CASH"
    ]

    if cash_rows:
        cash = cash_rows[-1]["target_weight"]
    else:
        cash = max(0.0, 1.0 - risky)
        rows.append({
            "asset": "CASH",
            "target_weight": round(cash, 6),
            "paper_weight": round(cash, 6),
            "weight": round(cash, 6),
            "allocation": round(cash, 6),
            "target_exposure": round(cash, 6),
            "adaptive_weight": round(cash, 6),
            "source": "adaptive_weighting_v4_derived_cash",
            "base_weight": round(cash, 6),
            "registry_multiplier": 1.0,
            "regime_multiplier": 1.0,
        })

    total = risky + cash
    passthrough_matches = validate_passthrough(
        rows,
        frame,
    )

    issues = []

    if abs(total - 1.0) > 0.0001:
        issues.append({
            "issue": "PORTFOLIO_WEIGHT_SUM_MISMATCH",
            "total_weight": round(total, 6),
        })

    if not passthrough_matches:
        issues.append({
            "issue": "ADAPTIVE_PASSTHROUGH_MISMATCH",
        })

    return {
        "success": len(issues) == 0,
        "rows": rows,
        "issues": issues,
        "summary": {
            "asset_count": len(rows),
            "risky_weight": round(risky, 6),
            "cash_weight": round(cash, 6),
            "gross_exposure": round(risky, 6),
            "total_weight": round(total, 6),
            "source": "adaptive_weighting_v4_passthrough",
            "adaptive_passthrough_valid": (
                passthrough_matches
            ),
            "second_risk_scaling_applied": False,
        },
    }


def validate_passthrough(
    rows: list[dict],
    source: pd.DataFrame,
) -> bool:
    source_weights = {
        str(row.get("asset")): finite_number(
            row.get("adaptive_weight")
        )
        for _, row in source.iterrows()
    }

    for row in rows:
        asset = row["asset"]

        if asset not in source_weights:
            continue

        if abs(
            row["target_weight"]
            - source_weights[asset]
        ) > TOLERANCE:
            return False

    return True


def fallback_cash_portfolio(
    reason: str,
) -> dict:
    row = {
        "asset": "CASH",
        "target_weight": 1.0,
        "paper_weight": 1.0,
        "weight": 1.0,
        "allocation": 1.0,
        "target_exposure": 1.0,
        "adaptive_weight": 1.0,
        "source": "fallback_cash",
        "base_weight": 1.0,
        "registry_multiplier": 1.0,
        "regime_multiplier": 1.0,
    }

    return {
        "success": False,
        "rows": [row],
        "issues": [{
            "issue": "ADAPTIVE_WEIGHTING_UNAVAILABLE",
            "reason": reason,
        }],
        "summary": {
            "asset_count": 1,
            "risky_weight": 0.0,
            "cash_weight": 1.0,
            "gross_exposure": 0.0,
            "total_weight": 1.0,
            "source": "fallback_cash",
            "adaptive_passthrough_valid": False,
            "second_risk_scaling_applied": False,
        },
    }


def finite_number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    return result if math.isfinite(result) else default
