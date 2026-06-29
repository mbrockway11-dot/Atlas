"""Population topology tools for Atlas profile feature graphs.

This module extends Atlas' existing graph/topology work to the population
scale. Existing topology files describe structure inside one identity. This
module builds a graph between identities using the validated profile-level
feature matrix.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from atlas.research.validation import normalize_profile_features

POPULATION_TOPOLOGY_VERSION = "1.0"


def _feature_columns(profile_features: pd.DataFrame) -> list[str]:
    return [column for column in profile_features.columns if column != "name"]


def _normalized_matrix(profile_features: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    if profile_features.empty or "name" not in profile_features.columns:
        return [], np.empty((0, 0), dtype=float)

    normalized = normalize_profile_features(profile_features)
    columns = _feature_columns(normalized)
    names = normalized["name"].astype(str).tolist()

    if not columns:
        return names, np.empty((len(names), 0), dtype=float)

    matrix = normalized[columns].to_numpy(dtype=float)
    matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
    return names, matrix


def cosine_similarity_matrix(profile_features: pd.DataFrame) -> pd.DataFrame:
    """Build a deterministic pairwise cosine similarity matrix."""
    names, matrix = _normalized_matrix(profile_features)

    if not names:
        return pd.DataFrame()

    if matrix.size == 0:
        return pd.DataFrame(np.eye(len(names)), index=names, columns=names)

    norms = np.linalg.norm(matrix, axis=1)
    denominator = norms[:, None] * norms[None, :]

    with np.errstate(divide="ignore", invalid="ignore"):
        similarities = np.divide(
            matrix @ matrix.T,
            denominator,
            out=np.zeros((len(names), len(names)), dtype=float),
            where=denominator != 0,
        )

    np.fill_diagonal(similarities, 1.0)
    return pd.DataFrame(similarities, index=names, columns=names)


def euclidean_similarity_matrix(profile_features: pd.DataFrame) -> pd.DataFrame:
    """Build pairwise similarity from normalized Euclidean distance."""
    names, matrix = _normalized_matrix(profile_features)

    if not names:
        return pd.DataFrame()

    if matrix.size == 0:
        return pd.DataFrame(np.eye(len(names)), index=names, columns=names)

    distances = np.linalg.norm(matrix[:, None, :] - matrix[None, :, :], axis=2)
    similarities = 1.0 / (1.0 + distances)
    np.fill_diagonal(similarities, 1.0)
    return pd.DataFrame(similarities, index=names, columns=names)


def pairwise_similarity_matrix(
    profile_features: pd.DataFrame,
    *,
    metric: str = "cosine",
) -> pd.DataFrame:
    """Build pairwise profile similarity matrix."""
    if metric == "euclidean":
        return euclidean_similarity_matrix(profile_features)
    return cosine_similarity_matrix(profile_features)


def build_population_topology_graph(
    profile_features: pd.DataFrame,
    *,
    threshold: float = 0.75,
    top_k: int = 5,
    metric: str = "cosine",
) -> dict[str, Any]:
    """Build a population similarity graph from profile-level features.

    Edges are kept when they meet the similarity threshold or appear in the
    top-k neighbor set for either endpoint. This prevents the graph from going
    fully empty when the threshold is strict while still making the threshold
    meaningful.
    """
    similarity = pairwise_similarity_matrix(profile_features, metric=metric)
    names = list(similarity.index)

    nodes = {
        name: {
            "id": name,
            "label": name,
            "degree": 0,
            "weighted_degree": 0.0,
            "component": None,
            "community": None,
        }
        for name in names
    }

    edges: dict[str, dict[str, Any]] = {}
    top_pairs = _top_neighbor_pairs(similarity, top_k=top_k)

    for left_index, source in enumerate(names):
        for target in names[left_index + 1:]:
            value = float(similarity.loc[source, target])
            pair = _edge_key(source, target)
            keep = value >= threshold or pair in top_pairs

            if not keep:
                continue

            edges[pair] = {
                "id": pair,
                "source": source,
                "target": target,
                "weight": value,
                "similarity": value,
                "distance": float(1.0 - value),
                "metric": metric,
                "above_threshold": bool(value >= threshold),
                "top_k_edge": bool(pair in top_pairs),
            }

    degrees = compute_degrees(nodes, edges)
    weighted = compute_weighted_degrees(nodes, edges)
    components = connected_components(nodes, edges)
    communities = deterministic_communities(nodes, edges)
    centrality = centrality_scores(nodes, edges)

    for node_id, node in nodes.items():
        node["degree"] = degrees[node_id]
        node["weighted_degree"] = weighted[node_id]
        node["component"] = components["node_component"].get(node_id)
        node["community"] = communities["node_community"].get(node_id)
        node.update(centrality.get(node_id, {}))

    return {
        "version": POPULATION_TOPOLOGY_VERSION,
        "metric": metric,
        "threshold": float(threshold),
        "top_k": int(top_k),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "components": components["components"],
        "communities": communities["communities"],
        "summary": build_graph_summary(nodes, edges, components, communities),
    }


def _top_neighbor_pairs(similarity: pd.DataFrame, *, top_k: int) -> set[str]:
    if similarity.empty or top_k <= 0:
        return set()

    pairs: set[str] = set()
    names = list(similarity.index)

    for source in names:
        candidates = []
        for target in names:
            if source == target:
                continue
            candidates.append((target, float(similarity.loc[source, target])))
        candidates.sort(key=lambda item: (-item[1], item[0]))

        for target, _ in candidates[:top_k]:
            pairs.add(_edge_key(source, target))

    return pairs


def _edge_key(source: str, target: str) -> str:
    left, right = sorted([source, target])
    return f"{left}::{right}"


def compute_degrees(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, int]:
    """Compute unweighted node degree."""
    degrees = {node_id: 0 for node_id in nodes}

    for edge in edges.values():
        degrees[edge["source"]] += 1
        degrees[edge["target"]] += 1

    return degrees


def compute_weighted_degrees(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, float]:
    """Compute weighted node degree from edge similarities."""
    degrees = {node_id: 0.0 for node_id in nodes}

    for edge in edges.values():
        weight = float(edge.get("weight", 0.0))
        degrees[edge["source"]] += weight
        degrees[edge["target"]] += weight

    return degrees


def adjacency(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    """Build undirected adjacency map."""
    graph = {node_id: set() for node_id in nodes}

    for edge in edges.values():
        source = edge["source"]
        target = edge["target"]
        graph[source].add(target)
        graph[target].add(source)

    return graph


def connected_components(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute deterministic connected components."""
    graph = adjacency(nodes, edges)
    visited: set[str] = set()
    components = []
    node_component: dict[str, int] = {}

    for node_id in sorted(nodes):
        if node_id in visited:
            continue

        stack = [node_id]
        visited.add(node_id)
        members = []

        while stack:
            current = stack.pop()
            members.append(current)
            for neighbor in sorted(graph[current], reverse=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        members = sorted(members)
        component_id = len(components)
        for member in members:
            node_component[member] = component_id
        components.append({"component": component_id, "profile_count": len(members), "members": members})

    components.sort(key=lambda item: (-item["profile_count"], item["members"][0] if item["members"] else ""))
    remap = {component["component"]: index for index, component in enumerate(components)}
    for index, component in enumerate(components):
        old = component["component"]
        component["component"] = index
        for member in component["members"]:
            node_component[member] = index

    return {"components": components, "node_component": node_component, "component_remap": remap}


def deterministic_communities(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Detect simple deterministic communities by weighted label propagation."""
    if not nodes:
        return {"communities": [], "node_community": {}}

    graph = adjacency(nodes, edges)
    edge_weights = {
        (edge["source"], edge["target"]): float(edge.get("weight", 1.0))
        for edge in edges.values()
    }
    edge_weights.update({(target, source): weight for (source, target), weight in list(edge_weights.items())})

    labels = {node_id: node_id for node_id in nodes}

    for _ in range(25):
        changed = False
        for node_id in sorted(nodes):
            if not graph[node_id]:
                continue
            scores: dict[str, float] = {}
            for neighbor in graph[node_id]:
                label = labels[neighbor]
                scores[label] = scores.get(label, 0.0) + edge_weights.get((node_id, neighbor), 1.0)
            best_label = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0][0]
            if labels[node_id] != best_label:
                labels[node_id] = best_label
                changed = True
        if not changed:
            break

    grouped: dict[str, list[str]] = {}
    for node_id, label in labels.items():
        grouped.setdefault(label, []).append(node_id)

    communities_raw = [sorted(members) for members in grouped.values()]
    communities_raw.sort(key=lambda members: (-len(members), members[0] if members else ""))

    communities = []
    node_community: dict[str, int] = {}
    for community_id, members in enumerate(communities_raw):
        for member in members:
            node_community[member] = community_id
        communities.append(
            {
                "community": community_id,
                "profile_count": len(members),
                "members": members,
            }
        )

    return {"communities": communities, "node_community": node_community}


def centrality_scores(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Compute lightweight degree and closeness centrality without networkx."""
    graph = adjacency(nodes, edges)
    n = len(nodes)
    degrees = compute_degrees(nodes, edges)
    weighted = compute_weighted_degrees(nodes, edges)
    scores: dict[str, dict[str, float]] = {}

    for node_id in nodes:
        distances = _shortest_path_lengths(graph, node_id)
        reachable = [distance for target, distance in distances.items() if target != node_id]
        closeness = 0.0
        if reachable and sum(reachable) > 0:
            closeness = len(reachable) / sum(reachable)
            if n > 1:
                closeness *= len(reachable) / (n - 1)

        scores[node_id] = {
            "degree_centrality": float(degrees[node_id] / (n - 1)) if n > 1 else 0.0,
            "weighted_degree_centrality": float(weighted[node_id] / (n - 1)) if n > 1 else 0.0,
            "closeness_centrality": float(closeness),
        }

    return scores


def _shortest_path_lengths(graph: dict[str, set[str]], start: str) -> dict[str, int]:
    distances = {start: 0}
    queue = [start]

    while queue:
        current = queue.pop(0)
        for neighbor in sorted(graph[current]):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)

    return distances


def build_graph_summary(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    components: dict[str, Any],
    communities: dict[str, Any],
) -> dict[str, Any]:
    """Build population topology graph summary."""
    node_count = len(nodes)
    edge_count = len(edges)
    possible_edges = node_count * (node_count - 1) / 2 if node_count > 1 else 0
    density = float(edge_count / possible_edges) if possible_edges else 0.0

    sorted_nodes = sorted(
        nodes.values(),
        key=lambda node: (-float(node.get("weighted_degree", 0.0)), -int(node.get("degree", 0)), node["id"]),
    )

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "density": density,
        "component_count": len(components["components"]),
        "community_count": len(communities["communities"]),
        "average_degree": float(sum(node.get("degree", 0) for node in nodes.values()) / node_count) if node_count else 0.0,
        "most_connected_profiles": [
            {
                "name": node["id"],
                "degree": int(node.get("degree", 0)),
                "weighted_degree": float(node.get("weighted_degree", 0.0)),
                "community": node.get("community"),
                "component": node.get("component"),
            }
            for node in sorted_nodes[:25]
        ],
    }


def topology_nodes_dataframe(graph: dict[str, Any]) -> pd.DataFrame:
    """Convert graph nodes to a dataframe."""
    return pd.DataFrame(list(graph.get("nodes", {}).values()))


def topology_edges_dataframe(graph: dict[str, Any]) -> pd.DataFrame:
    """Convert graph edges to a dataframe."""
    return pd.DataFrame(list(graph.get("edges", {}).values()))


def population_topology_report_to_json(report: dict[str, Any]) -> str:
    """Serialize population topology report."""
    return json.dumps(report, indent=2, sort_keys=True)