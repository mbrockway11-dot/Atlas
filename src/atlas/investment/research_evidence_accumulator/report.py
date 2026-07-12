"""Atlas Research Evidence Accumulator v1 reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_evidence_accumulator.accumulator import (
    build_accumulated_evidence,
)
from atlas.investment.research_evidence_accumulator.config import (
    CONSISTENCY_CSV,
    CONTRADICTIONS_CSV,
    DECAY_CSV,
    EXPERIMENT_EVIDENCE_CSV,
    HISTORY_CSV,
    OUTPUT_DIR,
    RECOMMENDATIONS_CSV,
    REPORT_JSON,
    REPORT_MD,
    RUN_LINEAGE_CSV,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    SUFFICIENCY_CSV,
    VARIANT_EVIDENCE_CSV,
    VERSION,
)
from atlas.investment.research_evidence_accumulator.history import (
    merge_run_history,
    merge_variant_history,
)
from atlas.investment.research_evidence_accumulator.identity import (
    stable_id,
)
from atlas.investment.research_evidence_accumulator.loader import (
    load_accumulator_sources,
    safe_read_csv,
)


RUN_ARCHIVE_CSV = (
    OUTPUT_DIR
    / "_execution_run_archive.csv"
)

VARIANT_ARCHIVE_CSV = (
    OUTPUT_DIR
    / "_variant_result_archive.csv"
)


def build_research_evidence_accumulator_report() -> dict[str, Any]:
    sources = load_accumulator_sources()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_runs = safe_read_csv(
        RUN_ARCHIVE_CSV
    )

    existing_variants = safe_read_csv(
        VARIANT_ARCHIVE_CSV
    )

    run_history = merge_run_history(
        existing_runs,
        sources.get(
            "execution_runs",
            pd.DataFrame(),
        ),
    )

    variant_history = (
        merge_variant_history(
            existing_variants,
            sources.get(
                "variant_results",
                pd.DataFrame(),
            ),
        )
    )

    run_history.to_csv(
        RUN_ARCHIVE_CSV,
        index=False,
    )

    variant_history.to_csv(
        VARIANT_ARCHIVE_CSV,
        index=False,
    )

    bundle = build_accumulated_evidence(
        program_registry=sources.get(
            "program_registry",
            pd.DataFrame(),
        ),
        run_history=run_history,
        variant_history=variant_history,
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

    generated_at = datetime.now(
        UTC
    ).isoformat()

    accumulator_run_id = stable_id(
        "REVIDRUN",
        {
            "state_hash": state_hash,
            "run_ids": (
                sorted(
                    run_history[
                        "run_id"
                    ].astype(str).tolist()
                )
                if not run_history.empty
                else []
            ),
            "variant_rows": int(
                len(
                    variant_history
                )
            ),
        },
    )

    recommendations = bundle[
        "recommendations"
    ]

    recommendation_counts = (
        recommendations[
            "recommendation"
        ].value_counts().to_dict()
        if not recommendations.empty
        else {}
    )

    durable_variants = (
        int(
            bundle[
                "variant_evidence"
            ][
                "durability_status"
            ].astype(str).eq(
                "DURABLE"
            ).sum()
        )
        if not bundle[
            "variant_evidence"
        ].empty
        else 0
    )

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "accumulator_run_id": (
            accumulator_run_id
        ),
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Research Evidence Accumulator v1 "
            f"combined {len(run_history)} execution run(s), "
            f"evaluated {len(bundle['variant_evidence'])} "
            f"longitudinal variant record(s), identified "
            f"{durable_variants} durable variant(s), and "
            f"produced {len(recommendations)} program "
            "recommendation(s)."
        ),
        "counts": {
            "execution_runs": int(
                len(run_history)
            ),
            "variant_history_rows": int(
                len(
                    variant_history
                )
            ),
            "experiment_evidence_rows": int(
                len(
                    bundle[
                        "experiment_evidence"
                    ]
                )
            ),
            "variant_evidence_rows": int(
                len(
                    bundle[
                        "variant_evidence"
                    ]
                )
            ),
            "durable_variants": (
                durable_variants
            ),
            "contradiction_rows": int(
                len(
                    bundle[
                        "contradictions"
                    ]
                )
            ),
            "decay_rows": int(
                len(
                    bundle["decay"]
                )
            ),
            "sufficiency_rows": int(
                len(
                    bundle[
                        "sufficiency"
                    ]
                )
            ),
            "program_recommendations": int(
                len(
                    recommendations
                )
            ),
        },
        "recommendation_counts": (
            recommendation_counts
        ),
        "top_recommendations": (
            recommendations.head(
                10
            ).to_dict(
                orient="records"
            )
            if not recommendations.empty
            else []
        ),
        "contract": {
            "research_only": True,
            "accumulates_existing_evidence": True,
            "preserves_run_lineage": True,
            "measures_consistency": True,
            "measures_contradictions": True,
            "measures_decay": True,
            "measures_sample_sufficiency": True,
            "changes_program_status": False,
            "program_transition_authorized": False,
            "changes_engines": False,
            "changes_portfolio": False,
            "implementation_authorized": False,
            "production_eligible": False,
            "execution_instruction": False,
            "manual_review_required": True,
        },
        "outputs": {
            "experiment_evidence_csv": str(
                EXPERIMENT_EVIDENCE_CSV
            ),
            "variant_evidence_csv": str(
                VARIANT_EVIDENCE_CSV
            ),
            "run_lineage_csv": str(
                RUN_LINEAGE_CSV
            ),
            "consistency_csv": str(
                CONSISTENCY_CSV
            ),
            "decay_csv": str(
                DECAY_CSV
            ),
            "contradictions_csv": str(
                CONTRADICTIONS_CSV
            ),
            "sufficiency_csv": str(
                SUFFICIENCY_CSV
            ),
            "recommendations_csv": str(
                RECOMMENDATIONS_CSV
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
        bundle=bundle,
        report=report,
    )

    return report


def write_outputs(
    *,
    bundle: dict[str, pd.DataFrame],
    report: dict,
) -> None:
    mappings = {
        "experiment_evidence": (
            EXPERIMENT_EVIDENCE_CSV
        ),
        "variant_evidence": (
            VARIANT_EVIDENCE_CSV
        ),
        "run_lineage": (
            RUN_LINEAGE_CSV
        ),
        "consistency": CONSISTENCY_CSV,
        "decay": DECAY_CSV,
        "contradictions": (
            CONTRADICTIONS_CSV
        ),
        "sufficiency": SUFFICIENCY_CSV,
        "recommendations": (
            RECOMMENDATIONS_CSV
        ),
    }

    for key, path in mappings.items():
        bundle[key].to_csv(
            path,
            index=False,
        )

    append_evidence_history(
        report,
        bundle[
            "recommendations"
        ],
    )

    state = {
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "accumulator_run_id": report[
            "accumulator_run_id"
        ],
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "counts": report["counts"],
        "recommendation_counts": report[
            "recommendation_counts"
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


def append_evidence_history(
    report: dict,
    recommendations: pd.DataFrame,
) -> None:
    existing = safe_read_csv(
        HISTORY_CSV
    )

    rows = []

    for _, row in (
        recommendations.iterrows()
    ):
        rows.append({
            "accumulator_run_id": report[
                "accumulator_run_id"
            ],
            "generated_at": report[
                "generated_at"
            ],
            "state_hash": report[
                "state_hash"
            ],
            "research_program_id": row[
                "research_program_id"
            ],
            "experiment_id": row[
                "experiment_id"
            ],
            "best_variant_id": row[
                "best_variant_id"
            ],
            "best_variant_evidence_score": row[
                "best_variant_evidence_score"
            ],
            "best_variant_durability": row[
                "best_variant_durability"
            ],
            "recommendation": row[
                "recommendation"
            ],
            "program_transition_authorized": False,
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
                "accumulator_run_id",
                "research_program_id",
            ],
            keep="last",
        )

    history.to_csv(
        HISTORY_CSV,
        index=False,
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Atlas Research Evidence Accumulator v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Durable variants: "
            f"`{report['counts']['durable_variants']}`"
        ),
        "",
        "## Recommendation Counts",
        "",
        "```json",
        json.dumps(
            report[
                "recommendation_counts"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Program Recommendations",
        "",
    ]

    recommendations = report.get(
        "top_recommendations",
        [],
    )

    if not recommendations:
        lines.extend([
            "_No accumulated program recommendations are available._",
            "",
        ])
    else:
        for row in recommendations:
            lines.extend([
                (
                    f"### "
                    f"{row.get('research_program_id')}"
                ),
                "",
                (
                    f"- Current status: "
                    f"`{row.get('current_status')}`"
                ),
                (
                    f"- Best variant: "
                    f"`{row.get('best_variant_id')}`"
                ),
                (
                    f"- Evidence score: "
                    f"`{row.get('best_variant_evidence_score')}`"
                ),
                (
                    f"- Durability: "
                    f"`{row.get('best_variant_durability')}`"
                ),
                (
                    f"- Recommendation: "
                    f"`{row.get('recommendation')}`"
                ),
                (
                    f"- Reason: "
                    f"{row.get('recommendation_reason')}"
                ),
                (
                    "- Transition authorized: "
                    f"`{row.get('program_transition_authorized')}`"
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
