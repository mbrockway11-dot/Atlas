"""Variant Review Board v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.variant_review.config import (
    APPROVED_CSV,
    BOARD_CSV,
    HELD_CSV,
    IMPLEMENTATION_BACKLOG_CSV,
    MORE_RESEARCH_CSV,
    OUTPUT_DIR,
    REJECTED_CSV,
    REPORT_JSON,
    REPORT_MD,
    REVIEW_QUEUE_CSV,
    SCHEMA_VERSION,
    VERSION,
)
from atlas.investment.variant_review.evidence import (
    build_supporting_maps,
)
from atlas.investment.variant_review.loader import (
    load_variant_review_inputs,
)
from atlas.investment.variant_review.outputs import (
    split_review_outputs,
)
from atlas.investment.variant_review.scoring import (
    build_review_board,
)


def build_variant_review_report() -> dict[str, Any]:
    """Score and organize validated variants for manual review."""
    inputs = load_variant_review_inputs()

    maps = build_supporting_maps(
        validation_folds=inputs[
            "validation_folds"
        ],
        research_priorities=inputs[
            "research_priorities"
        ],
        learning_memory=inputs[
            "learning_memory"
        ],
        governance_snapshots=inputs[
            "governance_snapshots"
        ],
        engine_performance=inputs[
            "engine_performance"
        ],
        conflicts=inputs[
            "conflicts"
        ],
        longitudinal_evidence=inputs[
            "accumulated_variant_evidence"
        ],
    )

    board = build_review_board(
        inputs["registry"],
        maps,
    )

    outputs = split_review_outputs(
        board
    )

    decision_counts = (
        board[
            "recommended_decision"
        ].value_counts().to_dict()
        if not board.empty
        else {}
    )

    report = {
        "success": bool(
            not board.empty
        ),
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Variant Review Board v1 evaluated "
            f"{len(board)} registered variant(s), "
            f"recommended {len(outputs['approved'])} "
            f"for approval, held {len(outputs['held'])}, "
            f"rejected {len(outputs['rejected'])}, and "
            f"requested more research for "
            f"{len(outputs['more_research'])}."
        ),
        "counts": {
            "registry_rows": int(
                len(
                    inputs["registry"]
                )
            ),
            "board_rows": int(
                len(board)
            ),
            "recommended_approvals": int(
                len(
                    outputs["approved"]
                )
            ),
            "held": int(
                len(outputs["held"])
            ),
            "rejected": int(
                len(
                    outputs["rejected"]
                )
            ),
            "more_research": int(
                len(
                    outputs[
                        "more_research"
                    ]
                )
            ),
            "implementation_backlog": int(
                len(
                    outputs["backlog"]
                )
            ),
        },
        "decision_counts": (
            decision_counts
        ),
        "top_variants": (
            board.head(10).to_dict(
                orient="records"
            )
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "creates_engine_code": False,
            "changes_engine_registry": False,
            "changes_research_governance": False,
            "changes_ensemble": False,
            "changes_optimizer": False,
            "recommended_approval_is_manual_approval": False,
            "manual_review_required": True,
            "manual_implementation_required": True,
            "production_activation": False,
            "deterministic_given_inputs": True,
        },
        "outputs": {
            "board_csv": str(
                BOARD_CSV
            ),
            "approved_csv": str(
                APPROVED_CSV
            ),
            "held_csv": str(
                HELD_CSV
            ),
            "rejected_csv": str(
                REJECTED_CSV
            ),
            "more_research_csv": str(
                MORE_RESEARCH_CSV
            ),
            "review_queue_csv": str(
                REVIEW_QUEUE_CSV
            ),
            "implementation_backlog_csv": str(
                IMPLEMENTATION_BACKLOG_CSV
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
        board=board,
        outputs=outputs,
    )

    return report


def write_outputs(
    *,
    report: dict,
    board: pd.DataFrame,
    outputs: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    board.to_csv(
        BOARD_CSV,
        index=False,
    )

    outputs["approved"].to_csv(
        APPROVED_CSV,
        index=False,
    )

    outputs["held"].to_csv(
        HELD_CSV,
        index=False,
    )

    outputs["rejected"].to_csv(
        REJECTED_CSV,
        index=False,
    )

    outputs[
        "more_research"
    ].to_csv(
        MORE_RESEARCH_CSV,
        index=False,
    )

    outputs[
        "review_queue"
    ].to_csv(
        REVIEW_QUEUE_CSV,
        index=False,
    )

    outputs["backlog"].to_csv(
        IMPLEMENTATION_BACKLOG_CSV,
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
        build_markdown(
            report
        ),
        encoding="utf-8",
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Variant Review Board v1",
        "",
        report["summary"],
        "",
        "## Decision Counts",
        "",
        "```json",
        json.dumps(
            report[
                "decision_counts"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Ranked Variants",
        "",
    ]

    for row in report.get(
        "top_variants",
        [],
    ):
        lines.extend([
            (
                f"### Rank {row.get('review_rank')} - "
                f"{row.get('variant_id')}"
            ),
            "",
            (
                f"- Variant: "
                f"`{row.get('variant_name')}`"
            ),
            (
                f"- Parent engine: "
                f"`{row.get('parent_engine_id')}`"
            ),
            (
                f"- Overall score: "
                f"`{row.get('overall_review_score')}`"
            ),
            (
                f"- Recommendation: "
                f"`{row.get('recommended_decision')}`"
            ),
            (
                f"- Reason: "
                f"{row.get('decision_reason')}"
            ),
            (
                f"- Manual review: "
                f"`{row.get('review_status')}`"
            ),
            (
                f"- Production eligible: "
                f"`{row.get('production_eligible')}`"
            ),
            "",
        ])

    lines.extend([
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


