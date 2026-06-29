from atlas.research import (
    build_profile_vectors,
    build_research_matrix,
)


def test_profile_vectors():

    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
        ]
    )

    vectors = build_profile_vectors(rows)

    assert len(vectors) == 21

    first = vectors[0]

    assert "planet" in first
    assert "cipher" in first
    assert "vector" in first

    assert "entropy" in first["vector"]
    assert "density" in first["vector"]
    assert "node_coverage" in first["vector"]