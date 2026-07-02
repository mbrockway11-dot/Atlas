"""Bridge compiled temporal CSS into the unified AtlasGraph model."""

from __future__ import annotations

from typing import Any

from atlas.graph.semantic import AtlasEdge, AtlasGraph, AtlasNode


TEMPORAL_GRAPH_BRIDGE_VERSION = "0.1"


def build_temporal_graph(
    *,
    profile_key: str,
    css: dict[str, Any],
    runtime_result: dict[str, Any] | None = None,
) -> AtlasGraph:
    """Build semantic graph from compiled temporal CSS."""
    temporal = css.get("temporal", {})
    natal = temporal.get("natal", {})
    ephemeris = natal.get("ephemeris", {})

    sidereal = ephemeris.get("sidereal", {})
    natal_planets = sidereal.get("planets", {})

    transits = ephemeris.get("transits", {})
    transit_chart = transits.get("transit_chart", {})
    transit_planets = transit_chart.get("planets", {})
    transit_contacts = transits.get("contacts", [])

    yogas = ephemeris.get("yogas", {})
    yoga_matches = yogas.get("matches", [])

    dignity = ephemeris.get("dignity", {})
    dignity_by_planet = dignity.get("dignities", {})

    nodes: list[AtlasNode] = []
    edges: list[AtlasEdge] = []

    for planet_name, position in natal_planets.items():
        planet_dignity = dignity_by_planet.get(planet_name, {})

        nodes.append(
            AtlasNode(
                id=f"natal:planet:{planet_name}",
                kind="natal_planet",
                label=planet_name,
                weight=float(planet_dignity.get("strength_score", 1.0) or 1.0),
                attributes={
                    "sign": position.get("sign"),
                    "longitude": position.get("longitude"),
                    "degree_in_sign": position.get("degree_in_sign"),
                    "retrograde": position.get("retrograde"),
                    "dignity": planet_dignity,
                },
            )
        )

    for planet_name, position in transit_planets.items():
        nodes.append(
            AtlasNode(
                id=f"transit:planet:{planet_name}",
                kind="transit_planet",
                label=f"Transit {planet_name}",
                attributes={
                    "sign": position.get("sign"),
                    "longitude": position.get("longitude"),
                    "degree_in_sign": position.get("degree_in_sign"),
                    "retrograde": position.get("retrograde"),
                },
            )
        )

    for index, contact in enumerate(transit_contacts):
        transit_planet = contact.get("transit_planet")
        natal_planet = contact.get("natal_planet")

        if not transit_planet or not natal_planet:
            continue

        edges.append(
            AtlasEdge(
                id=f"transit_contact:{index}:{transit_planet}:{natal_planet}",
                source=f"transit:planet:{transit_planet}",
                target=f"natal:planet:{natal_planet}",
                kind="transit_contact",
                weight=_contact_weight(contact),
                attributes=contact,
            )
        )

    for index, yoga in enumerate(yoga_matches):
        yoga_id = f"yoga:{index}:{_slug(yoga.get('name', 'unknown'))}"

        nodes.append(
            AtlasNode(
                id=yoga_id,
                kind="yoga",
                label=str(yoga.get("name", "Unknown Yoga")),
                weight=float(yoga.get("score", 1.0) or 1.0),
                attributes=yoga,
            )
        )

    metadata = {
        "graph_type": "temporal_semantic_graph",
        "bridge_version": TEMPORAL_GRAPH_BRIDGE_VERSION,
        "profile_key": profile_key,
        "ephemeris_status": ephemeris.get("ephemeris_status"),
        "sidereal_status": ephemeris.get("sidereal_status"),
        "transits_status": ephemeris.get("transits_status"),
        "yogas_status": ephemeris.get("yogas_status"),
    }

    if runtime_result:
        metadata["runtime"] = runtime_result.get("metadata", {})
        metadata["runtime_scoring"] = runtime_result.get("scoring", {})
        metadata["runtime_activation"] = runtime_result.get("activation", {})

    return AtlasGraph(
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata=metadata,
    )


def _contact_weight(contact: dict[str, Any]) -> float:
    """Return deterministic edge weight for one transit contact."""
    weight = 1.0

    if contact.get("same_sign"):
        weight += 1.0

    if contact.get("opposition"):
        weight += 0.75

    return weight


def _slug(value: str) -> str:
    """Build stable lowercase slug."""
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(":", "_")
    )
