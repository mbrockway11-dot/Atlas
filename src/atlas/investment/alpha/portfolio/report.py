
"""Portfolio Construction Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from atlas.investment.alpha.portfolio.allocator import allocate_from_rankings
from atlas.investment.alpha.portfolio.risk import summarize_portfolio_risk


OUT_DIR = Path("output/investment_alpha")
LATEST_RANKINGS_CSV = OUT_DIR / "cross_sectional_alpha_latest.csv"

PORTFOLIO_CSV = OUT_DIR / "alpha_portfolio_latest.csv"
REPORT_JSON = OUT_DIR / "alpha_portfolio_report.json"
REPORT_MD = OUT_DIR / "alpha_portfolio_report.md"


def build_alpha_portfolio_report() -> dict:
    """Build latest alpha portfolio from cross-sectional rankings."""
    if not LATEST_RANKINGS_CSV.exists():
        report = {
            "success": False,
            "error": "Missing cross_sectional_alpha_latest.csv. Run build_cross_sectional_alpha_ranker.py first.",
        }
        write_outputs(report, pd.DataFrame())
        return report

    latest = pd.read_csv(LATEST_RANKINGS_CSV)

    portfolio = allocate_from_rankings(latest)
    risk = summarize_portfolio_risk(portfolio)

    report = {
        "success": True,
        "summary": f"Alpha Portfolio constructed {len(portfolio)} row(s). Risk label: {risk.get('risk_label')}.",
        "risk": risk,
        "portfolio": portfolio.to_dict("records"),
        "outputs": {
            "portfolio_csv": str(PORTFOLIO_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, portfolio)
    return report


def write_outputs(report: dict, portfolio: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not portfolio.empty:
        portfolio.to_csv(PORTFOLIO_CSV, index=False)
    else:
        pd.DataFrame().to_csv(PORTFOLIO_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict) -> str:
    lines = [
        "# Alpha Portfolio Construction Report",
        "",
        report.get("summary", report.get("error", "")),
        "",
        "## Portfolio",
        "",
    ]

    for row in report.get("portfolio", []) or []:
        lines.append(
            f"- `{row.get('asset')}` weight=`{row.get('target_weight')}` "
            f"rank=`{row.get('rank')}` label=`{row.get('rank_label')}`"
        )

    lines.extend([
        "",
        "## Risk",
        "",
        "```json",
        json.dumps(report.get("risk", {}), indent=2),
        "```",
        "",
    ])

    return "\n".join(lines)
