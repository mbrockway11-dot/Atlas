from atlas.research import (
    build_feature_correlation_audit,
    build_research_matrix,
)


def test_build_feature_correlation_audit():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
            "Leonardo da Vinci",
        ]
    )

    audit = build_feature_correlation_audit(rows)

    assert audit
    assert "feature_a" in audit[0]
    assert "feature_b" in audit[0]
    assert "correlation" in audit[0]
    assert "absolute_correlation" in audit[0]
    assert "correlation_class" in audit[0]
    assert "sample_size" in audit[0]