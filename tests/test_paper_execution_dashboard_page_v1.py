"""Static tests for the G.7 read-only Streamlit page."""

from __future__ import annotations

from pathlib import Path


PAGE = Path(
    "dashboard/pages/"
    "paper_execution.py"
)


def test_page_exists_and_renders():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "render_paper_execution_page"
        in text
    )

    assert (
        "Paper Execution"
        in text
    )


def test_page_is_read_only():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        "run_paper_execution",
        "PaperBroker(",
        ".submit(",
        "dispatch",
        "cancel_order",
        "cancel(",
        "api_key",
        "api_secret",
        "exchange_client",
        "broker_client",
        "ATLAS_APPROVAL_SECRET",
    ]

    for value in forbidden:
        assert value not in text


def test_page_displays_required_sections():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    required = [
        "Execution Safety Contract",
        "Portfolio Intent Plan",
        "Latest Paper Execution",
        "Paper Account",
        "Order Lifecycle",
        "Execution History",
    ]

    for value in required:
        assert value in text
