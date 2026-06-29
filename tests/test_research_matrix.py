from atlas.acf.builder import build_acf_profile
from atlas.research.matrix import build_profile_matrix_rows, build_research_matrix


def test_build_profile_matrix_rows():
    acf = build_acf_profile("Michael Elvis Brockway")
    rows = build_profile_matrix_rows(acf)

    assert len(rows) == 21

    row = rows[0]

    assert row["name"] == "Michael Elvis Brockway"
    assert "cipher" in row
    assert "planet" in row
    assert "grid_size" in row
    assert "node_coverage" in row
    assert "entropy" in row
    assert "kamea_score" not in row


def test_build_research_matrix():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
        ]
    )

    assert len(rows) == 42
    assert "kamea_score" not in rows[0]