
"""Alpha Ensemble v5.1 diversification-aware allocation safety.

The ensemble publishes allocation intelligence consumed by Adaptive
Weighting. A lack of normally qualified assets must not silently convert
a regime cash recommendation into an unintended 100% cash target.

Fallback policy:

1. Use normally qualified PROMOTE_LONG or MAINTAIN assets.
2. If none qualify, preserve the regime cash recommendation and allocate
   the remaining risky budget defensively across the top WATCH assets.
3. Use 100% cash only when neither normal nor defensive candidates exist.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


MAX_ASSET_WEIGHT = 0.35
MAX_SECTOR_WEIGHT = 0.45
MIN_POSITION_WEIGHT = 0.03
MAX_POSITIONS = 6

DEFENSIVE_POSITION_COUNT = 2
DEFENSIVE_MIN_SCORE = 0.45
DEFENSIVE_MIN_CONFIDENCE = 0.65


def build_ensemble_allocations(
    scores: list[dict],
    regime: dict | None = None,
) -> list[dict]:
    regime = regime or {}

    recommended_cash = clamp(
        regime.get(
            "recommended_cash_weight",
            0.30,
        )
    )

    risky_budget = max(
        0.0,
        1.0 - recommended_cash,
    )

    candidates = normal_candidates(scores)
    fallback_policy = "NORMAL_QUALIFIED_ALLOCATION"

    if not candidates:
        candidates = defensive_candidates(scores)
        fallback_policy = "DEFENSIVE_WATCH_FALLBACK"

    if not candidates:
        return [{
            "asset": "CASH",
            "ensemble_score": 1.0,
            "confidence": 1.0,
            "conviction": 1.0,
            "ensemble_target_weight": 1.0,
            "ensemble_action": "RESERVE_CASH",
            "ensemble_rank": None,
            "sector": "cash",
            "diversification_multiplier": 1.0,
            "source_count": 0,
            "allocation_policy": (
                "EMERGENCY_CASH_FALLBACK"
            ),
            "regime_cash_weight": (
                recommended_cash
            ),
            "source": "alpha_ensemble_v6_1",
        }]

    candidates = candidates[:MAX_POSITIONS]

    weighted_candidates = apply_diversification_scores(
        candidates
    )

    allocations = allocate_risky_budget(
        weighted_candidates,
        risky_budget=risky_budget,
    )

    allocations = apply_caps(
        allocations,
        risky_budget=risky_budget,
    )

    output = []

    for row in allocations:
        weight = round(
            float(
                row.get(
                    "ensemble_target_weight",
                    0.0,
                )
            ),
            6,
        )

        if weight < MIN_POSITION_WEIGHT:
            continue

        output.append({
            "asset": row["asset"],
            "ensemble_score": round(
                number(
                    row.get("ensemble_score")
                ),
                6,
            ),
            "confidence": round(
                number(row.get("confidence")),
                6,
            ),
            "conviction": round(
                number(row.get("conviction")),
                6,
            ),
            "ensemble_target_weight": weight,
            "ensemble_action": row.get(
                "ensemble_action"
            ),
            "ensemble_rank": row.get(
                "ensemble_rank"
            ),
            "sector": row.get(
                "sector",
                "unknown",
            ),
            "diversification_multiplier": row.get(
                "diversification_multiplier",
                1.0,
            ),
            "source_count": row.get(
                "source_count",
                0,
            ),
            "allocation_policy": fallback_policy,
            "regime_cash_weight": (
                recommended_cash
            ),
            "source": "alpha_ensemble_v6_1",
        })

    allocated_risky = sum(
        number(
            row.get("ensemble_target_weight")
        )
        for row in output
    )

    cash_weight = round(
        max(
            0.0,
            1.0 - allocated_risky,
        ),
        6,
    )

    output.append({
        "asset": "CASH",
        "ensemble_score": 1.0,
        "confidence": 1.0,
        "conviction": 1.0,
        "ensemble_target_weight": cash_weight,
        "ensemble_action": "RESERVE_CASH",
        "ensemble_rank": None,
        "sector": "cash",
        "diversification_multiplier": 1.0,
        "source_count": 0,
        "allocation_policy": fallback_policy,
        "regime_cash_weight": (
            recommended_cash
        ),
        "source": "alpha_ensemble_v6_1",
    })

    return reconcile_total_weight(output)


def normal_candidates(
    scores: list[dict],
) -> list[dict]:
    candidates = [
        row.copy()
        for row in scores
        if row.get("ensemble_action")
        in {
            "PROMOTE_LONG",
            "MAINTAIN",
        }
        and number(
            row.get("confidence")
        ) >= 0.45
        and number(
            row.get("ensemble_score")
        ) >= 0.52
    ]

    return rank_candidates(candidates)


def defensive_candidates(
    scores: list[dict],
) -> list[dict]:
    """Select high-confidence WATCH assets without promoting them.

    This preserves partial market exposure while respecting the cash
    recommendation of a defensive regime.
    """
    candidates = [
        row.copy()
        for row in scores
        if row.get("ensemble_action") == "WATCH"
        and number(
            row.get("ensemble_score")
        ) >= DEFENSIVE_MIN_SCORE
        and number(
            row.get("confidence")
        ) >= DEFENSIVE_MIN_CONFIDENCE
        and str(
            row.get("direction", "")
        ).upper()
        in {
            "LONG",
            "NEUTRAL",
        }
    ]

    candidates = rank_candidates(candidates)

    return candidates[
        :DEFENSIVE_POSITION_COUNT
    ]


def rank_candidates(
    candidates: list[dict],
) -> list[dict]:
    return sorted(
        candidates,
        key=lambda row: (
            -number(
                row.get("conviction")
            ),
            -number(
                row.get("confidence")
            ),
            -number(
                row.get("ensemble_score")
            ),
            str(row.get("asset", "")),
        ),
    )


def apply_diversification_scores(
    candidates: list[dict],
) -> list[dict]:
    rows = [
        row.copy()
        for row in candidates
    ]

    sector_counts = Counter(
        str(
            row.get(
                "sector",
                "unknown",
            )
        )
        for row in rows
    )

    for row in rows:
        sector = str(
            row.get(
                "sector",
                "unknown",
            )
        )

        sector_penalty = (
            1.0
            / max(
                1.0,
                sector_counts[sector] ** 0.5,
            )
        )

        multiplier = max(
            0.60,
            sector_penalty,
        )

        row[
            "diversification_multiplier"
        ] = round(multiplier, 6)

        row["raw_allocation_score"] = (
            max(
                number(
                    row.get("conviction")
                ),
                0.000001,
            )
            * multiplier
        )

    return rows


def allocate_risky_budget(
    candidates: list[dict],
    *,
    risky_budget: float,
) -> list[dict]:
    rows = [
        row.copy()
        for row in candidates
    ]

    raw_total = sum(
        number(
            row.get(
                "raw_allocation_score"
            )
        )
        for row in rows
    )

    if raw_total <= 0:
        equal_weight = (
            risky_budget / len(rows)
            if rows
            else 0.0
        )

        for row in rows:
            row[
                "ensemble_target_weight"
            ] = equal_weight

        return rows

    for row in rows:
        row["ensemble_target_weight"] = (
            number(
                row.get(
                    "raw_allocation_score"
                )
            )
            / raw_total
            * risky_budget
        )

    return rows


def apply_caps(
    candidates: list[dict],
    *,
    risky_budget: float,
) -> list[dict]:
    rows = [
        row.copy()
        for row in candidates
    ]

    for _ in range(20):
        sector_totals: dict[str, float] = {}

        for row in rows:
            sector = str(
                row.get(
                    "sector",
                    "unknown",
                )
            )

            sector_totals[sector] = (
                sector_totals.get(
                    sector,
                    0.0,
                )
                + number(
                    row.get(
                        "ensemble_target_weight"
                    )
                )
            )

        changed = False

        for row in rows:
            original = number(
                row.get(
                    "ensemble_target_weight"
                )
            )

            capped = min(
                original,
                MAX_ASSET_WEIGHT,
            )

            sector = str(
                row.get(
                    "sector",
                    "unknown",
                )
            )

            sector_total = sector_totals.get(
                sector,
                0.0,
            )

            if (
                sector_total
                > MAX_SECTOR_WEIGHT
                and sector_total > 0
            ):
                capped *= (
                    MAX_SECTOR_WEIGHT
                    / sector_total
                )

            row[
                "ensemble_target_weight"
            ] = capped

            if abs(capped - original) > 1e-12:
                changed = True

        total = sum(
            number(
                row.get(
                    "ensemble_target_weight"
                )
            )
            for row in rows
        )

        remaining = max(
            0.0,
            risky_budget - total,
        )

        if remaining <= 1e-9:
            break

        eligible = [
            row
            for row in rows
            if number(
                row.get(
                    "ensemble_target_weight"
                )
            )
            < MAX_ASSET_WEIGHT - 1e-9
        ]

        if not eligible:
            break

        eligible_total = sum(
            max(
                number(
                    row.get(
                        "raw_allocation_score"
                    )
                ),
                0.000001,
            )
            for row in eligible
        )

        for row in eligible:
            share = (
                max(
                    number(
                        row.get(
                            "raw_allocation_score"
                        )
                    ),
                    0.000001,
                )
                / eligible_total
            )

            room = (
                MAX_ASSET_WEIGHT
                - number(
                    row.get(
                        "ensemble_target_weight"
                    )
                )
            )

            addition = min(
                remaining * share,
                room,
            )

            row[
                "ensemble_target_weight"
            ] += addition

        if not changed and remaining <= 1e-9:
            break

    return rows


def reconcile_total_weight(
    allocations: list[dict],
) -> list[dict]:
    """Correct floating-point drift through the cash row."""
    if not allocations:
        return allocations

    total = sum(
        number(
            row.get(
                "ensemble_target_weight"
            )
        )
        for row in allocations
    )

    difference = 1.0 - total

    cash_row = next(
        (
            row
            for row in allocations
            if row.get("asset") == "CASH"
        ),
        None,
    )

    if cash_row is not None:
        cash_row[
            "ensemble_target_weight"
        ] = round(
            max(
                0.0,
                number(
                    cash_row.get(
                        "ensemble_target_weight"
                    )
                )
                + difference,
            ),
            6,
        )

    return allocations


def number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: Any) -> float:
    return max(
        0.0,
        min(
            1.0,
            number(value),
        ),
    )


