
"""Cross-Sectional Alpha Ranker report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.ranker.ensemble_overlay import overlay_ensemble_scores
from atlas.investment.alpha.ranker.loader import load_asset_features, load_ensemble_signals
from atlas.investment.alpha.ranker.scoring import add_cross_sectional_scores

OUT_DIR = Path("output/investment_alpha")
RANKINGS_CSV = OUT_DIR / "cross_sectional_alpha_rankings.csv"
LATEST_CSV = OUT_DIR / "cross_sectional_alpha_latest.csv"
REPORT_JSON = OUT_DIR / "cross_sectional_alpha_ranker_report.json"
REPORT_MD = OUT_DIR / "cross_sectional_alpha_ranker_report.md"


def build_cross_sectional_alpha_ranker_report() -> dict[str, Any]:
    asset_features = load_asset_features()
    ensemble = load_ensemble_signals()

    if asset_features.empty:
        report = {
            "success": False,
            "error": "Missing market_asset_features.csv. Run build_market_features.py first.",
        }
        write_outputs(report, pd.DataFrame(), pd.DataFrame())
        return report

    ranked = add_cross_sectional_scores(asset_features)
    ranked = overlay_ensemble_scores(ranked, ensemble)
    ranked = ranked.sort_values(["date", "final_rank"])

    latest_date = ranked["date"].max()
    latest = ranked[ranked["date"] == latest_date].sort_values("final_rank")

    top_cols = [
        "asset",
        "final_rank",
        "final_alpha_score",
        "raw_alpha_score",
        "ensemble_confidence",
        "ensemble_confirmed",
        "final_rank_label",
    ]

    report = {
        "success": True,
        "summary": (
            f"Cross-Sectional Alpha Ranker scored {len(ranked)} asset-date row(s) "
            f"across {ranked['asset'].nunique()} asset(s). Latest date: {latest_date}."
        ),
        "row_count": int(len(ranked)),
        "asset_count": int(ranked["asset"].nunique()),
        "latest_date": str(latest_date),
        "latest_top_assets": latest[top_cols].head(10).to_dict("records"),
        "outputs": {
            "rankings_csv": str(RANKINGS_CSV),
            "latest_csv": str(LATEST_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, ranked, latest)
    return report


def write_outputs(report: dict[str, Any], ranked: pd.DataFrame, latest: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(RANKINGS_CSV, index=False)
    latest.to_csv(LATEST_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Cross-Sectional Alpha Ranker Report",
        "",
        report.get("summary", report.get("error", "")),
        "",
        "## Latest Top Assets",
        "",
    ]

    for row in report.get("latest_top_assets", []) or []:
        lines.append(
            f"- `{row.get('asset')}` rank=`{row.get('final_rank')}` "
            f"score=`{row.get('final_alpha_score')}` "
            f"ensemble=`{row.get('ensemble_confidence')}` "
            f"label=`{row.get('final_rank_label')}`"
        )

    return "\n".join(lines) + "\n"
