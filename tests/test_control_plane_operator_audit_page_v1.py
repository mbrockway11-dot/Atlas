"""Static dashboard safety tests for the F.3 operator audit UI."""

from __future__ import annotations

from pathlib import Path


PAGE = Path(
    "dashboard/pages/"
    "atlas_control_plane.py"
)


def test_page_has_operator_audit_view():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "Operator Audit Trail"
        in text
    )

    assert (
        "render_operator_audit"
        in text
    )


def test_page_uses_session_identity():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "atlas_operator_session_id"
        in text
    )

    assert (
        "atlas_operator_identity"
        in text
    )


def test_page_does_not_display_sensitive_audit_values():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        '["signature"]',
        '["nonce"]',
        '["secret"]',
        "ATLAS_APPROVAL_SECRET",
    ]

    for value in forbidden:
        assert value not in text
