
"""Explainability engine for Atlas Synthesis."""

from __future__ import annotations

from typing import Any


SYNTHESIS_EXPLAINABILITY_VERSION = "1.0"


def build_explainability_report(synthesis: dict[str, Any]) -> dict[str, Any]:
    """Build explainability report from synthesis payload."""
    evidence = synthesis.get("evidence", {}).get("evidence", [])
    fusion_themes = synthesis.get("fusion", {}).get("themes", [])
    reasoning = synthesis.get("reasoning", {}).get("inferences", [])
    graph = synthesis.get("inference_graph", {})

    evidence_by_feature = group_by(evidence, "feature")
    themes_by_feature = {
        item.get("feature"): item
        for item in fusion_themes
    }

    explanations = [
        explain_inference(
            inference=item,
            evidence_by_feature=evidence_by_feature,
            themes_by_feature=themes_by_feature,
            graph=graph,
        )
        for item in reasoning
    ]

    return {
        "success": True,
        "version": SYNTHESIS_EXPLAINABILITY_VERSION,
        "explanation_count": len(explanations),
        "explanations": explanations,
    }


def explain_inference(
    *,
    inference: dict[str, Any],
    evidence_by_feature: dict[str, list[dict[str, Any]]],
    themes_by_feature: dict[str, dict[str, Any]],
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Explain one inference."""
    supporting_features = inference.get("supporting_features", [])

    evidence_rows = []
    engines = set()

    for feature in supporting_features:
        for item in evidence_by_feature.get(feature, []):
            engine = item.get("engine", "unknown")
            engines.add(engine.split(".")[0])
            evidence_rows.append(
                {
                    "feature": feature,
                    "engine": engine,
                    "confidence": item.get("confidence"),
                    "value": item.get("value"),
                    "explanation": item.get("explanation"),
                }
            )

    theme_rows = [
        themes_by_feature.get(feature, {})
        for feature in supporting_features
        if feature in themes_by_feature
    ]

    return {
        "inference": inference.get("inference"),
        "category": inference.get("category"),
        "confidence": inference.get("confidence"),
        "plain_english": plain_english_explanation(inference, supporting_features, sorted(engines)),
        "supporting_features": supporting_features,
        "supporting_engines": sorted(engines),
        "supporting_evidence": evidence_rows,
        "supporting_themes": theme_rows,
        "graph_edges": related_edges(graph, inference.get("inference"), supporting_features),
        "reasoning_statement": inference.get("explanation", ""),
    }


def plain_english_explanation(
    inference: dict[str, Any],
    features: list[str],
    engines: list[str],
) -> str:
    """Build compact human-readable explanation."""
    name = inference.get("inference", "this inference")
    feature_text = ", ".join(features[:6])
    engine_text = ", ".join(engines[:8])

    return (
        f"Atlas inferred {name} because the consensus layer found reinforcing support "
        f"across these features: {feature_text}. Supporting evidence came from: {engine_text}."
    )


def related_edges(
    graph: dict[str, Any],
    inference_name: str | None,
    features: list[str],
) -> list[dict[str, Any]]:
    """Return graph edges related to inference/features."""
    if not inference_name:
        return []

    target = f"inference:{inference_name}"
    feature_nodes = {f"theme:{feature}" for feature in features}

    return [
        edge
        for edge in graph.get("edges", [])
        if edge.get("target") == target
        or edge.get("source") in feature_nodes
        or edge.get("target") in feature_nodes
    ]


def group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    """Group dict rows by key."""
    output: dict[str, list[dict[str, Any]]] = {}

    for item in items:
        output.setdefault(str(item.get(key, "unknown")), []).append(item)

    return output
