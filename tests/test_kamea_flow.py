from atlas.kamea.identity_graph import build_kamea_identity_graph
from atlas.kamea_flow.confluence import build_riverbed_confluence
from atlas.kamea_flow.report import build_kamea_flow_report
from atlas.visualization.kamea_riverbed import render_planetary_riverbed_svg
from atlas.visualization.kamea_unified_shape import render_unified_kamea_shape_svg


def payload(name: str, key: str) -> dict:
    base = {"profile_key": key, "identity": {"name": name, "full_name": name}}
    base["kamea"] = build_kamea_identity_graph(base)
    return base


def test_canonical_flow_preserves_21_independent_tributaries():
    report = build_kamea_flow_report(payload("Nikola Tesla", "nikola_tesla"))
    assert report["flow"]["step_count"] > 0
    assert report["tributaries"]["tributary_count"] == 21
    assert report["metrics"]["metrics"]["cipher_flow_balance"] > 0.99
    assert report["metrics"]["metrics"]["planetary_flow_balance"] > 0.99
    assert all(not step["node"].startswith("unknown") for step in report["flow"]["steps"])


def test_flow_edges_never_bridge_cipher_planet_streams():
    report = build_kamea_flow_report(payload("Nikola Tesla", "nikola_tesla"))
    for edge in report["flow"]["edges"]:
        assert edge["stream_id"] == f"{edge['cipher']}::{edge['planet']}"
        assert edge["source"].startswith(f"{edge['planet']}:")
        assert edge["target"].startswith(f"{edge['planet']}:")
    expected_traversals = sum(max(0, row["step_count"] - 1) for row in report["tributaries"]["tributaries"])
    assert sum(edge["count"] for edge in report["flow"]["edges"]) == expected_traversals


def test_riverbed_requires_cross_cipher_same_planet_reproduction():
    report = build_kamea_flow_report(payload("Nikola Tesla", "nikola_tesla"))
    riverbed = report["riverbed"]
    assert riverbed["summary"]["planet_count"] == 7
    assert riverbed["summary"]["invariant_node_count"] > 0
    for row in riverbed["planetary_riverbeds"]:
        assert row["stream_count"] == 3
        assert all(node["cipher_coverage"] >= 2 for node in row["invariant_nodes"])
        assert all(edge["cipher_coverage"] >= 2 for edge in row["invariant_edges"])


def test_riverbed_svg_and_pair_confluence_are_deterministic():
    tesla = build_kamea_flow_report(payload("Nikola Tesla", "nikola_tesla"))
    edison = build_kamea_flow_report(payload("Thomas Edison", "thomas_edison"))
    first = build_riverbed_confluence("nikola_tesla", tesla, "thomas_edison", edison)
    second = build_riverbed_confluence("nikola_tesla", tesla, "thomas_edison", edison)
    assert first == second
    assert first["summary"]["planet_count"] == 7
    svg = render_planetary_riverbed_svg(tesla["riverbed"]["planetary_riverbeds"][0])
    assert "<svg" in svg
    assert "Invariant Riverbed" in svg
    assert first["shape_confluence"]["planetary_shape_comparisons"]
    unified_svg = render_unified_kamea_shape_svg(tesla["shape"])
    assert "normalized to one unit field" in unified_svg


def test_shape_analysis_uses_unified_coordinates_not_node_numbers():
    report = build_kamea_flow_report(payload("Nikola Tesla", "nikola_tesla"))
    shape = report["shape"]
    assert shape["number_labels_used_in_shape_metrics"] is False
    assert shape["summary"]["stream_count"] == 21
    assert {row["source_grid_size"] for row in shape["streams"]} == {3, 4, 5, 6, 7, 8, 9}
    assert all(0.0 <= coordinate <= 1.0 for row in shape["streams"] for point in row["normalized_points"] for coordinate in point)
    assert all(row["field_resolution"] == 33 for row in shape["planetary_fields"])
