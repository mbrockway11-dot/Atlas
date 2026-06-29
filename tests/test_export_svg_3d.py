from atlas.export.svg import export_graph_svg_3d, graph_to_svg_3d
from atlas.topology.graph import TopologyGraph


def test_graph_to_svg_3d_contains_depth_elements():
    edge = ((0, 0), (1, 1))

    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge,),
        node_weights={(0, 0): 1, (1, 1): 4},
        edge_weights={edge: 3},
    )

    svg = graph_to_svg_3d(graph, grid_size=2)

    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert "<defs>" in svg
    assert 'id="soft-shadow"' in svg
    assert 'id="node-gradient"' in svg
    assert 'id="edges-3d"' in svg
    assert 'id="nodes-3d"' in svg
    assert 'class="edge-3d"' in svg
    assert 'class="node-3d"' in svg
    assert 'data-weight="4"' in svg
    assert svg.endswith("</svg>")


def test_export_graph_svg_3d(tmp_path):
    edge = ((0, 0), (1, 1))

    graph = TopologyGraph(
        nodes=((0, 0), (1, 1)),
        edges=(edge,),
        node_weights={(0, 0): 1, (1, 1): 2},
        edge_weights={edge: 2},
    )

    output_path = tmp_path / "graph_3d.svg"
    result_path = export_graph_svg_3d(graph, output_path, grid_size=2)

    assert result_path == output_path
    assert output_path.exists()

    svg = output_path.read_text(encoding="utf-8")

    assert "<svg" in svg
    assert "</svg>" in svg
    assert 'class="node-3d"' in svg
    assert 'class="edge-3d"' in svg


def test_graph_to_svg_3d_rejects_invalid_grid_size():
    graph = TopologyGraph(
        nodes=(),
        edges=(),
        node_weights={},
        edge_weights={},
    )

    try:
        graph_to_svg_3d(graph, grid_size=0)
    except ValueError as error:
        assert str(error) == "grid_size must be greater than zero."
    else:
        raise AssertionError("Expected ValueError.")