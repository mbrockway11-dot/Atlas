"""Atlas Research Experiment Execution Lab v1 reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from atlas.investment.research_experiment_execution.config import (
    ACCEPTANCE_RESULTS_CSV,
    EVIDENCE_SUMMARY_CSV,
    EXCLUSIONS_CSV,
    FOLD_RESULTS_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    RUNS_CSV,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    TRADE_COMPARISON_CSV,
    VALIDATION_CSV,
    VARIANT_RESULTS_CSV,
    VERSION,
)
from atlas.investment.research_experiment_execution.executor import (
    execute_experiment_bundle,
)
from atlas.investment.research_experiment_execution.loader import (
    load_execution_sources,
)


def build_research_experiment_execution_report() -> dict[str, Any]:
    sources = load_execution_sources()

    bundle = execute_experiment_bundle(
        sources
    )

    runs = bundle["runs"]
    variant_results = bundle[
        "variant_results"
    ]

    completed_runs = (
        int(
            runs[
                "run_status"
            ].astype(str).eq(
                "COMPLETED"
            ).sum()
        )
        if not runs.empty
        else 0
    )

    passing_variants = (
        int(
            variant_results[
                "acceptance_passed"
            ].astype(bool).sum()
        )
        if not variant_results.empty
        else 0
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

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Research Experiment Execution Lab v1 "
            f"created {len(runs)} execution run(s), "
            f"completed {completed_runs}, evaluated "
            f"{len(variant_results)} candidate variant(s), "
            f"and found {passing_variants} passing variant(s)."
        ),
        "observation_source_path": (
            sources.get(
                "observation_source_path",
                "",
            )
        ),
        "counts": {
            "runs": int(
                len(runs)
            ),
            "completed_runs": (
                completed_runs
            ),
            "fold_results": int(
                len(
                    bundle[
                        "fold_results"
                    ]
                )
            ),
            "variant_results": int(
                len(
                    variant_results
                )
            ),
            "passing_variants": (
                passing_variants
            ),
            "trade_comparison_rows": int(
                len(
                    bundle[
                        "trade_comparison"
                    ]
                )
            ),
            "acceptance_results": int(
                len(
                    bundle[
                        "acceptance_results"
                    ]
                )
            ),
            "exclusions": int(
                len(
                    bundle[
                        "exclusions"
                    ]
                )
            ),
            "validation_checks": int(
                len(
                    bundle[
                        "validation"
                    ]
                )
            ),
        },
        "contract": {
            "research_only": True,
            "consumes_frozen_designs": True,
            "invents_gates": False,
            "changes_thresholds": False,
            "executes_only_designed_programs": True,
            "non_overlapping_walk_forward": True,
            "embargo_enforced": True,
            "future_data_prohibited": True,
            "changes_engine_code": False,
            "changes_program_status": False,
            "changes_portfolio": False,
            "implementation_authorized": False,
            "production_eligible": False,
            "execution_instruction": False,
            "manual_transition_required": True,
        },
        "outputs": {
            "runs_csv": str(
                RUNS_CSV
            ),
            "fold_results_csv": str(
                FOLD_RESULTS_CSV
            ),
            "variant_results_csv": str(
                VARIANT_RESULTS_CSV
            ),
            "trade_comparison_csv": str(
                TRADE_COMPARISON_CSV
            ),
            "acceptance_results_csv": str(
                ACCEPTANCE_RESULTS_CSV
            ),
            "exclusions_csv": str(
                EXCLUSIONS_CSV
            ),
            "validation_csv": str(
                VALIDATION_CSV
            ),
            "evidence_summary_csv": str(
                EVIDENCE_SUMMARY_CSV
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
    bundle: dict,
    report: dict,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    mappings = {
        "runs": RUNS_CSV,
        "fold_results": (
            FOLD_RESULTS_CSV
        ),
        "variant_results": (
            VARIANT_RESULTS_CSV
        ),
        "trade_comparison": (
            TRADE_COMPARISON_CSV
        ),
        "acceptance_results": (
            ACCEPTANCE_RESULTS_CSV
        ),
        "exclusions": EXCLUSIONS_CSV,
        "validation": VALIDATION_CSV,
        "evidence_summary": (
            EVIDENCE_SUMMARY_CSV
        ),
    }

    for key, path in mappings.items():
        bundle[key].to_csv(
            path,
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
        "observation_source_path": report[
            "observation_source_path"
        ],
        "counts": report["counts"],
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


def build_markdown(
    report: dict,
) -> str:
    return "\n".join([
        "# Atlas Research Experiment Execution Lab v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Observation source: "
            f"`{report['observation_source_path']}`"
        ),
        (
            f"- Completed runs: "
            f"`{report['counts']['completed_runs']}`"
        ),
        (
            f"- Passing variants: "
            f"`{report['counts']['passing_variants']}`"
        ),
        "",
        "## Counts",
        "",
        "```json",
        json.dumps(
            report["counts"],
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
