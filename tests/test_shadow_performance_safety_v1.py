"""Static safety checks for the G.14 historical ledger."""

from __future__ import annotations

from pathlib import Path


MODULE = Path(
    "src/atlas/investment/"
    "execution/performance_ledger.py"
)


def test_performance_ledger_is_observational():
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


def test_performance_ledger_declares_contract():
    text = MODULE.read_text(
        encoding="utf-8"
    )

    assert (
        '"append_only_source": True'
        in text
    )

    assert (
        '"hash_chained": True'
        in text
    )

    assert (
        '"read_only_views": True'
        in text
    )

    assert (
        '"submits_orders": False'
        in text
    )
