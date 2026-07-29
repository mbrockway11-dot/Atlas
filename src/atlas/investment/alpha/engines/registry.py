"""Alpha Engine Framework v1 registry and orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv

from atlas.investment.alpha.backtester.schema import (
    filter_approved_assets,
    normalize_market_frame,
)
from atlas.investment.alpha.engines.base import AlphaEngine
from atlas.investment.alpha.engines.defensive_risk_off import (
    DefensiveRiskOffEngine,
)
from atlas.investment.alpha.engines.drawdown_recovery import (
    DrawdownRecoveryEngine,
)
from atlas.investment.alpha.engines.market_breadth import (
    MarketBreadthEngine,
)
from atlas.investment.alpha.engines.mean_reversion import (
    MeanReversionEngine,
)
from atlas.investment.alpha.engines.momentum import (
    CrossSectionalMomentumEngine,
)
from atlas.investment.alpha.engines.schema import (
    empty_signal_frame,
    normalize_signal_output,
)
from atlas.investment.alpha.engines.trend import (
    TrendContinuationEngine,
)
from atlas.investment.alpha.engines.volatility_compression import (
    VolatilityCompressionEngine,
)
from atlas.investment.alpha.engines.volatility_expansion import (
    VolatilityExpansionEngine,
)


MARKET_FEATURES_PATH = Path(
    "output/investment_alpha/market_features.csv"
)
APPROVED_UNIVERSE_PATH = Path(
    "output/investment_market_universe/approved_universe.csv"
)
OUT_DIR = Path(
    "output/investment_alpha_engines"
)
SIGNALS_CSV = OUT_DIR / "alpha_engine_signals.csv"
LATEST_CSV = OUT_DIR / "alpha_engine_latest.csv"
SUMMARY_CSV = OUT_DIR / "alpha_engine_summary.csv"
REPORT_JSON = OUT_DIR / "alpha_engine_report.json"
REPORT_MD = OUT_DIR / "alpha_engine_report.md"


def registered_engines() -> list[AlphaEngine]:
    """Return engines in deterministic execution order."""
    return [
        TrendContinuationEngine(),
        CrossSectionalMomentumEngine(),
        VolatilityExpansionEngine(),
        MeanReversionEngine(),
        VolatilityCompressionEngine(),
        MarketBreadthEngine(),
        DrawdownRecoveryEngine(),
        DefensiveRiskOffEngine(),
    ]


def run_alpha_engines(
    *,
    market_features_path: str | Path = MARKET_FEATURES_PATH,
    approved_universe_path: str | Path = APPROVED_UNIVERSE_PATH,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run all registered alpha engines."""
    market_path = Path(market_features_path)

    if (
        not market_path.exists()
        or not market_path.is_file()
        or market_path.stat().st_size == 0
    ):
        report = {
            "success": False,
            "error": (
                "Missing or empty Market Features v2 artifact: "
                f"{market_path}"
            ),
            "engine_count": 0,
            "signal_count": 0,
        }

        if write_outputs:
            export_report(
                report,
                empty_signal_frame(),
                empty_signal_frame(),
                pd.DataFrame(),
            )

        return report

    market = pd.read_csv(market_path)
    market = normalize_market_frame(market)

    approved = safe_read_csv(
        approved_universe_path
    )
    market = filter_approved_assets(
        market,
        approved,
    )

    engines = registered_engines()
    frames: list[pd.DataFrame] = []
    engine_status: list[dict[str, Any]] = []

    for engine in engines:
        missing_features = [
            feature
            for feature in engine.metadata.required_features
            if feature not in market.columns
        ]

        signals = engine.run(market)

        engine_status.append({
            "engine_id": engine.metadata.engine_id,
            "engine_version": engine.metadata.version,
            "family": engine.metadata.family,
            "description": engine.metadata.description,
            "holding_period": engine.metadata.holding_period,
            "required_features": list(
                engine.metadata.required_features
            ),
            "missing_features": missing_features,
            "signal_rows": int(len(signals)),
            "active": not missing_features,
        })

        if not signals.empty:
            frames.append(signals)

    signals = (
        normalize_signal_output(
            pd.concat(
                frames,
                ignore_index=True,
            )
        )
        if frames
        else empty_signal_frame()
    )

    latest = latest_signals(signals)
    summary = summarize_engines(signals)

    active_count = sum(
        1
        for row in engine_status
        if row["active"]
    )

    report = {
        "success": active_count > 0,
        "framework_version": "2.0.0",
        "market_rows": int(len(market)),
        "approved_asset_count": int(
            market["asset"].nunique()
            if not market.empty
            else 0
        ),
        "registered_engine_count": len(engines),
        "active_engine_count": active_count,
        "signal_count": int(len(signals)),
        "latest_signal_count": int(len(latest)),
        "engines": engine_status,
        "summary_rows": summary.to_dict(
            orient="records"
        ),
        "summary": (
            "Alpha Engine Framework v2 ran "
            f"{active_count}/{len(engines)} active engine(s) "
            f"and produced {len(signals)} signal row(s)."
        ),
        "outputs": {
            "signals_csv": str(SIGNALS_CSV),
            "latest_csv": str(LATEST_CSV),
            "summary_csv": str(SUMMARY_CSV),
            "report_json": str(REPORT_JSON),
            "report_markdown": str(REPORT_MD),
        },
    }

    if write_outputs:
        export_report(
            report,
            signals,
            latest,
            summary,
        )

    return report


