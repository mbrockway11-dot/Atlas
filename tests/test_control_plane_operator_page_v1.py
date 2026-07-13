"""Static safety tests for F.2 dashboard operator controls."""

from __future__ import annotations

from pathlib import Path


PAGE = Path(
    "dashboard/pages/"
    "atlas_control_plane.py"
)


def test_page_uses_operator_service_boundary():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "create_guarded_approval"
        in text
    )

    assert (
        "dispatch_guarded_approval"
        in text
    )

    assert (
        "reconcile_guarded_dispatch"
        in text
    )


def test_page_does_not_import_raw_execution_services():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        "dispatch_approved_plan",
        (
            "from atlas.investment."
            "control_plane_approval import"
        ),
        "run_research_cycle",
        "execute_job",
        "subprocess.run",
        "subprocess.Popen",
        "ATLAS_APPROVAL_SECRET",
        "approval_signature",
        "sign_approval",
    ]

    for value in forbidden:
        assert value not in text


def test_page_requires_typed_confirmations():
    text = PAGE.read_text(
        encoding="utf-8"
    )

    assert (
        "Type the exact approval phrase"
        in text
    )

    assert (
        "Type the exact dispatch phrase"
        in text
    )
