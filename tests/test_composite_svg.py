from atlas.export.composite_svg import CompositeImageCell, export_composite_svg


def test_export_composite_svg(tmp_path):
    image_a = tmp_path / "a.svg"
    image_b = tmp_path / "b.svg"

    image_a.write_text("<svg></svg>", encoding="utf-8")
    image_b.write_text("<svg></svg>", encoding="utf-8")

    output_path = tmp_path / "composite.svg"

    export_composite_svg(
        cells=[
            CompositeImageCell(
                image_path=image_a,
                row_label="ordinal",
                column_label="saturn",
            ),
            CompositeImageCell(
                image_path=image_b,
                row_label="ordinal",
                column_label="jupiter",
            ),
        ],
        output_path=output_path,
        row_labels=["ordinal"],
        column_labels=["saturn", "jupiter"],
        title="Test Composite",
    )

    svg = output_path.read_text(encoding="utf-8")

    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Test Composite" in svg
    assert 'href="a.svg"' in svg
    assert 'href="b.svg"' in svg