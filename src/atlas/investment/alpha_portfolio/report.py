
"""Alpha Portfolio v3.1 report/export."""

from __future__ import annotations

from datetime import datetime, UTC
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha_portfolio.loader import (
    ADAPTIVE_WEIGHTS,
    load_alpha_portfolio_inputs,
)
from atlas.investment.alpha_portfolio.portfolio import (
    build_alpha_portfolio,
)


OUT_DIR = Path("output/investment_alpha")
PORTFOLIO_CSV = OUT_DIR / "alpha_portfolio.csv"
REPORT_JSON = OUT_DIR / "alpha_portfolio_report.json"
REPORT_MD = OUT_DIR / "alpha_portfolio_report.md"


def build_alpha_portfolio_report() -> dict[str, Any]:
    result = build_alpha_portfolio(
        load_alpha_portfolio_inputs()
    )

    summary = result["summary"]

    text_summary = (
        f"Alpha Portfolio v3.1 preserved "
        f"{len(result.get('rows', []))} Adaptive Weighting v4 "
        f"target row(s). Risky={summary['risky_weight']}, "
        f"cash={summary['cash_weight']}, "
        f"total={summary['total_weight']}."
    )

    report = {
        "success": result.get("success", False),
        "version": "alpha_portfolio_v3_1",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": text_summary,
        "text_summary": text_summary,
        "portfolio_summary": summary,
        "rows": result["rows"],
        "issues": result.get("issues", []),
        "source_fingerprint": file_fingerprint(
            ADAPTIVE_WEIGHTS
        ),
        "contract": {
            "authoritative_input": (
                "adaptive_weighting_v4"
            ),
            "second_risk_scaling_applied": False,
            "normalization_applied": False,
            "execution_instruction": False,
        },
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

    pd.DataFrame(
        report.get("rows", [])
    ).to_csv(
        PORTFOLIO_CSV,
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
        "# Alpha Portfolio v3.1 Report",
        "",
        report.get("summary", ""),
        "",
        "## Target Allocations",
        "",
    ]

    for row in report.get("rows", []):
        lines.append(
            f"- `{row.get('asset')}` "
            f"target_weight=`{row.get('target_weight')}` "
            f"source=`{row.get('source')}`"
        )

    lines.extend([
        "",
        "## Validation",
        "",
        "```json",
        json.dumps(
            {
                "success": report.get("success"),
                "issues": report.get("issues", []),
                "contract": report.get("contract", {}),
            },
            indent=2,
        ),
        "```",
    ])

    return "\n".join(lines) + "\n"


def file_fingerprint(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
