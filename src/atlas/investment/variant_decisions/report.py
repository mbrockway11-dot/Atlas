"""Manual Variant Decision Ledger v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.variant_decisions.builder import (
    build_current_ledger_rows,
    merge_preserving_manual_decisions,
)
from atlas.investment.variant_decisions.config import (
    APPROVED_CSV,
    ARCHIVED_CSV,
    DECISION_HISTORY_CSV,
    DEFERRED_CSV,
    IMPLEMENTATION_QUEUE_CSV,
    LEDGER_CSV,
    OUTPUT_DIR,
    REJECTED_CSV,
    REPORT_JSON,
    REPORT_MD,
    REVISIT_CSV,
    SCHEMA_VERSION,
    VERSION,
)
from atlas.investment.variant_decisions.loader import (
    load_variant_decision_inputs,
    safe_read_csv,
)
from atlas.investment.variant_decisions.outputs import (
    build_decision_outputs,
)


def build_variant_decision_report() -> dict[str, Any]:
    """Synchronize board evidence without overwriting human decisions."""
    inputs = load_variant_decision_inputs()

    incoming = build_current_ledger_rows(
        inputs["review_board"],
        inputs["variant_registry"],
    )

    existing = safe_read_csv(
        LEDGER_CSV
    )

    ledger, merge_stats = (
        merge_preserving_manual_decisions(
            existing,
            incoming,
        )
    )

    decision_outputs = (
        build_decision_outputs(
            ledger
        )
    )

    decision_counts = (
        ledger[
            "manual_decision"
        ].astype(str)
        .str.upper()
        .value_counts()
        .to_dict()
        if not ledger.empty
        else {}
    )

    report = {
        "success": bool(
            not ledger.empty
        ),
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Manual Variant Decision Ledger v1 "
            f"contains {len(ledger)} variant record(s), "
            f"preserved {merge_stats['preserved_manual_rows']} "
            f"manual decision(s), and produced "
            f"{len(decision_outputs['implementation_queue'])} "
            "implementation queue row(s)."
        ),
        "counts": {
            "ledger_rows": int(
                len(ledger)
            ),
            "approved_rows": int(
                len(
                    decision_outputs[
                        "approved"
                    ]
                )
            ),
            "rejected_rows": int(
                len(
                    decision_outputs[
                        "rejected"
                    ]
                )
            ),
            "archived_rows": int(
                len(
                    decision_outputs[
                        "archived"
                    ]
                )
            ),
            "deferred_rows": int(
                len(
                    decision_outputs[
                        "deferred"
                    ]
                )
            ),
            "revisit_rows": int(
                len(
                    decision_outputs[
                        "revisit"
                    ]
                )
            ),
            "implementation_queue_rows": int(
                len(
                    decision_outputs[
                        "implementation_queue"
                    ]
                )
            ),
            **merge_stats,
        },
        "decision_counts": (
            decision_counts
        ),
        "ledger_preview": (
            ledger.head(20).to_dict(
                orient="records"
            )
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_engine_registry": False,
            "changes_engine_code": False,
            "changes_optimizer": False,
            "manual_decisions_are_authoritative": True,
            "never_overwrite_human_decisions": True,
            "board_evidence_can_refresh": True,
            "manual_decision_requires_explicit_command": True,
            "approved_variants_can_self_implement": False,
            "approved_variants_are_production_eligible": False,
            "deterministic_given_inputs": True,
        },
        "outputs": {
            "ledger_csv": str(
                LEDGER_CSV
            ),
            "decision_history_csv": str(
                DECISION_HISTORY_CSV
            ),
            "approved_csv": str(
                APPROVED_CSV
            ),
            "rejected_csv": str(
                REJECTED_CSV
            ),
            "archived_csv": str(
                ARCHIVED_CSV
            ),
            "deferred_csv": str(
                DEFERRED_CSV
            ),
            "revisit_csv": str(
                REVISIT_CSV
            ),
            "implementation_queue_csv": str(
                IMPLEMENTATION_QUEUE_CSV
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
        report,
        ledger,
        decision_outputs,
    )

    return report


def write_outputs(
    report: dict,
    ledger: pd.DataFrame,
    outputs: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ledger.to_csv(
        LEDGER_CSV,
        index=False,
    )

    if not DECISION_HISTORY_CSV.exists():
        pd.DataFrame().to_csv(
            DECISION_HISTORY_CSV,
            index=False,
        )

    outputs[
        "approved"
    ].to_csv(
        APPROVED_CSV,
        index=False,
    )

    outputs[
        "rejected"
    ].to_csv(
        REJECTED_CSV,
        index=False,
    )

    outputs[
        "archived"
    ].to_csv(
        ARCHIVED_CSV,
        index=False,
    )

    outputs[
        "deferred"
    ].to_csv(
        DEFERRED_CSV,
        index=False,
    )

    outputs[
        "revisit"
    ].to_csv(
        REVISIT_CSV,
        index=False,
    )

    outputs[
        "implementation_queue"
    ].to_csv(
        IMPLEMENTATION_QUEUE_CSV,
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
        "# Manual Variant Decision Ledger v1",
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
        "## Variant Decisions",
        "",
    ]

    for row in report.get(
        "ledger_preview",
        [],
    ):
        lines.extend([
            (
                f"### {row.get('variant_id')}"
            ),
            "",
            (
                f"- Variant: "
                f"`{row.get('variant_name')}`"
            ),
            (
                f"- Board recommendation: "
                f"`{row.get('board_recommendation')}`"
            ),
            (
                f"- Board score: "
                f"`{row.get('board_score')}`"
            ),
            (
                f"- Human decision: "
                f"`{row.get('manual_decision')}`"
            ),
            (
                f"- Reviewer: "
                f"`{row.get('manual_reviewer')}`"
            ),
            (
                f"- Implementation status: "
                f"`{row.get('implementation_status')}`"
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
