"""Identity layer similarity utilities."""

from typing import Any

from atlas.research.similarity import cosine_similarity


def layer_subtype_vector(layer: dict[str, Any]) -> dict[str, float]:
    """Extract subtype vector from identity layer."""
    return layer["subtype"]["scores"]


def layer_feature_vector(layer: dict[str, Any]) -> dict[str, float]:
    """Extract compact numeric feature vector from identity layer."""
    features = layer["features"]

    return {
        "self_loops": features["self_loops"],
        "density": features["density"],
        "clusters": float(features["clusters"]),
        "entropy": features["entropy"],
        "axis_strength": features["axis_strength"],
        "kamea_score": layer["kamea_score"],
    }


def compare_identity_layers(
    layer_a: dict[str, Any],
    layer_b: dict[str, Any],
) -> dict[str, Any]:
    """Compare two identity layers."""
    subtype_similarity = cosine_similarity(
        layer_subtype_vector(layer_a),
        layer_subtype_vector(layer_b),
    )

    feature_similarity = cosine_similarity(
        layer_feature_vector(layer_a),
        layer_feature_vector(layer_b),
    )

    overall_similarity = (subtype_similarity + feature_similarity) / 2.0

    return {
        "layer_a": layer_a["layer_id"],
        "layer_b": layer_b["layer_id"],
        "cipher_a": layer_a["cipher"],
        "cipher_b": layer_b["cipher"],
        "planet_a": layer_a["planet"],
        "planet_b": layer_b["planet"],
        "subtype_similarity": subtype_similarity,
        "feature_similarity": feature_similarity,
        "overall_similarity": overall_similarity,
    }
