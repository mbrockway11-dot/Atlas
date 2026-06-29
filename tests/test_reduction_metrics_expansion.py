from atlas.research import build_research_matrix


def test_research_matrix_contains_reduction_metrics():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    assert len(rows) == 21

    row = rows[0]

    expected = [
        "reduction_iterations",
        "surviving_node_ratio",
        "surviving_edge_ratio",
        "collapse_iteration",
        "collapse_ratio",
        "core_survival_score",
        "topology_stability",
        "reduction_entropy",
        "node_survival_auc",
        "edge_survival_auc",
        "edge_loss_rate",
        "collapse_slope",
    ]

    for key in expected:
        assert key in row


def test_reduction_metric_ranges_are_valid():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    bounded_metrics = [
        "surviving_node_ratio",
        "surviving_edge_ratio",
        "collapse_ratio",
        "core_survival_score",
        "topology_stability",
        "reduction_entropy",
        "node_survival_auc",
        "edge_survival_auc",
        "edge_loss_rate",
        "collapse_slope",
    ]

    for row in rows:
        assert row["reduction_iterations"] >= 0
        assert row["collapse_iteration"] >= 0

        for metric in bounded_metrics:
            assert 0.0 <= row[metric] <= 1.0