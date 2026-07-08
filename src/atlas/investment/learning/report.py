
"""Investment Learning report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.learning.adaptive_calibration import build_calibration_recommendations
from atlas.investment.learning.regime_detector import detect_learning_regime
from atlas.investment.learning.strategy_scorecard import build_strategy_scorecard
from atlas.investment.learning.trade_outcomes import load_performance_snapshots, load_trade_outcomes


OUT_DIR = Path("output/investment_learning")
REPORT_JSON = OUT_DIR / "learning_report.json"
REPORT_MD = OUT_DIR / "learning_report.md"
SCORECARD_CSV = OUT_DIR / "strategy_scorecard.csv"


def build_learning_report() -> dict[str, Any]:
    ledger = load_trade_outcomes()
    snapshots = load_performance_snapshots()

    scorecard = build_strategy_scorecard(ledger)
    regime = detect_learning_regime(snapshots)
    recommendations = build_calibration_recommendations(scorecard, regime)

    report = {
        "success": True,
        "summary": (
            f"Learning Engine evaluated {len(scorecard)} scorecard row(s). "
            f"Regime: {regime.get('learning_regime')}."
        ),
        "scorecard": scorecard,
        "learning_regime": regime,
        "recommendations": recommendations,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "scorecard_csv": str(SCORECARD_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("scorecard", [])).to_csv(SCORECARD_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Investment Learning Report",
        "",
        report.get("summary", ""),
        "",
        "## Learning Regime",
        "",
        "```json",
        json.dumps(report.get("learning_regime", {}), indent=2),
        "```",
        "",
        "## Recommendations",
        "",
    ]

    for rec in report.get("recommendations", []):
        lines.append(f"- {rec}")

    return "\n".join(lines) + "\n"
