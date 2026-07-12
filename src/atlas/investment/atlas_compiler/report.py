"""Atlas Compiler v1 orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.atlas_compiler.compiler import (
    compile_atlas_state,
)
from atlas.investment.atlas_compiler.config import (
    COMPILED_STATE_JSON,
    COMPILED_STATE_MD,
    COMPONENT_INVENTORY_CSV,
    COMPONENT_VALIDATION_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    STATE_MANIFEST_CSV,
)
from atlas.investment.atlas_compiler.loader import (
    load_compiler_sources,
)
from atlas.investment.atlas_compiler.tables import (
    build_inventory_frame,
    build_validation_frame,
)


def build_atlas_compiler_report() -> dict[str, Any]:
    """Compile all registered Atlas investment state."""
    sources = load_compiler_sources()

    state = compile_atlas_state(
        sources
    )

    inventory = build_inventory_frame(
        state
    )

    validation = build_validation_frame(
        state
    )

    section_counts = {
        section: int(
            len(components)
        )
        for section, components in (
            state["sections"].items()
        )
    }

    report = {
        "success": state["success"],
        "version": state["version"],
        "schema_version": (
            state["schema_version"]
        ),
        "generated_at": (
            state["generated_at"]
        ),
        "state_hash": (
            state["state_hash"]
        ),
        "summary": state["summary"],
        "counts": {
            "registered_sources": int(
                len(sources)
            ),
            "valid_sources": int(
                inventory[
                    "valid"
                ].astype(bool).sum()
            )
            if not inventory.empty
            else 0,
            "invalid_sources": int(
                (
                    ~inventory[
                        "valid"
                    ].astype(bool)
                ).sum()
            )
            if not inventory.empty
            else 0,
            "required_failures": int(
                len(
                    state[
                        "validation"
                    ][
                        "invalid_required_components"
                    ]
                )
            ),
            "sections": section_counts,
        },
        "validation": state[
            "validation"
        ],
        "contract": state[
            "contract"
        ],
        "outputs": {
            "compiled_state_json": str(
                COMPILED_STATE_JSON
            ),
            "compiled_state_markdown": str(
                COMPILED_STATE_MD
            ),
            "component_inventory_csv": str(
                COMPONENT_INVENTORY_CSV
            ),
            "component_validation_csv": str(
                COMPONENT_VALIDATION_CSV
            ),
            "state_manifest_csv": str(
                STATE_MANIFEST_CSV
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
        state=state,
        report=report,
        inventory=inventory,
        validation=validation,
    )

    return report


def write_outputs(
    *,
    state: dict,
    report: dict,
    inventory: pd.DataFrame,
    validation: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    COMPILED_STATE_JSON.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    COMPILED_STATE_MD.write_text(
        build_state_markdown(
            state
        ),
        encoding="utf-8",
    )

    inventory.to_csv(
        COMPONENT_INVENTORY_CSV,
        index=False,
    )

    validation.to_csv(
        COMPONENT_VALIDATION_CSV,
        index=False,
    )

    append_manifest(
        report
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
        build_report_markdown(
            report
        ),
        encoding="utf-8",
    )


def append_manifest(
    report: dict,
) -> None:
    row = {
        "generated_at": report[
            "generated_at"
        ],
        "version": report["version"],
        "schema_version": report[
            "schema_version"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "success": report[
            "success"
        ],
        "registered_sources": report[
            "counts"
        ][
            "registered_sources"
        ],
        "valid_sources": report[
            "counts"
        ][
            "valid_sources"
        ],
        "required_failures": report[
            "counts"
        ][
            "required_failures"
        ],
    }

    existing = pd.DataFrame()

    if (
        STATE_MANIFEST_CSV.exists()
        and STATE_MANIFEST_CSV.stat().st_size > 0
    ):
        try:
            existing = pd.read_csv(
                STATE_MANIFEST_CSV
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            OSError,
        ):
            existing = pd.DataFrame()

    manifest = pd.concat(
        [
            existing,
            pd.DataFrame([
                row
            ]),
        ],
        ignore_index=True,
    )

    manifest.to_csv(
        STATE_MANIFEST_CSV,
        index=False,
    )


def build_state_markdown(
    state: dict,
) -> str:
    lines = [
        "# Atlas Compiled State v1",
        "",
        state["summary"],
        "",
        f"- State hash: `{state['state_hash']}`",
        f"- Generated at: `{state['generated_at']}`",
        f"- Success: `{state['success']}`",
        "",
        "## Canonical Sections",
        "",
    ]

    for section, components in (
        state["sections"].items()
    ):
        lines.append(
            f"### {section}"
        )

        lines.append("")

        if not components:
            lines.append(
                "_No valid components._"
            )
            lines.append("")
            continue

        for component_id, payload in (
            components.items()
        ):
            lines.append(
                f"- `{component_id}`"
            )

            if isinstance(
                payload,
                dict,
            ):
                summary = payload.get(
                    "summary"
                )

                version = payload.get(
                    "version"
                )

                if version:
                    lines.append(
                        f"  - Version: `{version}`"
                    )

                if summary:
                    lines.append(
                        f"  - Summary: {summary}"
                    )

        lines.append("")

    lines.extend([
        "## Validation",
        "",
        "```json",
        json.dumps(
            state["validation"],
            indent=2,
        ),
        "```",
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            state["contract"],
            indent=2,
        ),
        "```",
        "",
    ])

    return "\n".join(lines)


def build_report_markdown(
    report: dict,
) -> str:
    return "\n".join([
        "# Atlas Compiler v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        f"- State hash: `{report['state_hash']}`",
        (
            "- Registered sources: "
            f"`{report['counts']['registered_sources']}`"
        ),
        (
            "- Valid sources: "
            f"`{report['counts']['valid_sources']}`"
        ),
        (
            "- Required failures: "
            f"`{report['counts']['required_failures']}`"
        ),
        "",
        "## Section Counts",
        "",
        "```json",
        json.dumps(
            report["counts"]["sections"],
            indent=2,
        ),
        "```",
        "",
        "## Validation",
        "",
        "```json",
        json.dumps(
            report["validation"],
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
