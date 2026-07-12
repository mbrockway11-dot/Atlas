"""Atlas State API validation."""

from __future__ import annotations

from typing import Any

from atlas.investment.state_api.api import (
    get_current_state,
    list_components,
    list_sections,
)
from atlas.investment.state_api.config import (
    ALLOWED_SECTIONS,
)


def validate_state(
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the State API contract."""
    current = (
        state
        if state is not None
        else get_current_state()
    )

    sections = current.get(
        "sections",
        {},
    )

    missing_sections = [
        section
        for section in ALLOWED_SECTIONS
        if section not in sections
    ]

    malformed_sections = [
        section
        for section, payload in (
            sections.items()
        )
        if not isinstance(
            payload,
            dict,
        )
    ]

    component_count = sum(
        len(payload)
        for payload in sections.values()
        if isinstance(
            payload,
            dict,
        )
    )

    source_contract = current.get(
        "contract",
        {},
    )

    violations = []

    if source_contract.get(
        "read_only"
    ) is not True:
        violations.append(
            "COMPILED_STATE_NOT_READ_ONLY"
        )

    if source_contract.get(
        "execution_instruction"
    ) is not False:
        violations.append(
            "COMPILED_STATE_EXECUTION_ENABLED"
        )

    if missing_sections:
        violations.append(
            "MISSING_CANONICAL_SECTIONS"
        )

    if malformed_sections:
        violations.append(
            "MALFORMED_CANONICAL_SECTIONS"
        )

    return {
        "success": (
            not violations
        ),
        "state_hash": current.get(
            "state_hash"
        ),
        "section_count": len(
            sections
        ),
        "component_count": (
            component_count
        ),
        "sections": sorted(
            sections
        ),
        "components": sorted(
            {
                component
                for payload in (
                    sections.values()
                )
                if isinstance(
                    payload,
                    dict,
                )
                for component in payload
            }
        ),
        "missing_sections": (
            missing_sections
        ),
        "malformed_sections": (
            malformed_sections
        ),
        "violations": violations,
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_compiled_state": False,
            "stable_access_interface": True,
        },
    }
