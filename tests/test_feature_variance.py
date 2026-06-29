from atlas.research import (
    build_feature_variance_audit,
    build_research_matrix,
)


def test_build_feature_variance_audit():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
            "Leonardo da Vinci",
        ]
    )

    audit = build_feature_variance_audit(rows)

    assert audit
    assert "feature" in audit[0]
    assert "std" in audit[0]
    assert "variance" in audit[0]
    assert "variance_class" in audit[0]

    features = {
        row["feature"]
        for row in audit
    }

    assert "entropy" in features
    assert "max_depth" in features