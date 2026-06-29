from atlas.research import (
    build_population_baselines,
    build_research_matrix,
    get_metric_baseline,
)


def test_population_baselines():

    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    baselines = build_population_baselines(rows)

    assert len(baselines) == 21

    entropy = get_metric_baseline(
        baselines,
        "ordinal",
        "Saturn",
        "entropy",
    )

    assert "mean" in entropy
    assert "std" in entropy
    assert "minimum" in entropy
    assert "maximum" in entropy