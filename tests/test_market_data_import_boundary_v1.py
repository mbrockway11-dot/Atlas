"""Regression tests for execution and market-data package boundaries."""

from __future__ import annotations

import subprocess
import sys


def run_import(statement: str):
    return subprocess.run(
        [
            sys.executable,
            "-c",
            statement,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_market_data_imports_before_execution_pipeline():
    result = run_import(
        "from atlas.investment.market_data import "
        "LATEST_MARKET_SNAPSHOT_JSON, MarketDataRouter; "
        "print(LATEST_MARKET_SNAPSHOT_JSON); "
        "print(MarketDataRouter)"
    )

    assert result.returncode == 0, (
        result.stderr
    )


def test_shadow_pipeline_imports_directly():
    result = run_import(
        "from atlas.investment.execution.shadow_pipeline "
        "import run_shadow_pipeline; "
        "print(run_shadow_pipeline)"
    )

    assert result.returncode == 0, (
        result.stderr
    )


def test_market_data_then_shadow_pipeline_imports():
    result = run_import(
        "import atlas.investment.market_data; "
        "from atlas.investment.execution.shadow_pipeline "
        "import run_shadow_pipeline; "
        "print(run_shadow_pipeline)"
    )

    assert result.returncode == 0, (
        result.stderr
    )


def test_shadow_pipeline_then_market_data_imports():
    result = run_import(
        "from atlas.investment.execution.shadow_pipeline "
        "import run_shadow_pipeline; "
        "import atlas.investment.market_data; "
        "print(run_shadow_pipeline)"
    )

    assert result.returncode == 0, (
        result.stderr
    )
