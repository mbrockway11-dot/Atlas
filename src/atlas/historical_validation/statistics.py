"""Small-sample validation statistics and falsification utilities."""

from __future__ import annotations

import math
import random
from typing import Any

from atlas.historical_validation.controls import holdout_split


def validate_hypotheses(
    hypotheses: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    exposures: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    *,
    permutation_iterations: int = 1_000,
    seed: int = 19690720,
    known_confounders: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exposure_index = build_exposure_index(exposures)
    split = holdout_split([row["profile_key"] for row in windows])
    results: list[dict[str, Any]] = []
    permutation_rows: list[dict[str, Any]] = []
    for offset, hypothesis in enumerate(hypotheses):
        observations = [
            {
                **window,
                "exposed": int(window_exposed(window["window_id"], hypothesis, exposure_index)),
            }
            for window in windows
        ]
        event = [row for row in observations if row["window_kind"] == "event"]
        control = [row for row in observations if row["window_kind"] != "event"]
        a = sum(row["exposed"] for row in event)
        b = len(event) - a
        c = sum(row["exposed"] for row in control)
        d = len(control) - c
        event_rate = a / len(event) if event else 0.0
        baseline_rate = c / len(control) if control else 0.0
        effect = event_rate - baseline_rate
        odds_ratio, ci_low, ci_high = odds_ratio_ci(a, b, c, d)
        p_value = fisher_exact_two_sided(a, b, c, d)
        distribution = permutation_distribution(
            observations,
            iterations=permutation_iterations,
            seed=seed + offset,
        )
        permutation_p = (1 + sum(abs(value) >= abs(effect) for value in distribution)) / (len(distribution) + 1)
        placebo_percentile = percentile_rank(abs(effect), [abs(value) for value in distribution])
        for iteration, value in enumerate(distribution):
            permutation_rows.append({
                "hypothesis_id": hypothesis["hypothesis_id"],
                "iteration": iteration,
                "permuted_effect_size": value,
                "seed": seed + offset,
            })
        discovery = cohort_metrics(observations, set(split["discovery"]))
        holdout = cohort_metrics(observations, set(split["holdout"]))
        relevant_exposures = [
            row for row in exposures
            if matches_hypothesis(row, hypothesis) and row["minimum_orb"] <= float(hypothesis["orb"])
        ]
        stable_count = sum(bool(row.get("contact_stable_across_birth_time_range")) for row in relevant_exposures)
        sensitivity = stable_count / len(relevant_exposures) if relevant_exposures else None
        event_ids = sorted({row.get("event_id") for row in event if row.get("event_id")})
        profile_keys = sorted({row["profile_key"] for row in observations})
        pair_count = sum(
            any(event_id in relationship.get("shared_event_ids", []) for event_id in event_ids)
            for relationship in relationships
        )
        results.append({
            "hypothesis_id": hypothesis["hypothesis_id"],
            "hypothesis_status": hypothesis.get("status"),
            "rationale_type": hypothesis.get("rationale_type"),
            "profiles_included": profile_keys,
            "profile_count": len(profile_keys),
            "events_included": event_ids,
            "event_count": len(event_ids),
            "relationship_pairs_included": pair_count,
            "exact_transit_definition": {
                "transit_planet": hypothesis["transit_planet"],
                "natal_target": hypothesis["natal_target"],
                "aspect": hypothesis["aspect"],
                "orb": hypothesis["orb"],
                "lead_days": hypothesis.get("lead_days"),
                "lag_days": hypothesis.get("lag_days"),
            },
            "event_exposed": a,
            "event_unexposed": b,
            "control_exposed": c,
            "control_unexposed": d,
            "observed_event_rate": round(event_rate, 6),
            "matched_baseline_rate": round(baseline_rate, 6),
            "effect_size_rate_difference": round(effect, 6),
            "odds_ratio": odds_ratio,
            "confidence_interval_95": [ci_low, ci_high],
            "raw_p_value": p_value,
            "corrected_p_value": None,
            "corrected_significance": False,
            "placebo_percentile": placebo_percentile,
            "permutation_p_value": permutation_p,
            "permutation_iterations": permutation_iterations,
            "discovery_performance": discovery,
            "holdout_performance": holdout,
            "sensitivity_to_birth_time_uncertainty": sensitivity,
            "source_coverage": source_coverage(event),
            "known_confounders": known_confounders or [
                "single mission family with correlated events",
                "all pilot outcomes are positive",
                "unknown birth times for all pilot profiles",
                "very small cohort",
                "controls are within-person date shifts, not independent people",
            ],
            "event_fixed_effects": "event-family stratification recorded; inferential fixed-effect model not estimable in this pilot",
            "replication_status": "unreplicated_pilot",
            "decision": "pending_fdr",
            "claim_type": "statistical_association",
            "causal_claim": False,
        })
    apply_bh_fdr(results)
    for row in results:
        sufficient = row["profile_count"] >= 30 and row["event_count"] >= 10
        holdout_direction = row["holdout_performance"].get("effect_size_rate_difference")
        same_direction = holdout_direction is not None and row["effect_size_rate_difference"] * holdout_direction > 0
        if sufficient and row["corrected_significance"] and same_direction:
            row["decision"] = "retained_for_independent_replication"
        elif row["hypothesis_status"] == "preregistered_negative_control" and not row["corrected_significance"]:
            row["decision"] = "negative_control_not_rejected"
        else:
            row["decision"] = "not_retained_underpowered_or_unreplicated"
    return results, permutation_rows


def build_exposure_index(exposures: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in exposures:
        index.setdefault(row["window_id"], []).append(row)
    return index


def window_exposed(window_id: str, hypothesis: dict[str, Any], index: dict[str, list[dict[str, Any]]]) -> bool:
    return any(
        matches_hypothesis(row, hypothesis) and float(row["minimum_orb"]) <= float(hypothesis["orb"])
        for row in index.get(window_id, [])
    )


def matches_hypothesis(row: dict[str, Any], hypothesis: dict[str, Any]) -> bool:
    return all(row.get(key) == hypothesis.get(key) for key in ("transit_planet", "natal_target", "aspect"))


def odds_ratio_ci(a: int, b: int, c: int, d: int) -> tuple[float | None, float | None, float | None]:
    if a + c == 0 or b + d == 0:
        return None, None, None
    aa, bb, cc, dd = (float(value) for value in (a, b, c, d))
    if any(value == 0 for value in (aa, bb, cc, dd)):
        aa, bb, cc, dd = (value + 0.5 for value in (aa, bb, cc, dd))
    odds_ratio = (aa * dd) / (bb * cc)
    standard_error = math.sqrt(1 / aa + 1 / bb + 1 / cc + 1 / dd)
    log_or = math.log(odds_ratio)
    return tuple(round(value, 6) for value in (odds_ratio, math.exp(log_or - 1.96 * standard_error), math.exp(log_or + 1.96 * standard_error)))


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    row1, row2, col1 = a + b, c + d, a + c
    total = row1 + row2
    if total == 0:
        return 1.0
    lower = max(0, col1 - row2)
    upper = min(row1, col1)

    def probability(x: int) -> float:
        return math.comb(row1, x) * math.comb(row2, col1 - x) / math.comb(total, col1)

    observed = probability(a)
    return round(min(1.0, sum(probability(x) for x in range(lower, upper + 1) if probability(x) <= observed + 1e-12)), 12)


def permutation_distribution(observations: list[dict[str, Any]], *, iterations: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    labels = [int(row["outcome_present"]) for row in observations]
    exposures = [int(row["exposed"]) for row in observations]
    event_count = sum(labels)
    distribution = []
    for _ in range(iterations):
        shuffled = list(labels)
        rng.shuffle(shuffled)
        event_values = [exposure for exposure, label in zip(exposures, shuffled, strict=True) if label]
        control_values = [exposure for exposure, label in zip(exposures, shuffled, strict=True) if not label]
        event_rate = sum(event_values) / max(len(event_values), 1)
        control_rate = sum(control_values) / max(len(control_values), 1)
        distribution.append(round(event_rate - control_rate, 6))
    assert event_count == sum(labels)
    return distribution


def apply_bh_fdr(results: list[dict[str, Any]], alpha: float = 0.05) -> None:
    ordered = sorted(enumerate(results), key=lambda item: item[1]["raw_p_value"])
    count = len(ordered)
    adjusted = [1.0] * count
    running = 1.0
    for reverse_rank in range(count - 1, -1, -1):
        original_index, row = ordered[reverse_rank]
        rank = reverse_rank + 1
        running = min(running, row["raw_p_value"] * count / rank)
        adjusted[original_index] = min(1.0, running)
    for index, row in enumerate(results):
        row["corrected_p_value"] = round(adjusted[index], 12)
        row["corrected_significance"] = adjusted[index] <= alpha


def cohort_metrics(observations: list[dict[str, Any]], profiles: set[str]) -> dict[str, Any]:
    selected = [row for row in observations if row["profile_key"] in profiles]
    event = [row for row in selected if row["window_kind"] == "event"]
    control = [row for row in selected if row["window_kind"] != "event"]
    if not event or not control:
        return {"profile_count": len(profiles), "estimable": False, "effect_size_rate_difference": None}
    event_rate = sum(row["exposed"] for row in event) / len(event)
    control_rate = sum(row["exposed"] for row in control) / len(control)
    return {"profile_count": len(profiles), "estimable": True, "event_rate": round(event_rate, 6), "baseline_rate": round(control_rate, 6), "effect_size_rate_difference": round(event_rate - control_rate, 6)}


def source_coverage(event_rows: list[dict[str, Any]]) -> float:
    if not event_rows:
        return 0.0
    return round(sum(bool(row.get("source_citations")) for row in event_rows) / len(event_rows), 6)


def percentile_rank(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    below = sum(item < value for item in values)
    equal = sum(item == value for item in values)
    return round((below + 0.5 * equal) / len(values) * 100, 2)
