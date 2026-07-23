"""Small-sample association tests with dependency and falsification controls."""

from __future__ import annotations

from collections import defaultdict
import math
import random
from statistics import mean
from typing import Any

from atlas.historical_validation.statistics import apply_bh_fdr, fisher_exact_two_sided, odds_ratio_ci
from atlas.symbolic_behavior.registry import behavior_profile_index


MIN_PROFILES = 30
MIN_BEHAVIOR_PROFILES = 10


def evaluate_symbolic_behavior_associations(
    observations: list[dict[str, Any]],
    features: list[dict[str, Any]],
    *,
    permutation_iterations: int = 1_000,
    seed: int = 8675309,
    annotation_blinded: bool = False,
) -> list[dict[str, Any]]:
    all_profiles = sorted({row["profile_key"] for row in observations})
    behavior_index = behavior_profile_index(observations)
    by_feature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in features:
        by_feature[row["feature_id"]].append(row)
    results: list[dict[str, Any]] = []
    for behavior_id, positive_profiles in sorted(behavior_index.items()):
        if not positive_profiles or len(positive_profiles) == len(all_profiles):
            continue
        for feature_id, rows in sorted(by_feature.items()):
            template = rows[0]
            values = {row["profile_key"]: row["value"] for row in rows if row["profile_key"] in all_profiles}
            if len(values) != len(all_profiles):
                continue
            if template["value_type"] == "numeric":
                result = numeric_result(behavior_id, positive_profiles, all_profiles, feature_id, values, template, permutation_iterations, seed + len(results))
                if result:
                    results.append(result)
            else:
                for value in sorted(set(values.values()), key=str):
                    token_profiles = {profile for profile, observed in values.items() if observed == value}
                    if not token_profiles or len(token_profiles) == len(all_profiles):
                        continue
                    results.append(categorical_result(behavior_id, positive_profiles, all_profiles, feature_id, value, token_profiles, template))
    if results:
        apply_bh_fdr(results)
    for row in results:
        sufficiently_powered = row["profile_count"] >= MIN_PROFILES and row["behavior_profile_count"] >= MIN_BEHAVIOR_PROFILES
        row["sufficiently_powered"] = sufficiently_powered
        row["replication_status"] = "unreplicated_pilot"
        row["annotation_blinded"] = annotation_blinded
        row["decision"] = "retained_for_independent_replication" if sufficiently_powered and row["corrected_significance"] and annotation_blinded else "not_retained_underpowered_nonsignificant_or_unblinded"
        row["causal_claim"] = False
        row["contrast_definition"] = "Profiles with this documented behavior versus other profiles in the documented pilot; comparison does not mean behavioral absence."
    return results


def categorical_result(behavior_id: str, positive: set[str], profiles: list[str], feature_id: str, value: Any, token_profiles: set[str], template: dict[str, Any]) -> dict[str, Any]:
    negative = set(profiles) - positive
    a = len(positive & token_profiles); b = len(positive - token_profiles)
    c = len(negative & token_profiles); d = len(negative - token_profiles)
    odds, low, high = odds_ratio_ci(a, b, c, d)
    positive_rate = a / len(positive)
    comparison_rate = c / len(negative)
    result = base_result(behavior_id, profiles, positive, feature_id, template)
    result["association_id"] = f"{result['association_id']}={value}"
    return result | {
        "test_type": "fisher_exact_categorical",
        "feature_value": value,
        "contingency_table": {"behavior_and_feature": a, "behavior_without_feature": b, "comparison_and_feature": c, "comparison_without_feature": d},
        "behavior_feature_rate": round(positive_rate, 6),
        "comparison_feature_rate": round(comparison_rate, 6),
        "effect_size": round(positive_rate - comparison_rate, 6),
        "odds_ratio": odds, "confidence_interval_95": [low, high],
        "raw_p_value": fisher_exact_two_sided(a, b, c, d),
        "corrected_p_value": None, "corrected_significance": False,
    }


def numeric_result(behavior_id: str, positive: set[str], profiles: list[str], feature_id: str, values: dict[str, Any], template: dict[str, Any], iterations: int, seed: int) -> dict[str, Any] | None:
    try:
        numeric = {key: float(value) for key, value in values.items()}
    except (TypeError, ValueError):
        return None
    negative = set(profiles) - positive
    positive_values = [numeric[key] for key in positive]
    negative_values = [numeric[key] for key in negative]
    if not positive_values or not negative_values or len(set(numeric.values())) < 2:
        return None
    effect = mean(positive_values) - mean(negative_values)
    pooled = pooled_standard_deviation(positive_values, negative_values)
    standardized = effect / pooled if pooled else 0.0
    rng = random.Random(seed)
    labels = [profile in positive for profile in profiles]
    vector = [numeric[profile] for profile in profiles]
    extreme = 0
    for _ in range(iterations):
        shuffled = list(labels); rng.shuffle(shuffled)
        left = [value for value, label in zip(vector, shuffled, strict=True) if label]
        right = [value for value, label in zip(vector, shuffled, strict=True) if not label]
        if abs(mean(left) - mean(right)) >= abs(effect) - 1e-12:
            extreme += 1
    return base_result(behavior_id, profiles, positive, feature_id, template) | {
        "test_type": "permutation_mean_difference",
        "feature_value": None,
        "behavior_mean": round(mean(positive_values), 6),
        "comparison_mean": round(mean(negative_values), 6),
        "effect_size": round(effect, 6),
        "standardized_effect": round(standardized, 6),
        "permutation_iterations": iterations,
        "raw_p_value": round((extreme + 1) / (iterations + 1), 12),
        "corrected_p_value": None, "corrected_significance": False,
    }


def base_result(behavior_id: str, profiles: list[str], positive: set[str], feature_id: str, template: dict[str, Any]) -> dict[str, Any]:
    return {
        "association_id": f"{behavior_id}:{feature_id}",
        "behavior_id": behavior_id, "feature_id": feature_id,
        "feature_family": template["feature_family"],
        "independence_group": template["independence_group"],
        "input_dependencies": template["input_dependencies"],
        "profile_count": len(profiles), "behavior_profile_count": len(positive),
        "behavior_profiles": sorted(positive),
        "evidence_kind": "exploratory_statistical_association",
    }


def pooled_standard_deviation(left: list[float], right: list[float]) -> float:
    if len(left) + len(right) < 3:
        return 0.0
    left_variance = sum((value - mean(left)) ** 2 for value in left)
    right_variance = sum((value - mean(right)) ** 2 for value in right)
    return math.sqrt((left_variance + right_variance) / max(len(left) + len(right) - 2, 1))


def build_independence_audit(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    by_behavior: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        by_behavior[row["behavior_id"]].append(row)
    for behavior_id, rows in sorted(by_behavior.items()):
        nominal = [row for row in rows if row["raw_p_value"] <= 0.05]
        corrected = [row for row in rows if row["corrected_significance"]]
        groups = sorted({row["independence_group"] for row in corrected})
        independent_base_groups = sorted(set(groups) & {"birth_input", "name_input"})
        output.append({
            "behavior_id": behavior_id,
            "tested_associations": len(rows),
            "nominal_associations": len(nominal),
            "corrected_associations": len(corrected),
            "independent_groups_after_correction": groups,
            "independent_base_groups_after_correction": independent_base_groups,
            "independent_group_count": len(independent_base_groups),
            "cross_family_signal": set(independent_base_groups) == {"birth_input", "name_input"},
            "warning": "Vedic and birth-date numerology share birth_input. Name numerology, Gematria, and Kamea share name_input. Mixed features are not independent corroboration.",
        })
    return output
