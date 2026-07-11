"""Independence analysis for Atlas alpha engines."""

from __future__ import annotations

import pandas as pd


def build_engine_correlation_matrix(
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Correlate engine scores over common asset-timestamp rows."""
    if (
        signals is None
        or signals.empty
    ):
        return pd.DataFrame()

    working = signals[
        [
            "timestamp",
            "asset",
            "engine_id",
            "normalized_score",
        ]
    ].copy()

    working["normalized_score"] = (
        pd.to_numeric(
            working["normalized_score"],
            errors="coerce",
        )
    )

    working = working.dropna(
        subset=[
            "timestamp",
            "asset",
            "engine_id",
            "normalized_score",
        ]
    )

    pivot = working.pivot_table(
        index=[
            "timestamp",
            "asset",
        ],
        columns="engine_id",
        values="normalized_score",
        aggfunc="last",
    )

    return pivot.corr(
        method="pearson",
        min_periods=20,
    )


def build_engine_independence_summary(
    correlation: pd.DataFrame,
) -> pd.DataFrame:
    """Convert the matrix into pairwise independence scores."""
    columns = [
        "engine_a",
        "engine_b",
        "correlation",
        "absolute_correlation",
        "independence_score",
    ]

    if (
        correlation is None
        or correlation.empty
    ):
        return pd.DataFrame(columns=columns)

    engines = list(
        correlation.columns
    )

    rows: list[dict] = []

    for index, engine_a in enumerate(
        engines
    ):
        for engine_b in engines[
            index + 1:
        ]:
            value = correlation.loc[
                engine_a,
                engine_b,
            ]

            if pd.isna(value):
                continue

            absolute = abs(float(value))

            rows.append({
                "engine_a": engine_a,
                "engine_b": engine_b,
                "correlation": round(
                    float(value),
                    8,
                ),
                "absolute_correlation": round(
                    absolute,
                    8,
                ),
                "independence_score": round(
                    max(
                        0.0,
                        1.0 - absolute,
                    ),
                    8,
                ),
            })

    return pd.DataFrame(
        rows,
        columns=columns,
    ).sort_values(
        [
            "independence_score",
            "engine_a",
            "engine_b",
        ],
        ascending=[
            False,
            True,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)
