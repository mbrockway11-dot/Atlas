from atlas.research import (
    build_population_baselines,
    build_research_matrix,
    compute_layer_zscores,
    compute_profile_zscores,
)


def test_layer_zscores():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    baselines = build_population_baselines(rows)

    result = compute_layer_zscores(
        rows[0],
        baselines,
    )

    assert "entropy" in result
    assert "density" in result
    assert "kamea_score" not in result


def test_profile_zscores():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    baselines = build_population_baselines(rows)

    calibrated = compute_profile_zscores(
        rows,
        baselines,
    )

    assert len(calibrated) == len(rows)
    assert "zscores" in calibrated[0]
    assert "kamea_score" not in calibrated[0]
    assert "kamea_score" not in calibrated[0]["zscores"]