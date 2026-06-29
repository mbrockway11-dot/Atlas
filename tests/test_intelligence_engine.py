import pandas as pd

from atlas.intelligence.engine import (
    build_confidence,
    build_evidence,
    build_population_position,
    build_provenance,
    build_statistical_position,
    build_topology_position,
)
from atlas.intelligence.explain import build_intelligence_summary
from atlas.intelligence.models import (
    ConfidenceSummary,
    EvidenceRecord,
    IntelligenceEngineConfig,
    IntelligenceSummary,
    PopulationPosition,
    ProvenanceRecord,
    StatisticalPosition,
    TopologyPosition,
)


def sample_profile_features():
    return pd.DataFrame(
        [
            {
                "name": "Alpha",
                "metric_a_mean": 0.0,
                "metric_b_mean": 0.0,
                "metric_c_mean": 0.0,
            },
            {
                "name": "Beta",
                "metric_a_mean": 0.1,
                "metric_b_mean": 0.1,
                "metric_c_mean": 0.1,
            },
            {
                "name": "Gamma",
                "metric_a_mean": 5.0,
                "metric_b_mean": 5.0,
                "metric_c_mean": 5.0,
            },
            {
                "name": "Delta",
                "metric_a_mean": 5.2,
                "metric_b_mean": 5.2,
                "metric_c_mean": 5.2,
            },
        ]
    )


def test_build_population_position_returns_model():
    config = IntelligenceEngineConfig(neighbor_limit=2)
    result = build_population_position("Alpha", sample_profile_features(), config)

    assert isinstance(result, PopulationPosition)
    assert len(result.nearest_neighbors) == 2
    assert result.outlier_rank is not None
    assert result.centroid_distance is not None


def test_build_statistical_position_returns_model():
    config = IntelligenceEngineConfig(cluster_count=2, principal_components=2)
    result = build_statistical_position("Alpha", sample_profile_features(), config)

    assert isinstance(result, StatisticalPosition)
    assert result.cluster is not None
    assert result.silhouette is not None
    assert result.principal_components is not None
    assert isinstance(result.explained_variance_ratio, list)


def test_build_topology_position_returns_model():
    config = IntelligenceEngineConfig(topology_threshold=0.5, topology_top_k=1)
    result = build_topology_position("Alpha", sample_profile_features(), config)

    assert isinstance(result, TopologyPosition)
    assert result.available is True
    assert result.degree >= 0
    assert result.community is not None
    assert result.component is not None


def test_evidence_and_confidence_are_models():
    population_position = PopulationPosition(
        nearest_neighbors=[{"name": "Beta", "similarity": 0.99}],
        outlier_rank=2,
        centroid_distance=1.5,
    )

    statistical_position = StatisticalPosition(
        cluster={"cluster": 0, "distance_to_centroid": 0.1},
        silhouette={"cluster": 0, "silhouette": 0.8},
        principal_components={"name": "Alpha", "pc1": 0.1, "pc2": -0.2},
        explained_variance_ratio=[0.8, 0.2],
    )

    topology_position = TopologyPosition(
        available=True,
        degree=3,
        weighted_degree=2.5,
        component=0,
        community=0,
        degree_centrality=1.0,
        weighted_degree_centrality=0.8,
        closeness_centrality=1.0,
    )

    evidence = build_evidence(
        population_position,
        statistical_position,
        topology_position,
    )
    confidence = build_confidence(evidence)

    assert len(evidence) == 5
    assert all(isinstance(item, EvidenceRecord) for item in evidence)
    assert isinstance(confidence, ConfidenceSummary)
    assert confidence.score > 0.0
    assert confidence.label in {"low", "moderate", "high"}


def test_intelligence_summary_is_generated():
    population_position = PopulationPosition(
        nearest_neighbors=[{"name": "Beta", "similarity": 0.99}],
        outlier_rank=2,
        centroid_distance=1.5,
    )

    statistical_position = StatisticalPosition(
        cluster={"cluster": 0, "distance_to_centroid": 0.1},
        silhouette={"cluster": 0, "silhouette": 0.8},
        principal_components={"name": "Alpha", "pc1": 0.1, "pc2": -0.2},
        explained_variance_ratio=[0.8, 0.2],
    )

    topology_position = TopologyPosition(
        available=True,
        degree=3,
        weighted_degree=2.5,
        component=0,
        community=0,
        degree_centrality=1.0,
        weighted_degree_centrality=0.8,
        closeness_centrality=1.0,
    )

    confidence = ConfidenceSummary(score=1.0, label="high", evidence_count=5)

    summary = build_intelligence_summary(
        population_position,
        statistical_position,
        topology_position,
        confidence,
    )

    assert isinstance(summary, IntelligenceSummary)
    assert "high" in summary.headline
    assert "closest structural neighbor" in summary.population
    assert "cluster" in summary.statistics
    assert "degree" in summary.topology


def test_provenance_records_are_generated():
    provenance = build_provenance()

    assert provenance
    assert all(isinstance(item, ProvenanceRecord) for item in provenance)
    assert any(item.section == "population_position" for item in provenance)
    assert any(item.section == "summary" for item in provenance)


def test_payload_models_convert_to_dict():
    population_position = PopulationPosition(
        nearest_neighbors=[{"name": "Beta", "similarity": 0.99}],
        outlier_rank=1,
        centroid_distance=2.0,
    )

    assert population_position.nearest_neighbors[0]["name"] == "Beta"