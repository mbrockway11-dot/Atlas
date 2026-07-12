"""Tests for Atlas Compiler v1."""

from __future__ import annotations

from copy import deepcopy

import pandas as pd

from atlas.investment.atlas_compiler.compiler import (
    compile_atlas_state,
)
from atlas.investment.atlas_compiler.tables import (
    build_inventory_frame,
    build_validation_frame,
)


def valid_sources() -> list[dict]:
    return [
        {
            "component_id": (
                "macro_intelligence"
            ),
            "section": (
                "market_context"
            ),
            "path": (
                "macro_report.json"
            ),
            "source_type": "json",
            "required": True,
            "exists": True,
            "valid": True,
            "error": "",
            "sha256": "aaa",
            "row_count": None,
            "payload": {
                "version": "macro_v1",
                "summary": (
                    "Macro context compiled."
                ),
            },
        },
        {
            "component_id": (
                "optimized_portfolio"
            ),
            "section": "portfolio",
            "path": (
                "optimized_portfolio.csv"
            ),
            "source_type": "csv",
            "required": True,
            "exists": True,
            "valid": True,
            "error": "",
            "sha256": "bbb",
            "row_count": 2,
            "payload": [
                {
                    "asset": "BTC-USD",
                    "weight": 0.60,
                },
                {
                    "asset": "CASH",
                    "weight": 0.40,
                },
            ],
        },
    ]


def test_compiler_builds_canonical_sections():
    state = compile_atlas_state(
        valid_sources()
    )

    assert state["success"] is True

    assert (
        "macro_intelligence"
        in state["sections"][
            "market_context"
        ]
    )

    assert (
        "optimized_portfolio"
        in state["sections"][
            "portfolio"
        ]
    )


def test_state_hash_is_deterministic():
    first = compile_atlas_state(
        valid_sources()
    )

    second = compile_atlas_state(
        valid_sources()
    )

    assert (
        first["state_hash"]
        == second["state_hash"]
    )


def test_generated_time_not_in_state_hash():
    first = compile_atlas_state(
        valid_sources()
    )

    second = compile_atlas_state(
        valid_sources()
    )

    assert (
        first["generated_at"]
        != ""
    )

    assert (
        first["state_hash"]
        == second["state_hash"]
    )


def test_required_failure_fails_compiler():
    sources = valid_sources()

    sources[0]["valid"] = False
    sources[0]["error"] = (
        "SOURCE_NOT_FOUND"
    )
    sources[0]["payload"] = None

    state = compile_atlas_state(
        sources
    )

    assert state["success"] is False

    assert (
        "macro_intelligence"
        in state["validation"][
            "invalid_required_components"
        ]
    )


def test_optional_failure_only_warns():
    sources = valid_sources()

    sources.append({
        "component_id": (
            "optional_component"
        ),
        "section": "research",
        "path": "optional.json",
        "source_type": "json",
        "required": False,
        "exists": False,
        "valid": False,
        "error": "SOURCE_NOT_FOUND",
        "sha256": "",
        "row_count": None,
        "payload": None,
    })

    state = compile_atlas_state(
        sources
    )

    assert state["success"] is True

    assert (
        "optional_component"
        in state["validation"][
            "invalid_optional_components"
        ]
    )


def test_inventory_contains_hashes():
    state = compile_atlas_state(
        valid_sources()
    )

    inventory = build_inventory_frame(
        state
    )

    assert not inventory.empty
    assert "sha256" in inventory.columns


def test_validation_marks_required_pass():
    state = compile_atlas_state(
        valid_sources()
    )

    validation = build_validation_frame(
        state
    )

    assert set(
        validation[
            "validation_status"
        ]
    ) == {"PASS"}


def test_compiler_never_issues_execution():
    state = compile_atlas_state(
        valid_sources()
    )

    assert (
        state["contract"][
            "execution_instruction"
        ]
        is False
    )

    assert (
        state["contract"][
            "changes_portfolio"
        ]
        is False
    )
