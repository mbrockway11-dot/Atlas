from atlas.export.svg import export_graph_svg, graph_to_svg
from atlas.topology.graph import TopologyGraph


def test_graph_to_svg_contains_svg_elements():
    edge = ((0, 0), (1, 1))

    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge,),
        node_weights={(0, 0): 1, (1, 1): 2},
        edge_weights={edge: 3},
    )

    svg = graph_to_svg(graph, grid_size=2)

    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert "<rect" in svg
    assert "<line" in svg
    assert "<circle" in svg
    assert 'stroke-width="4.50"' in svg
    assert 'r="9.00"' in svg
    assert svg.endswith("</svg>")


def test_export_graph_svg(tmp_path):
    edge = ((0, 0), (1, 1))

    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge,),
        node_weights={(0, 0): 1, (1, 1): 1},
        edge_weights={edge: 1},
    )

    output_path = tmp_path / "graph.svg"
    result_path = export_graph_svg(graph, output_path, grid_size=2)

    assert result_path == output_path
    assert output_path.exists()

    svg = output_path.read_text(encoding="utf-8")

    assert "<svg" in svg
    assert "</svg>" in svg


def test_graph_to_svg_rejects_invalid_grid_size():
    graph = TopologyGraph(
        nodes=(),
        edges=(),
        node_weights={},
        edge_weights={},
    )

    try:
        graph_to_svg(graph, grid_size=0)
    except ValueError as error:
        assert str(error) == "grid_size must be greater than zero."
    else:
        raise AssertionError("Expected ValueError.")