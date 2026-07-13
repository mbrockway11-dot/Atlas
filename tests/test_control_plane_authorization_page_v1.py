"""Static dashboard tests for F.4 role enforcement."""

from __future__ import annotations

from pathlib import Path


PAGE = Path(
    "dashboard/pages/"
    "atlas_control_plane.py"
)


def test_page_displays_backend_resolved_role():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "Resolved role:"
        in text
    )

    assert (
        "get_operator_capabilities"
        in text
    )


def test_page_has_no_role_selector():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        'selectbox("Role"',
        "selectbox('Role'",
        "operator_role_selector",
        "set_operator_role",
    ]

    for value in forbidden:
        assert value not in text


def test_controls_are_capability_gated():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "can_create_approval"
        in text
    )

    assert (
        "can_dispatch"
        in text
    )

    assert (
        "can_reconcile"
        in text
    )
