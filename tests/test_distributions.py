from atlas.research import (
    build_metric_distributions,
    build_research_matrix,
)


def test_metric_distributions():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    distributions = build_metric_distributions(rows)

    assert len(distributions) == 21

    saturn = distributions[
        (
            "ordinal",
            "Saturn",
        )
    ]

    assert saturn["sample_size"] == 3

    metrics = saturn["metrics"]

    assert "kamea_score" not in metrics

    entropy = metrics["entropy"]

    assert "mean" in entropy
    assert "median" in entropy
    assert "std" in entropy
    assert "iqr" in entropy