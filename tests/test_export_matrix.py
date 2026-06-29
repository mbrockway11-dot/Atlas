from atlas.research.export_matrix import export_research_matrix


def test_export_research_matrix(tmp_path):
    output = tmp_path / "matrix.csv"

    result = export_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
        ],
        output,
    )

    assert result == output
    assert output.exists()

    text = output.read_text(encoding="utf-8")

    assert "Michael Elvis Brockway" in text
    assert "Nikola Tesla" in text
    assert "planet" in text
    assert "cipher" in text