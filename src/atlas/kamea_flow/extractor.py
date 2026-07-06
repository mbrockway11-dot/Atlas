
"""Kamea Flow extraction.

This module extracts ordered Kamea construction passes from canonical payloads.
It is intentionally defensive because older compiled payloads may have partial
or differently-shaped Kamea data.
"""

from __future__ import annotations

from typing import Any

from atlas.kamea_flow.models import KameaFlowStep


def extract_kamea_flow_steps(payload: dict[str, Any]) -> list[KameaFlowStep]:
    """Extract ordered Kamea flow steps from a canonical payload."""
    kamea = payload.get("kamea", {}) or {}

    passes = (
        kamea.get("construction_passes")
        or kamea.get("passes")
        or kamea.get("flow_passes")
        or []
    )

    steps: list[KameaFlowStep] = []

    if passes:
        for pass_index, construction_pass in enumerate(passes):
            steps.extend(
                extract_steps_from_pass(
                    construction_pass,
                    pass_index=pass_index,
                )
            )

    if not steps:
        steps = extract_steps_from_graph(kamea)

    return sorted(steps, key=lambda item: item.index)


def extract_steps_from_pass(
    construction_pass: dict[str, Any],
    *,
    pass_index: int,
) -> list[KameaFlowStep]:
    """Extract flow steps from one construction pass."""
    cipher = str(
        construction_pass.get("cipher")
        or construction_pass.get("cipher_name")
        or "unknown_cipher"
    )

    planet = str(
        construction_pass.get("planet")
        or construction_pass.get("planet_name")
        or "unknown_planet"
    )

    raw_steps = (
        construction_pass.get("steps")
        or construction_pass.get("path")
        or construction_pass.get("nodes")
        or []
    )

    steps = []

    for local_index, item in enumerate(as_list(raw_steps)):
        node = node_label(item)
        value = numeric_value(item)
        x, y = coordinates(item)

        steps.append(
            KameaFlowStep(
                index=pass_index * 10000 + local_index,
                cipher=cipher,
                planet=planet,
                node=node,
                value=value,
                x=x,
                y=y,
                weight=weight_value(item),
            )
        )

    return steps


def extract_steps_from_graph(kamea: dict[str, Any]) -> list[KameaFlowStep]:
    """Fallback extraction from Kamea graph nodes."""
    graph = kamea.get("graph", {}) or kamea.get("identity_graph", {}) or {}
    nodes = graph.get("nodes", {}) or kamea.get("nodes", {}) or {}

    steps = []

    if isinstance(nodes, dict):
        iterable = nodes.items()
    else:
        iterable = enumerate(as_list(nodes))

    for index, item in enumerate(iterable):
        if isinstance(item, tuple) and len(item) == 2:
            key, node_data = item
        else:
            key, node_data = index, item

        if not isinstance(node_data, dict):
            node_data = {"node": key, "value": key}

        x, y = coordinates(node_data)

        steps.append(
            KameaFlowStep(
                index=index,
                cipher=str(node_data.get("cipher") or "unknown_cipher"),
                planet=str(node_data.get("planet") or "unknown_planet"),
                node=str(node_data.get("node") or node_data.get("id") or key),
                value=numeric_value(node_data),
                x=x,
                y=y,
                weight=weight_value(node_data),
            )
        )

    return steps


def as_list(value: Any) -> list[Any]:
    """Convert value to list."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [value]


def node_label(item: Any) -> str:
    """Extract node label."""
    if isinstance(item, dict):
        return str(
            item.get("node")
            or item.get("id")
            or item.get("label")
            or item.get("value")
            or "unknown"
        )

    return str(item)


def numeric_value(item: Any) -> float:
    """Extract numeric node value."""
    if isinstance(item, dict):
        for key in ["value", "number", "node", "id"]:
            if key in item:
                return float_or_zero(item.get(key))

    return float_or_zero(item)


def coordinates(item: Any) -> tuple[float, float]:
    """Extract or derive coordinates."""
    if isinstance(item, dict):
        if "x" in item or "y" in item:
            return float_or_zero(item.get("x")), float_or_zero(item.get("y"))

        if "coord" in item and isinstance(item.get("coord"), (list, tuple)):
            coord = item.get("coord")
            if len(coord) >= 2:
                return float_or_zero(coord[0]), float_or_zero(coord[1])

        if "position" in item and isinstance(item.get("position"), (list, tuple)):
            position = item.get("position")
            if len(position) >= 2:
                return float_or_zero(position[0]), float_or_zero(position[1])

    value = numeric_value(item)

    # Fallback: place on a 9-wide reduced lattice.
    x = (value - 1) % 9
    y = (value - 1) // 9

    return x, y


def weight_value(item: Any) -> float:
    """Extract node weight."""
    if isinstance(item, dict):
        for key in ["weight", "count", "visits", "frequency"]:
            if key in item:
                return max(1.0, float_or_zero(item.get(key)))

    return 1.0


def float_or_zero(value: Any) -> float:
    """Convert to float or zero."""
    try:
        return float(value)
    except Exception:
        return 0.0
