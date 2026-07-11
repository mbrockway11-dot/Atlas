"""Regime Intelligence v1 report orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.regime_intelligence.classifier import (
    classify_regime,
)
from atlas.investment.regime_intelligence.features import (
    build_market_state_history,
)
from atlas.investment.regime_intelligence.loader import (
    load_regime_inputs,
)
from atlas.investment.regime_intelligence.suitability import (
    build_engine_suitability,
)


OUT_DIR = Path(
    "output/investment_regime_intelligence"
)

REPORT_JSON = (
    OUT_DIR
    / "regime_intelligence_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "regime_intelligence_report.md"
)

STATE_HISTORY_CSV = (
    OUT_DIR
    / "market_state_history.csv"
)

CURRENT_STATE_CSV = (
    OUT_DIR
    / "current_market_state.csv"
)

ENGINE_SUITABILITY_CSV = (
    OUT_DIR
    / "engine_regime_suitability.csv"
)

REGIME_HISTORY_CSV = (
    OUT_DIR
    / "regime_history.csv"
)


def build_regime_intelligence_report() -> dict[str, Any]:
    """Build canonical market-regime intelligence."""
    inputs = load_regime_inputs()

    state_history = (
        build_market_state_history(
            inputs["market_history"]
        )
    )

    regime = classify_regime(
        state_history
    )

    engine_suitability = (
        build_engine_suitability(
            regime,
            inputs.get(
                "alpha_engine_summary",
            ),
        )
    )

    if not engine_suitability:
        engine_summary_path = Path(
            "output/investment_alpha_engines/"
            "alpha_engine_summary.csv"
        )

        if (
            engine_summary_path.exists()
            and engine_summary_path.stat().st_size > 0
        ):
            engine_summary = pd.read_csv(
                engine_summary_path
            )

            engine_suitability = (
                build_engine_suitability(
                    regime,
                    engine_summary,
                )
            )

    report = {
        "success": True,
        "version": (
            "regime_intelligence_v1"
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Regime Intelligence v1 classified "
            f"the current market as "
            f"{regime.get('regime')} "
            f"with confidence "
            f"{regime.get('confidence')}."
        ),
        "regime": regime,
        "state_observations": int(
            len(state_history)
        ),
        "engine_suitability": (
            engine_suitability
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "market_state_classifier": True,
            "replaces_learning_regime": False,
            "replaces_ensemble_breadth_regime": False,
            "deterministic": True,
        },
        "outputs": {
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
            "state_history_csv": str(
                STATE_HISTORY_CSV
            ),
            "current_state_csv": str(
                CURRENT_STATE_CSV
            ),
            "engine_suitability_csv": str(
                ENGINE_SUITABILITY_CSV
            ),
            "regime_history_csv": str(
                REGIME_HISTORY_CSV
            ),
        },
    }

    write_outputs(
        report,
        state_history,
        engine_suitability,
    )

    return report


def write_outputs(
    report: dict,
    state_history: pd.DataFrame,
    engine_suitability: list[dict],
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_history.to_csv(
        STATE_HISTORY_CSV,
        index=False,
    )

    if not state_history.empty:
        state_history.tail(1).to_csv(
            CURRENT_STATE_CSV,
            index=False,
        )
    else:
        pd.DataFrame().to_csv(
            CURRENT_STATE_CSV,
            index=False,
        )

    pd.DataFrame(
        engine_suitability
    ).to_csv(
        ENGINE_SUITABILITY_CSV,
        index=False,
    )

    regime = report.get(
        "regime",
        {},
    )

    history_row = {
        "generated_at": report.get(
            "generated_at"
        ),
        "regime": regime.get(
            "regime"
        ),
        "primary_regime": regime.get(
            "primary_regime"
        ),
        "secondary_regime": regime.get(
            "secondary_regime"
        ),
        "confidence": regime.get(
            "confidence"
        ),
        "primary_score": regime.get(
            "primary_score"
        ),
        "secondary_score": regime.get(
            "secondary_score"
        ),
        "score_gap": regime.get(
            "score_gap"
        ),
        "is_transition": regime.get(
            "is_transition"
        ),
        "stability_score": regime.get(
            "stability_score"
        ),
    }

    old = pd.DataFrame()

    if (
        REGIME_HISTORY_CSV.exists()
        and REGIME_HISTORY_CSV.stat().st_size > 0
    ):
        try:
            old = pd.read_csv(
                REGIME_HISTORY_CSV
            )
        except Exception:
            old = pd.DataFrame()

    history = pd.concat(
        [
            old,
            pd.DataFrame([
                history_row
            ]),
        ],
        ignore_index=True,
    )

    history.to_csv(
        REGIME_HISTORY_CSV,
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
    regime = report.get(
        "regime",
        {},
    )

    lines = [
        "# Regime Intelligence v1",
        "",
        report.get(
            "summary",
            "",
        ),
        "",
        "## Current Regime",
        "",
        f"- Regime: `{regime.get('regime')}`",
        (
            "- Primary: "
            f"`{regime.get('primary_regime')}`"
        ),
        (
            "- Secondary: "
            f"`{regime.get('secondary_regime')}`"
        ),
        (
            "- Confidence: "
            f"`{regime.get('confidence')}`"
        ),
        (
            "- Transition: "
            f"`{regime.get('is_transition')}`"
        ),
        (
            "- Stability: "
            f"`{regime.get('stability_score')}`"
        ),
        (
            "- Transition reason: "
            f"{regime.get('transition_reason')}"
        ),
        "",
        "## Component Scores",
        "",
    ]

    for name, value in (
        regime.get(
            "component_scores",
            {},
        )
    ).items():
        lines.append(
            f"- `{name}`: `{value}`"
        )

    lines.extend([
        "",
        "## Engine Suitability",
        "",
    ])

    for row in report.get(
        "engine_suitability",
        [],
    ):
        lines.append(
            "- "
            f"`{row.get('engine_id')}` "
            f"family=`{row.get('family')}` "
            f"suitability="
            f"`{row.get('effective_suitability')}`"
        )

    lines.extend([
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
