"""Corpus duplicate and alias detection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


STOP_TOKENS = {
    "sir",
    "saint",
    "st",
    "dr",
    "doctor",
    "prof",
    "professor",
    "mr",
    "mrs",
    "ms",
}


@dataclass(frozen=True)
class DuplicateDetectionResult:
    """Duplicate detection result."""

    exact_duplicates: list[dict[str, Any]]
    possible_aliases: list[dict[str, Any]]


def canonicalize_name(name: str) -> str:
    """Normalize a name for duplicate comparison."""
    normalized = name.lower().strip()
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("_", " ")
    normalized = re.sub(r"[^\w\s]", "", normalized)
    tokens = [
        token
        for token in normalized.split()
        if token and token not in STOP_TOKENS
    ]
    return " ".join(tokens)


def name_tokens(name: str) -> set[str]:
    """Return canonical name tokens."""
    return set(canonicalize_name(name).split())


def detect_duplicate_names(names: list[str]) -> list[dict[str, Any]]:
    """Detect exact duplicates after canonicalization."""
    grouped: dict[str, list[str]] = {}

    for name in names:
        canonical = canonicalize_name(name)
        grouped.setdefault(canonical, [])
        grouped[canonical].append(name)

    return [
        {
            "canonical": canonical,
            "names": values,
            "count": len(values),
        }
        for canonical, values in grouped.items()
        if len(values) > 1
    ]


def detect_possible_aliases(
    names: list[str],
    similarity_threshold: float = 0.72,
) -> list[dict[str, Any]]:
    """Detect likely aliases using token containment and string similarity."""
    aliases = []

    canonical_names = [
        {
            "name": name,
            "canonical": canonicalize_name(name),
            "tokens": name_tokens(name),
        }
        for name in names
    ]

    for index_a, item_a in enumerate(canonical_names):
        for index_b, item_b in enumerate(canonical_names):
            if index_b <= index_a:
                continue

            if item_a["canonical"] == item_b["canonical"]:
                continue

            score = alias_similarity_score(item_a, item_b)

            if score >= similarity_threshold:
                aliases.append(
                    {
                        "name_a": item_a["name"],
                        "name_b": item_b["name"],
                        "canonical_a": item_a["canonical"],
                        "canonical_b": item_b["canonical"],
                        "similarity": score,
                        "reason": alias_reason(item_a, item_b),
                    }
                )

    return sorted(
        aliases,
        key=lambda item: item["similarity"],
        reverse=True,
    )


def detect_duplicates_and_aliases(
    names: list[str],
    similarity_threshold: float = 0.72,
) -> DuplicateDetectionResult:
    """Detect exact duplicates and possible aliases."""
    return DuplicateDetectionResult(
        exact_duplicates=detect_duplicate_names(names),
        possible_aliases=detect_possible_aliases(
            names,
            similarity_threshold=similarity_threshold,
        ),
    )


def alias_similarity_score(
    item_a: dict[str, Any],
    item_b: dict[str, Any],
) -> float:
    """Score likely alias relationship."""
    tokens_a = item_a["tokens"]
    tokens_b = item_b["tokens"]

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    smaller = min(len(tokens_a), len(tokens_b))
    larger = max(len(tokens_a), len(tokens_b))

    containment = len(intersection) / smaller
    overlap = len(intersection) / larger

    sequence = SequenceMatcher(
        None,
        item_a["canonical"],
        item_b["canonical"],
    ).ratio()

    if containment == 1.0:
        return max(0.85, (containment + overlap + sequence) / 3.0)

    return (containment + overlap + sequence) / 3.0


def alias_reason(
    item_a: dict[str, Any],
    item_b: dict[str, Any],
) -> str:
    """Explain why two names may be aliases."""
    tokens_a = item_a["tokens"]
    tokens_b = item_b["tokens"]

    if tokens_a <= tokens_b or tokens_b <= tokens_a:
        return "One name token set is contained in the other."

    if tokens_a & tokens_b:
        return "Names share one or more canonical tokens."

    return "Names have high string similarity."


def duplicate_detection_result_to_dict(
    result: DuplicateDetectionResult,
) -> dict[str, Any]:
    """Convert duplicate detection result to dictionary."""
    return {
        "exact_duplicates": result.exact_duplicates,
        "possible_aliases": result.possible_aliases,
        "exact_duplicate_count": len(result.exact_duplicates),
        "possible_alias_count": len(result.possible_aliases),
    }