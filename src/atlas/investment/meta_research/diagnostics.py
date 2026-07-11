"""Engine-level diagnostics for Meta Research Engine v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.meta_research.config import (
    MIN_ENGINE_TRADES,
)
from atlas.investment.meta_research.statistics import (
    summarize_returns,
)


DIAGNOSTIC_COLUMNS = [
    "engine_id",
    "family",
    "trade_count",
    "asset_count",
    "year_count",
    "win_rate",
    "mean_return",
    "median_return",
    "return_std",
    "profit_factor",
    "downside_mean",
    "best_return",
    "worst_return",
    "long_trade_count",
    "short_trade_count",
    "long_mean_return",
    "short_mean_return",
    "best_asset",
    "worst_asset",
    "best_year",
    "worst_year",
    "sufficient_evidence",
]


def build_engine_diagnostics(
    evidence: pd.DataFrame,
) -> pd.DataFrame:
    if evidence is None or evidence.empty:
        return pd.DataFrame(
            columns=DIAGNOSTIC_COLUMNS
        )

    rows = []

    for engine_id, group in evidence.groupby(
        "engine_id",
        sort=True,
    ):
        metrics = summarize_returns(
            group["strategy_return"]
        )

        asset_summary = (
            group.groupby(
                "asset"
            )["strategy_return"]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        year_summary = (
            group.groupby(
                "calendar_year"
            )["strategy_return"]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        long_returns = group.loc[
            group["direction"]
            .astype(str)
            .str.upper()
            .eq("LONG"),
            "strategy_return",
        ]

        short_returns = group.loc[
            group["direction"]
            .astype(str)
            .str.upper()
            .eq("SHORT"),
            "strategy_return",
        ]

        rows.append({
            "engine_id": engine_id,
            "family": str(
                group["family"].iloc[0]
            ),
            "trade_count": metrics[
                "observation_count"
            ],
            "asset_count": int(
                group["asset"].nunique()
            ),
            "year_count": int(
                group[
                    "calendar_year"
                ].nunique()
            ),
            "win_rate": metrics[
                "win_rate"
            ],
            "mean_return": metrics[
                "mean_return"
            ],
            "median_return": metrics[
                "median_return"
            ],
            "return_std": metrics[
                "return_std"
            ],
            "profit_factor": metrics[
                "profit_factor"
            ],
            "downside_mean": metrics[
                "downside_mean"
            ],
            "best_return": metrics[
                "best_return"
            ],
            "worst_return": metrics[
                "worst_return"
            ],
            "long_trade_count": int(
                len(long_returns)
            ),
            "short_trade_count": int(
                len(short_returns)
            ),
            "long_mean_return": round(
                float(
                    long_returns.mean()
                )
                if not long_returns.empty
                else 0.0,
                8,
            ),
            "short_mean_return": round(
                float(
                    short_returns.mean()
                )
                if not short_returns.empty
                else 0.0,
                8,
            ),
            "best_asset": (
                str(
                    asset_summary.index[0]
                )
                if not asset_summary.empty
                else ""
            ),
            "worst_asset": (
                str(
                    asset_summary.index[-1]
                )
                if not asset_summary.empty
                else ""
            ),
            "best_year": (
                int(
                    year_summary.index[0]
                )
                if not year_summary.empty
                else None
            ),
            "worst_year": (
                int(
                    year_summary.index[-1]
                )
                if not year_summary.empty
                else None
            ),
            "sufficient_evidence": (
                metrics[
                    "observation_count"
                ]
                >= MIN_ENGINE_TRADES
            ),
        })

    return pd.DataFrame(
        rows,
        columns=DIAGNOSTIC_COLUMNS,
    ).sort_values(
        [
            "profit_factor",
            "mean_return",
            "engine_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)
