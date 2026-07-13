"""Tests for portfolio optimizer report normalization."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution.portfolio_bridge import (
    extract_target_rows,
    load_portfolio_targets,
)


def test_extracts_nested_portfolio_rows():
    rows = extract_target_rows({
        "data": {
            "portfolio": [
                {
                    "asset": "BTC-USD",
                    "weight": 0.5,
                }
            ]
        }
    })

    assert len(rows) == 1

    assert (
        rows[0]["asset"]
        == "BTC-USD"
    )


def test_loader_supports_weight_aliases(
    tmp_path: Path,
):
    path = (
        tmp_path / "portfolio.json"
    )

    path.write_text(
        json.dumps({
            "portfolio_rows": [
                {
                    "symbol": "BTC-USD",
                    "portfolio_weight": 0.40,
                    "rank": 1,
                },
                {
                    "ticker": "ETH-USD",
                    "allocation": 0.30,
                    "rank": 2,
                },
                {
                    "asset": "CASH",
                    "weight": 0.30,
                },
            ]
        }),
        encoding="utf-8",
    )

    targets = load_portfolio_targets(
        report_path=path,
        prices={
            "BTC-USD": 50_000.0,
            "ETH-USD": 2_000.0,
        },
    )

    assert [
        target.asset
        for target in targets
    ] == [
        "BTC-USD",
        "ETH-USD",
    ]

    assert [
        target.target_weight
        for target in targets
    ] == [
        0.40,
        0.30,
    ]
