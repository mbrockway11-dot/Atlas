import pandas as pd

from atlas.features.clustering import (
    cluster_corpus,
    cluster_result_to_dict,
)


def test_cluster_corpus():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1, "feature_b": 0.1},
            {"name": "B", "feature_a": 0.2, "feature_b": 0.2},
            {"name": "C", "feature_a": 0.9, "feature_b": 0.9},
            {"name": "D", "feature_a": 1.0, "feature_b": 1.0},
        ]
    )

    result = cluster_corpus(
        dataframe=dataframe,
        cluster_count=2,
    )

    assert result.cluster_count == 2
    assert result.feature_count == 2
    assert len(result.assignments) == 4
    assert len(result.clusters) == 2


def test_cluster_result_to_dict():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1, "feature_b": 0.1},
            {"name": "B", "feature_a": 0.2, "feature_b": 0.2},
            {"name": "C", "feature_a": 0.9, "feature_b": 0.9},
            {"name": "D", "feature_a": 1.0, "feature_b": 1.0},
        ]
    )

    result = cluster_corpus(
        dataframe=dataframe,
        cluster_count=2,
    )

    data = cluster_result_to_dict(result)

    assert data["cluster_count"] == 2
    assert data["assignments"]
    assert data["clusters"]