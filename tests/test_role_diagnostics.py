from atlas.classification.role_diagnostics import (
    audit_functional_roles_v2,
    group_rows_by_profile,
)
from atlas.research import build_research_matrix


def test_role_diagnostics_audits_research_rows():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    audit = audit_functional_roles_v2(rows)

    assert audit["valid"] is True
    assert audit["row_count"] == len(rows)
    assert audit["profile_count"] == 3
    assert audit["role_distribution"]
    assert audit["modifier_distribution"]
    assert audit["profile_role_distribution"]
    assert audit["profile_modifier_distribution"]
    assert audit["evidence_metric_distribution"]
    assert audit["role_metric_signal"]
    assert audit["profile_consensus"]
    assert audit["profile_results"]


def test_role_distribution_ratios_sum_to_one():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    audit = audit_functional_roles_v2(rows)

    total = sum(
        item["ratio"]
        for item in audit["role_distribution"]
    )

    assert abs(total - 1.0) < 0.000001


def test_profile_consensus_bounds_are_valid():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    audit = audit_functional_roles_v2(rows)

    for record in audit["profile_consensus"]:
        assert 0.0 <= record["role_consensus"] <= 1.0
        assert 0.0 <= record["modifier_consensus"] <= 1.0
        assert 0.0 <= record["confidence"] <= 1.0


def test_group_rows_by_profile():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
        ]
    )

    grouped = group_rows_by_profile(rows)

    assert len(grouped) == 2

    for profile_rows in grouped.values():
        assert len(profile_rows) == 21