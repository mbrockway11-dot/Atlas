"""Static safety tests for the G.13 analytics layer."""

from __future__ import annotations

from pathlib import Path


MODULE = Path(
    "src/atlas/investment/"
    "execution/analytics.py"
)


def test_analytics_is_read_only():
    text = MODULE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        "run_paper_execution",
        "PaperBroker(",
        ".submit(",
        "place_order",
        "send_order",
        "write_paper_account",
        "api_secret",
        "private_key",
        "live_execution=True",
    ]

    for value in forbidden:
        assert value not in text


def test_analytics_declares_safety_contract():
    text = MODULE.read_text(
        encoding="utf-8"
    )

    assert (
        '"read_only": True'
        in text
    )

    assert (
        '"verified_records_only": True'
        in text
    )

    assert (
        '"submits_orders": False'
        in text
    )
