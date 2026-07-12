"""Atlas Research Candidate Consolidator reporting."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_candidate_consolidator.clustering import (
    build_candidate_clusters,
)
from atlas.investment.research_candidate_consolidator.config import (
    AUDIT_CSV,
    CONFLICTS_CSV,
    DIMENSIONS_CSV,
    HISTORY_CSV,
    MEMBERS_CSV,
    OUTPUT_DIR,
    PROGRAMS_CSV,
    PROGRAM_SCORES_CSV,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    UNCONSOLIDATED_CSV,
    VERSION,
)
from atlas.investment.research_candidate_consolidator.enrichment import (
    enrich_candidates,
)
from atlas.investment.research_candidate_consolidator.loader import (
    load_consolidator_sources,
)
from atlas.investment.research_candidate_consolidator.programs import (
    build_research_programs,
)


def build_candidate_consolidator_report() -> dict[str, Any]:
    """Build consolidated research programs."""
    sources = load_consolidator_sources()

    candidates = enrich_candidates(
        sources.get(
            "priority_queue",
            pd.DataFrame(),
        )
    )

    clusters = build_candidate_clusters(
        candidates
    )

    bundle = build_research_programs(
        candidates,
        clusters,
    )

    programs = bundle[
        "programs"
    ]

    generated_at = datetime.now(
        UTC
    ).isoformat()

    state_hash = str(
        sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        )
    )

    run_id = build_run_id(
        state_hash=state_hash,
        programs=programs,
    )

    source_candidate_count = int(
        len(candidates)
    )

    consolidated_candidate_count = int(
        len(
            bundle[
                "members"
            ]
        )
    )

    reduction_ratio = (
        0.0
        if source_candidate_count == 0
        else 1.0
        - (
            len(programs)
            / source_candidate_count
        )
    )

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "consolidator_run_id": (
            run_id
        ),
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Research Candidate Consolidator v1 "
            f"evaluated {source_candidate_count} candidate(s), "
            f"formed {len(programs)} research program(s), "
            f"and linked {consolidated_candidate_count} "
            "candidate membership record(s)."
        ),
        "counts": {
            "source_candidates": (
                source_candidate_count
            ),
            "clusters": int(
                len(clusters)
            ),
            "research_programs": int(
                len(programs)
            ),
            "program_members": int(
                len(
                    bundle[
                        "members"
                    ]
                )
            ),
            "dimensions": int(
                len(
                    bundle[
                        "dimensions"
                    ]
                )
            ),
            "conflicts": int(
                len(
                    bundle[
                        "conflicts"
                    ]
                )
            ),
            "unconsolidated_candidates": int(
                len(
                    bundle[
                        "unconsolidated"
                    ]
                )
            ),
        },
        "reduction_ratio": round(
            reduction_ratio,
            8,
        ),
        "top_programs": (
            programs.head(10).to_dict(
                orient="records"
            )
            if not programs.empty
            else []
        ),
        "contract": {
            "advisory_only": True,
            "execution_instruction": False,
            "execution_authorized": False,
            "changes_source_candidates": False,
            "preserves_candidate_lineage": True,
            "creates_research_programs": True,
            "executes_research": False,
            "changes_engines": False,
            "changes_portfolio": False,
            "requires_human_approval": True,
            "deterministic_given_sources": True,
        },
        "outputs": {
            "programs_csv": str(
                PROGRAMS_CSV
            ),
            "members_csv": str(
                MEMBERS_CSV
            ),
            "dimensions_csv": str(
                DIMENSIONS_CSV
            ),
            "conflicts_csv": str(
                CONFLICTS_CSV
            ),
            "program_scores_csv": str(
                PROGRAM_SCORES_CSV
            ),
            "unconsolidated_csv": str(
                UNCONSOLIDATED_CSV
            ),
            "audit_csv": str(
                AUDIT_CSV
            ),
            "history_csv": str(
                HISTORY_CSV
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
        report=report,
        bundle=bundle,
    )

    return report


def build_run_id(
    *,
    state_hash: str,
    programs: pd.DataFrame,
) -> str:
    payload = {
        "state_hash": state_hash,
        "programs": (
            programs[
                [
                    "research_program_id",
                    "program_priority_score",
                ]
            ].to_dict(
                orient="records"
            )
            if not programs.empty
            else []
        ),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:20]

    return f"RCONS-{digest}"


def write_outputs(
    *,
    report: dict,
    bundle: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    bundle[
        "programs"
    ].to_csv(
        PROGRAMS_CSV,
        index=False,
    )

    bundle[
        "members"
    ].to_csv(
        MEMBERS_CSV,
        index=False,
    )

    bundle[
        "dimensions"
    ].to_csv(
        DIMENSIONS_CSV,
        index=False,
    )

    bundle[
        "conflicts"
    ].to_csv(
        CONFLICTS_CSV,
        index=False,
    )

    bundle[
        "programs"
    ].to_csv(
        PROGRAM_SCORES_CSV,
        index=False,
    )

    bundle[
        "unconsolidated"
    ].to_csv(
        UNCONSOLIDATED_CSV,
        index=False,
    )

    bundle[
        "audit"
    ].to_csv(
        AUDIT_CSV,
        index=False,
    )

    append_history(
        report,
        bundle["programs"],
    )

    state = {
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "consolidator_run_id": report[
            "consolidator_run_id"
        ],
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "counts": report["counts"],
        "reduction_ratio": report[
            "reduction_ratio"
        ],
        "top_programs": report[
            "top_programs"
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
        build_markdown(report),
        encoding="utf-8",
    )


def append_history(
    report: dict,
    programs: pd.DataFrame,
) -> None:
    existing = pd.DataFrame()

    if (
        HISTORY_CSV.exists()
        and HISTORY_CSV.stat().st_size > 0
    ):
        try:
            existing = pd.read_csv(
                HISTORY_CSV
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            OSError,
        ):
            existing = pd.DataFrame()

    rows = []

    for _, row in (
        programs.iterrows()
    ):
        rows.append({
            "consolidator_run_id": (
                report[
                    "consolidator_run_id"
                ]
            ),
            "generated_at": (
                report["generated_at"]
            ),
            "state_hash": (
                report["state_hash"]
            ),
            "research_program_id": row[
                "research_program_id"
            ],
            "program_rank": row[
                "program_rank"
            ],
            "program_priority_score": row[
                "program_priority_score"
            ],
            "member_count": row[
                "member_count"
            ],
            "recommendation": row[
                "recommendation"
            ],
            "execution_instruction": False,
        })

    incoming = pd.DataFrame(rows)

    history = pd.concat(
        [
            existing,
            incoming,
        ],
        ignore_index=True,
    )

    if not history.empty:
        history = history.drop_duplicates(
            subset=[
                "consolidator_run_id",
                "research_program_id",
            ],
            keep="first",
        )

    history.to_csv(
        HISTORY_CSV,
        index=False,
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Atlas Research Candidate Consolidator v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Reduction ratio: "
            f"`{report['reduction_ratio']}`"
        ),
        (
            f"- Conflicts detected: "
            f"`{report['counts']['conflicts']}`"
        ),
        "",
        "## Top Research Programs",
        "",
    ]

    programs = report.get(
        "top_programs",
        [],
    )

    if not programs:
        lines.extend([
            "_No consolidated programs were created._",
            "",
        ])
    else:
        for program in programs:
            lines.extend([
                (
                    f"### Rank "
                    f"{program.get('program_rank')} - "
                    f"{program.get('program_title')}"
                ),
                "",
                (
                    f"- Program: "
                    f"`{program.get('research_program_id')}`"
                ),
                (
                    f"- Engine: "
                    f"`{program.get('parent_engine_id')}`"
                ),
                (
                    f"- Members: "
                    f"`{program.get('member_count')}`"
                ),
                (
                    f"- Dimensions: "
                    f"`{program.get('dimension_count')}`"
                ),
                (
                    f"- Score: "
                    f"`{program.get('program_priority_score')}`"
                ),
                (
                    f"- Confidence: "
                    f"`{program.get('cluster_confidence')}`"
                ),
                (
                    f"- Recommendation: "
                    f"`{program.get('recommendation')}`"
                ),
                (
                    "- Execution authorized: "
                    f"`{program.get('execution_authorized')}`"
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
