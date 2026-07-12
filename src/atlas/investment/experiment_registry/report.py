"""Atlas Experiment Registry v1 orchestration."""

from __future__ import annotations
import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from atlas.common.io import safe_read_csv
from atlas.investment.experiment_registry.builder import (
    build_registry_bundle,
)
from atlas.investment.experiment_registry.config import (
    ARTIFACTS_CSV,
    EXPERIMENTS_CSV,
    METRICS_CSV,
    OBSERVATIONS_CSV,
    ORCHESTRATOR_RUNS_CSV,
    OUTPUT_DIR,
    RELATIONSHIPS_CSV,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    STATUS_HISTORY_CSV,
    VERSION,
)
from atlas.investment.experiment_registry.loader import (
    load_experiment_sources,
)
from atlas.investment.experiment_registry.storage import (
    merge_registry_bundle,
)


PATHS = {
    "experiments": EXPERIMENTS_CSV,
    "observations": OBSERVATIONS_CSV,
    "metrics": METRICS_CSV,
    "artifacts": ARTIFACTS_CSV,
    "relationships": RELATIONSHIPS_CSV,
    "statuses": STATUS_HISTORY_CSV,
    "orchestrator_runs": (
        ORCHESTRATOR_RUNS_CSV
    ),
}


def build_experiment_registry_report() -> dict[str, Any]:
    """Build and persist the append-only experiment registry."""
    sources = load_experiment_sources()

    incoming = build_registry_bundle(
        sources
    )

    existing = {
        name: safe_read_csv(path)
        for name, path in PATHS.items()
    }

    merged, merge_stats = (
        merge_registry_bundle(
            existing=existing,
            incoming=incoming,
        )
    )

    type_counts = (
        merged["experiments"][
            "experiment_type"
        ].value_counts().to_dict()
        if not merged[
            "experiments"
        ].empty
        else {}
    )

    status_counts = (
        merged["experiments"][
            "current_status"
        ].value_counts().to_dict()
        if not merged[
            "experiments"
        ].empty
        else {}
    )

    report = {
        "success": True,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Atlas Experiment Registry v1 contains "
            f"{len(merged['experiments'])} experiment(s), "
            f"{len(merged['observations'])} observation(s), "
            f"{len(merged['metrics'])} metric record(s), "
            f"and {len(merged['relationships'])} "
            "relationship(s)."
        ),
        "counts": {
            "experiments": len(
                merged["experiments"]
            ),
            "observations": len(
                merged["observations"]
            ),
            "metrics": len(
                merged["metrics"]
            ),
            "artifacts": len(
                merged["artifacts"]
            ),
            "relationships": len(
                merged["relationships"]
            ),
            "status_history": len(
                merged["statuses"]
            ),
            "orchestrator_runs": len(
                merged[
                    "orchestrator_runs"
                ]
            ),
        },
        "experiment_type_counts": (
            type_counts
        ),
        "status_counts": (
            status_counts
        ),
        "merge_stats": merge_stats,
        "contract": {
            "append_only": True,
            "read_only_sources": True,
            "execution_instruction": False,
            "changes_experiment_evidence": False,
            "overwrites_existing_observations": False,
            "preserves_rejected_experiments": True,
            "preserves_human_decisions": True,
            "records_compiler_hash": True,
            "records_orchestrator_runs": True,
            "production_eligible": False,
        },
        "outputs": {
            name: str(path)
            for name, path in (
                PATHS.items()
            )
        }
        | {
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
        merged=merged,
        report=report,
    )

    return report


def write_outputs(
    *,
    merged: dict[str, pd.DataFrame],
    report: dict,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name, path in PATHS.items():
        merged[name].to_csv(
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
        "counts": report["counts"],
        "experiment_type_counts": (
            report[
                "experiment_type_counts"
            ]
        ),
        "status_counts": (
            report["status_counts"]
        ),
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
        "# Atlas Experiment Registry v1",
        "",
        report["summary"],
        "",
        "## Experiment Types",
        "",
        "```json",
        json.dumps(
            report[
                "experiment_type_counts"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Current Statuses",
        "",
        "```json",
        json.dumps(
            report[
                "status_counts"
            ],
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
