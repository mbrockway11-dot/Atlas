"""Yoga evaluation engine for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.temporal.aspects import AspectChart
from atlas.temporal.dignity import DignityChart
from atlas.temporal.houses import HouseChart
from atlas.temporal.models import NatalChart
from atlas.temporal.yoga_rules import (
    YogaCondition,
    YogaRule,
    all_yogas,
)


YOGA_ENGINE_VERSION = "1.0"


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------


@dataclass(frozen=True)
class YogaMatch:
    """One successfully matched yoga."""

    name: str
    category: str
    source: str
    score: float
    conditions_passed: int
    conditions_total: int


@dataclass(frozen=True)
class YogaEvaluation:
    """Complete yoga evaluation."""

    version: str
    name: str
    matches: list[YogaMatch]
    summary: dict[str, Any]


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------


def evaluate_all_yogas(
    *,
    natal: NatalChart,
    houses: HouseChart,
    dignity: DignityChart,
    aspects: AspectChart,
) -> YogaEvaluation:
    """Evaluate every canonical yoga."""

    matches: list[YogaMatch] = []

    for yoga in all_yogas():

        score = evaluate_yoga(
            yoga,
            natal=natal,
            houses=houses,
            dignity=dignity,
            aspects=aspects,
        )

        if score is None:
            continue

        matches.append(score)

    return YogaEvaluation(
        version=YOGA_ENGINE_VERSION,
        name=natal.name,
        matches=matches,
        summary={
            "matched": len(matches),
            "evaluated": len(all_yogas()),
        },
    )


# ------------------------------------------------------------
# Yoga Evaluation
# ------------------------------------------------------------


def evaluate_yoga(
    yoga: YogaRule,
    *,
    natal: NatalChart,
    houses: HouseChart,
    dignity: DignityChart,
    aspects: AspectChart,
) -> YogaMatch | None:
    """Evaluate one yoga."""

    passed = 0

    for condition in yoga.conditions:

        if evaluate_condition(
            condition,
            natal=natal,
            houses=houses,
            dignity=dignity,
            aspects=aspects,
        ):
            passed += 1

    if passed != len(yoga.conditions):
        return None

    score = passed / len(yoga.conditions)

    if score < yoga.minimum_score:
        return None

    return YogaMatch(
        name=yoga.name,
        category=yoga.category,
        source=yoga.source,
        score=score,
        conditions_passed=passed,
        conditions_total=len(yoga.conditions),
    )


# ------------------------------------------------------------
# Condition Dispatcher
# ------------------------------------------------------------


def evaluate_condition(
    condition: YogaCondition,
    *,
    natal: NatalChart,
    houses: HouseChart,
    dignity: DignityChart,
    aspects: AspectChart,
) -> bool:
    """Dispatch one condition."""

    dispatch = {
        "conjunction": evaluate_conjunction,
        "minimum_strength": evaluate_minimum_strength,
        "debilitated": evaluate_debilitated,
        "debilitation_cancelled": evaluate_placeholder,
        "house_lord_relationship": evaluate_placeholder,
        "dusthana_exchange": evaluate_placeholder,
        "mahapurusha": evaluate_placeholder,
    }

    evaluator = dispatch.get(condition.type)

    if evaluator is None:
        return False

    return evaluator(
        condition.parameters,
        natal=natal,
        houses=houses,
        dignity=dignity,
        aspects=aspects,
    )


# ------------------------------------------------------------
# Evaluators
# ------------------------------------------------------------


def evaluate_conjunction(
    params: dict[str, Any],
    *,
    natal: NatalChart,
    **_,
) -> bool:
    """True if two planets occupy the same sign."""

    a = natal.planets[params["planet_a"]]
    b = natal.planets[params["planet_b"]]

    return a.sign_index == b.sign_index


def evaluate_minimum_strength(
    params: dict[str, Any],
    *,
    dignity: DignityChart,
    **_,
) -> bool:
    """Planet exceeds minimum dignity score."""

    planet = params["planet"]

    return (
        dignity.dignities[planet].strength_score
        >= params["score"]
    )


def evaluate_debilitated(
    params: dict[str, Any],
    *,
    dignity: DignityChart,
    **_,
) -> bool:
    """Planet is debilitated."""

    target = params["planet"]

    if target == "*":

        return any(
            value.debilitated
            for value in dignity.dignities.values()
        )

    return dignity.dignities[target].debilitated


def evaluate_placeholder(
    *_,
    **__,
) -> bool:
    """Placeholder until implemented."""

    return False


# ------------------------------------------------------------
# Serialization
# ------------------------------------------------------------


def yoga_evaluation_to_dict(
    evaluation: YogaEvaluation,
) -> dict[str, Any]:
    """Convert evaluation into JSON."""

    return {
        "version": evaluation.version,
        "name": evaluation.name,
        "matches": [
            asdict(match)
            for match in evaluation.matches
        ],
        "summary": evaluation.summary,
    }