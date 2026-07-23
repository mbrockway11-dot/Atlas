
"""Kamea Flow models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


KAMEA_FLOW_VERSION = "1.0.0"


@dataclass(frozen=True)
class KameaFlowStep:
    """One ordered movement through a Kamea field."""

    index: int
    stream_index: int
    stream_id: str
    cipher: str
    planet: str
    node: str
    local_node: str
    value: float
    x: float
    y: float
    normalized_x: float
    normalized_y: float
    grid_size: int
    visit_depth: int
    weight: float


@dataclass(frozen=True)
class KameaFlowEdge:
    """One directed transition in a Kamea flow."""

    source: str
    target: str
    cipher: str
    planet: str
    stream_id: str
    count: int
    distance: float
    direction_x: float
    direction_y: float


def flow_step_to_dict(step: KameaFlowStep) -> dict[str, Any]:
    """Convert flow step to dict."""
    return asdict(step)


def flow_edge_to_dict(edge: KameaFlowEdge) -> dict[str, Any]:
    """Convert flow edge to dict."""
    return asdict(edge)
