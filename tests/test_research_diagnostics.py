from atlas.diagnostics import (
    audit_metric,
    audit_research_matrix,
    numeric_columns,
)
from atlas.research import build_research_matrix


def test_numeric_columns_excludes_metadata():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
        ]
    )

    columns = numeric_columns(rows)

    assert "name" not in columns
    assert "cipher" not in columns
    assert "planet" not in columns
    assert "kamea" not in columns
    assert "subtype_primary" not in columns
    assert "subtype_secondary" not in columns

    assert "density" in columns
    assert "entropy" in columns
    assert "component_count" in columns


def test_audit_metric_returns_expected_fields():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
        ]
    )

    audit = audit_metric(rows, "density")

    assert audit["metric"] == "density"
    assert audit["row_count"] == len(rows)
    assert audit["value_count"] == len(rows)
    assert audit["null_count"] == 0
    assert audit["minimum"] <= audit["maximum"]
    assert audit["std"] >= 0.0
    assert audit["variance"] >= 0.0
    assert audit["range"] >= 0.0
    assert audit["unique_value_count"] >= 1
    assert 0.0 <= audit["constant_ratio"] <= 1.0
    assert 0.0 <= audit["quality_rank"] <= 1.0
    assert audit["quality_grade"] in ["A", "B", "C", "D", "F"]
    assert audit["diagnostic"]


def test_audit_research_matrix_returns_metrics():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    audit = audit_research_matrix(rows)

    assert audit["valid"] is True
    assert audit["row_count"] == len(rows)
    assert audit["metric_count"] > 0
    assert audit["metrics"]

    metric_names = {
        metric["metric"]
        for metric in audit["metrics"]
    }

    assert "density" in metric_names
    assert "entropy" in metric_names
    assert "component_count" in metric_names


def test_constant_metric_receives_low_grade():
    rows = [
        {
            "metric": 1.0,
        },
        {
            "metric": 1.0,
        },
        {
            "metric": 1.0,
        },
    ]

    audit = audit_metric(rows, "metric")

    assert audit["unique_value_count"] == 1
    assert audit["range"] == 0.0
    assert audit["quality_grade"] == "F"