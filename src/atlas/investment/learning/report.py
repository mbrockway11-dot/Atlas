
"""Investment Learning v2 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.learning.adaptive_calibration import build_calibration_recommendations
from atlas.investment.learning.regime_detector import detect_learning_regime
from atlas.investment.learning.strategy_scorecard import build_strategy_scorecard
from atlas.investment.learning.trade_outcomes import (
    load_equity_curve,
    load_performance_attribution,
    load_performance_snapshots,
    load_trade_outcomes,
    load_unrealized_positions,
)


OUT_DIR = Path("output/investment_learning")
REPORT_JSON = OUT_DIR / "learning_report.json"
REPORT_MD = OUT_DIR / "learning_report.md"
SCORECARD_CSV = OUT_DIR / "strategy_scorecard.csv"
REGIME_CSV = OUT_DIR / "learning_regime_history.csv"


def build_learning_report() -> dict[str, Any]:
    snapshots = load_performance_snapshots()
    attribution = load_performance_attribution()
    equity_curve = load_equity_curve()
    unrealized = load_unrealized_positions()
    ledger = load_trade_outcomes()

    scorecard = build_strategy_scorecard(attribution if not attribution.empty else unrealized, ledger)
    regime = detect_learning_regime(equity_curve, snapshots)
    recommendations = build_calibration_recommendations(scorecard, regime)

    report = {
        "success": True,
        "version": "learning_v2",
        "summary": (
            f"Learning v2 evaluated {len(scorecard)} scorecard row(s) "
            f"from MTM/Performance v3. Regime: {regime.get('learning_regime')}."
        ),
        "scorecard": scorecard,
        "learning_regime": regime,
        "recommendations": recommendations,
        "inputs": {
            "performance_snapshots": int(len(snapshots)),
            "equity_curve_rows": int(len(equity_curve)),
            "attribution_rows": int(len(attribution)),
            "unrealized_rows": int(len(unrealized)),
            "ledger_rows": int(len(ledger)),
        },
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "scorecard_csv": str(SCORECARD_CSV),
            "regime_csv": str(REGIME_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("scorecard", [])).to_csv(SCORECARD_CSV, index=False)

    regime_row = pd.DataFrame([report.get("learning_regime", {})])
    if REGIME_CSV.exists():
        old = pd.read_csv(REGIME_CSV)
        regime_hist = pd.concat([old, regime_row], ignore_index=True)
    else:
        regime_hist = regime_row
    regime_hist.to_csv(REGIME_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Investment Learning v2 Report",
        "",
        report.get("summary", ""),
        "",
        "## Learning Regime",
        "",
        "```json",
        json.dumps(report.get("learning_regime", {}), indent=2),
        "```",
        "",
        "## Scorecard",
        "",
    ]

    for row in report.get("scorecard", []):
        lines.append(
            f"- `{row.get('asset')}` score=`{row.get('score')}` status=`{row.get('status')}`"
        )

    lines.extend(["", "## Recommendations", ""])

    for rec in report.get("recommendations", []):
        lines.append(f"- {rec}")

    return "\n".join(lines) + "\n"
