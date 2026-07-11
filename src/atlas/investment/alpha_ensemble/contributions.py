"""Per-asset engine contribution ledger for Ensemble Intelligence v7."""

from __future__ import annotations

import math

import pandas as pd


def build_contribution_ledger(
    signals: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate every eligible engine's contribution to each asset."""
    columns = [
        "asset",
        "engine_id",
        "family",
        "decision",
        "direction",
        "normalized_score",
        "signal_confidence",
        "governance_weight",
        "weighted_contribution",
        "signed_contribution",
        "contribution_share",
        "reason_codes",
        "source",
    ]

    if (
        signals is None
        or signals.empty
        or governance is None
        or governance.empty
    ):
        return pd.DataFrame(
            columns=columns
        )

    required = {
        "asset",
        "engine_id",
        "normalized_score",
    }

    if not required.issubset(
        signals.columns
    ):
        return pd.DataFrame(
            columns=columns
        )

    eligible = governance[
        governance["eligible"]
    ].copy()

    if eligible.empty:
        return pd.DataFrame(
            columns=columns
        )

    governance_map = {
        str(
            row["engine_id"]
        ): row.to_dict()
        for _, row in eligible.iterrows()
    }

    rows: list[dict] = []

    for _, signal in signals.iterrows():
        engine_id = str(
            signal.get("engine_id")
        )

        policy = governance_map.get(
            engine_id
        )

        if not policy:
            continue

        score = clamp(
            finite(
                signal.get(
                    "normalized_score"
                ),
                default=0.5,
            )
        )

        signal_confidence = clamp(
            finite(
                signal.get(
                    "confidence"
                ),
                default=1.0,
            )
        )

        governance_weight = clamp(
            finite(
                policy.get(
                    "governance_weight"
                )
            )
        )

        weighted = (
            score
            * signal_confidence
            * governance_weight
        )

        signed = (
            score - 0.5
        ) * 2.0 * signal_confidence * governance_weight

        rows.append({
            "asset": str(
                signal.get("asset")
            ),
            "engine_id": engine_id,
            "family": str(
                policy.get(
                    "family",
                    "unknown",
                )
            ),
            "decision": str(
                policy.get(
                    "decision",
                    "",
                )
            ),
            "direction": str(
                signal.get(
                    "direction",
                    "NEUTRAL",
                )
            ),
            "normalized_score": round(
                score,
                8,
            ),
            "signal_confidence": round(
                signal_confidence,
                8,
            ),
            "governance_weight": round(
                governance_weight,
                8,
            ),
            "weighted_contribution": round(
                weighted,
                8,
            ),
            "signed_contribution": round(
                signed,
                8,
            ),
            "contribution_share": 0.0,
            "reason_codes": str(
                signal.get(
                    "reason_codes",
                    "",
                )
            ),
            "source": (
                "ensemble_intelligence_v7"
            ),
        })

    result = pd.DataFrame(
        rows,
        columns=columns,
    )

    if result.empty:
        return result

    totals = (
        result.groupby(
            "asset"
        )[
            "weighted_contribution"
        ]
        .transform("sum")
    )

    result["contribution_share"] = (
        result["weighted_contribution"]
        / totals.where(
            totals.abs() > 1e-12,
            1.0,
        )
    ).round(8)

    return result.sort_values(
        [
            "asset",
            "weighted_contribution",
            "engine_id",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def clamp(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            finite(value),
        ),
    )
