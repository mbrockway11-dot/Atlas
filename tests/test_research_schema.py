from atlas.research import (
    audit_research_rows,
    build_research_matrix,
    classify_column,
)


def test_research_schema_classifies_known_columns():
    assert classify_column("cipher") == "construction_metadata"
    assert classify_column("planet") == "construction_metadata"
    assert classify_column("unique_nodes") == "primary_topology"
    assert classify_column("entropy") == "information_measure"
    assert classify_column("max_node_weight") == "transitional_metric"
    assert classify_column("profile_node_persistence_ratio") == "identity_persistence"
    assert classify_column("kamea_score") == "deprecated"


def test_research_matrix_has_no_deprecated_columns():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    audit = audit_research_rows(rows)

    assert audit["valid"] is True
    assert audit["deprecated_columns"] == []
    assert "kamea_score" not in audit["column_classes"]


def test_research_matrix_columns_are_known():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    audit = audit_research_rows(rows)

    assert audit["unknown_columns"] == []
    assert audit["missing_columns"] == []