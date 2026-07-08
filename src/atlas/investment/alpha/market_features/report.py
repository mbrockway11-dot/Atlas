
"""Market Feature Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.market_features.engine import build_market_feature_frame


DEFAULT_ROOT = Path(r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine")
OUT_DIR = Path("output/investment_alpha")
ASSET_FEATURES_CSV = OUT_DIR / "market_asset_features.csv"
MARKET_FEATURES_CSV = OUT_DIR / "market_features.csv"
REPORT_JSON = OUT_DIR / "market_feature_report.json"
REPORT_MD = OUT_DIR / "market_feature_report.md"


def build_market_feature_report(root: str | Path = DEFAULT_ROOT) -> dict[str, Any]:
    """Build and export market features."""
    result = build_market_feature_frame(root)

    if not result.get("success"):
        report = {
            "success": False,
            "summary": result.get("error"),
            "root": str(root),
        }
        write_report(report)
        return report

    asset_features: pd.DataFrame = result["asset_features"]
    market_features: pd.DataFrame = result["market_features"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    asset_features.to_csv(ASSET_FEATURES_CSV, index=False)
    market_features.to_csv(MARKET_FEATURES_CSV, index=False)

    report = {
        "success": True,
        "root": str(root),
        "summary": result["summary"],
        "asset_feature_rows": int(len(asset_features)),
        "market_feature_rows": int(len(market_features)),
        "asset_count": int(asset_features["asset"].nunique()),
        "assets": sorted(asset_features["asset"].dropna().astype(str).unique().tolist()),
        "asset_features_csv": str(ASSET_FEATURES_CSV),
        "market_features_csv": str(MARKET_FEATURES_CSV),
        "market_feature_columns": list(market_features.columns),
        "asset_feature_columns": list(asset_features.columns),
    }

    write_report(report)
    return report


def write_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Market Feature Engine Report",
        "",
        report.get("summary", ""),
        "",
        "## Outputs",
        "",
        f"- Asset features: `{report.get('asset_features_csv', 'n/a')}`",
        f"- Market features: `{report.get('market_features_csv', 'n/a')}`",
        "",
        "## Coverage",
        "",
        f"- Asset feature rows: `{report.get('asset_feature_rows', 0)}`",
        f"- Market feature rows: `{report.get('market_feature_rows', 0)}`",
        f"- Asset count: `{report.get('asset_count', 0)}`",
        "",
        "## Assets",
        "",
    ]

    for asset in report.get("assets", []) or []:
        lines.append(f"- `{asset}`")

    lines.extend(["", "## Market Feature Columns", ""])

    for col in report.get("market_feature_columns", []) or []:
        lines.append(f"- `{col}`")

    lines.append("")
    return "\n".join(lines)
