"""Atlas Compiler inventory and validation tables."""

from __future__ import annotations

import pandas as pd


INVENTORY_COLUMNS = [
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


def build_inventory_frame(
    state: dict,
) -> pd.DataFrame:
    """Build the canonical source inventory table."""
    inventory = state.get(
        "inventory",
        [],
    )

    frame = pd.DataFrame(
        inventory
    )

    for column in INVENTORY_COLUMNS:
        if column not in frame.columns:
            frame[column] = None

    return frame[
        INVENTORY_COLUMNS
    ]


def build_validation_frame(
    state: dict,
) -> pd.DataFrame:
    """Build one validation result per component."""
    rows = []

    for component in state.get(
        "inventory",
        [],
    ):
        required = bool(
            component.get(
                "required",
                False,
            )
        )

        valid = bool(
            component.get(
                "valid",
                False,
            )
        )

        if valid:
            validation_status = "PASS"
        elif required:
            validation_status = (
                "FAIL_REQUIRED"
            )
        else:
            validation_status = (
                "WARN_OPTIONAL"
            )

        rows.append({
            "component_id": component.get(
                "component_id"
            ),
            "section": component.get(
                "section"
            ),
            "required": required,
            "exists": bool(
                component.get(
                    "exists",
                    False,
                )
            ),
            "valid": valid,
            "validation_status": (
                validation_status
            ),
            "error": component.get(
                "error",
                "",
            ),
            "sha256": component.get(
                "sha256",
                "",
            ),
        })

    return pd.DataFrame(rows)
