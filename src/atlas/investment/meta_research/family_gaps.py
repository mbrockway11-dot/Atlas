"""Engine-family coverage and gap analysis."""

from __future__ import annotations

import pandas as pd

from atlas.investment.meta_research.config import (
    EXPECTED_ENGINE_FAMILIES,
)


GAP_COLUMNS = [
    "family",
    "engine_count",
    "eligible_engine_count",
    "promoted_engine_count",
    "positive_engine_count",
    "best_profit_factor",
    "best_mean_return",
    "coverage_status",
    "gap_score",
    "research_need",
]


def build_engine_family_gaps(
    diagnostics: pd.DataFrame,
    decisions: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    diagnostics = (
        diagnostics.copy()
        if diagnostics is not None
        else pd.DataFrame()
    )

    decisions = (
        decisions.copy()
        if decisions is not None
        else pd.DataFrame()
    )

    governance = latest_governance(
        governance
    )

    families = set(
        EXPECTED_ENGINE_FAMILIES
    )

    for frame in [
        diagnostics,
        decisions,
        governance,
    ]:
        if (
            not frame.empty
            and "family" in frame.columns
        ):
            families.update(
                frame[
                    "family"
                ].dropna().astype(str)
            )

    rows = []

    for family in sorted(families):
        family_diagnostics = filter_family(
            diagnostics,
            family,
        )

        family_decisions = filter_family(
            decisions,
            family,
        )

        family_governance = filter_family(
            governance,
            family,
        )

        engine_count = int(
            family_diagnostics[
                "engine_id"
            ].nunique()
            if (
                not family_diagnostics.empty
                and "engine_id"
                in family_diagnostics.columns
            )
            else family_decisions[
                "engine_id"
            ].nunique()
            if (
                not family_decisions.empty
                and "engine_id"
                in family_decisions.columns
            )
            else 0
        )

        eligible_count = count_truth(
            family_governance,
            "eligible",
        )

        promoted_count = (
            int(
                family_decisions[
                    "decision"
                ].astype(str)
                .str.upper()
                .eq("PROMOTE")
                .sum()
            )
            if (
                not family_decisions.empty
                and "decision"
                in family_decisions.columns
            )
            else 0
        )

        positive_count = (
            int(
                (
                    pd.to_numeric(
                        family_diagnostics[
                            "mean_return"
                        ],
                        errors="coerce",
                    ).fillna(0.0) > 0
                ).sum()
            )
            if (
                not family_diagnostics.empty
                and "mean_return"
                in family_diagnostics.columns
            )
            else 0
        )

        best_profit_factor = maximum(
            family_diagnostics,
            "profit_factor",
        )

        best_mean_return = maximum(
            family_diagnostics,
            "mean_return",
        )

        if engine_count == 0:
            coverage_status = (
                "MISSING_FAMILY"
            )

            gap_score = 1.0

            research_need = (
                "No engine currently covers this "
                "strategy family."
            )

        elif positive_count == 0:
            coverage_status = (
                "FAILED_COVERAGE"
            )

            gap_score = 0.85

            research_need = (
                "The family is represented, but "
                "no engine has positive historical "
                "expectancy."
            )

        elif eligible_count == 0:
            coverage_status = (
                "RESEARCH_ONLY"
            )

            gap_score = 0.65

            research_need = (
                "Positive evidence exists, but no "
                "engine is currently governance-eligible."
            )

        elif engine_count == 1:
            coverage_status = (
                "SINGLE_ENGINE_DEPENDENCY"
            )

            gap_score = 0.45

            research_need = (
                "The family depends on one engine; "
                "develop an independent alternative."
            )

        else:
            coverage_status = (
                "COVERED"
            )

            gap_score = 0.10

            research_need = (
                "No immediate structural family gap."
            )

        rows.append({
            "family": family,
            "engine_count": engine_count,
            "eligible_engine_count": (
                eligible_count
            ),
            "promoted_engine_count": (
                promoted_count
            ),
            "positive_engine_count": (
                positive_count
            ),
            "best_profit_factor": (
                best_profit_factor
            ),
            "best_mean_return": (
                best_mean_return
            ),
            "coverage_status": (
                coverage_status
            ),
            "gap_score": round(
                gap_score,
                8,
            ),
            "research_need": (
                research_need
            ),
        })

    return pd.DataFrame(
        rows,
        columns=GAP_COLUMNS,
    ).sort_values(
        [
            "gap_score",
            "family",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def latest_governance(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    result = frame.copy()

    if "effective_at" not in result.columns:
        return result

    result[
        "effective_at"
    ] = pd.to_datetime(
        result["effective_at"],
        errors="coerce",
        utc=True,
    )

    latest = result[
        "effective_at"
    ].max()

    if pd.isna(latest):
        return result

    return result[
        result["effective_at"].eq(
            latest
        )
    ].copy()


def filter_family(
    frame: pd.DataFrame,
    family: str,
) -> pd.DataFrame:
    if (
        frame is None
        or frame.empty
        or "family" not in frame.columns
    ):
        return pd.DataFrame()

    return frame[
        frame["family"]
        .astype(str)
        .eq(family)
    ].copy()


def count_truth(
    frame: pd.DataFrame,
    column: str,
) -> int:
    if (
        frame is None
        or frame.empty
        or column not in frame.columns
    ):
        return 0

    return int(
        frame[column]
        .astype(str)
        .str.lower()
        .isin([
            "true",
            "1",
            "yes",
        ])
        .sum()
    )


def maximum(
    frame: pd.DataFrame,
    column: str,
) -> float:
    if (
        frame is None
        or frame.empty
        or column not in frame.columns
    ):
        return 0.0

    values = pd.to_numeric(
        frame[column],
        errors="coerce",
    ).dropna()

    return round(
        float(
            values.max()
        )
        if not values.empty
        else 0.0,
        8,
    )
