"""Atlas Research Program Manager v1 reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_program_manager.config import (
    ACTIVE_QUEUE_CSV,
    APPROVAL_QUEUE_CSV,
    ARCHIVED_CSV,
    BLOCKED_QUEUE_CSV,
    DEPENDENCIES_CSV,
    EVIDENCE_CSV,
    OUTPUT_DIR,
    PROMOTION_QUEUE_CSV,
    REGISTRY_CSV,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    STATUS_HISTORY_CSV,
    VERSION,
)
from atlas.investment.research_program_manager.evaluation import (
    build_program_dependencies,
    build_program_queues,
    evaluate_program_state,
)
from atlas.investment.research_program_manager.loader import (
    load_program_manager_sources,
    safe_read_csv,
)
from atlas.investment.research_program_manager.registry import (
    build_program_evidence,
    build_program_registry,
)


def build_research_program_manager_report() -> dict[str, Any]:
    """Build and persist authoritative research-program state."""
    sources = load_program_manager_sources()

    existing_registry = safe_read_csv(
        REGISTRY_CSV
    )

    existing_history = safe_read_csv(
        STATUS_HISTORY_CSV
    )

    state_hash = str(
        sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        )
    )

    registry = build_program_registry(
        consolidated_programs=sources[
            "consolidated_programs"
        ],
        existing_registry=existing_registry,
        state_hash=state_hash,
    )

    evidence = build_program_evidence(
        registry=registry,
        members=sources[
            "program_members"
        ],
        dimensions=sources[
            "program_dimensions"
        ],
        conflicts=sources[
            "program_conflicts"
        ],
        state_hash=state_hash,
    )

    dependencies = (
        build_program_dependencies(
            registry=registry,
            members=sources[
                "program_members"
            ],
            conflicts=sources[
                "program_conflicts"
            ],
        )
    )

    registry = evaluate_program_state(
        registry=registry,
        evidence=evidence,
        dependencies=dependencies,
    )

    queues = build_program_queues(
        registry
    )

    status_counts = (
        registry[
            "current_status"
        ].value_counts().to_dict()
        if not registry.empty
        else {}
    )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Research Program Manager v1 "
            f"manages {len(registry)} program(s), "
            f"with {len(queues['approval'])} awaiting approval, "
            f"{len(queues['active'])} active, "
            f"{len(queues['blocked'])} blocked, and "
            f"{len(queues['promotion'])} promotion-ready."
        ),
        "counts": {
            "programs": int(
                len(registry)
            ),
            "status_history": int(
                len(existing_history)
            ),
            "evidence_records": int(
                len(evidence)
            ),
            "dependencies": int(
                len(dependencies)
            ),
            "awaiting_approval": int(
                len(
                    queues["approval"]
                )
            ),
            "active": int(
                len(
                    queues["active"]
                )
            ),
            "blocked": int(
                len(
                    queues["blocked"]
                )
            ),
            "promotion_ready": int(
                len(
                    queues["promotion"]
                )
            ),
            "archived_or_terminal": int(
                len(
                    queues["archived"]
                )
            ),
            "stale_active": int(
                registry[
                    "is_stale"
                ].astype(bool).sum()
            )
            if not registry.empty
            else 0,
        },
        "status_counts": (
            status_counts
        ),
        "top_approval_queue": (
            queues[
                "approval"
            ].head(10).to_dict(
                orient="records"
            )
            if not queues[
                "approval"
            ].empty
            else []
        ),
        "top_active_queue": (
            queues[
                "active"
            ].head(10).to_dict(
                orient="records"
            )
            if not queues[
                "active"
            ].empty
            else []
        ),
        "contract": {
            "authoritative_program_state": True,
            "manual_transitions_only": True,
            "append_only_status_history": True,
            "preserves_human_decisions": True,
            "execution_instruction": False,
            "execution_authorized": False,
            "implementation_authorized": False,
            "production_eligible": False,
            "executes_experiments": False,
            "changes_engines": False,
            "changes_portfolio": False,
            "changes_source_candidates": False,
            "legal_transitions_enforced": True,
            "deterministic_given_sources_and_decisions": True,
        },
        "outputs": {
            "registry_csv": str(
                REGISTRY_CSV
            ),
            "status_history_csv": str(
                STATUS_HISTORY_CSV
            ),
            "evidence_csv": str(
                EVIDENCE_CSV
            ),
            "dependencies_csv": str(
                DEPENDENCIES_CSV
            ),
            "approval_queue_csv": str(
                APPROVAL_QUEUE_CSV
            ),
            "active_queue_csv": str(
                ACTIVE_QUEUE_CSV
            ),
            "blocked_queue_csv": str(
                BLOCKED_QUEUE_CSV
            ),
            "promotion_queue_csv": str(
                PROMOTION_QUEUE_CSV
            ),
            "archived_csv": str(
                ARCHIVED_CSV
            ),
            "state_json": str(
                STATE_JSON
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
        registry=registry,
        history=existing_history,
        evidence=evidence,
        dependencies=dependencies,
        queues=queues,
        report=report,
    )

    return report


def write_outputs(
    *,
    registry: pd.DataFrame,
    history: pd.DataFrame,
    evidence: pd.DataFrame,
    dependencies: pd.DataFrame,
    queues: dict[str, pd.DataFrame],
    report: dict,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    registry.to_csv(
        REGISTRY_CSV,
        index=False,
    )

    history.to_csv(
        STATUS_HISTORY_CSV,
        index=False,
    )

    evidence.to_csv(
        EVIDENCE_CSV,
        index=False,
    )

    dependencies.to_csv(
        DEPENDENCIES_CSV,
        index=False,
    )

    queues[
        "approval"
    ].to_csv(
        APPROVAL_QUEUE_CSV,
        index=False,
    )

    queues[
        "active"
    ].to_csv(
        ACTIVE_QUEUE_CSV,
        index=False,
    )

    queues[
        "blocked"
    ].to_csv(
        BLOCKED_QUEUE_CSV,
        index=False,
    )

    queues[
        "promotion"
    ].to_csv(
        PROMOTION_QUEUE_CSV,
        index=False,
    )

    queues[
        "archived"
    ].to_csv(
        ARCHIVED_CSV,
        index=False,
    )

    state = {
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "counts": report[
            "counts"
        ],
        "status_counts": report[
            "status_counts"
        ],
        "contract": report[
            "contract"
        ],
        "source": SOURCE,
    }

    STATE_JSON.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
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
        "# Atlas Research Program Manager v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Programs: "
            f"`{report['counts']['programs']}`"
        ),
        (
            f"- Awaiting approval: "
            f"`{report['counts']['awaiting_approval']}`"
        ),
        (
            f"- Active: "
            f"`{report['counts']['active']}`"
        ),
        (
            f"- Blocked: "
            f"`{report['counts']['blocked']}`"
        ),
        (
            f"- Promotion ready: "
            f"`{report['counts']['promotion_ready']}`"
        ),
        "",
        "## Status Counts",
        "",
        "```json",
        json.dumps(
            report["status_counts"],
            indent=2,
        ),
        "```",
        "",
        "## Approval Queue",
        "",
    ]

    approval = report.get(
        "top_approval_queue",
        [],
    )

    if not approval:
        lines.extend([
            "_No programs currently await approval._",
            "",
        ])
    else:
        for row in approval:
            lines.extend([
                (
                    f"### {row.get('program_title')}"
                ),
                "",
                (
                    f"- Program: "
                    f"`{row.get('research_program_id')}`"
                ),
                (
                    f"- Engine: "
                    f"`{row.get('parent_engine_id')}`"
                ),
                (
                    f"- Priority score: "
                    f"`{row.get('program_priority_score')}`"
                ),
                (
                    f"- Confidence: "
                    f"`{row.get('cluster_confidence')}`"
                ),
                (
                    f"- Blocked: "
                    f"`{row.get('is_blocked')}`"
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
