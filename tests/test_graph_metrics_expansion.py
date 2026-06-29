from atlas.research import build_research_matrix


def test_research_matrix_contains_graph_metrics():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    assert len(rows) == 21

    row = rows[0]

    expected = [
        "component_count",
        "largest_component_size",
        "largest_component_ratio",
        "mean_degree",
        "max_degree",
        "degree_std",
        "hub_count",
        "hub_ratio",
        "leaf_count",
        "leaf_ratio",
        "bridge_count",
        "bridge_ratio",
        "articulation_count",
        "articulation_ratio",
    ]

    for key in expected:
        assert key in row


def test_graph_metric_ranges_are_valid():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    for row in rows:
        assert row["component_count"] >= 0
        assert row["largest_component_size"] >= 0
        assert 0.0 <= row["largest_component_ratio"] <= 1.0

        assert row["mean_degree"] >= 0.0
        assert row["max_degree"] >= 0
        assert row["degree_std"] >= 0.0

        assert row["hub_count"] >= 0
        assert 0.0 <= row["hub_ratio"] <= 1.0

        assert row["leaf_count"] >= 0
        assert 0.0 <= row["leaf_ratio"] <= 1.0

        assert row["bridge_count"] >= 0
        assert 0.0 <= row["bridge_ratio"] <= 1.0

        assert row["articulation_count"] >= 0
        assert 0.0 <= row["articulation_ratio"] <= 1.0