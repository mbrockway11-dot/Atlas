
"""Alpha Portfolio v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha_portfolio.loader import load_alpha_portfolio_inputs
from atlas.investment.alpha_portfolio.portfolio import build_alpha_portfolio


OUT_DIR = Path("output/investment_alpha")
PORTFOLIO_CSV = OUT_DIR / "alpha_portfolio.csv"
REPORT_JSON = OUT_DIR / "alpha_portfolio_report.json"
REPORT_MD = OUT_DIR / "alpha_portfolio_report.md"


def build_alpha_portfolio_report() -> dict[str, Any]:
    result = build_alpha_portfolio(load_alpha_portfolio_inputs())

    report = {
        "success": True,
        "version": "alpha_portfolio_v3",
        "summary": (
            f"Alpha Portfolio v3 built {len(result.get('rows', []))} target allocation row(s) "
            f"from Adaptive Weighting v4. Risky={result['summary']['risky_weight']}, "
            f"cash={result['summary']['cash_weight']}."
        ),
        "text_summary": (
            f"Alpha Portfolio v3 built {len(result.get('rows', []))} target allocation row(s) "
            f"from Adaptive Weighting v4. Risky={result['summary']['risky_weight']}, "
            f"cash={result['summary']['cash_weight']}."
        ),
        "portfolio_summary": result["summary"],
        "rows": result["rows"],
        "outputs": {
            "portfolio_csv": str(PORTFOLIO_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("rows", [])).to_csv(PORTFOLIO_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Portfolio v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Target Allocations",
        "",
    ]

    for row in report.get("rows", []):
        lines.append(
            f"- `{row.get('asset')}` target_weight=`{row.get('target_weight')}` source=`{row.get('source')}`"
        )

    return "\n".join(lines) + "\n"
