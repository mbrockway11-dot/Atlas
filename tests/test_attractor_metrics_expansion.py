from atlas.research import build_research_matrix


def test_research_matrix_contains_attractor_metrics():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    assert len(rows) == 21

    row = rows[0]

    expected = [
        "attractor_node_count",
        "attractor_edge_count",
        "attractor_node_ratio",
        "attractor_edge_ratio",
        "attractor_density",
        "attractor_mean_node_score",
        "attractor_min_node_score",
        "attractor_max_node_score",
        "attractor_stability",
        "attractor_signature",
    ]

    for key in expected:
        assert key in row


def test_attractor_metric_ranges_are_valid():
    rows = build_research_matrix(["Michael Elvis Brockway"])

    bounded_metrics = [
        "attractor_node_ratio",
        "attractor_edge_ratio",
        "attractor_density",
        "attractor_mean_node_score",
        "attractor_min_node_score",
        "attractor_max_node_score",
        "attractor_stability",
    ]

    for row in rows:
        assert row["attractor_node_count"] >= 0
        assert row["attractor_edge_count"] >= 0

        for metric in bounded_metrics:
            assert 0.0 <= row[metric] <= 1.0


def test_attractor_signature_is_stable():
    first = build_research_matrix(["Michael Elvis Brockway"])
    second = build_research_matrix(["Michael Elvis Brockway"])

    first_signatures = [
        row["attractor_signature"]
        for row in first
    ]

    second_signatures = [
        row["attractor_signature"]
        for row in second
    ]

    assert first_signatures == second_signatures