"""Research-governed engine admission for Alpha Ensemble v6."""

from __future__ import annotations

import math

import pandas as pd


ELIGIBLE_DECISIONS = {
    "PROMOTE",
    "KEEP",
}


def build_engine_governance(
    decisions: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Research Lab decisions into ensemble governance rows."""
    columns = [
        "engine_id",
        "family",
        "decision",
        "eligible",
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

    if decisions is None or decisions.empty:
        return pd.DataFrame(columns=columns)

    frame = decisions.copy()

    if "engine_id" not in frame.columns:
        return pd.DataFrame(columns=columns)

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

    if "family" not in frame.columns:
        frame["family"] = "unknown"

    if "hard_failures" not in frame.columns:
        frame["hard_failures"] = ""

    frame["hard_failures"] = (
        frame["hard_failures"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    frame["family"] = (
        frame["family"]
        .fillna("unknown")
        .astype(str)
    )

    frame["eligible"] = (
        frame["decision"].isin(
            ELIGIBLE_DECISIONS
        )
        & frame["hard_failures"]
        .fillna("")
        .astype(str)
        .eq("")
    )

    frame["governance_weight"] = frame.apply(
        calculate_governance_weight,
        axis=1,
    )

    eligible_total = float(
        frame.loc[
            frame["eligible"],
            "governance_weight",
        ].sum()
    )

    if eligible_total > 0:
        frame.loc[
            frame["eligible"],
            "governance_weight",
        ] = (
            frame.loc[
                frame["eligible"],
                "governance_weight",
            ]
            / eligible_total
        )

    frame.loc[
        ~frame["eligible"],
        "governance_weight",
    ] = 0.0

    return frame[
        columns
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


def calculate_governance_weight(
    row: pd.Series,
) -> float:
    """Build an unnormalized reliability weight."""
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
            row.get("portfolio_sharpe")
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


def governance_by_engine(
    governance: pd.DataFrame,
) -> dict[str, dict]:
    """Index governance rows by engine ID."""
    if governance is None or governance.empty:
        return {}

    return {
        str(row["engine_id"]): row.to_dict()
        for _, row in governance.iterrows()
    }


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
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


