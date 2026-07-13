"""Audit Atlas artifact input-lineage contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from atlas.investment.artifact_lineage import (
    build_lineage_audit,
)


OUTPUT_DIR = Path(
    "output/investment_architecture_audit"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "artifact_lineage_audit.json"
)

EDGES_CSV = (
    OUTPUT_DIR
    / "artifact_lineage_edges.csv"
)

JOB_INPUTS_CSV = (
    OUTPUT_DIR
    / "artifact_lineage_job_inputs.csv"
)


def main() -> int:
    audit = build_lineage_audit()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_JSON.write_text(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    pd.DataFrame(
        audit["edges"]
    ).to_csv(
        EDGES_CSV,
        index=False,
    )

    job_rows = [
        {
            "job_id": result["job_id"],
            "success": result["success"],
            "required_input_count": (
                result[
                    "required_input_count"
                ]
            ),
            "valid_required_input_count": (
                result[
                    "valid_required_input_count"
                ]
            ),
            "missing_or_invalid_required_count": (
                result[
                    "missing_or_invalid_required_count"
                ]
            ),
            "optional_input_count": (
                result[
                    "optional_input_count"
                ]
            ),
            "invalid_optional_count": (
                result[
                    "invalid_optional_count"
                ]
            ),
        }
        for result in audit["jobs"]
    ]

    pd.DataFrame(
        job_rows
    ).to_csv(
        JOB_INPUTS_CSV,
        index=False,
    )

    print(
        "ATLAS ARTIFACT LINEAGE AUDIT "
        + (
            "PASSED"
            if audit["success"]
            else "FAILED"
        )
    )
    print(
        "Input contracts:",
        audit["input_contract_count"],
    )
    print(
        "Registered jobs:",
        audit["registered_job_count"],
    )
    print(
        "Lineage edges:",
        audit["lineage_edge_count"],
    )
    print(
        "Explicit input artifacts:",
        audit[
            "explicit_input_artifact_count"
        ],
    )
    print(
        "Filesystem-incomplete jobs:",
        len(
            audit[
                "incomplete_job_inputs"
            ]
        ),
    )
    print("Report:", REPORT_JSON)
    print("Edges:", EDGES_CSV)
    print("Jobs:", JOB_INPUTS_CSV)

    if audit["registry_errors"]:
        print("Registry errors:")

        for error in audit[
            "registry_errors"
        ]:
            print("-", error)

    return 0 if audit["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
