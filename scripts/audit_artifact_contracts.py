"""Audit canonical Atlas artifact producer/output contracts."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.artifact_contracts import (
    build_contract_audit,
)


OUTPUT_PATH = Path(
    "output/investment_architecture_audit/"
    "artifact_contract_audit.json"
)


def main() -> int:
    audit = build_contract_audit()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        "ATLAS ARTIFACT CONTRACT AUDIT "
        + (
            "PASSED"
            if audit["success"]
            else "FAILED"
        )
    )
    print(
        "Contracts:",
        audit["contract_count"],
    )
    print(
        "Registered jobs:",
        audit["registered_job_count"],
    )
    print(
        "Registered artifacts:",
        audit["registered_artifact_count"],
    )
    print(
        "Assigned artifacts:",
        audit["assigned_artifact_count"],
    )
    print(
        "Unassigned artifacts:",
        audit["unassigned_artifact_count"],
    )
    print(
        "Filesystem-complete jobs:",
        (
            audit["contract_count"]
            - len(
                audit[
                    "failed_job_contracts"
                ]
            )
        ),
    )
    print(
        "Output:",
        OUTPUT_PATH,
    )

    if audit["registry_errors"]:
        print("Registry errors:")

        for error in audit[
            "registry_errors"
        ]:
            print("-", error)

    # Missing runtime outputs are diagnostic and do not make the structural
    # architecture audit fail. Contract registry errors do.
    return 0 if audit["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
