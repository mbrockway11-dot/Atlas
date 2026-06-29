from atlas.research import (
    build_population_statistics,
    build_research_matrix,
)


def test_population_statistics():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    stats = build_population_statistics(rows)

    assert len(stats) == 21

    saturn = stats[
        (
            "ordinal",
            "Saturn",
        )
    ]

    assert saturn["sample_size"] == 3

    metrics = saturn["metrics"]

    assert "entropy" in metrics
    assert "density" in metrics
    assert "kamea_score" not in metrics