"""Canonical Atlas state construction."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from atlas.investment.atlas_compiler.config import (
    SCHEMA_VERSION,
    SOURCE,
    VERSION,
)


SECTION_ORDER = [
    "market_context",
    "alpha",
    "research",
    "ensemble",
    "learning",
    "governance",
    "variants",
    "portfolio",
]


def compile_atlas_state(
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compile all valid source artifacts into one canonical state."""
    sections = {
        section: {}
        for section in SECTION_ORDER
    }

    inventory = []
    required_failures = []
    optional_failures = []

    for source in sorted(
        sources,
        key=lambda row: (
            str(row.get("section", "")),
            str(row.get("component_id", "")),
        ),
    ):
        component_id = str(
            source.get(
                "component_id",
                ""
            )
        )

        section = str(
            source.get(
                "section",
                "unclassified",
            )
        )

        valid = bool(
            source.get(
                "valid",
                False,
            )
        )

        required = bool(
            source.get(
                "required",
                False,
            )
        )

        inventory_row = {
            key: source.get(key)
            for key in [
                "component_id",
                "section",
                "path",
                "source_type",
                "required",
                "exists",
                "valid",
                "error",
                "sha256",
                "row_count",
            ]
        }

        inventory.append(
            inventory_row
        )

        if not valid:
            if required:
                required_failures.append(
                    component_id
                )
            else:
                optional_failures.append(
                    component_id
                )

            continue

        if section not in sections:
            sections[section] = {}

        sections[section][
            component_id
        ] = source.get("payload")

    canonical_payload = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "sections": sections,
        "source_hashes": {
            row["component_id"]: row[
                "sha256"
            ]
            for row in inventory
            if row.get("sha256")
        },
    }

    state_hash = hash_payload(
        canonical_payload
    )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    return {
        "success": (
            len(required_failures) == 0
        ),
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "state_hash": state_hash,
        "summary": (
            "Atlas Compiler v1 assembled "
            f"{sum(len(value) for value in sections.values())} "
            f"valid component(s) across "
            f"{len(sections)} canonical section(s)."
        ),
        "sections": sections,
        "inventory": inventory,
        "validation": {
            "required_component_count": sum(
                bool(row.get("required"))
                for row in inventory
            ),
            "valid_required_components": sum(
                bool(row.get("required"))
                and bool(row.get("valid"))
                for row in inventory
            ),
            "invalid_required_components": (
                required_failures
            ),
            "invalid_optional_components": (
                optional_failures
            ),
            "all_required_valid": (
                len(required_failures) == 0
            ),
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "canonical_state": True,
            "changes_upstream_artifacts": False,
            "changes_engine_code": False,
            "changes_engine_registry": False,
            "changes_portfolio": False,
            "changes_manual_decisions": False,
            "state_hash_excludes_generated_at": True,
            "deterministic_given_inputs": True,
        },
        "source": SOURCE,
    }


def hash_payload(
    payload: dict,
) -> str:
    """Create a deterministic hash of canonical compiler content."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()
