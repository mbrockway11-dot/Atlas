"""Meta Research Engine v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.meta_research.config import (
    ENGINE_DIAGNOSTICS_CSV,
    FAILURE_MODES_CSV,
    FAMILY_GAPS_CSV,
    FEATURE_INTERACTIONS_CSV,
    HYPOTHESIS_LIBRARY_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    RESEARCH_PRIORITIES_CSV,
    SCHEMA_VERSION,
    VERSION,
)
from atlas.investment.meta_research.diagnostics import (
    build_engine_diagnostics,
)
from atlas.investment.meta_research.evidence import (
    build_research_evidence,
)
from atlas.investment.meta_research.failure_modes import (
    build_engine_failure_modes,
)
from atlas.investment.meta_research.family_gaps import (
    build_engine_family_gaps,
)
from atlas.investment.meta_research.hypotheses import (
    build_hypothesis_library,
)
from atlas.investment.meta_research.interactions import (
    build_feature_interactions,
)
from atlas.investment.meta_research.loader import (
    load_meta_research_inputs,
)
from atlas.investment.meta_research.priorities import (
    build_research_priorities,
)


def build_meta_research_report() -> dict[str, Any]:
    """Build evidence-backed research hypotheses."""
    inputs = load_meta_research_inputs()

    evidence = build_research_evidence(
        inputs["trades"],
        inputs["market_history"],
    )

    diagnostics = build_engine_diagnostics(
        evidence
    )

    interactions = build_feature_interactions(
        evidence
    )

    failure_modes = (
        build_engine_failure_modes(
            interactions
        )
    )

    family_gaps = build_engine_family_gaps(
        diagnostics,
        inputs["research_decisions"],
        inputs["governance_snapshots"],
    )

    hypotheses = build_hypothesis_library(
        interactions,
        failure_modes,
        family_gaps,
    )

    priorities = build_research_priorities(
        hypotheses
    )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    report = {
        "success": bool(
            not evidence.empty
        ),
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": generated_at,
        "summary": (
            "Meta Research Engine v1 analyzed "
            f"{len(evidence)} historical trade row(s), "
            f"{len(diagnostics)} engine(s), "
            f"{len(interactions)} feature-state interaction(s), "
            f"identified {len(failure_modes)} failure mode(s), "
            f"and proposed {len(hypotheses)} hypothesis/hypotheses."
        ),
        "counts": {
            "evidence_rows": int(
                len(evidence)
            ),
            "engine_diagnostics": int(
                len(diagnostics)
            ),
            "feature_interactions": int(
                len(interactions)
            ),
            "failure_modes": int(
                len(failure_modes)
            ),
            "family_gaps": int(
                len(family_gaps)
            ),
            "hypotheses": int(
                len(hypotheses)
            ),
            "research_priorities": int(
                len(priorities)
            ),
        },
        "top_priorities": (
            priorities.head(10).to_dict(
                orient="records"
            )
        ),
        "top_hypotheses": (
            hypotheses.head(10).to_dict(
                orient="records"
            )
        ),
        "methodology": {
            "uses_realized_non_overlapping_trades": True,
            "uses_contemporaneous_features": True,
            "uses_future_features": False,
            "feature_segmentation": (
                "per-engine numeric terciles "
                "and categorical states"
            ),
            "automatic_strategy_generation": False,
            "automatic_parameter_changes": False,
            "statistical_significance_claimed": False,
            "important_limitation": (
                "The engine identifies deterministic "
                "patterns and research candidates. "
                "It does not establish causality, and "
                "every hypothesis requires separate "
                "walk-forward validation."
            ),
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_engine_registry": False,
            "changes_research_governance": False,
            "changes_ensemble_weights": False,
            "creates_executable_code": False,
            "hypothesis_generation_only": True,
            "deterministic_given_inputs": True,
        },
        "outputs": {
            "engine_diagnostics_csv": str(
                ENGINE_DIAGNOSTICS_CSV
            ),
            "feature_interactions_csv": str(
                FEATURE_INTERACTIONS_CSV
            ),
            "failure_modes_csv": str(
                FAILURE_MODES_CSV
            ),
            "family_gaps_csv": str(
                FAMILY_GAPS_CSV
            ),
            "research_priorities_csv": str(
                RESEARCH_PRIORITIES_CSV
            ),
            "hypothesis_library_csv": str(
                HYPOTHESIS_LIBRARY_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_outputs(
        report=report,
        diagnostics=diagnostics,
        interactions=interactions,
        failure_modes=failure_modes,
        family_gaps=family_gaps,
        priorities=priorities,
        hypotheses=hypotheses,
    )

    return report


def write_outputs(
    *,
    report: dict,
    diagnostics: pd.DataFrame,
    interactions: pd.DataFrame,
    failure_modes: pd.DataFrame,
    family_gaps: pd.DataFrame,
    priorities: pd.DataFrame,
    hypotheses: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    diagnostics.to_csv(
        ENGINE_DIAGNOSTICS_CSV,
        index=False,
    )

    interactions.to_csv(
        FEATURE_INTERACTIONS_CSV,
        index=False,
    )

    failure_modes.to_csv(
        FAILURE_MODES_CSV,
        index=False,
    )

    family_gaps.to_csv(
        FAMILY_GAPS_CSV,
        index=False,
    )

    priorities.to_csv(
        RESEARCH_PRIORITIES_CSV,
        index=False,
    )

    hypotheses.to_csv(
        HYPOTHESIS_LIBRARY_CSV,
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
    lines = [
        "# Meta Research Engine v1",
        "",
        report["summary"],
        "",
        "## Research Priorities",
        "",
    ]

    for row in report.get(
        "top_priorities",
        [],
    ):
        lines.append(
            "- "
            f"Rank `{row.get('research_rank')}` — "
            f"`{row.get('research_target')}` "
            f"type=`{row.get('target_type')}` "
            f"priority=`{row.get('priority_score')}` "
            f"confidence=`{row.get('confidence')}`"
        )

    lines.extend([
        "",
        "## Leading Hypotheses",
        "",
    ])

    for row in report.get(
        "top_hypotheses",
        [],
    ):
        lines.extend([
            (
                f"### {row.get('hypothesis_id')}"
            ),
            "",
            (
                f"- Type: "
                f"`{row.get('hypothesis_type')}`"
            ),
            (
                f"- Priority: "
                f"`{row.get('priority')}`"
            ),
            (
                f"- Confidence: "
                f"`{row.get('confidence')}`"
            ),
            (
                f"- Thesis: "
                f"{row.get('thesis')}"
            ),
            (
                f"- Proposed test: "
                f"{row.get('proposed_test')}"
            ),
            "",
        ])

    lines.extend([
        "## Methodology",
        "",
        "```json",
        json.dumps(
            report["methodology"],
            indent=2,
        ),
        "```",
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
