"""Safety-contract tests for the G.12 shadow portfolio pipeline."""

from __future__ import annotations

from pathlib import Path


MODULE = Path(
    "src/atlas/investment/"
    "execution/shadow_pipeline.py"
)


def test_pipeline_remains_paper_only():
    text = MODULE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        "live_execution=True",
        "place_order",
        "send_order",
        "api_secret",
        "private_key",
        "broker.submit",
    ]

    for value in forbidden:
        assert value not in text


def test_pipeline_requires_market_audit():
    text = MODULE.read_text(
        encoding="utf-8"
    )

    assert (
        "validate_market_data_audit"
        in text
    )

    assert (
        "MARKET_DATA_AUDIT_INVALID"
        in text
    )
