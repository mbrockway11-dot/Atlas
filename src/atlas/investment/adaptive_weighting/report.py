
"""Adaptive Weighting v5 report/export."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.adaptive_weighting.loader import (
    load_adaptive_weighting_inputs,
)
from atlas.investment.adaptive_weighting.weighting import (
    build_adaptive_weights,
)


OUT_DIR = Path(
    "output/investment_adaptive_weighting"
)
REPORT_JSON = (
    OUT_DIR / "adaptive_weighting_report.json"
)
REPORT_MD = (
    OUT_DIR / "adaptive_weighting_report.md"
)
WEIGHTS_CSV = OUT_DIR / "adaptive_weights.csv"


def build_adaptive_weighting_report() -> dict[str, Any]:
    result = build_adaptive_weights(
        load_adaptive_weighting_inputs()
    )

    summary = (
        "Adaptive Weighting v5 preserved Alpha Ensemble "
        f"v5.1 regime exposure at "
        f"{result.get('adaptive_risky_weight', 0.0):.1%} risky / "
        f"{result.get('adaptive_cash_weight', 0.0):.1%} cash "
        f"and produced {len(result.get('rows', []))} "
        "adaptive weight row(s)."
    )

    report = {
        "success": result.get(
            "success",
            False,
        ),
        "version": "adaptive_weighting_v5",
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": summary,
        "text_summary": summary,
        **result,
        "contract": {
            "authoritative_allocation_source": (
                "alpha_ensemble_v5_1"
            ),
            "cash_boundary_preserved": True,
            "risky_boundary_preserved": True,
            "registry_modifies_relative_weights_only": True,
            "learning_modifies_relative_weights_only": True,
            "portfolio_gross_override_applied": False,
            "execution_instruction": False,
        },
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "weights_csv": str(WEIGHTS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(
    report: dict[str, Any],
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        report.get("rows", [])
    ).to_csv(
        WEIGHTS_CSV,
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


def build_markdown(
    report: dict[str, Any],
) -> str:
    lines = [
        "# Adaptive Weighting v5 Report",
        "",
        report.get("summary", ""),
        "",
        "## Regime Boundary",
        "",
        f"- Ensemble risky: "
        f"`{report.get('ensemble_risky_weight')}`",
        f"- Adaptive risky: "
        f"`{report.get('adaptive_risky_weight')}`",
        f"- Ensemble cash: "
        f"`{report.get('ensemble_cash_weight')}`",
        f"- Adaptive cash: "
        f"`{report.get('adaptive_cash_weight')}`",
        f"- Preserved: "
        f"`{report.get('regime_preserved')}`",
        "",
        "## Adaptive Weights",
        "",
    ]

    for row in report.get("rows", []):
        lines.append(
            f"- `{row.get('asset')}` "
            f"adaptive_weight=`{row.get('adaptive_weight')}` "
            f"base=`{row.get('base_weight')}` "
            f"registry_multiplier="
            f"`{row.get('registry_multiplier')}`"
        )

    if report.get("issues"):
        lines.extend([
            "",
            "## Issues",
            "",
            "```json",
            json.dumps(
                report.get("issues"),
                indent=2,
            ),
            "```",
        ])

    return "\n".join(lines) + "\n"
