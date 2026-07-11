"""Validation diagnostics for historical Atlas alpha engines."""

from __future__ import annotations

import math

import pandas as pd


VALIDATION_COLUMNS = [
    "engine_id",
    "segment_type",
    "segment_value",
    "trade_count",
    "win_rate",
    "mean_return",
    "median_return",
    "return_std",
    "profit_factor",
    "best_trade",
    "worst_trade",
]


def build_validation_segments(
    trades: pd.DataFrame,
    *,
    cost_bps: float = 10.0,
) -> pd.DataFrame:
    """Build net performance by engine, direction, asset, regime, and year."""
    if trades is None or trades.empty:
        return pd.DataFrame(
            columns=VALIDATION_COLUMNS
        )

    working = trades.copy()

    working["timestamp"] = pd.to_datetime(
        working["timestamp"],
        errors="coerce",
        utc=True,
    )

    working["gross_return"] = pd.to_numeric(
        working["strategy_return"],
        errors="coerce",
    )

    working = working.dropna(
        subset=[
            "engine_id",
            "timestamp",
            "gross_return",
        ]
    )

    round_trip_cost = (
        float(cost_bps)
        / 10_000.0
    )

    working["net_return"] = (
        working["gross_return"]
        - round_trip_cost
    )

    working["year"] = (
        working["timestamp"]
        .dt.year
        .astype("Int64")
        .astype(str)
    )

    rows: list[dict] = []

    for engine_id, engine_group in working.groupby(
        "engine_id",
        sort=True,
    ):
        rows.append({
            "engine_id": engine_id,
            "segment_type": "overall",
            "segment_value": "ALL",
            **summarize_returns(
                engine_group["net_return"]
            ),
        })

        for segment_type, column in [
            ("direction", "direction"),
            ("asset", "asset"),
            ("regime", "regime"),
            ("year", "year"),
        ]:
            if column not in engine_group.columns:
                continue

            for segment_value, group in engine_group.groupby(
                column,
                dropna=False,
                sort=True,
            ):
                rows.append({
                    "engine_id": engine_id,
                    "segment_type": segment_type,
                    "segment_value": str(
                        segment_value
                    ),
                    **summarize_returns(
                        group["net_return"]
                    ),
                })

    result = pd.DataFrame(rows)

    for column in VALIDATION_COLUMNS:
        if column not in result.columns:
            result[column] = None

    return result[
        VALIDATION_COLUMNS
    ].sort_values(
        [
            "engine_id",
            "segment_type",
            "segment_value",
        ],
        kind="stable",
    ).reset_index(drop=True)


def summarize_returns(
    values: pd.Series,
) -> dict:
    """Summarize one return sample."""
    returns = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if returns.empty:
        return {
            "trade_count": 0,
            "win_rate": None,
            "mean_return": None,
            "median_return": None,
            "return_std": None,
            "profit_factor": None,
            "best_trade": None,
            "worst_trade": None,
        }

    gains = float(
        returns[
            returns > 0
        ].sum()
    )

    losses = abs(
        float(
            returns[
                returns < 0
            ].sum()
        )
    )

    profit_factor = (
        gains / losses
        if losses > 0
        else None
    )

    return {
        "trade_count": int(
            len(returns)
        ),
        "win_rate": round(
            float(
                (returns > 0).mean()
            ),
            8,
        ),
        "mean_return": round(
            float(returns.mean()),
            8,
        ),
        "median_return": round(
            float(returns.median()),
            8,
        ),
        "return_std": round(
            float(
                returns.std(
                    ddof=0
                )
            ),
            8,
        ),
        "profit_factor": (
            round(
                float(profit_factor),
                8,
            )
            if profit_factor is not None
            and math.isfinite(
                profit_factor
            )
            else None
        ),
        "best_trade": round(
            float(returns.max()),
            8,
        ),
        "worst_trade": round(
            float(returns.min()),
            8,
        ),
    }


def classify_engine_status(
    validation: pd.DataFrame,
) -> list[dict]:
    """Classify engines using non-overlapping net performance."""
    if validation is None or validation.empty:
        return []

    overall = validation[
        validation["segment_type"].eq(
            "overall"
        )
    ].copy()

    rows: list[dict] = []

    for _, row in overall.iterrows():
        trades = int(
            row.get("trade_count") or 0
        )

        mean_return = safe_float(
            row.get("mean_return")
        )

        profit_factor = safe_float(
            row.get("profit_factor")
        )

        if (
            trades >= 100
            and mean_return > 0
            and profit_factor >= 1.20
        ):
            status = "VALIDATION_CANDIDATE"

        elif (
            trades >= 100
            and mean_return > 0
            and profit_factor >= 1.05
        ):
            status = "REVISE"

        else:
            status = "REJECT"

        rows.append({
            "engine_id": str(
                row.get("engine_id")
            ),
            "status": status,
            "trade_count": trades,
            "mean_return": mean_return,
            "profit_factor": profit_factor,
        })

    return rows


def safe_float(
    value,
    *,
    default: float = 0.0,
) -> float:
    """Convert a value into a finite float."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result
