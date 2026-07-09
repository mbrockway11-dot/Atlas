
"""Adaptive Weighting v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.adaptive_weighting.loader import load_adaptive_weighting_inputs
from atlas.investment.adaptive_weighting.weighting import build_adaptive_weights


OUT_DIR = Path("output/investment_adaptive_weighting")
REPORT_JSON = OUT_DIR / "adaptive_weighting_report.json"
REPORT_MD = OUT_DIR / "adaptive_weighting_report.md"
WEIGHTS_CSV = OUT_DIR / "adaptive_weights.csv"


def build_adaptive_weighting_report() -> dict[str, Any]:
    result = build_adaptive_weights(load_adaptive_weighting_inputs())

    report = {
        "success": True,
        "version": "adaptive_weighting_v3",
        "summary": (
            f"Adaptive Weighting v3 produced {len(result.get('rows', []))} adaptive weight row(s). "
            f"Regime multiplier={result.get('regime_multiplier')}."
        ),
        **result,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "weights_csv": str(WEIGHTS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("rows", [])).to_csv(WEIGHTS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Adaptive Weighting v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Adaptive Weights",
        "",
    ]

    for row in report.get("rows", []):
        lines.append(
            f"- `{row.get('asset')}` adaptive_weight=`{row.get('adaptive_weight')}` "
            f"registry_multiplier=`{row.get('registry_multiplier')}`"
        )

    return "\n".join(lines) + "\n"
