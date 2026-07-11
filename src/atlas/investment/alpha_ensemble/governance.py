"""Research-governed engine admission for Alpha Ensemble v6.1."""

from __future__ import annotations

import math

import pandas as pd

from atlas.investment.alpha_ensemble.modifiers import (
    build_learning_modifier_map,
    build_regime_modifier_map,
)


ELIGIBLE_DECISIONS = {
    "PROMOTE",
    "KEEP",
}


GOVERNANCE_COLUMNS = [
    "engine_id",
    "family",
    "decision",
    "eligible",
    "base_governance_weight",
    "learning_raw_multiplier",
    "learning_modifier",
    "learning_recommendation",
    "learning_reliability",
    "regime_raw_suitability",
    "regime_modifier",
    "market_regime",
    "regime_confidence",
    "combined_modifier",
    "governance_weight",
    "promotion_score",
    "performance_score",
    "stability_score",
    "risk_score",
    "independence_score",
    "portfolio_sharpe",
    "portfolio_recovery_factor",
    "hard_failures",
]


def build_engine_governance(
    decisions: pd.DataFrame,
    learning_recommendations: pd.DataFrame | None = None,
    regime_suitability: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build Research Lab admission with bounded adaptive modifiers."""
    if decisions is None or decisions.empty:
        return pd.DataFrame(
            columns=GOVERNANCE_COLUMNS
        )

    frame = decisions.copy()

    if "engine_id" not in frame.columns:
        return pd.DataFrame(
            columns=GOVERNANCE_COLUMNS
        )

    frame["engine_id"] = (
        frame["engine_id"]
        .astype(str)
    )

    if "decision" not in frame.columns:
        frame["decision"] = "RETIRE"

    frame["decision"] = (
        frame["decision"]
        .fillna("RETIRE")
        .astype(str)
        .str.upper()
    )

    numeric_columns = [
        "promotion_score",
        "performance_score",
        "stability_score",
        "risk_score",
        "independence_score",
        "portfolio_sharpe",
        "portfolio_recovery_factor",
    ]

    for column in numeric_columns:
        if column not in frame.columns:
            frame[column] = 0.0

        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        ).fillna(0.0)

    if "family" not in frame.columns:
        frame["family"] = "unknown"

    frame["family"] = (
        frame["family"]
        .fillna("unknown")
        .astype(str)
    )

    if "hard_failures" not in frame.columns:
        frame["hard_failures"] = ""

    frame["hard_failures"] = (
        frame["hard_failures"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    frame["eligible"] = (
        frame["decision"].isin(
            ELIGIBLE_DECISIONS
        )
        & frame["hard_failures"].eq("")
    )

    learning_map = build_learning_modifier_map(
        learning_recommendations
    )

    regime_map = build_regime_modifier_map(
        regime_suitability
    )

    rows: list[dict] = []

    for _, row in frame.iterrows():
        engine_id = str(
            row["engine_id"]
        )

        eligible = bool(
            row["eligible"]
        )

        base_weight = (
            calculate_base_governance_weight(
                row
            )
            if eligible
            else 0.0
        )

        learning = learning_map.get(
            engine_id,
            {
                "learning_raw_multiplier": 1.0,
                "learning_modifier": 1.0,
                "learning_recommendation": (
                    "NO_LEARNING_INPUT"
                ),
                "learning_reliability": 0.0,
            },
        )

        regime = regime_map.get(
            engine_id,
            {
                "regime_raw_suitability": 0.50,
                "regime_modifier": 1.0,
                "market_regime": "UNKNOWN",
                "regime_confidence": 0.0,
            },
        )

        combined_modifier = (
            finite(
                learning.get(
                    "learning_modifier"
                ),
                default=1.0,
            )
            * finite(
                regime.get(
                    "regime_modifier"
                ),
                default=1.0,
            )
        )

        adjusted_weight = (
            base_weight
            * combined_modifier
            if eligible
            else 0.0
        )

        rows.append({
            **row.to_dict(),
            "base_governance_weight": (
                base_weight
            ),
            **learning,
            **regime,
            "combined_modifier": (
                combined_modifier
            ),
            "governance_weight": (
                adjusted_weight
            ),
        })

    result = pd.DataFrame(
        rows
    )

    eligible_total = float(
        result.loc[
            result["eligible"],
            "governance_weight",
        ].sum()
    )

    if eligible_total > 0:
        result.loc[
            result["eligible"],
            "governance_weight",
        ] = (
            result.loc[
                result["eligible"],
                "governance_weight",
            ]
            / eligible_total
        )

    result.loc[
        ~result["eligible"],
        [
            "base_governance_weight",
            "governance_weight",
        ],
    ] = 0.0

    for column in [
        "base_governance_weight",
        "learning_raw_multiplier",
        "learning_modifier",
        "learning_reliability",
        "regime_raw_suitability",
        "regime_modifier",
        "regime_confidence",
        "combined_modifier",
        "governance_weight",
    ]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).fillna(0.0).round(8)

    for column in GOVERNANCE_COLUMNS:
        if column not in result.columns:
            result[column] = None

    return result[
        GOVERNANCE_COLUMNS
    ].sort_values(
        [
            "eligible",
            "governance_weight",
            "engine_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def calculate_base_governance_weight(
    row: pd.Series,
) -> float:
    """Build the original Research Lab reliability weight."""
    if str(
        row.get("decision", "")
    ).upper() not in ELIGIBLE_DECISIONS:
        return 0.0

    hard_failures = row.get(
        "hard_failures",
        "",
    )

    if (
        not pd.isna(hard_failures)
        and str(hard_failures).strip()
    ):
        return 0.0

    promotion = clamp(
        finite(
            row.get("promotion_score")
        )
    )

    performance = clamp(
        finite(
            row.get("performance_score")
        )
    )

    stability = clamp(
        finite(
            row.get("stability_score")
        )
    )

    risk = clamp(
        finite(
            row.get("risk_score")
        )
    )

    independence = clamp(
        finite(
            row.get("independence_score")
        )
    )

    sharpe = clamp(
        finite(
            row.get(
                "portfolio_sharpe"
            )
        ) / 1.5
    )

    recovery = clamp(
        finite(
            row.get(
                "portfolio_recovery_factor"
            )
        ) / 2.0
    )

    decision_multiplier = (
        1.0
        if str(
            row.get("decision")
        ).upper() == "PROMOTE"
        else 0.65
    )

    score = (
        promotion * 0.30
        + performance * 0.20
        + stability * 0.15
        + risk * 0.10
        + independence * 0.10
        + sharpe * 0.10
        + recovery * 0.05
    )

    return max(
        0.0,
        score * decision_multiplier,
    )


# Backward-compatible alias.
calculate_governance_weight = (
    calculate_base_governance_weight
)


def governance_by_engine(
    governance: pd.DataFrame,
) -> dict[str, dict]:
    if (
        governance is None
        or governance.empty
    ):
        return {}

    return {
        str(
            row["engine_id"]
        ): row.to_dict()
        for _, row in governance.iterrows()
    }


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
            float(value),
        ),
    )
