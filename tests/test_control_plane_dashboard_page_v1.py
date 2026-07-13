"""Static safety tests for the Phase F.1 Streamlit page."""

from __future__ import annotations

from pathlib import Path


PAGE = Path(
    "dashboard/pages/"
    "atlas_control_plane.py"
)


def test_control_plane_page_exists():
    assert PAGE.exists()


def test_control_plane_page_is_read_only():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        "dispatch_approved_plan(",
        "create_approval(",
        "run_research_cycle(",
        "execute_job(",
        "subprocess.run(",
        "subprocess.Popen(",
    ]

    for value in forbidden:
        assert value not in text


def test_control_plane_page_uses_view_model():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "build_control_plane_dashboard_model"
        in text
    )

    assert (
        "Read-only operational view"
        in text
    )
