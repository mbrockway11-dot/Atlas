
"""Risk Engine v2 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.risk_engine.action_risk import action_risk, rebalance_risk
from atlas.investment.risk_engine.concentration import concentration_risk
from atlas.investment.risk_engine.drawdown import drawdown_risk
from atlas.investment.risk_engine.exposure import exposure_risk
from atlas.investment.risk_engine.learning_risk import learning_risk
from atlas.investment.risk_engine.loader import load_risk_inputs
from atlas.investment.risk_engine.scoring import aggregate_risk


OUT_DIR = Path("output/investment_risk")
REPORT_JSON = OUT_DIR / "risk_engine_report.json"
REPORT_MD = OUT_DIR / "risk_engine_report.md"
BLOCKS_CSV = OUT_DIR / "risk_blocks.csv"


def build_risk_engine_report() -> dict[str, Any]:
    inputs = load_risk_inputs()

    blocks = [
        exposure_risk(inputs["portfolio_state"]),
        concentration_risk(inputs["portfolio_state"]),
        drawdown_risk(inputs["performance"]),
        learning_risk(inputs["learning"]),
        action_risk(inputs["action_engine"]),
        rebalance_risk(inputs["rebalance"]),
    ]

    aggregate = aggregate_risk(blocks)

    report = {
        "success": True,
        "summary": (
            f"Risk Engine v2 classified portfolio as {aggregate['risk_label']} "
            f"with score {aggregate['aggregate_risk_score']}."
        ),
        "aggregate": aggregate,
        "risk_blocks": blocks,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "blocks_csv": str(BLOCKS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("risk_blocks", [])).to_csv(BLOCKS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Risk Engine v2 Report",
        "",
        report.get("summary", ""),
        "",
        "## Aggregate",
        "",
        "```json",
        json.dumps(report.get("aggregate", {}), indent=2),
        "```",
        "",
        "## Risk Blocks",
        "",
    ]

    for block in report.get("risk_blocks", []):
        lines.append(
            f"- `{block.get('risk_type')}` score=`{block.get('risk_score')}` "
            f"warnings=`{len(block.get('warnings', []) or [])}`"
        )

    return "\n".join(lines) + "\n"
