"""Adaptive Research Prioritizer v1 reporting."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.adaptive_research_prioritizer.candidates import (
    build_research_candidates,
)
from atlas.investment.adaptive_research_prioritizer.config import (
    CANDIDATE_SCORES_CSV,
    COVERAGE_GAPS_CSV,
    DUPLICATION_FLAGS_CSV,
    EXPLANATIONS_CSV,
    OUTPUT_DIR,
    PRIORITY_HISTORY_CSV,
    PRIORITY_QUEUE_CSV,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_VERSION,
    SCORE_COMPONENTS_CSV,
    SOURCE,
    STATE_JSON,
    VERSION,
)
from atlas.investment.adaptive_research_prioritizer.loader import (
    load_prioritizer_sources,
)
from atlas.investment.adaptive_research_prioritizer.queue import (
    build_explanations,
    build_priority_queue,
)
from atlas.investment.adaptive_research_prioritizer.scoring import (
    score_research_candidates,
)


def build_adaptive_research_prioritizer_report() -> dict[str, Any]:
    """Build the advisory adaptive research queue."""
    sources = load_prioritizer_sources()

    candidates = build_research_candidates(
        sources
    )

    scored = score_research_candidates(
        candidates,
        sources,
    )

    scores = scored["scores"]

    queue = build_priority_queue(
        scores
    )

    explanations = build_explanations(
        scores
    )

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

    prioritizer_run_id = build_run_id(
        state_hash=state_hash,
        queue=queue,
    )

    recommendation_counts = (
        queue[
            "recommendation"
        ].value_counts().to_dict()
        if not queue.empty
        else {}
    )

    priority_counts = (
        queue[
            "priority_band"
        ].value_counts().to_dict()
        if not queue.empty
        else {}
    )

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "prioritizer_run_id": (
            prioritizer_run_id
        ),
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Adaptive Research Prioritizer v1 "
            f"evaluated {len(candidates)} candidate(s), "
            f"ranked {len(queue)} research item(s), and "
            f"identified "
            f"{recommendation_counts.get('RESEARCH_NOW', 0)} "
            "immediate research priority item(s)."
        ),
        "counts": {
            "candidates": int(
                len(candidates)
            ),
            "ranked_candidates": int(
                len(queue)
            ),
            "rank_eligible": int(
                queue[
                    "rank_eligible"
                ].astype(bool).sum()
            )
            if not queue.empty
            else 0,
            "research_now": int(
                recommendation_counts.get(
                    "RESEARCH_NOW",
                    0,
                )
            ),
            "queue": int(
                recommendation_counts.get(
                    "QUEUE",
                    0,
                )
            ),
            "monitor": int(
                recommendation_counts.get(
                    "MONITOR",
                    0,
                )
            ),
            "defer": int(
                recommendation_counts.get(
                    "DEFER",
                    0,
                )
            ),
        },
        "priority_band_counts": (
            priority_counts
        ),
        "recommendation_counts": (
            recommendation_counts
        ),
        "top_priorities": (
            queue.head(10).to_dict(
                orient="records"
            )
        ),
        "contract": {
            "advisory_only": True,
            "execution_instruction": False,
            "execution_authorized": False,
            "creates_hypotheses": False,
            "executes_research": False,
            "changes_engines": False,
            "changes_portfolio": False,
            "changes_manual_decisions": False,
            "requires_human_approval": True,
            "uses_experiment_history": True,
            "uses_knowledge_graph": True,
            "uses_current_regime": True,
            "penalizes_duplicate_research": True,
            "deterministic_given_sources": True,
        },
        "outputs": {
            "priority_queue_csv": str(
                PRIORITY_QUEUE_CSV
            ),
            "candidate_scores_csv": str(
                CANDIDATE_SCORES_CSV
            ),
            "score_components_csv": str(
                SCORE_COMPONENTS_CSV
            ),
            "duplication_flags_csv": str(
                DUPLICATION_FLAGS_CSV
            ),
            "coverage_gaps_csv": str(
                COVERAGE_GAPS_CSV
            ),
            "explanations_csv": str(
                EXPLANATIONS_CSV
            ),
            "priority_history_csv": str(
                PRIORITY_HISTORY_CSV
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
        queue=queue,
        scores=scores,
        components=scored[
            "components"
        ],
        duplication_flags=scored[
            "duplication_flags"
        ],
        coverage_gaps=scored[
            "coverage_gaps"
        ],
        explanations=explanations,
    )

    return report


def build_run_id(
    *,
    state_hash: str,
    queue: pd.DataFrame,
) -> str:
    payload = {
        "state_hash": state_hash,
        "queue": (
            queue[
                [
                    "candidate_id",
                    "final_priority_score",
                    "recommendation",
                ]
            ].to_dict(
                orient="records"
            )
            if not queue.empty
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

    return f"RPRIO-{digest}"


def write_outputs(
    *,
    report: dict,
    queue: pd.DataFrame,
    scores: pd.DataFrame,
    components: pd.DataFrame,
    duplication_flags: pd.DataFrame,
    coverage_gaps: pd.DataFrame,
    explanations: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    queue.to_csv(
        PRIORITY_QUEUE_CSV,
        index=False,
    )

    scores.to_csv(
        CANDIDATE_SCORES_CSV,
        index=False,
    )

    components.to_csv(
        SCORE_COMPONENTS_CSV,
        index=False,
    )

    duplication_flags.to_csv(
        DUPLICATION_FLAGS_CSV,
        index=False,
    )

    coverage_gaps.to_csv(
        COVERAGE_GAPS_CSV,
        index=False,
    )

    explanations.to_csv(
        EXPLANATIONS_CSV,
        index=False,
    )

    append_history(
        report,
        queue,
    )

    state = {
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "prioritizer_run_id": report[
            "prioritizer_run_id"
        ],
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "counts": report["counts"],
        "priority_band_counts": report[
            "priority_band_counts"
        ],
        "recommendation_counts": report[
            "recommendation_counts"
        ],
        "top_priorities": report[
            "top_priorities"
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
    queue: pd.DataFrame,
) -> None:
    existing = pd.DataFrame()

    if (
        PRIORITY_HISTORY_CSV.exists()
        and PRIORITY_HISTORY_CSV.stat().st_size > 0
    ):
        try:
            existing = pd.read_csv(
                PRIORITY_HISTORY_CSV
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            OSError,
        ):
            existing = pd.DataFrame()

    rows = []

    for _, row in queue.iterrows():
        rows.append({
            "prioritizer_run_id": (
                report[
                    "prioritizer_run_id"
                ]
            ),
            "generated_at": (
                report["generated_at"]
            ),
            "state_hash": (
                report["state_hash"]
            ),
            "candidate_id": row[
                "candidate_id"
            ],
            "priority_rank": row[
                "priority_rank"
            ],
            "final_priority_score": (
                row[
                    "final_priority_score"
                ]
            ),
            "priority_band": row[
                "priority_band"
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
                "prioritizer_run_id",
                "candidate_id",
            ],
            keep="first",
        )

    history.to_csv(
        PRIORITY_HISTORY_CSV,
        index=False,
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Adaptive Research Prioritizer v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Immediate priorities: "
            f"`{report['counts']['research_now']}`"
        ),
        (
            f"- Queue candidates: "
            f"`{report['counts']['queue']}`"
        ),
        "",
        "## Top Research Priorities",
        "",
    ]

    priorities = report.get(
        "top_priorities",
        [],
    )

    if not priorities:
        lines.extend([
            "_No research candidates were available._",
            "",
        ])
    else:
        for row in priorities:
            lines.extend([
                (
                    f"### Rank "
                    f"{row.get('priority_rank')} - "
                    f"{row.get('title')}"
                ),
                "",
                (
                    f"- Candidate: "
                    f"`{row.get('candidate_id')}`"
                ),
                (
                    f"- Score: "
                    f"`{row.get('final_priority_score')}`"
                ),
                (
                    f"- Priority: "
                    f"`{row.get('priority_band')}`"
                ),
                (
                    f"- Recommendation: "
                    f"`{row.get('recommendation')}`"
                ),
                (
                    f"- Action: "
                    f"{row.get('research_action')}"
                ),
                (
                    "- Execution authorized: "
                    f"`{row.get('execution_authorized')}`"
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
