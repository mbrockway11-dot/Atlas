from pathlib import Path

from atlas.calibration.models import ProfileMetrics
from atlas.calibration.similarity_matrix import (
    SIMILARITY_MATRIX_VERSION,
    build_similarity_matrix,
    export_similarity_matrix_csv,
    export_similarity_matrix_json,
    similarity_matrix_to_dict,
)


def _metrics(
    identity: str,
    node_count: int,
    edge_count: int,
    density: float,
) -> ProfileMetrics:
    return ProfileMetrics(
        identity=identity,
        node_count=node_count,
        edge_count=edge_count,
        density=density,
        average_degree=4.0,
        hub_ratio=0.2,
        bridge_ratio=0.1,
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


def _profiles() -> list[ProfileMetrics]:
    return [
        _metrics("A", 10, 20, 0.5),
        _metrics("B", 12, 24, 0.6),
        _metrics("C", 30, 60, 1.0),
    ]


def test_build_similarity_matrix_without_self():
    matrix = build_similarity_matrix(
        _profiles(),
    )

    assert matrix.version == SIMILARITY_MATRIX_VERSION
    assert matrix.profile_count == 3
    assert matrix.pair_count == 3
    assert len(matrix.results) == 3
    assert matrix.summary["result_count"] == 3


def test_build_similarity_matrix_with_self():
    matrix = build_similarity_matrix(
        _profiles(),
        include_self=True,
    )

    assert matrix.profile_count == 3
    assert matrix.pair_count == 9
    assert len(matrix.results) == 9


def test_similarity_matrix_to_dict():
    matrix = build_similarity_matrix(
        _profiles(),
    )

    data = similarity_matrix_to_dict(matrix)

    assert data["version"] == SIMILARITY_MATRIX_VERSION
    assert data["profile_count"] == 3
    assert data["pair_count"] == 3
    assert "summary" in data
    assert "results" in data


def test_export_similarity_matrix_json(tmp_path: Path):
    matrix = build_similarity_matrix(
        _profiles(),
    )

    output_path = tmp_path / "similarity_matrix.json"

    export_similarity_matrix_json(
        matrix,
        output_path,
    )

    assert output_path.exists()
    assert "similarity" in output_path.read_text(encoding="utf-8")


def test_export_similarity_matrix_csv(tmp_path: Path):
    matrix = build_similarity_matrix(
        _profiles(),
    )

    output_path = tmp_path / "similarity_matrix.csv"

    export_similarity_matrix_csv(
        matrix,
        output_path,
    )

    text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "identity_a,identity_b,similarity" in text