"""Persistent strategy memory for Learning Engine v3.1."""

from __future__ import annotations

from datetime import UTC, datetime
import math
from pathlib import Path

import pandas as pd


MEMORY_COLUMNS = [
    "observed_at",
    "engine_id",
    "family",
    "decision",
    "promotion_score",
    "performance_score",
    "stability_score",
    "risk_score",
    "independence_score",
    "trade_count",
    "mean_return",
    "profit_factor",
    "portfolio_cumulative_return",
    "portfolio_sharpe",
    "portfolio_recovery_factor",
    "max_drawdown",
    "hard_failures",
]


def build_strategy_memory_snapshot(
    decisions: pd.DataFrame,
) -> pd.DataFrame:
    """Convert Research Lab decisions into one memory snapshot."""
    if decisions is None or decisions.empty:
        return pd.DataFrame(
            columns=MEMORY_COLUMNS
        )

    frame = decisions.copy()

    if "engine_id" not in frame.columns:
        return pd.DataFrame(
            columns=MEMORY_COLUMNS
        )

    observed_at = datetime.now(
        UTC
    ).isoformat()

    frame.insert(
        0,
        "observed_at",
        observed_at,
    )

    defaults = {
        "family": "unknown",
        "decision": "UNKNOWN",
        "promotion_score": 0.0,
        "performance_score": 0.0,
        "stability_score": 0.0,
        "risk_score": 0.0,
        "independence_score": 0.0,
        "trade_count": 0,
        "mean_return": 0.0,
        "profit_factor": 0.0,
        "portfolio_cumulative_return": 0.0,
        "portfolio_sharpe": 0.0,
        "portfolio_recovery_factor": 0.0,
        "max_drawdown": 0.0,
        "hard_failures": "",
    }

    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default

    text_columns = [
        "engine_id",
        "family",
        "decision",
        "hard_failures",
    ]

    for column in text_columns:
        frame[column] = (
            frame[column]
            .fillna(
                defaults.get(
                    column,
                    "",
                )
            )
            .astype(str)
        )

    numeric_columns = [
        column
        for column in MEMORY_COLUMNS
        if column not in {
            "observed_at",
            "engine_id",
            "family",
            "decision",
            "hard_failures",
        }
    ]

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        ).fillna(0.0)

    return frame[
        MEMORY_COLUMNS
    ].sort_values(
        "engine_id",
        kind="stable",
    ).reset_index(drop=True)


def append_strategy_memory(
    snapshot: pd.DataFrame,
    path: str | Path,
) -> pd.DataFrame:
    """Append each learning run as a distinct persistent observation."""
    target = Path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = load_memory(target)

    if snapshot is None or snapshot.empty:
        return existing.reset_index(drop=True)

    current = snapshot.copy()

    # Generate a single unique run identifier and retain observed_at for
    # temporal analysis. The run identifier prevents identical research
    # states from being collapsed across separate learning cycles.
    run_id = (
        pd.Timestamp.now(tz="UTC")
        .isoformat()
    )

    if "memory_run_id" not in existing.columns:
        existing["memory_run_id"] = ""

    current["memory_run_id"] = run_id

    if "observed_at" not in current.columns:
        current["observed_at"] = run_id

    current["observed_at"] = pd.to_datetime(
        current["observed_at"],
        errors="coerce",
        utc=True,
    )

    current["observed_at"] = current[
        "observed_at"
    ].fillna(
        pd.Timestamp.now(tz="UTC")
    )

    combined = pd.concat(
        [
            existing,
            current,
        ],
        ignore_index=True,
        sort=False,
    )

    combined["observed_at"] = pd.to_datetime(
        combined["observed_at"],
        errors="coerce",
        utc=True,
    )

    combined = combined.dropna(
        subset=[
            "observed_at",
            "engine_id",
        ]
    )

    combined["engine_id"] = (
        combined["engine_id"]
        .astype(str)
    )

    combined["memory_run_id"] = (
        combined["memory_run_id"]
        .fillna("")
        .astype(str)
    )

    combined = combined.sort_values(
        [
            "engine_id",
            "observed_at",
            "memory_run_id",
        ],
        kind="stable",
    )

    # Remove only accidental duplicate writes from the exact same run.
    combined = combined.drop_duplicates(
        subset=[
            "memory_run_id",
            "engine_id",
        ],
        keep="last",
    )

    combined["observed_at"] = (
        combined["observed_at"]
        .astype(str)
    )

    output_columns = [
        "memory_run_id",
        *MEMORY_COLUMNS,
    ]

    for column in output_columns:
        if column not in combined.columns:
            combined[column] = None

    combined = combined[
        output_columns
    ].reset_index(drop=True)

    combined.to_csv(
        target,
        index=False,
    )

    return combined

def load_memory(
    path: str | Path,
) -> pd.DataFrame:
    """Load persistent strategy memory safely."""
    target = Path(path)

    columns = [
        "memory_run_id",
        *MEMORY_COLUMNS,
    ]

    if (
        not target.exists()
        or not target.is_file()
        or target.stat().st_size == 0
    ):
        return pd.DataFrame(
            columns=columns
        )

    try:
        frame = pd.read_csv(target)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ):
        return pd.DataFrame(
            columns=columns
        )

    # Backward compatibility for memory created before run IDs existed.
    if "memory_run_id" not in frame.columns:
        frame["memory_run_id"] = [
            f"legacy_{index}"
            for index in range(len(frame))
        ]

    for column in columns:
        if column not in frame.columns:
            frame[column] = None

    return frame[
        columns
    ]

