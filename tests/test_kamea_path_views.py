"""Tests for Kamea analysis/render path views."""

from atlas.kamea.path_views import build_kamea_path_views
from atlas.kamea.projection import project_values_to_kamea


def test_build_kamea_path_views_preserves_analysis_and_dedupes_render():
    """Analysis path should preserve repetitions while render path removes them."""
    path = project_values_to_kamea(
        [5, 8, 5, 5, 2, 8],
        "saturn",
    )

    views = build_kamea_path_views(path)

    # ------------------------------------------------------------------
    # Analysis path preserves the complete wrapped sequence
    # ------------------------------------------------------------------

    assert views["analysis_path"]["wrapped_values"] == [
        5,
        8,
        5,
        5,
        2,
        8,
    ]

    # ------------------------------------------------------------------
    # Node weights
    # ------------------------------------------------------------------

    assert views["analysis_path"]["node_weights"][5] == 3
    assert views["analysis_path"]["node_weights"][8] == 2
    assert views["analysis_path"]["node_weights"][2] == 1

    # ------------------------------------------------------------------
    # Edge weights
    # ------------------------------------------------------------------

    assert views["analysis_path"]["edge_weights"]["5->8"] == 1
    assert views["analysis_path"]["edge_weights"]["8->5"] == 1
    assert views["analysis_path"]["edge_weights"]["5->5"] == 1
    assert views["analysis_path"]["edge_weights"]["5->2"] == 1
    assert views["analysis_path"]["edge_weights"]["2->8"] == 1

    # ------------------------------------------------------------------
    # Visit history (z-axis depth)
    # ------------------------------------------------------------------

    visit_history = views["analysis_path"]["visit_history"]

    assert "visits" in visit_history
    assert "node_histories" in visit_history
    assert "node_weights" in visit_history

    assert visit_history["node_weights"]["5"] == 3
    assert visit_history["node_weights"]["8"] == 2
    assert visit_history["node_weights"]["2"] == 1

    assert visit_history["max_depth"] == 2

    visits_to_5 = visit_history["node_histories"]["5"]

    assert len(visits_to_5) == 3

    assert visits_to_5[0]["sequence_index"] == 0
    assert visits_to_5[0]["visit_depth"] == 0

    assert visits_to_5[1]["sequence_index"] == 2
    assert visits_to_5[1]["visit_depth"] == 1

    assert visits_to_5[2]["sequence_index"] == 3
    assert visits_to_5[2]["visit_depth"] == 2

    # ------------------------------------------------------------------
    # Render path removes repeated wrapped values
    # ------------------------------------------------------------------

    assert views["render_path"]["wrapped_values"] == [
        5,
        8,
        2,
    ]