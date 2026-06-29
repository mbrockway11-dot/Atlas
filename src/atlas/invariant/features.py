"""Invariant feature extraction adapter for Kamea topology paths.

This module preserves the original InvariantFeatures API while delegating
measurement logic to atlas.measurement modules.

features.py is now an adapter/facade:

KameaPath
    -> invariant orientations
    -> measurement modules
    -> backward-compatible InvariantFeatures object
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from atlas.invariant.rotations import all_invariant_orientations
from atlas.measurement.coverage import (
    CoverageMeasurement as CoverageMetrics,
    measure_coverage,
)
from atlas.measurement.dynamics import (
    DynamicsMeasurement as DynamicsMetrics,
    measure_dynamics,
)
from atlas.measurement.organization import (
    OrganizationMeasurement as OrganizationMetrics,
    measure_organization,
)
from atlas.measurement.stability import (
    StabilityMeasurement as StabilityMetrics,
    measure_stability,
)
from atlas.measurement.structural_roles import (
    StructuralRoleMeasurement as StructuralRoleMetrics,
    measure_structural_roles,
)


Coordinate = tuple[int, int]
Edge = tuple[Coordinate, Coordinate]


@dataclass(frozen=True)
class InvariantFeatures:
    """Rotation/mirror invariant structural features.

    Original flat fields are preserved for backward compatibility.
    Structured measurement categories are additive.
    """

    node_weights: dict[Coordinate, float]
    node_ranking: list[tuple[Coordinate, float]]
    edge_weights: dict[Edge, float]
    self_loops: float
    degrees: dict[Coordinate, float]
    density: float
    clusters: int
    entropy: float
    axis_strength: float
    coverage: CoverageMetrics
    organization: OrganizationMetrics
    stability: StabilityMetrics
    dynamics: DynamicsMetrics
    structural_roles: StructuralRoleMetrics


def extract_invariant_features(
    path: Iterable[Coordinate] | Any,
    grid_size: int,
) -> InvariantFeatures:
    """Extract invariant measurements from all required orientations.

    Accepts either:
    - a coordinate iterable: [(0, 0), (1, 1), ...]
    - a KameaPath object with a .coordinates attribute
    """
    coordinate_path = _coerce_coordinate_path(path)
    orientations = all_invariant_orientations(coordinate_path, grid_size)

    node_accumulator: dict[Coordinate, float] = defaultdict(float)
    edge_accumulator: dict[Edge, float] = defaultdict(float)
    degree_accumulator: dict[Coordinate, float] = defaultdict(float)

    self_loop_total = 0.0

    coverage_total = _empty_metric_totals(CoverageMetrics)
    organization_total = _empty_metric_totals(OrganizationMetrics)
    stability_total = _empty_metric_totals(StabilityMetrics)
    dynamics_total = _empty_metric_totals(DynamicsMetrics)

    # Structural roles are a distribution, not a flat dataclass.
    structural_roles_total: dict[str, float] = defaultdict(float)

    count = len(orientations)

    for oriented_path in orientations.values():
        path_list = list(oriented_path)

        nodes = Counter(path_list)
        edges = Counter(zip(path_list[:-1], path_list[1:]))

        for node, weight in nodes.items():
            node_accumulator[node] += weight

        for edge, weight in edges.items():
            edge_accumulator[edge] += weight

        degrees = _degree_counts(edges)

        for node, degree in degrees.items():
            degree_accumulator[node] += degree

        self_loops = _self_loop_count(edges)
        self_loop_total += self_loops

        coverage = measure_coverage(
            nodes=nodes,
            edges=edges,
            grid_size=grid_size,
        )
        organization = measure_organization(
            nodes=nodes,
            edges=edges,
            grid_size=grid_size,
        )
        stability = measure_stability(
            nodes=nodes,
            edges=edges,
        )
        dynamics = measure_dynamics(
            path=path_list,
            grid_size=grid_size,
        )
        structural_roles = measure_structural_roles(
            path=path_list,
            nodes=nodes,
            edges=edges,
        )

        _accumulate_dataclass(coverage_total, coverage)
        _accumulate_dataclass(organization_total, organization)
        _accumulate_dataclass(stability_total, stability)
        _accumulate_dataclass(dynamics_total, dynamics)

        for role, value in structural_roles.roles.items():
            structural_roles_total[role] += value

    node_weights = {
        node: value / count
        for node, value in node_accumulator.items()
    }

    edge_weights = {
        edge: value / count
        for edge, value in edge_accumulator.items()
    }

    degrees_mean = {
        node: value / count
        for node, value in degree_accumulator.items()
    }

    node_ranking = sorted(
        node_weights.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    coverage_avg = _average_ratio_dataclass(
        CoverageMetrics,
        coverage_total,
        count,
    )
    organization_avg = _average_organization(
        organization_total,
        count,
    )
    stability_avg = _average_ratio_dataclass(
        StabilityMetrics,
        stability_total,
        count,
    )
    dynamics_avg = _average_ratio_dataclass(
        DynamicsMetrics,
        dynamics_total,
        count,
    )
    structural_roles_avg = _average_structural_roles(
        structural_roles_total,
        count,
    )

    return InvariantFeatures(
        node_weights=node_weights,
        node_ranking=node_ranking,
        edge_weights=edge_weights,
        self_loops=self_loop_total / count,
        degrees=degrees_mean,
        density=organization_avg.density,
        clusters=organization_avg.clusters,
        entropy=organization_avg.entropy,
        axis_strength=organization_avg.axis_strength,
        coverage=coverage_avg,
        organization=organization_avg,
        stability=stability_avg,
        dynamics=dynamics_avg,
        structural_roles=structural_roles_avg,
    )


def invariant_features_to_dict(features: InvariantFeatures) -> dict[str, Any]:
    """Convert invariant features to JSON-safe dictionary."""
    return {
        "node_weights": [
            {
                "node": list(node),
                "weight": weight,
            }
            for node, weight in features.node_weights.items()
        ],
        "node_ranking": [
            {
                "node": list(node),
                "weight": weight,
            }
            for node, weight in features.node_ranking
        ],
        "edge_weights": [
            {
                "edge": [
                    list(edge[0]),
                    list(edge[1]),
                ],
                "weight": weight,
            }
            for edge, weight in features.edge_weights.items()
        ],
        "self_loops": features.self_loops,
        "degrees": [
            {
                "node": list(node),
                "degree": degree,
            }
            for node, degree in features.degrees.items()
        ],
        "density": features.density,
        "clusters": features.clusters,
        "entropy": features.entropy,
        "axis_strength": features.axis_strength,
        "coverage": asdict(features.coverage),
        "organization": asdict(features.organization),
        "stability": asdict(features.stability),
        "dynamics": asdict(features.dynamics),
        "structural_roles": features.structural_roles.roles,
    }


def _coerce_coordinate_path(path: Iterable[Coordinate] | Any) -> list[Coordinate]:
    """Accept KameaPath or coordinate iterable and return coordinate list."""
    if hasattr(path, "coordinates"):
        return [
            tuple(coordinate)
            for coordinate in path.coordinates
        ]

    return [
        tuple(coordinate)
        for coordinate in path
    ]


def _degree_counts(edges: Counter[Edge]) -> dict[Coordinate, int]:
    """Calculate weighted degree counts."""
    degrees: dict[Coordinate, int] = defaultdict(int)

    for (source, target), weight in edges.items():
        degrees[source] += weight
        degrees[target] += weight

    return dict(degrees)


def _self_loop_count(edges: Counter[Edge]) -> float:
    """Count weighted self-loops."""
    return sum(
        weight
        for edge, weight in edges.items()
        if edge[0] == edge[1]
    )


def _empty_metric_totals(metric_class) -> dict[str, float]:
    """Create zero totals for dataclass fields."""
    return {
        field: 0.0
        for field in metric_class.__dataclass_fields__
    }


def _accumulate_dataclass(
    totals: dict[str, float],
    metric,
) -> None:
    """Accumulate flat dataclass numeric fields."""
    for key, value in asdict(metric).items():
        totals[key] += float(value)


def _average_ratio_dataclass(
    metric_class,
    totals: dict[str, float],
    count: int,
):
    """Average accumulated ratio-style dataclass totals."""
    if count == 0:
        return metric_class(
            **{
                key: 0.0
                for key in metric_class.__dataclass_fields__
            }
        )

    return metric_class(
        **{
            key: _clamp_ratio(value / count)
            for key, value in totals.items()
        }
    )


def _average_organization(
    totals: dict[str, float],
    count: int,
) -> OrganizationMetrics:
    """Average organization metrics while preserving cluster count semantics."""
    if count == 0:
        return OrganizationMetrics(
            density=0.0,
            clusters=0,
            entropy=0.0,
            axis_strength=0.0,
            reciprocity=0.0,
            compression_ratio=0.0,
        )

    return OrganizationMetrics(
        density=_clamp_ratio(totals["density"] / count),
        clusters=int(round(totals["clusters"] / count)),
        entropy=_clamp_ratio(totals["entropy"] / count),
        axis_strength=_clamp_ratio(totals["axis_strength"] / count),
        reciprocity=_clamp_ratio(totals["reciprocity"] / count),
        compression_ratio=_clamp_ratio(totals["compression_ratio"] / count),
    )


def _average_structural_roles(
    totals: dict[str, float],
    count: int,
) -> StructuralRoleMetrics:
    """Average structural role distribution."""
    if count == 0:
        return StructuralRoleMetrics(roles={})

    return StructuralRoleMetrics(
        roles={
            role: _clamp_ratio(value / count)
            for role, value in totals.items()
        }
    )


def _clamp_ratio(value: float) -> float:
    """Clamp ratio-like metric to 0-1."""
    return max(0.0, min(1.0, float(value)))