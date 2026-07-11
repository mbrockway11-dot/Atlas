"""Portfolio Optimizer v2 report orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.portfolio_optimizer.loader import (
    load_optimizer_inputs,
)
from atlas.investment.portfolio_optimizer.optimizer import (
    optimize_portfolio,
)


OUT_DIR = Path(
    "output/investment_portfolio_optimizer"
)

PORTFOLIO_CSV = (
    OUT_DIR
    / "optimized_portfolio.csv"
)

COVARIANCE_CSV = (
    OUT_DIR
    / "portfolio_covariance.csv"
)

REPORT_JSON = (
    OUT_DIR
    / "portfolio_optimizer_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "portfolio_optimizer_report.md"
)


def build_portfolio_optimizer_report() -> dict[str, Any]:
    """Build a read-only optimized research portfolio."""
    inputs = load_optimizer_inputs()

    result = optimize_portfolio(
        ensemble_scores=inputs[
            "ensemble_scores"
        ],
        contributions=inputs[
            "ensemble_contributions"
        ],
        market_history=inputs[
            "market_history"
        ],
        fusion_report=inputs[
            "fusion_report"
        ],
        current_portfolio=inputs[
            "current_portfolio"
        ],
        approved_universe=inputs[
            "approved_universe"
        ],
    )

    portfolio = result[
        "portfolio"
    ]

    covariance = result.pop(
        "covariance",
        pd.DataFrame(),
    )

    report = {
        "success": bool(
            not portfolio.empty
        ),
        "version": (
            "portfolio_optimizer_v2"
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Portfolio Optimizer v2 constructed "
            f"{len(portfolio)} portfolio row(s), "
            f"including cash, with annualized "
            f"volatility "
            f"{result['risk'].get('annualized_volatility')}."
        ),
        "portfolio": portfolio.to_dict(
            "records"
        ),
        "risk": result[
            "risk"
        ],
        "controls": result[
            "controls"
        ],
        "diagnostics": result[
            "diagnostics"
        ],
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "replaces_alpha_portfolio": False,
            "uses_ensemble_v7": True,
            "uses_historical_covariance": True,
            "uses_macro_regime_controls": True,
            "deterministic": True,
        },
        "outputs": {
            "portfolio_csv": str(
                PORTFOLIO_CSV
            ),
            "covariance_csv": str(
                COVARIANCE_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_outputs(
        report,
        portfolio,
        covariance,
    )

    return report


def write_outputs(
    report: dict,
    portfolio: pd.DataFrame,
    covariance: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    portfolio.to_csv(
        PORTFOLIO_CSV,
        index=False,
    )

    covariance.to_csv(
        COVARIANCE_CSV,
        index=True,
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
    report: dict,
) -> str:
    lines = [
        "# Portfolio Optimizer v2",
        "",
        report["summary"],
        "",
        "## Optimized Portfolio",
        "",
    ]

    for row in report.get(
        "portfolio",
        [],
    ):
        lines.append(
            "- "
            f"`{row.get('asset')}` "
            f"weight=`{row.get('target_weight')}` "
            f"score=`{row.get('optimizer_score')}` "
            f"risk_contribution="
            f"`{row.get('risk_contribution')}`"
        )

    lines.extend([
        "",
        "## Risk",
        "",
        "```json",
        json.dumps(
            report.get(
                "risk",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## Context Controls",
        "",
        "```json",
        json.dumps(
            report.get(
                "controls",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## Diagnostics",
        "",
        "```json",
        json.dumps(
            report.get(
                "diagnostics",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            report.get(
                "contract",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
    ])

    return "\n".join(lines)
