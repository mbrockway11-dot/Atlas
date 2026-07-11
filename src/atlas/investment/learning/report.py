"""Learning Engine v3.1 report and persistent memory exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.learning.adaptive_calibration import (
    aggregate_learning_confidence,
    build_adaptive_recommendations,
)
from atlas.investment.learning.engine_learning import (
    build_engine_learning_recommendations,
)
from atlas.investment.learning.loader import (
    load_learning_inputs,
)
from atlas.investment.learning.market_memory import (
    append_market_memory,
    build_market_memory_snapshot,
)
from atlas.investment.learning.regime_detector import (
    detect_learning_regime,
)
from atlas.investment.learning.strategy_memory import (
    append_strategy_memory,
    build_strategy_memory_snapshot,
    build_strategy_memory_summary,
)
from atlas.investment.learning.strategy_scorecard import (
    build_asset_scorecard,
)


OUT_DIR = Path(
    "output/investment_learning"
)

REPORT_JSON = (
    OUT_DIR
    / "learning_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "learning_report.md"
)

SCORECARD_CSV = (
    OUT_DIR
    / "strategy_scorecard.csv"
)

REGIME_CSV = (
    OUT_DIR
    / "learning_regime_history.csv"
)

STRATEGY_MEMORY_CSV = (
    OUT_DIR
    / "strategy_memory.csv"
)

STRATEGY_MEMORY_SUMMARY_CSV = (
    OUT_DIR
    / "strategy_memory_summary.csv"
)

ENGINE_RECOMMENDATIONS_CSV = (
    OUT_DIR
    / "engine_learning_recommendations.csv"
)

MARKET_MEMORY_CSV = (
    OUT_DIR
    / "market_memory.csv"
)


def build_learning_report() -> dict[str, Any]:
    """Build Learning Engine v3.1 without changing execution."""
    inputs = load_learning_inputs()

    regime = detect_learning_regime(
        inputs["performance"],
        inputs["equity_curve"],
    )

    scorecard = build_asset_scorecard(
        inputs["attribution"],
        inputs["broker_fills"],
    )

    confidence = aggregate_learning_confidence(
        regime,
        scorecard,
    )

    recommendations = build_adaptive_recommendations(
        regime,
        scorecard,
        inputs["risk"],
    )

    strategy_snapshot = (
        build_strategy_memory_snapshot(
            inputs["research_decisions"]
        )
    )

    strategy_memory = append_strategy_memory(
        strategy_snapshot,
        STRATEGY_MEMORY_CSV,
    )

    strategy_summary = (
        build_strategy_memory_summary(
            strategy_memory
        )
    )

    engine_recommendations = (
        build_engine_learning_recommendations(
            strategy_summary
        )
    )

    market_snapshot = (
        build_market_memory_snapshot(
            inputs["ensemble_report"],
            inputs["ensemble_scores"],
        )
    )

    market_memory = append_market_memory(
        market_snapshot,
        MARKET_MEMORY_CSV,
    )

    report = {
        "success": True,
        "version": "learning_engine_v3_1",
        "summary": (
            "Learning Engine v3.1 evaluated "
            f"{len(scorecard)} asset scorecard row(s), "
            f"{len(strategy_summary)} strategy-memory row(s), "
            f"and {len(engine_recommendations)} engine "
            "recommendation(s). "
            f"Regime: {regime.get('learning_regime')}. "
            f"Confidence={confidence}."
        ),
        "learning_regime": regime,
        "learning_confidence": confidence,
        "scorecard": scorecard,
        "recommendations": recommendations,
        "strategy_memory": (
            strategy_summary.to_dict(
                orient="records"
            )
        ),
        "engine_recommendations": (
            engine_recommendations
        ),
        "market_memory_latest": (
            market_memory.tail(1).to_dict(
                orient="records"
            )
        ),
        "counts": {
            "asset_scorecard_rows": len(
                scorecard
            ),
            "strategy_memory_rows": len(
                strategy_summary
            ),
            "engine_recommendations": len(
                engine_recommendations
            ),
            "market_memory_observations": len(
                market_memory
            ),
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "persistent_strategy_memory": True,
            "persistent_market_memory": True,
            "research_lab_feedback": True,
            "ensemble_v6_feedback": True,
            "downstream_compatibility": True,
        },
        "outputs": {
            "json": str(
                REPORT_JSON
            ),
            "markdown": str(
                REPORT_MD
            ),
            "scorecard_csv": str(
                SCORECARD_CSV
            ),
            "regime_csv": str(
                REGIME_CSV
            ),
            "strategy_memory_csv": str(
                STRATEGY_MEMORY_CSV
            ),
            "strategy_memory_summary_csv": str(
                STRATEGY_MEMORY_SUMMARY_CSV
            ),
            "engine_recommendations_csv": str(
                ENGINE_RECOMMENDATIONS_CSV
            ),
            "market_memory_csv": str(
                MARKET_MEMORY_CSV
            ),
        },
    }

    write_outputs(
        report,
        strategy_summary,
        engine_recommendations,
    )

    return report


def write_outputs(
    report: dict[str, Any],
    strategy_summary: pd.DataFrame,
    engine_recommendations: list[dict],
) -> None:
    """Write deterministic Learning Engine v3.1 outputs."""
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        report.get("scorecard", [])
    ).to_csv(
        SCORECARD_CSV,
        index=False,
    )

    strategy_summary.to_csv(
        STRATEGY_MEMORY_SUMMARY_CSV,
        index=False,
    )

    pd.DataFrame(
        engine_recommendations
    ).to_csv(
        ENGINE_RECOMMENDATIONS_CSV,
        index=False,
    )

    regime_row = {
        **report.get(
            "learning_regime",
            {},
        ),
        "learning_confidence": (
            report.get(
                "learning_confidence"
            )
        ),
    }

    old = pd.DataFrame()

    if (
        REGIME_CSV.exists()
        and REGIME_CSV.stat().st_size > 0
    ):
        try:
            old = pd.read_csv(
                REGIME_CSV
            )
        except Exception:
            old = pd.DataFrame()

    current = pd.DataFrame([
        regime_row
    ])

    history = (
        pd.concat(
            [
                old,
                current,
            ],
            ignore_index=True,
        )
        if not old.empty
        else current
    )

    history.to_csv(
        REGIME_CSV,
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
    """Render Learning Engine v3.1 report."""
    lines = [
        "# Learning Engine v3.1 Report",
        "",
        report.get(
            "summary",
            "",
        ),
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
        "## Existing Recommendations",
        "",
    ]

    for recommendation in report.get(
        "recommendations",
        [],
    ):
        lines.append(
            f"- {recommendation}"
        )

    lines.extend([
        "",
        "## Engine Learning Recommendations",
        "",
    ])

    for row in report.get(
        "engine_recommendations",
        [],
    ):
        lines.append(
            "- "
            f"`{row.get('engine_id')}` "
            f"decision=`{row.get('latest_decision')}` "
            f"reliability=`{row.get('reliability')}` "
            f"recommendation=`{row.get('recommendation')}` "
            f"multiplier=`{row.get('learning_weight_multiplier')}`"
        )

    lines.extend([
        "",
        "## Strategy Memory",
        "",
    ])

    for row in report.get(
        "strategy_memory",
        [],
    ):
        lines.append(
            "- "
            f"`{row.get('engine_id')}` "
            f"status=`{row.get('memory_status')}` "
            f"observations=`{row.get('observation_count')}` "
            f"latest=`{row.get('latest_decision')}` "
            f"trend=`{row.get('promotion_score_trend')}`"
        )

    lines.extend([
        "",
        "## Asset Scorecard",
        "",
    ])

    for row in report.get(
        "scorecard",
        [],
    ):
        lines.append(
            "- "
            f"`{row.get('asset')}` "
            f"confidence=`{row.get('asset_confidence')}` "
            f"recommendation=`{row.get('recommendation')}`"
        )

    return "\n".join(lines) + "\n"
