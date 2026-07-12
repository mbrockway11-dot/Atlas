"""Atlas compiled-state comparison."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from atlas.investment.state_api.loader import (
    load_compiled_state,
)


def compare_states(
    left: dict[str, Any] | Path | str,
    right: dict[str, Any] | Path | str,
) -> dict[str, Any]:
    """Compare two compiled Atlas states."""
    left_state = resolve_state(left)
    right_state = resolve_state(right)

    left_sections = left_state[
        "sections"
    ]

    right_sections = right_state[
        "sections"
    ]

    all_sections = sorted(
        set(left_sections)
        | set(right_sections)
    )

    section_differences = {}

    added_components = []
    removed_components = []
    changed_components = []
    unchanged_components = []

    for section in all_sections:
        left_payload = left_sections.get(
            section,
            {},
        )

        right_payload = right_sections.get(
            section,
            {},
        )

        left_components = set(
            left_payload
            if isinstance(
                left_payload,
                dict,
            )
            else {}
        )

        right_components = set(
            right_payload
            if isinstance(
                right_payload,
                dict,
            )
            else {}
        )

        added = sorted(
            right_components
            - left_components
        )

        removed = sorted(
            left_components
            - right_components
        )

        changed = []
        unchanged = []

        for component in sorted(
            left_components
            & right_components
        ):
            left_value = left_payload[
                component
            ]

            right_value = right_payload[
                component
            ]

            qualified = (
                f"{section}.{component}"
            )

            if left_value == right_value:
                unchanged.append(
                    component
                )

                unchanged_components.append(
                    qualified
                )
            else:
                changed.append(
                    component
                )

                changed_components.append(
                    qualified
                )

        added_components.extend(
            f"{section}.{component}"
            for component in added
        )

        removed_components.extend(
            f"{section}.{component}"
            for component in removed
        )

        section_differences[
            section
        ] = {
            "added_components": added,
            "removed_components": removed,
            "changed_components": changed,
            "unchanged_components": (
                unchanged
            ),
        }

    return {
        "identical": (
            left_state[
                "state_hash"
            ]
            == right_state[
                "state_hash"
            ]
        ),
        "left_state_hash": left_state[
            "state_hash"
        ],
        "right_state_hash": right_state[
            "state_hash"
        ],
        "added_components": (
            added_components
        ),
        "removed_components": (
            removed_components
        ),
        "changed_components": (
            changed_components
        ),
        "unchanged_components": (
            unchanged_components
        ),
        "section_differences": (
            section_differences
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_state": False,
        },
    }


def resolve_state(
    value: dict[str, Any] | Path | str,
) -> dict[str, Any]:
    if isinstance(value, dict):
        return copy.deepcopy(value)

    return load_compiled_state(
        value,
        use_cache=False,
    )
