"""Atlas State API v1 validation reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from atlas.investment.state_api.api import (
    get_state_metadata,
)
from atlas.investment.state_api.config import (
    OUTPUT_DIR,
    SCHEMA_VERSION,
    VALIDATION_JSON,
    VALIDATION_MD,
    VERSION,
)
from atlas.investment.state_api.validation import (
    validate_state,
)


def build_state_api_validation_report() -> dict[str, Any]:
    """Validate and report the State API surface."""
    validation = validate_state()

    report = {
        "success": validation[
            "success"
        ],
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Atlas State API v1 exposed "
            f"{validation['section_count']} section(s) "
            f"and {validation['component_count']} "
            "compiled component(s)."
        ),
        "state_metadata": (
            get_state_metadata()
        ),
        "validation": validation,
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "writes_compiled_state": False,
            "writes_upstream_artifacts": False,
            "stable_access_interface": True,
            "defensive_copies": True,
            "deterministic_given_state": True,
        },
        "outputs": {
            "validation_json": str(
                VALIDATION_JSON
            ),
            "validation_markdown": str(
                VALIDATION_MD
            ),
        },
    }

    write_report(
        report
    )

    return report


def write_report(
    report: dict,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    VALIDATION_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    VALIDATION_MD.write_text(
        build_markdown(
            report
        ),
        encoding="utf-8",
    )


def build_markdown(
    report: dict,
) -> str:
    validation = report[
        "validation"
    ]

    return "\n".join([
        "# Atlas State API v1",
        "",
        report["summary"],
        "",
        (
            f"- Success: "
            f"`{report['success']}`"
        ),
        (
            f"- State hash: "
            f"`{validation['state_hash']}`"
        ),
        (
            f"- Sections: "
            f"`{validation['section_count']}`"
        ),
        (
            f"- Components: "
            f"`{validation['component_count']}`"
        ),
        "",
        "## Validation",
        "",
        "```json",
        json.dumps(
            validation,
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
