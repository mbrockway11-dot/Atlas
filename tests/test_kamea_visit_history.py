from atlas.kamea.projection import project_values_to_kamea
from atlas.kamea.visit_history import build_node_visit_history


def test_build_node_visit_history_tracks_depth():
    path = project_values_to_kamea([5, 8, 5, 5, 2, 8], "saturn")
    history = build_node_visit_history(path)

    assert history["node_weights"]["5"] == 3
    assert history["node_weights"]["8"] == 2
    assert history["node_weights"]["2"] == 1
    assert history["max_depth"] == 2

    visits_to_5 = history["node_histories"]["5"]

    assert visits_to_5[0]["sequence_index"] == 0
    assert visits_to_5[0]["visit_depth"] == 0

    assert visits_to_5[1]["sequence_index"] == 2
    assert visits_to_5[1]["visit_depth"] == 1

    assert visits_to_5[2]["sequence_index"] == 3
    assert visits_to_5[2]["visit_depth"] == 2