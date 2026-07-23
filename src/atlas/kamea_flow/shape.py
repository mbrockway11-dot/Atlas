"""Unified geometric analysis for differently sized planetary Kameas."""

from __future__ import annotations

from collections import Counter, defaultdict
import math
from typing import Any, Iterable


UNIFIED_SHAPE_VERSION = "1.0.0"
DEFAULT_FIELD_RESOLUTION = 33
DEFAULT_RESAMPLE_POINTS = 64


def build_unified_shape_analysis(
    flow: dict[str, Any],
    *,
    field_resolution: int = DEFAULT_FIELD_RESOLUTION,
    resample_points: int = DEFAULT_RESAMPLE_POINTS,
) -> dict[str, Any]:
    """Project every Kamea stream into the same unit-square geometry.

    Numeric node labels are intentionally excluded from all shape descriptors.
    Only ordered normalized coordinates and their derived geometry are used.
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for step in flow.get("steps", []) or []:
        grouped[str(step.get("stream_id"))].append(step)

    streams = []
    for stream_id, steps in sorted(grouped.items()):
        ordered = sorted(steps, key=lambda row: row.get("stream_index", row.get("index", 0)))
        points = [
            [round(float(row.get("normalized_x") or 0.0), 6), round(float(row.get("normalized_y") or 0.0), 6)]
            for row in ordered
        ]
        streams.append({
            "stream_id": stream_id,
            "cipher": str(ordered[0].get("cipher")) if ordered else "unknown",
            "planet": str(ordered[0].get("planet")) if ordered else "unknown",
            "source_grid_size": int(ordered[0].get("grid_size") or 0) if ordered else 0,
            "point_count": len(points),
            "normalized_points": points,
            "resampled_points": resample_polyline(points, resample_points),
            "shape_features": shape_features(points),
            "occupied_cells": sorted(rasterize_polyline(points, field_resolution)),
            "directed_cells": sorted(rasterize_directed_segments(points, field_resolution)),
        })

    planets = sorted({row["planet"] for row in streams})
    planetary_fields = [
        build_planetary_shape_field(
            planet,
            [row for row in streams if row["planet"] == planet],
            field_resolution=field_resolution,
        )
        for planet in planets
    ]
    return {
        "success": True,
        "version": UNIFIED_SHAPE_VERSION,
        "definition": "All Kamea paths normalized to [0,1]×[0,1]; analysis uses ordered geometry rather than node numbers.",
        "coordinate_policy": "x=column/(size-1), y=row/(size-1); common orientation retained",
        "field_resolution": field_resolution,
        "resample_points": resample_points,
        "number_labels_used_in_shape_metrics": False,
        "streams": streams,
        "planetary_fields": planetary_fields,
        "cross_planet_shape_similarity": cross_planet_similarity(planetary_fields),
        "summary": {
            "stream_count": len(streams),
            "planet_count": len(planetary_fields),
            "mean_within_planet_curve_similarity": _mean(row["mean_cipher_curve_similarity"] for row in planetary_fields),
            "mean_shape_consensus_ratio": _mean(row["shape_consensus_ratio"] for row in planetary_fields),
            "strongest_shape_consensus_planet": _strongest(planetary_fields, "shape_consensus_ratio"),
            "strongest_curve_agreement_planet": _strongest(planetary_fields, "mean_cipher_curve_similarity"),
        },
        "claim_type": "deterministic_geometric_measurement",
        "causal_claim": False,
    }


def build_planetary_shape_field(planet: str, streams: list[dict[str, Any]], *, field_resolution: int) -> dict[str, Any]:
    cell_coverage: Counter[tuple[int, int]] = Counter()
    edge_coverage: Counter[tuple[int, int, int, int]] = Counter()
    for stream in streams:
        cell_coverage.update({tuple(cell) for cell in stream["occupied_cells"]})
        edge_coverage.update({tuple(edge) for edge in stream["directed_cells"]})
    union_cells = set(cell_coverage)
    consensus_cells = {cell for cell, count in cell_coverage.items() if count >= 2}
    union_edges = set(edge_coverage)
    consensus_edges = {edge for edge, count in edge_coverage.items() if count >= 2}
    pairwise = []
    for index, left in enumerate(streams):
        for right in streams[index + 1:]:
            pairwise.append({
                "stream_a": left["stream_id"],
                "stream_b": right["stream_id"],
                "curve_similarity": curve_similarity(left["resampled_points"], right["resampled_points"]),
                "field_jaccard": jaccard({tuple(v) for v in left["occupied_cells"]}, {tuple(v) for v in right["occupied_cells"]}),
            })
    return {
        "planet": planet,
        "source_grid_sizes": sorted({stream["source_grid_size"] for stream in streams}),
        "stream_count": len(streams),
        "field_resolution": field_resolution,
        "union_cells": _cell_rows(union_cells),
        "consensus_cells": [
            {"x": cell[0], "y": cell[1], "cipher_coverage": cell_coverage[cell]}
            for cell in sorted(consensus_cells)
        ],
        "union_directed_segments": _edge_rows(union_edges),
        "consensus_directed_segments": [
            {"x1": edge[0], "y1": edge[1], "x2": edge[2], "y2": edge[3], "cipher_coverage": edge_coverage[edge]}
            for edge in sorted(consensus_edges)
        ],
        "union_cell_count": len(union_cells),
        "consensus_cell_count": len(consensus_cells),
        "union_segment_count": len(union_edges),
        "consensus_segment_count": len(consensus_edges),
        "shape_consensus_ratio": round(len(consensus_cells) / len(union_cells), 6) if union_cells else 0.0,
        "directional_consensus_ratio": round(len(consensus_edges) / len(union_edges), 6) if union_edges else 0.0,
        "mean_cipher_curve_similarity": _mean(row["curve_similarity"] for row in pairwise),
        "mean_cipher_field_jaccard": _mean(row["field_jaccard"] for row in pairwise),
        "pairwise_cipher_shapes": pairwise,
    }


def compare_unified_shape_fields(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_map = {row["planet"]: row for row in left.get("planetary_fields", []) or []}
    right_map = {row["planet"]: row for row in right.get("planetary_fields", []) or []}
    rows = []
    for planet in sorted(set(left_map) | set(right_map)):
        a = left_map.get(planet, {})
        b = right_map.get(planet, {})
        a_union = {(row["x"], row["y"]) for row in a.get("union_cells", []) or []}
        b_union = {(row["x"], row["y"]) for row in b.get("union_cells", []) or []}
        a_consensus = {(row["x"], row["y"]) for row in a.get("consensus_cells", []) or []}
        b_consensus = {(row["x"], row["y"]) for row in b.get("consensus_cells", []) or []}
        a_segments = {(row["x1"], row["y1"], row["x2"], row["y2"]) for row in a.get("consensus_directed_segments", []) or []}
        b_segments = {(row["x1"], row["y1"], row["x2"], row["y2"]) for row in b.get("consensus_directed_segments", []) or []}
        rows.append({
            "planet": planet,
            "union_shape_jaccard": jaccard(a_union, b_union),
            "consensus_shape_jaccard": jaccard(a_consensus, b_consensus),
            "directional_shape_jaccard": jaccard(a_segments, b_segments),
            "shared_union_cell_count": len(a_union & b_union),
            "shared_consensus_cell_count": len(a_consensus & b_consensus),
            "shared_directional_segment_count": len(a_segments & b_segments),
        })
    return {
        "planetary_shape_comparisons": rows,
        "mean_union_shape_jaccard": _mean(row["union_shape_jaccard"] for row in rows),
        "mean_consensus_shape_jaccard": _mean(row["consensus_shape_jaccard"] for row in rows),
        "mean_directional_shape_jaccard": _mean(row["directional_shape_jaccard"] for row in rows),
        "strongest_shape_confluence_planet": _strongest(rows, "consensus_shape_jaccard"),
    }


def shape_features(points: list[list[float]]) -> dict[str, float | int]:
    if not points:
        return {"path_length": 0.0, "displacement": 0.0, "tortuosity": 0.0, "mean_turn_radians": 0.0, "turn_variance": 0.0, "bounding_width": 0.0, "bounding_height": 0.0, "self_intersections": 0}
    lengths = [_distance(a, b) for a, b in zip(points, points[1:])]
    path_length = sum(lengths)
    displacement = _distance(points[0], points[-1]) if len(points) > 1 else 0.0
    turns = turning_angles(points)
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return {
        "path_length": round(path_length, 6),
        "displacement": round(displacement, 6),
        "tortuosity": round(path_length / displacement, 6) if displacement else round(path_length, 6),
        "mean_turn_radians": round(sum(abs(v) for v in turns) / len(turns), 6) if turns else 0.0,
        "turn_variance": round(_variance(turns), 6),
        "bounding_width": round(max(xs) - min(xs), 6),
        "bounding_height": round(max(ys) - min(ys), 6),
        "self_intersections": count_self_intersections(points),
    }


def resample_polyline(points: list[list[float]], count: int) -> list[list[float]]:
    if not points:
        return []
    if len(points) == 1 or count <= 1:
        return [list(points[0])] * max(count, 1)
    cumulative = [0.0]
    for left, right in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + _distance(left, right))
    total = cumulative[-1]
    if total == 0.0:
        return [list(points[0])] * count
    result = []
    segment = 0
    for index in range(count):
        target = total * index / (count - 1)
        while segment + 1 < len(cumulative) and cumulative[segment + 1] < target:
            segment += 1
        left_d, right_d = cumulative[segment], cumulative[min(segment + 1, len(points) - 1)]
        left, right = points[segment], points[min(segment + 1, len(points) - 1)]
        ratio = (target - left_d) / (right_d - left_d) if right_d > left_d else 0.0
        result.append([round(left[0] + (right[0] - left[0]) * ratio, 6), round(left[1] + (right[1] - left[1]) * ratio, 6)])
    return result


def curve_similarity(left: list[list[float]], right: list[list[float]]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    rmse = math.sqrt(sum(_distance(a, b) ** 2 for a, b in zip(left, right, strict=True)) / len(left))
    return round(max(0.0, 1.0 - rmse / math.sqrt(2.0)), 6)


def rasterize_polyline(points: list[list[float]], resolution: int) -> set[tuple[int, int]]:
    if not points:
        return set()
    cells = {_quantize(points[0], resolution)}
    for left, right in zip(points, points[1:]):
        cells.update(_segment_cells(left, right, resolution))
    return cells


def rasterize_directed_segments(points: list[list[float]], resolution: int) -> set[tuple[int, int, int, int]]:
    segments = set()
    for left, right in zip(points, points[1:]):
        cells = _segment_cells_ordered(left, right, resolution)
        segments.update((a[0], a[1], b[0], b[1]) for a, b in zip(cells, cells[1:]) if a != b)
    return segments


def cross_planet_similarity(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, left in enumerate(fields):
        left_cells = {(row["x"], row["y"]) for row in left["consensus_cells"]}
        for right in fields[index + 1:]:
            right_cells = {(row["x"], row["y"]) for row in right["consensus_cells"]}
            rows.append({"planet_a": left["planet"], "planet_b": right["planet"], "normalized_shape_jaccard": jaccard(left_cells, right_cells)})
    return sorted(rows, key=lambda row: (-row["normalized_shape_jaccard"], row["planet_a"], row["planet_b"]))


def turning_angles(points: list[list[float]]) -> list[float]:
    values = []
    for a, b, c in zip(points, points[1:], points[2:]):
        v1, v2 = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
        if math.hypot(*v1) == 0 or math.hypot(*v2) == 0:
            continue
        values.append(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1]))
    return values


def count_self_intersections(points: list[list[float]]) -> int:
    count = 0
    segments = list(zip(points, points[1:]))
    for index, (a, b) in enumerate(segments):
        for other_index in range(index + 2, len(segments)):
            if other_index == index + 1:
                continue
            c, d = segments[other_index]
            if _segments_intersect(a, b, c, d):
                count += 1
    return count


def jaccard(left: set[Any], right: set[Any]) -> float:
    union = left | right
    return round(len(left & right) / len(union), 6) if union else 0.0


def _segment_cells(left: list[float], right: list[float], resolution: int) -> set[tuple[int, int]]:
    return set(_segment_cells_ordered(left, right, resolution))


def _segment_cells_ordered(left: list[float], right: list[float], resolution: int) -> list[tuple[int, int]]:
    a, b = _quantize(left, resolution), _quantize(right, resolution)
    steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
    result = []
    for index in range(steps + 1):
        ratio = index / steps
        cell = (round(a[0] + (b[0] - a[0]) * ratio), round(a[1] + (b[1] - a[1]) * ratio))
        if not result or cell != result[-1]:
            result.append(cell)
    return result


def _quantize(point: list[float], resolution: int) -> tuple[int, int]:
    maximum = max(resolution - 1, 1)
    return (round(min(1.0, max(0.0, point[0])) * maximum), round(min(1.0, max(0.0, point[1])) * maximum))


def _cell_rows(cells: Iterable[tuple[int, int]]) -> list[dict[str, int]]:
    return [{"x": x, "y": y} for x, y in sorted(cells)]


def _edge_rows(edges: Iterable[tuple[int, int, int, int]]) -> list[dict[str, int]]:
    return [{"x1": a, "y1": b, "x2": c, "y2": d} for a, b, c, d in sorted(edges)]


def _distance(left: list[float], right: list[float]) -> float:
    return math.hypot(right[0] - left[0], right[1] - left[1])


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _segments_intersect(a: list[float], b: list[float], c: list[float], d: list[float]) -> bool:
    def orientation(p: list[float], q: list[float], r: list[float]) -> float:
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    return orientation(a, b, c) * orientation(a, b, d) < 0 and orientation(c, d, a) * orientation(c, d, b) < 0


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 6) if items else 0.0


def _strongest(rows: list[dict[str, Any]], metric: str) -> str | None:
    return max(rows, key=lambda row: (float(row.get(metric) or 0.0), row.get("planet", "")))["planet"] if rows else None
