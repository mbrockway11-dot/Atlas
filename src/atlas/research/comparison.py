"""Atlas ACF comparison engine."""

from typing import Any

from atlas.research.similarity import (
    absolute_distance,
    cosine_similarity,
    extract_essence_function_vector,
    extract_planetary_vector,
    extract_subtype_vector,
    mean_absolute_distance,
    similarity_from_distance,
)


def compare_acf_profiles(
    acf_a: dict[str, Any],
    acf_b: dict[str, Any],
) -> dict[str, Any]:
    """Compare two ACF profiles."""
    subtype_a = extract_subtype_vector(acf_a)
    subtype_b = extract_subtype_vector(acf_b)

    planetary_a = extract_planetary_vector(acf_a)
    planetary_b = extract_planetary_vector(acf_b)

    essence_a = extract_essence_function_vector(acf_a)
    essence_b = extract_essence_function_vector(acf_b)

    subtype_distance = mean_absolute_distance(subtype_a, subtype_b)
    planetary_distance = mean_absolute_distance(planetary_a, planetary_b)
    essence_distance = mean_absolute_distance(essence_a, essence_b)

    subtype_similarity = cosine_similarity(subtype_a, subtype_b)
    planetary_similarity = cosine_similarity(planetary_a, planetary_b)
    essence_similarity = cosine_similarity(essence_a, essence_b)

    overall_similarity = (
        subtype_similarity
        + planetary_similarity
        + essence_similarity
    ) / 3.0

    return {
        "profile_a": acf_a["identity"]["name"],
        "profile_b": acf_b["identity"]["name"],
        "overall_similarity": overall_similarity,
        "subtype": {
            "similarity": subtype_similarity,
            "mean_absolute_distance": subtype_distance,
            "distance_by_key": absolute_distance(subtype_a, subtype_b),
            "profile_a_primary": acf_a["invariant_analysis"]["subtype"]["primary_type"],
            "profile_b_primary": acf_b["invariant_analysis"]["subtype"]["primary_type"],
        },
        "planetary": {
            "similarity": planetary_similarity,
            "mean_absolute_distance": planetary_distance,
            "distance_by_key": absolute_distance(planetary_a, planetary_b),
            "profile_a_top_kameas": acf_a["invariant_analysis"]["top_kameas"],
            "profile_b_top_kameas": acf_b["invariant_analysis"]["top_kameas"],
        },
        "essence_function": {
            "similarity": essence_similarity,
            "mean_absolute_distance": essence_distance,
            "distance_by_key": absolute_distance(essence_a, essence_b),
            "profile_a_role": acf_a["essence"]["classification"]["function"]["role"],
            "profile_b_role": acf_b["essence"]["classification"]["function"]["role"],
        },
        "distance_summary": {
            "subtype_distance": subtype_distance,
            "planetary_distance": planetary_distance,
            "essence_distance": essence_distance,
            "subtype_distance_similarity": similarity_from_distance(subtype_distance),
            "planetary_distance_similarity": similarity_from_distance(planetary_distance),
            "essence_distance_similarity": similarity_from_distance(essence_distance),
        },
    }