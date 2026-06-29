from atlas.research import build_research_matrix


def test_research_matrix_contains_coherence_metrics():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    assert len(rows) == 21

    row = rows[0]

    expected = [
        "mean_node_coherence",
        "median_node_coherence",
        "std_node_coherence",
        "mean_edge_coherence",
        "median_edge_coherence",
        "std_edge_coherence",
        "core_node_ratio",
        "adaptive_node_ratio",
        "peripheral_node_ratio",
        "core_edge_ratio",
        "adaptive_edge_ratio",
        "peripheral_edge_ratio",
        "graph_coherence",
    ]

    for key in expected:
        assert key in row


def test_coherence_metric_ranges_are_valid():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    bounded_metrics = [
        "mean_node_coherence",
        "median_node_coherence",
        "mean_edge_coherence",
        "median_edge_coherence",
        "core_node_ratio",
        "adaptive_node_ratio",
        "peripheral_node_ratio",
        "core_edge_ratio",
        "adaptive_edge_ratio",
        "peripheral_edge_ratio",
        "graph_coherence",
    ]

    non_negative_metrics = [
        "std_node_coherence",
        "std_edge_coherence",
    ]

    for row in rows:
        for metric in bounded_metrics:
            assert 0.0 <= row[metric] <= 1.0

        for metric in non_negative_metrics:
            assert row[metric] >= 0.0


def test_coherence_region_ratios_sum_to_one_when_present():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    for row in rows:
        node_total = (
            row["core_node_ratio"]
            + row["adaptive_node_ratio"]
            + row["peripheral_node_ratio"]
        )

        edge_total = (
            row["core_edge_ratio"]
            + row["adaptive_edge_ratio"]
            + row["peripheral_edge_ratio"]
        )

        assert abs(node_total - 1.0) < 0.000001
        assert abs(edge_total - 1.0) < 0.000001