from atlas.calibration.models import (
    MetricDistribution,
    PopulationStatistics,
    ProfileMetrics,
)
from atlas.calibration.zscore_engine import (
    ZSCORE_ENGINE_VERSION,
    compute_profile_zscores,
    compute_zscore,
    zscore_report_to_dict,
)


def _metrics() -> ProfileMetrics:
    return ProfileMetrics(
        identity="Z Test",
        node_count=12,
        edge_count=20,
        density=0.5,
        average_degree=3.0,
        hub_ratio=0.4,
        bridge_ratio=0.2,
        articulation_ratio=0.1,
        leaf_ratio=0.2,
        chain_count=3,
        triangle_count=2,
        star_count=1,
        bottleneck_count=1,
        cycle_count=0,
        hierarchy_score=0.3,
        branching_score=0.4,
        cyclicity_score=0.5,
        bottleneck_score=0.6,
        persistence_score=0.7,
        truth_ratio=0.8,
        mean_node_coherence=0.5,
        mean_edge_coherence=0.4,
        reduction_ratio=0.75,
        topology_class="branching_tree",
        resonance_class="low_resonance",
    )


def _distribution(
    metric: str,
    mean: float,
    standard_deviation: float,
) -> MetricDistribution:
    return MetricDistribution(
        metric=metric,
        count=10,
        minimum=0.0,
        maximum=100.0,
        mean=mean,
        median=mean,
        variance=standard_deviation * standard_deviation,
        standard_deviation=standard_deviation,
        first_quartile=0.0,
        third_quartile=0.0,
        percentile_95=0.0,
    )


def _population() -> PopulationStatistics:
    return PopulationStatistics(
        version="1.0",
        profile_count=10,
        metrics={
            "node_count": _distribution("node_count", 10.0, 2.0),
            "edge_count": _distribution("edge_count", 10.0, 5.0),
            "density": _distribution("density", 0.5, 0.1),
            "hub_ratio": _distribution("hub_ratio", 0.2, 0.1),
        },
    )


def test_compute_zscore_zero_standard_deviation():
    assert compute_zscore(
        value=10.0,
        mean=5.0,
        standard_deviation=0.0,
    ) == 0.0


def test_compute_zscore_regular_value():
    assert compute_zscore(
        value=12.0,
        mean=10.0,
        standard_deviation=2.0,
    ) == 1.0


def test_compute_profile_zscores():
    report = compute_profile_zscores(
        _metrics(),
        _population(),
    )

    assert report.version == ZSCORE_ENGINE_VERSION
    assert report.identity == "Z Test"

    assert report.scores["node_count"] == 1.0
    assert report.scores["edge_count"] == 2.0
    assert report.scores["density"] == 0.0
    assert report.scores["hub_ratio"] == 2.0

    assert report.summary["metric_count"] == 4
    assert report.summary["max_abs_zscore"] == 2.0


def test_zscore_report_to_dict():
    report = compute_profile_zscores(
        _metrics(),
        _population(),
    )

    data = zscore_report_to_dict(report)

    assert data["version"] == ZSCORE_ENGINE_VERSION
    assert data["identity"] == "Z Test"
    assert "scores" in data
    assert "summary" in data