"""Tests for loading and pricing shadow target allocations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment.execution.shadow_pipeline import (
    build_targets,
    load_target_allocations,
)


def test_loads_portfolio_rows(
    tmp_path: Path,
):
    path = tmp_path / "targets.json"

    path.write_text(
        json.dumps({
            "portfolio_rows": [
                {
                    "asset": "BTC-USD",
                    "weight": 0.10,
                },
                {
                    "asset": "GLD",
                    "weight": 0.10,
                },
                {
                    "asset": "CASH",
                    "weight": 0.80,
                },
            ]
        }),
        encoding="utf-8",
    )

    allocations = (
        load_target_allocations(
            path
        )
    )

    assert allocations == {
        "BTC-USD": 0.10,
        "GLD": 0.10,
        "CASH": 0.80,
    }


def test_missing_reference_price_fails():
    with pytest.raises(
        ValueError,
        match=(
            "TARGET_REFERENCE_PRICE_MISSING"
        ),
    ):
        build_targets(
            {
                "BTC-USD": 0.10,
                "GLD": 0.10,
            },
            {
                "BTC-USD": 50_000.0,
            },
        )