def latest_signals(
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Return the latest signal for each engine and asset."""
    if signals.empty:
        return empty_signal_frame()

    return (
        signals.sort_values(
            "timestamp",
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                "engine_id",
                "asset",
            ],
            keep="last",
        )
        .sort_values(
            [
                "engine_id",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def summarize_engines(
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Build observed signal-distribution summaries."""
    columns = [
        "engine_id",
        "family",
        "signal_rows",
        "asset_count",
        "first_timestamp",
        "last_timestamp",
        "long_count",
        "short_count",
        "neutral_count",
        "mean_score",
        "mean_confidence",
        "mean_conviction",
    ]

    if signals.empty:
        return pd.DataFrame(columns=columns)

    rows = []

    for engine_id, group in signals.groupby(
        "engine_id",
        sort=True,
    ):
        directions = group[
            "direction"
        ].value_counts()

        rows.append({
            "engine_id": engine_id,
            "family": str(
                group["family"].iloc[0]
            ),
            "signal_rows": int(len(group)),
            "asset_count": int(
                group["asset"].nunique()
            ),
            "first_timestamp": str(
                group["timestamp"].min()
            ),
            "last_timestamp": str(
                group["timestamp"].max()
            ),
            "long_count": int(
                directions.get("LONG", 0)
            ),
            "short_count": int(
                directions.get("SHORT", 0)
            ),
            "neutral_count": int(
                directions.get("NEUTRAL", 0)
            ),
            "mean_score": round(
                float(
                    group[
                        "normalized_score"
                    ].mean()
                ),
                8,
            ),
            "mean_confidence": round(
                float(
                    group["confidence"].mean()
                ),
                8,
            ),
            "mean_conviction": round(
                float(
                    group["conviction"].mean()
                ),
                8,
            ),
        })

    return pd.DataFrame(rows, columns=columns)


def export_report(
    report: dict[str, Any],
    signals: pd.DataFrame,
    latest: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Write CSV, JSON, and Markdown artifacts."""
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    signals.to_csv(
        SIGNALS_CSV,
        index=False,
    )
    latest.to_csv(
        LATEST_CSV,
        index=False,
    )
    summary.to_csv(
        SUMMARY_CSV,
        index=False,
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )


def build_markdown(
    report: dict[str, Any],
) -> str:
    """Render the Alpha Engine Framework report."""
    lines = [
        "# Alpha Engine Framework v2",
        "",
        report.get(
            "summary",
            report.get("error", ""),
        ),
        "",
        "## Framework",
        "",
        f"- Success: `{report.get('success')}`",
        (
            "- Framework version: "
            f"`{report.get('framework_version')}`"
        ),
        f"- Market rows: `{report.get('market_rows', 0)}`",
        (
            "- Approved assets: "
            f"`{report.get('approved_asset_count', 0)}`"
        ),
        (
            "- Registered engines: "
            f"`{report.get('registered_engine_count', 0)}`"
        ),
        (
            "- Active engines: "
            f"`{report.get('active_engine_count', 0)}`"
        ),
        (
            "- Signal rows: "
            f"`{report.get('signal_count', 0)}`"
        ),
        "",
        "## Engines",
        "",
    ]

    for engine in report.get("engines", []):
        lines.extend([
            f"### {engine.get('engine_id')}",
            "",
            f"- Family: `{engine.get('family')}`",
            f"- Version: `{engine.get('engine_version')}`",
            f"- Active: `{engine.get('active')}`",
            (
                "- Holding period: "
                f"`{engine.get('holding_period')}`"
            ),
            (
                "- Signal rows: "
                f"`{engine.get('signal_rows')}`"
            ),
            (
                "- Missing features: "
                f"`{engine.get('missing_features')}`"
            ),
            "",
            str(engine.get("description", "")),
            "",
        ])

    lines.extend([
        "## Observed Signal Summary",
        "",
    ])

    summaries = report.get(
        "summary_rows",
        [],
    )

    if not summaries:
        lines.append("- No engine summary rows.")

    for row in summaries:
        lines.extend([
            f"### {row.get('engine_id')}",
            "",
            (
                "- Signal rows: "
                f"`{row.get('signal_rows')}`"
            ),
            (
                "- Assets: "
                f"`{row.get('asset_count')}`"
            ),
            (
                "- Long / Short / Neutral: "
                f"`{row.get('long_count')} / "
                f"{row.get('short_count')} / "
                f"{row.get('neutral_count')}`"
            ),
            (
                "- Mean score: "
                f"`{row.get('mean_score')}`"
            ),
            (
                "- Mean confidence: "
                f"`{row.get('mean_confidence')}`"
            ),
            (
                "- Mean conviction: "
                f"`{row.get('mean_conviction')}`"
            ),
            "",
        ])

    return "\n".join(lines)


__all__ = [
    "registered_engines",
    "run_alpha_engines",
]

