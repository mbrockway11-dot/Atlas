"""Atlas Research Experiment Designer reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from atlas.investment.research_experiment_designer.config import (
    ACCEPTANCE_CSV,
    DATASETS_CSV,
    DESIGNS_CSV,
    HYPOTHESES_CSV,
    METRICS_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    RISKS_CSV,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    VALIDATION_CSV,
    VARIANTS_CSV,
    VERSION,
    WALK_FORWARD_CSV,
)
from atlas.investment.research_experiment_designer.designer import (
    build_experiment_design_bundle,
)
from atlas.investment.research_experiment_designer.loader import (
    load_designer_sources,
)


def build_research_experiment_designer_report() -> dict[str, Any]:
    sources = load_designer_sources()

    bundle = build_experiment_design_bundle(
        sources
    )

    designs = bundle["designs"]
    validation = bundle["validation"]

    state_hash = str(
        sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        )
    )

    valid_design_count = 0

    if (
        not designs.empty
        and not validation.empty
    ):
        grouped = validation.groupby(
            "experiment_id"
        )["passed"].all()

        valid_design_count = int(
            grouped.sum()
        )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Research Experiment Designer v1 "
            f"created {len(designs)} experiment design(s), "
            f"including {len(bundle['variants'])} candidate "
            f"variant definition(s) and "
            f"{len(bundle['folds'])} walk-forward fold record(s)."
        ),
        "counts": {
            "designs": len(designs),
            "valid_designs": valid_design_count,
            "hypotheses": len(
                bundle["hypotheses"]
            ),
            "variants": len(
                bundle["variants"]
            ),
            "fold_records": len(
                bundle["folds"]
            ),
            "metrics": len(
                bundle["metrics"]
            ),
            "acceptance_criteria": len(
                bundle["criteria"]
            ),
            "dataset_requirements": len(
                bundle["datasets"]
            ),
            "risks": len(
                bundle["risks"]
            ),
            "validation_checks": len(
                validation
            ),
        },
        "contract": {
            "research_only": True,
            "designs_experiments": True,
            "executes_experiments": False,
            "changes_engines": False,
            "changes_portfolio": False,
            "changes_program_status": False,
            "manual_review_required": True,
            "execution_authorized": False,
            "execution_instruction": False,
            "production_eligible": False,
            "future_data_prohibited": True,
            "non_overlapping_walk_forward_required": True,
            "deterministic_given_sources": True,
        },
        "outputs": {
            "designs_csv": str(
                DESIGNS_CSV
            ),
            "hypotheses_csv": str(
                HYPOTHESES_CSV
            ),
            "variants_csv": str(
                VARIANTS_CSV
            ),
            "walk_forward_csv": str(
                WALK_FORWARD_CSV
            ),
            "metrics_csv": str(
                METRICS_CSV
            ),
            "acceptance_csv": str(
                ACCEPTANCE_CSV
            ),
            "datasets_csv": str(
                DATASETS_CSV
            ),
            "risks_csv": str(
                RISKS_CSV
            ),
            "validation_csv": str(
                VALIDATION_CSV
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

    paths = {
        "designs": DESIGNS_CSV,
        "hypotheses": HYPOTHESES_CSV,
        "variants": VARIANTS_CSV,
        "folds": WALK_FORWARD_CSV,
        "metrics": METRICS_CSV,
        "criteria": ACCEPTANCE_CSV,
        "datasets": DATASETS_CSV,
        "risks": RISKS_CSV,
        "validation": VALIDATION_CSV,
    }

    for key, path in paths.items():
        bundle[key].to_csv(
            path,
            index=False,
        )

    state = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
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
        ),
        encoding="utf-8",
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
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
        "# Atlas Research Experiment Designer v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        f"- State hash: `{report['state_hash']}`",
        (
            f"- Valid designs: "
            f"`{report['counts']['valid_designs']}`"
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
