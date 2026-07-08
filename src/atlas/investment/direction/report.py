
"""Market Direction Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.direction.exposure import target_market_exposure
from atlas.investment.direction.loader import load_strategy_registry
from atlas.investment.direction.voting import vote_direction


OUT_DIR = Path("output/investment_direction")
REPORT_JSON = OUT_DIR / "market_direction_report.json"
REPORT_MD = OUT_DIR / "market_direction_report.md"
SIGNALS_CSV = OUT_DIR / "market_direction_input_signals.csv"


def build_market_direction_report() -> dict[str, Any]:
    registry = load_strategy_registry()
    vote = vote_direction(registry)
    exposure = target_market_exposure(vote["direction"], vote["confidence"])

    report = {
        "success": True,
        "summary": (
            f"Market Direction Engine classified market as {vote['direction']} "
            f"with confidence {vote['confidence']}."
        ),
        "vote": vote,
        "exposure": exposure,
        "signal_count": int(len(registry)),
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "input_signals_csv": str(SIGNALS_CSV),
        },
    }

    write_outputs(report, registry)
    return report


def write_outputs(report: dict[str, Any], registry: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    registry.to_csv(SIGNALS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Market Direction Report",
        "",
        report.get("summary", ""),
        "",
        "## Vote",
        "",
        "```json",
        json.dumps(report.get("vote", {}), indent=2),
        "```",
        "",
        "## Exposure",
        "",
        "```json",
        json.dumps(report.get("exposure", {}), indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)
