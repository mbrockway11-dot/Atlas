"""Motion dynamics measurements."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, pi, sqrt

Coordinate = tuple[int, int]


@dataclass(frozen=True)
class DynamicsMeasurement:
    """Motion statistics of a Kamea traversal."""

    expansion_rate: float
    compression_rate: float
    oscillation_rate: float
    radial_bias: float
    rotational_bias: float
    directional_bias: float
    return_probability: float
    escape_probability: float


def measure_dynamics(
    path: list[Coordinate],
    grid_size: int,
) -> DynamicsMeasurement:
    """Measure path motion."""

    if len(path) < 2:
        return DynamicsMeasurement(
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )

    center = (
        (grid_size - 1) / 2,
        (grid_size - 1) / 2,
    )

    distances = [
        distance(node, center)
        for node in path
    ]

    expansion = 0
    compression = 0
    oscillation = 0

    seen = set()

    returns = 0
    escapes = 0

    direction_vectors = []

    angle_change = 0.0

    for i in range(1, len(path)):
        if distances[i] > distances[i - 1]:
            expansion += 1
        elif distances[i] < distances[i - 1]:
            compression += 1

        if i >= 2:
            if (
                distances[i - 1] > distances[i - 2]
                and distances[i - 1] > distances[i]
            ):
                oscillation += 1

            if (
                distances[i - 1] < distances[i - 2]
                and distances[i - 1] < distances[i]
            ):
                oscillation += 1

        current = path[i]

        if current in seen:
            returns += 1
        else:
            escapes += 1

        seen.add(path[i - 1])

        direction_vectors.append(
            (
                current[0] - path[i - 1][0],
                current[1] - path[i - 1][1],
            )
        )

        a1 = atan2(
            path[i - 1][0] - center[0],
            path[i - 1][1] - center[1],
        )

        a2 = atan2(
            current[0] - center[0],
            current[1] - center[1],
        )

        angle_change += abs(
            ((a2 - a1 + pi) % (2 * pi)) - pi
        )

    steps = len(path) - 1

    return DynamicsMeasurement(
        expansion_rate=safe_ratio(expansion, steps),
        compression_rate=safe_ratio(compression, steps),
        oscillation_rate=safe_ratio(
            oscillation,
            max(steps - 1, 1),
        ),
        radial_bias=safe_ratio(
            expansion + compression,
            steps,
        ),
        rotational_bias=safe_ratio(
            angle_change,
            steps * pi,
        ),
        directional_bias=directional_bias(
            direction_vectors,
        ),
        return_probability=safe_ratio(
            returns,
            steps,
        ),
        escape_probability=safe_ratio(
            escapes,
            steps,
        ),
    )


def directional_bias(vectors):
    if not vectors:
        return 0.0

    counts = {}

    for v in vectors:
        counts[v] = counts.get(v, 0) + 1

    return max(counts.values()) / len(vectors)


def distance(a, b):
    return sqrt(
        (a[0] - b[0]) ** 2
        + (a[1] - b[1]) ** 2
    )


def safe_ratio(a, b):
    if b == 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            float(a) / float(b),
        ),
    )