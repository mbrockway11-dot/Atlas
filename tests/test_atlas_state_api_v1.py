"""Tests for Atlas State API v1."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from atlas.investment.state_api.api import (
    get_component,
    get_current_state,
    get_market_context,
    get_portfolio_state,
    get_section,
    get_state_hash,
    list_components,
    list_sections,
)
from atlas.investment.state_api.comparison import (
    compare_states,
)
from atlas.investment.state_api.errors import (
    StateComponentNotFoundError,
    StateSectionNotFoundError,
)
from atlas.investment.state_api.loader import (
    clear_state_cache,
)
from atlas.investment.state_api.validation import (
    validate_state,
)


def sample_state() -> dict:
    return {
        "success": True,
        "version": "atlas_compiler_v1",
        "schema_version": "1.0.0",
        "generated_at": (
            "2026-07-12T00:00:00+00:00"
        ),
        "state_hash": "a" * 64,
        "summary": "Test state.",
        "sections": {
            "market_context": {
                "regime_intelligence": {
                    "regime": {
                        "regime": "TRANSITION"
                    }
                }
            },
            "alpha": {},
            "research": {},
            "ensemble": {},
            "learning": {},
            "governance": {},
            "variants": {},
            "portfolio": {
                "optimized_portfolio": [
                    {
                        "asset": "BTC-USD",
                        "target_weight": 0.60,
                    },
                    {
                        "asset": "CASH",
                        "target_weight": 0.40,
                    },
                ]
            },
        },
        "validation": {
            "all_required_valid": True,
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
        },
        "source": "atlas_compiler_v1",
    }


def write_state(
    tmp_path: Path,
    state: dict | None = None,
) -> Path:
    path = tmp_path / "state.json"

    path.write_text(
        json.dumps(
            state
            if state is not None
            else sample_state()
        ),
        encoding="utf-8",
    )

    return path


def test_get_current_state(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    clear_state_cache()

    state = get_current_state(
        path
    )

    assert state[
        "state_hash"
    ] == "a" * 64


def test_state_returns_defensive_copy(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    first = get_current_state(
        path
    )

    first["sections"][
        "portfolio"
    ].clear()

    second = get_current_state(
        path
    )

    assert (
        "optimized_portfolio"
        in second["sections"][
            "portfolio"
        ]
    )


def test_state_hash_accessor(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    assert (
        get_state_hash(path)
        == "a" * 64
    )


def test_list_sections(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    sections = list_sections(
        path
    )

    assert sections[0] == (
        "market_context"
    )

    assert "portfolio" in sections


def test_get_section(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    portfolio = get_section(
        "portfolio",
        path,
    )

    assert (
        "optimized_portfolio"
        in portfolio
    )


def test_missing_section_raises(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    with pytest.raises(
        StateSectionNotFoundError
    ):
        get_section(
            "missing",
            path,
        )


def test_get_component(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    component = get_component(
        "optimized_portfolio",
        section="portfolio",
        path=path,
    )

    assert len(component) == 2


def test_missing_component_raises(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    with pytest.raises(
        StateComponentNotFoundError
    ):
        get_component(
            "missing",
            path=path,
        )


def test_convenience_accessors(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    assert (
        "regime_intelligence"
        in get_market_context(path)
    )

    assert (
        "optimized_portfolio"
        in get_portfolio_state(path)
    )


def test_list_components(
    tmp_path: Path,
):
    path = write_state(
        tmp_path
    )

    components = list_components(
        path=path
    )

    assert (
        "optimized_portfolio"
        in components
    )


def test_compare_identical_states():
    left = sample_state()
    right = deepcopy(left)

    comparison = compare_states(
        left,
        right,
    )

    assert (
        comparison["identical"]
        is True
    )

    assert not comparison[
        "changed_components"
    ]


def test_compare_changed_component():
    left = sample_state()
    right = deepcopy(left)

    right["state_hash"] = "b" * 64

    right["sections"][
        "portfolio"
    ][
        "optimized_portfolio"
    ][0][
        "target_weight"
    ] = 0.50

    comparison = compare_states(
        left,
        right,
    )

    assert (
        comparison["identical"]
        is False
    )

    assert (
        "portfolio.optimized_portfolio"
        in comparison[
            "changed_components"
        ]
    )


def test_validate_state_contract():
    validation = validate_state(
        sample_state()
    )

    assert (
        validation["success"]
        is True
    )

    assert (
        validation[
            "component_count"
        ]
        == 2
    )


def test_api_never_issues_execution():
    validation = validate_state(
        sample_state()
    )

    assert (
        validation["contract"][
            "execution_instruction"
        ]
        is False
    )
