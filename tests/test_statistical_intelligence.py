import pandas as pd

from atlas.research.statistical import (
    build_statistical_intelligence_report,
    cluster_summary,
    cohort_separation,
    kmeans_clusters,
    principal_components,
    silhouette_scores,
)
from atlas.research.validation import build_profile_feature_matrix


def sample_matrix():
    rows = []
    profiles = [
        ("Alpha", 0.0),
        ("Beta", 0.1),
        ("Gamma", 5.0),
        ("Delta", 5.2),
        ("Epsilon", 10.0),
        ("Zeta", 10.1),
    ]

    for name, offset in profiles:
        for cipher in ["ordinal", "hebrew_phonetic", "hebrew_literal"]:
            for planet in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]:
                rows.append(
                    {
                        "name": name,
                        "cipher": cipher,
                        "planet": planet,
                        "kamea": planet,
                        "grid_size": 3,
                        "sequence_length": 10 + offset,
                        "unique_nodes": 5 + offset,
                        "density": 0.1 + offset,
                        "entropy": 1.0 + offset,
                        "edge_count": 4 + offset,
                    }
                )

    return pd.DataFrame(rows)


def sample_profile_features():
    return build_profile_feature_matrix(sample_matrix())


def test_principal_components_available():
    features = sample_profile_features()
    pca = principal_components(features, n_components=3)

    assert pca["available"] is True
    assert len(pca["coordinates"]) == 6
    assert len(pca["explained_variance_ratio"]) >= 1
    assert "pc1" in pca["top_loadings"]


def test_kmeans_clusters_assigns_every_profile():
    features = sample_profile_features()
    assignments = kmeans_clusters(features, k=3)

    assert len(assignments) == 6
    assert set(assignments.columns) == {"name", "cluster", "distance_to_centroid"}
    assert assignments["cluster"].nunique() == 3


def test_cluster_summary_counts_profiles():
    features = sample_profile_features()
    assignments = kmeans_clusters(features, k=3)
    summary = cluster_summary(assignments)

    assert summary["profile_count"].sum() == 6
    assert len(summary) == 3


def test_silhouette_scores_available():
    features = sample_profile_features()
    assignments = kmeans_clusters(features, k=3)
    scores = silhouette_scores(features, assignments)

    assert len(scores) == 6
    assert "silhouette" in scores.columns


def test_cohort_separation_available_with_index():
    features = sample_profile_features()
    cohort_index = pd.DataFrame(
        {
            "name": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"],
            "cohort": ["A", "A", "B", "B", "C", "C"],
        }
    )

    separation = cohort_separation(features, cohort_index)

    assert separation["available"] is True
    assert len(separation["cohorts"]) == 3
    assert separation["separation_ratio"] is not None


def test_statistical_report_contains_core_sections():
    features = sample_profile_features()
    report = build_statistical_intelligence_report(features, k=3, n_components=3)

    assert report["profile_count"] == 6
    assert report["feature_count"] > 0
    assert "principal_components" in report
    assert "clusters" in report
    assert "cluster_summary" in report
    assert "silhouette_scores" in report
    assert "cohort_separation" in report