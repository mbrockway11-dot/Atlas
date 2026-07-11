"""Macro-Regime Fusion v1 report orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.macro_regime_fusion.fusion import (
    build_fused_context,
)
from atlas.investment.macro_regime_fusion.loader import (
    load_macro_regime_inputs,
)
from atlas.investment.macro_regime_fusion.modifiers import (
    build_fused_engine_modifiers,
)


OUT_DIR = Path(
    "output/investment_macro_regime_fusion"
)

REPORT_JSON = (
    OUT_DIR
    / "macro_regime_fusion_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "macro_regime_fusion_report.md"
)

ENGINE_MODIFIERS_CSV = (
    OUT_DIR
    / "engine_context_modifiers.csv"
)

HISTORY_CSV = (
    OUT_DIR
    / "macro_regime_fusion_history.csv"
)


def build_macro_regime_fusion_report() -> dict[str, Any]:
    inputs = load_macro_regime_inputs()

    fused_context = build_fused_context(
        inputs["macro_report"],
        inputs["regime_report"],
    )

    engine_modifiers = (
        build_fused_engine_modifiers(
            fused_context,
            inputs["alpha_engine_summary"],
        )
    )

    success = (
        fused_context.get(
            "fused_regime"
        )
        != "INSUFFICIENT_DATA"
    )

    report = {
        "success": success,
        "version": "macro_regime_fusion_v1",
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Macro-Regime Fusion v1 classified "
            f"the unified context as "
            f"{fused_context.get('fused_regime')} "
            f"with confidence "
            f"{fused_context.get('confidence')}."
        ),
        "fused_context": fused_context,
        "engine_context_modifiers": (
            engine_modifiers
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "modifies_engine_eligibility": False,
            "modifies_orders": False,
            "bounded_context_controls": True,
            "research_lab_remains_authoritative": True,
        },
        "outputs": {
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
            "engine_modifiers_csv": str(
                ENGINE_MODIFIERS_CSV
            ),
            "history_csv": str(
                HISTORY_CSV
            ),
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
        report[
            "engine_context_modifiers"
        ]
    ).to_csv(
        ENGINE_MODIFIERS_CSV,
        index=False,
    )

    context = report[
        "fused_context"
    ]

    controls = context.get(
        "controls",
        {},
    )

    history_row = {
        "generated_at": report[
            "generated_at"
        ],
        "fused_regime": context.get(
            "fused_regime"
        ),
        "macro_regime": context.get(
            "macro_regime"
        ),
        "market_regime": context.get(
            "market_regime"
        ),
        "confidence": context.get(
            "confidence"
        ),
        "unified_risk_score": context.get(
            "unified_risk_score"
        ),
        "unified_support_score": context.get(
            "unified_support_score"
        ),
        "risk_budget_multiplier": controls.get(
            "risk_budget_multiplier"
        ),
        "minimum_cash_weight": controls.get(
            "minimum_cash_weight"
        ),
        "conviction_ceiling": controls.get(
            "conviction_ceiling"
        ),
        "volatility_target_multiplier": controls.get(
            "volatility_target_multiplier"
        ),
        "turnover_multiplier": controls.get(
            "turnover_multiplier"
        ),
    }

    previous = pd.DataFrame()

    if (
        HISTORY_CSV.exists()
        and HISTORY_CSV.stat().st_size > 0
    ):
        try:
            previous = pd.read_csv(
                HISTORY_CSV
            )
        except Exception:
            previous = pd.DataFrame()

    pd.concat(
        [
            previous,
            pd.DataFrame([
                history_row
            ]),
        ],
        ignore_index=True,
    ).to_csv(
        HISTORY_CSV,
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
    report: dict,
) -> str:
    context = report[
        "fused_context"
    ]

    controls = context.get(
        "controls",
        {},
    )

    lines = [
        "# Macro-Regime Fusion v1",
        "",
        report["summary"],
        "",
        "## Unified Context",
        "",
        (
            "- Fused regime: "
            f"`{context.get('fused_regime')}`"
        ),
        (
            "- Macro regime: "
            f"`{context.get('macro_regime')}`"
        ),
        (
            "- Market regime: "
            f"`{context.get('market_regime')}`"
        ),
        (
            "- Primary market regime: "
            f"`{context.get('primary_market_regime')}`"
        ),
        (
            "- Confidence: "
            f"`{context.get('confidence')}`"
        ),
        (
            "- Unified risk score: "
            f"`{context.get('unified_risk_score')}`"
        ),
        (
            "- Unified support score: "
            f"`{context.get('unified_support_score')}`"
        ),
        "",
        "## Bounded Controls",
        "",
    ]

    for key, value in controls.items():
        lines.append(
            f"- `{key}`: `{value}`"
        )

    lines.extend([
        "",
        "## Engine Context Modifiers",
        "",
    ])

    for row in report[
        "engine_context_modifiers"
    ]:
        lines.append(
            "- "
            f"`{row.get('engine_id')}` "
            f"family=`{row.get('family')}` "
            f"modifier="
            f"`{row.get('effective_context_modifier')}`"
        )

    lines.extend([
        "",
        "## Reason Codes",
        "",
    ])

    for reason in context.get(
        "reason_codes",
        [],
    ):
        lines.append(
            f"- `{reason}`"
        )

    lines.extend([
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            report["contract"],
            indent=2,
        ),
        "```",
        "",
    ])

    return "\n".join(lines)