def build_strategy_memory_summary(
    memory: pd.DataFrame,
    *,
    decay_rate: float = 0.12,
) -> pd.DataFrame:
    """Summarize engine persistence, momentum, and confidence decay."""
    columns = [
        "engine_id",
        "family",
        "observation_count",
        "latest_decision",
        "previous_decision",
        "decision_changed",
        "latest_promotion_score",
        "average_promotion_score",
        "promotion_score_trend",
        "latest_portfolio_sharpe",
        "average_portfolio_sharpe",
        "latest_profit_factor",
        "average_profit_factor",
        "latest_mean_return",
        "average_mean_return",
        "latest_max_drawdown",
        "decision_stability",
        "recency_weighted_reliability",
        "confidence_decay",
        "memory_status",
    ]

    if memory is None or memory.empty:
        return pd.DataFrame(columns=columns)

    frame = memory.copy()

    frame["observed_at"] = pd.to_datetime(
        frame["observed_at"],
        errors="coerce",
        utc=True,
    )

    frame = frame.dropna(
        subset=[
            "observed_at",
            "engine_id",
        ]
    )

    numeric_columns = [
        "promotion_score",
        "portfolio_sharpe",
        "profit_factor",
        "mean_return",
        "max_drawdown",
    ]

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        ).fillna(0.0)

    rows: list[dict] = []

    for engine_id, group in frame.groupby(
        "engine_id",
        sort=True,
    ):
        group = group.sort_values(
            "observed_at",
            kind="stable",
        ).reset_index(drop=True)

        latest = group.iloc[-1]

        previous = (
            group.iloc[-2]
            if len(group) > 1
            else latest
        )

        sequence = list(
            range(len(group))
        )

        weights = [
            math.exp(
                -float(decay_rate)
                * (
                    len(group)
                    - 1
                    - index
                )
            )
            for index in sequence
        ]

        weight_total = sum(weights)

        weighted_promotion = (
            sum(
                float(value) * weight
                for value, weight in zip(
                    group["promotion_score"],
                    weights,
                )
            )
            / weight_total
            if weight_total > 0
            else 0.0
        )

        decision_stability = float(
            group["decision"].eq(
                latest["decision"]
            ).mean()
        )

        age_days = max(
            0.0,
            (
                pd.Timestamp.now(tz="UTC")
                - latest["observed_at"]
            ).total_seconds()
            / 86_400.0,
        )

        confidence_decay = math.exp(
            -float(decay_rate)
            * age_days
        )

        reliability = (
            weighted_promotion
            * 0.55
            + clamp(
                float(
                    latest[
                        "portfolio_sharpe"
                    ]
                )
                / 1.5
            )
            * 0.20
            + clamp(
                float(
                    latest[
                        "profit_factor"
                    ]
                )
                / 1.5
            )
            * 0.15
            + decision_stability
            * 0.10
        ) * confidence_decay

        latest_decision = str(
            latest["decision"]
        )

        previous_decision = str(
            previous["decision"]
        )

        if latest_decision == "PROMOTE":
            memory_status = (
                "PROMOTION_CONFIRMED"
                if decision_stability >= 0.60
                else "PROMOTION_EMERGING"
            )
        elif latest_decision == "KEEP":
            memory_status = "MONITOR"
        elif latest_decision == "REVISE":
            memory_status = "RECALIBRATE"
        elif latest_decision == "RETIRE":
            memory_status = "RETIRED"
        else:
            memory_status = "UNKNOWN"

        rows.append({
            "engine_id": str(engine_id),
            "family": str(
                latest.get(
                    "family",
                    "unknown",
                )
            ),
            "observation_count": int(
                len(group)
            ),
            "latest_decision": (
                latest_decision
            ),
            "previous_decision": (
                previous_decision
            ),
            "decision_changed": (
                latest_decision
                != previous_decision
            ),
            "latest_promotion_score": round(
                float(
                    latest[
                        "promotion_score"
                    ]
                ),
                8,
            ),
            "average_promotion_score": round(
                float(
                    group[
                        "promotion_score"
                    ].mean()
                ),
                8,
            ),
            "promotion_score_trend": round(
                float(
                    latest[
                        "promotion_score"
                    ]
                    - previous[
                        "promotion_score"
                    ]
                ),
                8,
            ),
            "latest_portfolio_sharpe": round(
                float(
                    latest[
                        "portfolio_sharpe"
                    ]
                ),
                8,
            ),
            "average_portfolio_sharpe": round(
                float(
                    group[
                        "portfolio_sharpe"
                    ].mean()
                ),
                8,
            ),
            "latest_profit_factor": round(
                float(
                    latest[
                        "profit_factor"
                    ]
                ),
                8,
            ),
            "average_profit_factor": round(
                float(
                    group[
                        "profit_factor"
                    ].mean()
                ),
                8,
            ),
            "latest_mean_return": round(
                float(
                    latest[
                        "mean_return"
                    ]
                ),
                8,
            ),
            "average_mean_return": round(
                float(
                    group[
                        "mean_return"
                    ].mean()
                ),
                8,
            ),
            "latest_max_drawdown": round(
                float(
                    latest[
                        "max_drawdown"
                    ]
                ),
                8,
            ),
            "decision_stability": round(
                decision_stability,
                8,
            ),
            "recency_weighted_reliability": round(
                clamp(reliability),
                8,
            ),
            "confidence_decay": round(
                confidence_decay,
                8,
            ),
            "memory_status": memory_status,
        })

    return pd.DataFrame(
        rows,
        columns=columns,
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



