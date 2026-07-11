"""Market and ensemble memory for Learning Engine v3.1."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


MARKET_MEMORY_COLUMNS = [
    "observed_at",
    "ensemble_version",
    "ensemble_regime",
    "ensemble_success",
    "approved_assets",
    "research_engine_votes",
    "assets_with_research_engines",
    "promote_long",
    "maintain",
    "watch",
    "cash_weight",
    "median_score",
    "breadth",
    "top_asset",
    "top_score",
    "top_conviction",
]


def build_market_memory_snapshot(
    ensemble_report: dict,
    ensemble_scores: pd.DataFrame,
) -> pd.DataFrame:
    """Build one market-memory observation."""
    report = ensemble_report or {}

    regime = (
        report.get("regime", {})
        or {}
    )

    counts = (
        report.get("counts", {})
        or {}
    )

    scores = ensemble_scores.copy()

    top_asset = ""
    top_score = 0.0
    top_conviction = 0.0

    if not scores.empty:
        for column in [
            "ensemble_score",
            "conviction",
        ]:
            if column in scores.columns:
                scores[column] = pd.to_numeric(
                    scores[column],
                    errors="coerce",
                ).fillna(0.0)

        if "conviction" in scores.columns:
            scores = scores.sort_values(
                "conviction",
                ascending=False,
                kind="stable",
            )

        top = scores.iloc[0]

        top_asset = str(
            top.get("asset", "")
        )
        top_score = float(
            top.get(
                "ensemble_score",
                0.0,
            )
        )
        top_conviction = float(
            top.get(
                "conviction",
                0.0,
            )
        )

    cash_weight = 0.0

    for row in report.get(
        "allocations",
        [],
    ):
        if str(
            row.get("asset")
        ).upper() == "CASH":
            cash_weight = float(
                row.get(
                    "ensemble_target_weight",
                    0.0,
                )
            )
            break

    return pd.DataFrame([
        {
            "observed_at": datetime.now(
                UTC
            ).isoformat(),
            "ensemble_version": str(
                report.get(
                    "version",
                    "unknown",
                )
            ),
            "ensemble_regime": str(
                regime.get(
                    "regime",
                    "UNKNOWN",
                )
            ),
            "ensemble_success": bool(
                report.get(
                    "success",
                    False,
                )
            ),
            "approved_assets": int(
                counts.get(
                    "approved_assets",
                    0,
                )
            ),
            "research_engine_votes": int(
                counts.get(
                    "research_engine_votes",
                    0,
                )
            ),
            "assets_with_research_engines": int(
                counts.get(
                    "assets_with_research_engines",
                    0,
                )
            ),
            "promote_long": int(
                counts.get(
                    "promote_long",
                    0,
                )
            ),
            "maintain": int(
                counts.get(
                    "maintain",
                    0,
                )
            ),
            "watch": int(
                counts.get(
                    "watch",
                    0,
                )
            ),
            "cash_weight": cash_weight,
            "median_score": float(
                regime.get(
                    "median_score",
                    0.0,
                )
            ),
            "breadth": float(
                regime.get(
                    "breadth",
                    0.0,
                )
            ),
            "top_asset": top_asset,
            "top_score": top_score,
            "top_conviction": (
                top_conviction
            ),
        }
    ])


def append_market_memory(
    snapshot: pd.DataFrame,
    path: str | Path,
) -> pd.DataFrame:
    """Append market memory and retain deterministic history."""
    target = Path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = pd.DataFrame(
        columns=MARKET_MEMORY_COLUMNS
    )

    if (
        target.exists()
        and target.is_file()
        and target.stat().st_size > 0
    ):
        try:
            existing = pd.read_csv(
                target
            )
        except Exception:
            existing = pd.DataFrame(
                columns=MARKET_MEMORY_COLUMNS
            )

    combined = pd.concat(
        [
            existing,
            snapshot,
        ],
        ignore_index=True,
    )

    for column in MARKET_MEMORY_COLUMNS:
        if column not in combined.columns:
            combined[column] = None

    combined = combined[
        MARKET_MEMORY_COLUMNS
    ]

    combined.to_csv(
        target,
        index=False,
    )

    return combined
