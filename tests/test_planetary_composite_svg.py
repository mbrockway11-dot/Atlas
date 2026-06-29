from atlas.identity import build_identity_graph
from atlas.visualization import RenderOptions, render_planetary_composite_svg


def test_render_planetary_composite_svg():
    graph = build_identity_graph("Michael Elvis Brockway")

    saturn_layers = [
        layer
        for layer in graph["layers"]
        if layer["planet"] == "Saturn"
    ]

    svg = render_planetary_composite_svg(
        saturn_layers,
        RenderOptions(output_size=600),
    )

    assert "<svg" in svg
    assert "Saturn Composite" in svg
    assert "<polyline" in svg
    assert "Ordinal" in svg