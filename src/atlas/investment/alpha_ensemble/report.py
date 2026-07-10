
"""Alpha Ensemble v4 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha_ensemble.allocation import build_ensemble_allocations
from atlas.investment.alpha_ensemble.loader import load_alpha_ensemble_inputs
from atlas.investment.alpha_ensemble.scoring import score_ensemble
from atlas.investment.alpha_ensemble.signals import extract_candidate_signals


OUT_DIR = Path("output/investment_alpha_ensemble")
REPORT_JSON = OUT_DIR / "alpha_ensemble_report.json"
REPORT_MD = OUT_DIR / "alpha_ensemble_report.md"
SIGNALS_CSV = OUT_DIR / "alpha_ensemble_signals.csv"
SCORES_CSV = OUT_DIR / "alpha_ensemble_scores.csv"
ALLOCATIONS_CSV = OUT_DIR / "alpha_ensemble_allocations.csv"


def build_alpha_ensemble_report() -> dict[str, Any]:
    inputs = load_alpha_ensemble_inputs()
    signals = extract_candidate_signals(inputs)
    scores = score_ensemble(signals, inputs.get("learning", {}) or {}, inputs.get("performance", {}) or {})
    allocations = build_ensemble_allocations(scores)

    report = {
        "success": True,
        "version": "alpha_ensemble_v4",
        "summary": (
            f"Alpha Ensemble v4 combined {len(signals)} signal row(s), "
            f"scored {len(scores)} asset(s), produced {len(allocations)} allocation hint(s)."
        ),
        "text_summary": (
            f"Alpha Ensemble v4 combined {len(signals)} signal row(s), "
            f"scored {len(scores)} asset(s), produced {len(allocations)} allocation hint(s)."
        ),
        "signals": signals,
        "scores": scores,
        "allocations": allocations,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "signals_csv": str(SIGNALS_CSV),
            "scores_csv": str(SCORES_CSV),
            "allocations_csv": str(ALLOCATIONS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("signals", [])).to_csv(SIGNALS_CSV, index=False)
    pd.DataFrame(report.get("scores", [])).to_csv(SCORES_CSV, index=False)
    pd.DataFrame(report.get("allocations", [])).to_csv(ALLOCATIONS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Ensemble v4 Report",
        "",
        report.get("summary", ""),
        "",
        "## Scores",
        "",
    ]

    for row in report.get("scores", []):
        lines.append(
            f"- `{row.get('asset')}` score=`{row.get('ensemble_score')}` action=`{row.get('ensemble_action')}`"
        )

    lines += ["", "## Allocation Hints", ""]

    for row in report.get("allocations", []):
        lines.append(
            f"- `{row.get('asset')}` target=`{row.get('ensemble_target_weight')}`"
        )

    return "\n".join(lines) + "\n"
