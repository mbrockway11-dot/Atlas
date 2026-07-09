
"""Learning Engine v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.learning.adaptive_calibration import (
    aggregate_learning_confidence,
    build_adaptive_recommendations,
)
from atlas.investment.learning.loader import load_learning_inputs
from atlas.investment.learning.regime_detector import detect_learning_regime
from atlas.investment.learning.strategy_scorecard import build_asset_scorecard


OUT_DIR = Path("output/investment_learning")
REPORT_JSON = OUT_DIR / "learning_report.json"
REPORT_MD = OUT_DIR / "learning_report.md"
SCORECARD_CSV = OUT_DIR / "strategy_scorecard.csv"
REGIME_CSV = OUT_DIR / "learning_regime_history.csv"


def build_learning_report() -> dict[str, Any]:
    inputs = load_learning_inputs()

    regime = detect_learning_regime(inputs["performance"], inputs["equity_curve"])
    scorecard = build_asset_scorecard(inputs["attribution"], inputs["broker_fills"])
    confidence = aggregate_learning_confidence(regime, scorecard)
    recommendations = build_adaptive_recommendations(regime, scorecard, inputs["risk"])

    report = {
        "success": True,
        "version": "learning_engine_v3",
        "summary": (
            f"Learning Engine v3 evaluated {len(scorecard)} asset scorecard row(s). "
            f"Regime: {regime.get('learning_regime')}. Confidence={confidence}."
        ),
        "learning_regime": regime,
        "learning_confidence": confidence,
        "scorecard": scorecard,
        "recommendations": recommendations,
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

    regime_row = {
        **report.get("learning_regime", {}),
        "learning_confidence": report.get("learning_confidence"),
    }

    old = pd.DataFrame()
    if REGIME_CSV.exists() and REGIME_CSV.stat().st_size > 0:
        try:
            old = pd.read_csv(REGIME_CSV)
        except Exception:
            old = pd.DataFrame()

    history = pd.concat([old, pd.DataFrame([regime_row])], ignore_index=True) if not old.empty else pd.DataFrame([regime_row])
    history.to_csv(REGIME_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Learning Engine v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Recommendations",
        "",
    ]

    for rec in report.get("recommendations", []):
        lines.append(f"- {rec}")

    lines += [
        "",
        "## Scorecard",
        "",
    ]

    for row in report.get("scorecard", []):
        lines.append(
            f"- `{row.get('asset')}` confidence=`{row.get('asset_confidence')}` recommendation=`{row.get('recommendation')}`"
        )

    return "\n".join(lines) + "\n"
