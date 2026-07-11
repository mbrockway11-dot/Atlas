"""Research-governed engine admission for Ensemble Intelligence v7."""

from __future__ import annotations

import math

import pandas as pd

from atlas.investment.alpha_ensemble.modifiers import (
    build_fusion_modifier_map,
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
    "fusion_raw_modifier",
    "fusion_modifier",
    "fused_regime",
    "fusion_confidence",
    "family_engine_count",
    "diversification_modifier",
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
    context_modifiers: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build hard-gated, context-aware, diversified governance."""
    if decisions is None or decisions.empty:
        return pd.DataFrame(
            columns=GOVERNANCE_COLUMNS
        )

    frame = normalize_decisions(
        decisions
    )

    learning_map = build_learning_modifier_map(
        learning_recommendations
    )

    regime_map = build_regime_modifier_map(
        regime_suitability
    )

    fusion_map = build_fusion_modifier_map(
        context_modifiers
    )

    family_counts = (
        frame.loc[
            frame["eligible"]
        ][
            "family"
        ]
        .value_counts()
        .to_dict()
    )

    rows: list[dict] = []

    for _, row in frame.iterrows():
        engine_id = str(
            row["engine_id"]
        )

        family = str(
            row.get(
                "family",
                "unknown",
            )
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
            default_learning(),
        )

        regime = regime_map.get(
            engine_id,
            default_regime(),
        )

        fusion = fusion_map.get(
            engine_id,
            default_fusion(),
        )

        family_count = int(
            family_counts.get(
                family,
                0,
            )
        )

        diversification_modifier = (
            calculate_diversification_modifier(
                family_count
            )
            if eligible
            else 0.0
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
            * finite(
                fusion.get(
                    "fusion_modifier"
                ),
                default=1.0,
            )
            * diversification_modifier
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
            **fusion,
            "family_engine_count": (
                family_count
            ),
            "diversification_modifier": (
                diversification_modifier
            ),
            "combined_modifier": (
                combined_modifier
            ),
            "governance_weight": (
                adjusted_weight
            ),
        })

    result = pd.DataFrame(rows)

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

    numeric_columns = [
        "base_governance_weight",
        "learning_raw_multiplier",
        "learning_modifier",
        "learning_reliability",
        "regime_raw_suitability",
        "regime_modifier",
        "regime_confidence",
        "fusion_raw_modifier",
        "fusion_modifier",
        "fusion_confidence",
        "family_engine_count",
        "diversification_modifier",
        "combined_modifier",
        "governance_weight",
    ]

    for column in numeric_columns:
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


def normalize_decisions(
    decisions: pd.DataFrame,
) -> pd.DataFrame:
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

    for column in [
        "promotion_score",
        "performance_score",
        "stability_score",
        "risk_score",
        "independence_score",
        "portfolio_sharpe",
        "portfolio_recovery_factor",
    ]:
        if column not in frame.columns:
            frame[column] = 0.0

        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        ).fillna(0.0)

    frame["eligible"] = (
        frame["decision"].isin(
            ELIGIBLE_DECISIONS
        )
        & frame["hard_failures"].eq("")
    )

    return frame


def calculate_diversification_modifier(
    family_count: int,
) -> float:
    """Penalize duplicate eligible engines from the same family."""
    if family_count <= 1:
        return 1.0

    return max(
        0.70,
        1.0
        - 0.10
        * (
            family_count - 1
        ),
    )


def calculate_base_governance_weight(
    row: pd.Series,
) -> float:
    if str(
        row.get("decision", "")
    ).upper() not in ELIGIBLE_DECISIONS:
        return 0.0

    if str(
        row.get(
            "hard_failures",
            "",
        )
    ).strip():
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


def default_learning() -> dict:
    return {
        "learning_raw_multiplier": 1.0,
        "learning_modifier": 1.0,
        "learning_recommendation": (
            "NO_LEARNING_INPUT"
        ),
        "learning_reliability": 0.0,
    }


def default_regime() -> dict:
    return {
        "regime_raw_suitability": 0.50,
        "regime_modifier": 1.0,
        "market_regime": "UNKNOWN",
        "regime_confidence": 0.0,
    }


def default_fusion() -> dict:
    return {
        "fusion_raw_modifier": 1.0,
        "fusion_modifier": 1.0,
        "fused_regime": "UNKNOWN",
        "fusion_confidence": 0.0,
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
            finite(value),
        ),
    )
