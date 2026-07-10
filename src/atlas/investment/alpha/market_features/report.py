
"""Market Features v2 report and export."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.market_features.features import (
    build_feature_frame,
    build_latest_asset_features,
    build_market_aggregate,
)
from atlas.investment.alpha.market_features.loader import (
    load_market_feature_inputs,
)


OUT_DIR = Path("output/investment_alpha")

REPORT_JSON = OUT_DIR / "market_features_report.json"
REPORT_MD = OUT_DIR / "market_features_report.md"

FEATURE_HISTORY_CSV = OUT_DIR / "market_feature_history.csv"
LATEST_FEATURES_CSV = OUT_DIR / "market_features.csv"
MARKET_FEATURES_CSV = OUT_DIR / "market_aggregate_features.csv"


def build_market_feature_report(
    legacy_root: Path | None = None,
) -> dict[str, Any]:
    inputs = load_market_feature_inputs(legacy_root)

    universe_report = (
        inputs.get("universe_report", {}) or {}
    )
    approved_universe = inputs.get(
        "approved_universe"
    )
    prices = inputs.get("prices")

    if not universe_report:
        return build_failure_report(
            "Market Universe v1 report is unavailable."
        )

    if universe_report.get("success") is not True:
        return build_failure_report(
            "Market Universe v1 did not pass required core gates."
        )

    approved_assets = set(
        str(asset)
        for asset in universe_report.get(
            "approved_assets",
            [],
        )
    )

    if (
        approved_universe is not None
        and not approved_universe.empty
        and "asset" in approved_universe.columns
    ):
        approved_assets &= set(
            approved_universe["asset"]
            .dropna()
            .astype(str)
            .tolist()
        )

    if not approved_assets:
        return build_failure_report(
            "No approved Market Universe assets are available."
        )

    filtered_prices = prices[
        prices["asset"].astype(str).isin(
            approved_assets
        )
    ].copy()

    if filtered_prices.empty:
        return build_failure_report(
            "No approved-universe price rows are available."
        )

    history = build_feature_frame(filtered_prices)
    latest = build_latest_asset_features(history)
    aggregate = build_market_aggregate(latest)

    generated_at = datetime.now(UTC).isoformat()

    assets = (
        latest["asset"].astype(str).tolist()
        if not latest.empty
        else []
    )

    summary = (
        f"Market Features v2 generated features for "
        f"{len(assets)} approved asset(s) from "
        f"{len(filtered_prices)} Market Universe price row(s). "
        f"Market regime: {aggregate.get('market_regime')}."
    )

    report = {
        "success": True,
        "version": "market_features_v2",
        "source": "market_universe_v1",
        "generated_at": generated_at,
        "summary": summary,
        "text_summary": summary,
        "assets": assets,
        "approved_asset_count": len(
            approved_assets
        ),
        "asset_feature_rows": len(latest),
        "market_feature_rows": 1,
        "history_rows": len(history),
        "market_aggregate": aggregate,
        "latest_features": (
            records(latest)
        ),
        "execution_scope_changed": False,
        "execution_note": (
            "Market Features v2 expands research and ranking only. "
            "Execution remains restricted by approved-universe, "
            "portfolio, risk, and safety controls."
        ),
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "history_csv": str(FEATURE_HISTORY_CSV),
            "asset_features_csv": str(LATEST_FEATURES_CSV),
            "market_features_csv": str(MARKET_FEATURES_CSV),
        },
    }

    write_outputs(
        report=report,
        history=history,
        latest=latest,
        aggregate=aggregate,
    )

    return report


def build_failure_report(reason: str) -> dict[str, Any]:
    summary = f"Market Features v2 blocked: {reason}"

    report = {
        "success": False,
        "version": "market_features_v2",
        "source": "market_universe_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "text_summary": summary,
        "reason": reason,
        "assets": [],
        "approved_asset_count": 0,
        "asset_feature_rows": 0,
        "market_feature_rows": 0,
        "history_rows": 0,
        "market_aggregate": {},
        "latest_features": [],
        "execution_scope_changed": False,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "history_csv": str(FEATURE_HISTORY_CSV),
            "asset_features_csv": str(LATEST_FEATURES_CSV),
            "market_features_csv": str(MARKET_FEATURES_CSV),
        },
    }

    write_outputs(
        report=report,
        history=pd.DataFrame(),
        latest=pd.DataFrame(),
        aggregate={},
    )

    return report


def write_outputs(
    *,
    report: dict[str, Any],
    history: pd.DataFrame,
    latest: pd.DataFrame,
    aggregate: dict,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    (
        history
        if history is not None
        else pd.DataFrame()
    ).to_csv(
        FEATURE_HISTORY_CSV,
        index=False,
    )

    (
        latest
        if latest is not None
        else pd.DataFrame()
    ).to_csv(
        LATEST_FEATURES_CSV,
        index=False,
    )

    pd.DataFrame(
        [aggregate] if aggregate else []
    ).to_csv(
        MARKET_FEATURES_CSV,
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Market Features v2",
        "",
        report.get("summary", ""),
        "",
        f"Source: `{report.get('source')}`",
        "",
        "## Market Aggregate",
        "",
        "```json",
        json.dumps(
            report.get("market_aggregate", {}),
            indent=2,
        ),
        "```",
        "",
        "## Approved Asset Features",
        "",
    ]

    latest = report.get("latest_features", [])

    if not latest:
        lines.append("No asset features are available.")
    else:
        for row in latest:
            lines.append(
                f"- `{row.get('asset')}` "
                f"rank=`{row.get('cross_sectional_rank')}` "
                f"score=`{format_number(row.get('cross_sectional_score'))}` "
                f"30d_return=`{format_number(row.get('return_30d'))}` "
                f"trend=`{row.get('trend_state')}`"
            )

    lines.extend([
        "",
        "## Execution Boundary",
        "",
        report.get("execution_note", ""),
    ])

    return "\n".join(lines) + "\n"


def records(frame: pd.DataFrame) -> list[dict]:
    if frame is None or frame.empty:
        return []

    clean = frame.copy()
    clean = clean.where(
        pd.notna(clean),
        None,
    )

    return clean.to_dict("records")


def format_number(value) -> str:
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return "n/a"
