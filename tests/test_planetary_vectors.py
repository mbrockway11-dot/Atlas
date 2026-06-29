from atlas.research import (
    build_planetary_vectors,
    build_profile_vectors,
    build_research_matrix,
)


def test_planetary_vectors():

    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
        ]
    )

    vectors = build_profile_vectors(rows)

    planetary = build_planetary_vectors(vectors)

    assert len(planetary) == 7

    mercury = next(
        p
        for p in planetary
        if p["planet"] == "Mercury"
    )

    assert mercury["layer_count"] == 3
    assert "consensus" in mercury
    assert "consensus_strength" in mercury