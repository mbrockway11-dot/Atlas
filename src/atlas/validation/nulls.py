"""Transformation-conditioned null generators.

There is no single null distribution for "name variants". The perturbation
study established that different structural changes land in different places
relative to the population: a length-preserving edit and a token deletion are
not comparable, and comparing either against the global corpus mean measures
the structural change rather than the variant.

Each variant class therefore declares which nulls it requires, and a cohort
with no compatible null generator is a configuration error rather than a
result. Every generator produces a control that undergoes *the same
structural transformation* as the positive pair, so the only remaining
difference is whether the variant is genuine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from atlas.validation.perturbations import (
    delete_characters,
    delete_token,
    insert_characters,
    length_matched_random,
    shuffle_characters,
    substitute,
)
from atlas.validation.variants import VariantClass, levenshtein


@dataclass(frozen=True, slots=True)
class NullGenerator:
    """One null model: a control name derived from a canonical name."""

    name: str
    description: str
    # (canonical_name, variant_name, corpus_names, rng) -> control name
    generate: Callable[..., str | None]
    preserves_token_count: bool


def _edit_distance_matched_substitution(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Return a mutation of the canonical name at the variant's edit distance.

    The sharpest control for a token-preserving variant: identical
    morphology, identical amount of change, but the change is arbitrary
    rather than the real alternate form.
    """
    distance = max(1, levenshtein(canonical.lower(), variant.lower()))

    return substitute(canonical, count=distance, rng=rng)


def _edit_and_length_matched_mutation(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Mutate the canonical name to the variant's edit distance AND length.

    The substitution-only null is not a fair control for most real variants.
    "Theodore Roosevelt" -> "Teddy Roosevelt" is five edits *and* three
    characters shorter, while pure substitution preserves length exactly.
    Since length difference drives roughly 30% of score variance, comparing a
    length-changing positive against a length-preserving control measures the
    length change, not the variant.

    This applies the same net length change first, then makes up the
    remaining edits with substitutions.
    """
    length_delta = len(variant.replace(" ", "")) - len(
        canonical.replace(" ", "")
    )
    distance = max(1, levenshtein(canonical.lower(), variant.lower()))

    mutated = canonical

    if length_delta < 0:
        mutated = delete_characters(mutated, count=-length_delta, rng=rng)
    elif length_delta > 0:
        mutated = insert_characters(mutated, count=length_delta, rng=rng)

    remaining = distance - abs(length_delta)

    if remaining > 0:
        mutated = substitute(mutated, count=remaining, rng=rng)

    return mutated


def _letter_frequency_mutation(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Return a shuffle of the canonical name's own letters."""
    return shuffle_characters(canonical, rng=rng)


def _length_matched_random(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Return a random string matching the canonical name's shape."""
    return length_matched_random(canonical, rng=rng)


def _matched_unrelated_name(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Return a real corpus name matched to the *variant's* shape.

    Matched to the variant rather than the canonical name, because that is
    what the variant is being compared against: the question is whether the
    genuine variant beats an unrelated name of the same resulting shape.
    """
    target_tokens = len(variant.split())
    target_length = len(variant.replace(" ", ""))

    candidates = [
        name
        for name in corpus_names
        if len(name.split()) == target_tokens
        and abs(len(name.replace(" ", "")) - target_length) <= 1
        and name.lower() != canonical.lower()
        and name.lower() != variant.lower()
    ]

    if not candidates:
        return None

    return str(candidates[int(rng.integers(0, len(candidates)))])


def _random_token_deletion(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Delete a random token from the canonical name.

    The correct control for a token-reducing variant: the same structural
    operation, applied arbitrarily. If a genuine middle-name removal scores
    no better than deleting a random token, the encoding is responding to
    the deletion and not to which token was deleted.
    """
    if len(canonical.split()) < 2:
        return None

    return delete_token(canonical, rng=rng)


def _random_unrelated_token_deletion(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Delete a random token from an unrelated name of matching shape."""
    tokens = len(canonical.split())

    candidates = [
        name
        for name in corpus_names
        if len(name.split()) == tokens and name.lower() != canonical.lower()
    ]

    if not candidates:
        return None

    picked = str(candidates[int(rng.integers(0, len(candidates)))])

    return delete_token(picked, rng=rng)


def _structurally_matched_name(
    canonical: str,
    variant: str,
    corpus_names: Sequence[str],
    rng: np.random.Generator,
) -> str | None:
    """Return an unrelated name matched only on gross structure.

    For aliases, where shared spelling is not expected to survive, structural
    matching is the only defensible control.
    """
    return _matched_unrelated_name(canonical, variant, corpus_names, rng)


NULL_GENERATORS: tuple[NullGenerator, ...] = (
    NullGenerator(
        "edit_and_length_matched_mutation",
        "Canonical name mutated to the variant's edit distance AND net "
        "length change -- the only control that holds both amount of change "
        "and morphology fixed.",
        _edit_and_length_matched_mutation,
        preserves_token_count=True,
    ),
    NullGenerator(
        "edit_distance_matched_substitution",
        "Canonical name mutated by the same number of edits as the genuine "
        "variant, holding morphology and amount of change fixed.",
        _edit_distance_matched_substitution,
        preserves_token_count=True,
    ),
    NullGenerator(
        "letter_frequency_preserving_mutation",
        "Canonical name's own letters, reordered: same letter multiset, no "
        "real arrangement.",
        _letter_frequency_mutation,
        preserves_token_count=True,
    ),
    NullGenerator(
        "length_matched_random",
        "Random string matching the canonical name's length and token shape.",
        _length_matched_random,
        preserves_token_count=True,
    ),
    NullGenerator(
        "matched_unrelated_name",
        "A real, unrelated corpus name matched to the variant's token count "
        "and length.",
        _matched_unrelated_name,
        preserves_token_count=True,
    ),
    NullGenerator(
        "random_token_deletion",
        "A random token deleted from the canonical name -- the same "
        "structural operation as the genuine reduction.",
        _random_token_deletion,
        preserves_token_count=False,
    ),
    NullGenerator(
        "unrelated_token_deletion",
        "A random token deleted from an unrelated name of matching shape.",
        _random_unrelated_token_deletion,
        preserves_token_count=False,
    ),
    NullGenerator(
        "structurally_matched_name",
        "Unrelated name matched on resulting shape only, for aliases where "
        "shared spelling is not expected.",
        _structurally_matched_name,
        preserves_token_count=True,
    ),
)

NULL_GENERATORS_BY_NAME = {
    generator.name: generator for generator in NULL_GENERATORS
}


# Which nulls each variant class requires. A cohort whose class has no
# compatible generator is rejected rather than scored against a wrong null.
REQUIRED_NULLS: dict[VariantClass, tuple[str, ...]] = {
    VariantClass.ORTHOGRAPHIC: (
        "edit_and_length_matched_mutation",
        "edit_distance_matched_substitution",
        "matched_unrelated_name",
        "length_matched_random",
    ),
    VariantClass.TOKEN_PRESERVING: (
        "edit_and_length_matched_mutation",
        "edit_distance_matched_substitution",
        "letter_frequency_preserving_mutation",
        "matched_unrelated_name",
        "length_matched_random",
    ),
    VariantClass.TOKEN_REDUCING: (
        "random_token_deletion",
        "unrelated_token_deletion",
        "matched_unrelated_name",
    ),
    VariantClass.STRUCTURE_CHANGING: ("structurally_matched_name",),
}

# The null that is the principal comparison for each class -- the hardest
# control it must beat for a positive result to mean anything.
PRIMARY_NULL: dict[VariantClass, str] = {
    VariantClass.ORTHOGRAPHIC: "edit_and_length_matched_mutation",
    VariantClass.TOKEN_PRESERVING: "edit_and_length_matched_mutation",
    VariantClass.TOKEN_REDUCING: "random_token_deletion",
    VariantClass.STRUCTURE_CHANGING: "structurally_matched_name",
}


class NullModelError(ValueError):
    """A cohort has no compatible null generator."""


def nulls_for_class(variant_class: VariantClass) -> tuple[NullGenerator, ...]:
    """Return the required null generators for a variant class."""
    names = REQUIRED_NULLS.get(variant_class)

    if not names:
        # Report the argument as given. Reaching for `.value` here would
        # raise AttributeError on a plain string and mask the real problem,
        # which is that the class has no declared null.
        label = getattr(variant_class, "value", variant_class)

        raise NullModelError(
            f"No null model declared for variant class {label!r}. A cohort "
            "cannot be scored without one: the global population is not a "
            "valid control for a structural transformation."
        )

    return tuple(NULL_GENERATORS_BY_NAME[name] for name in names)


def generate_nulls(
    *,
    canonical: str,
    variant: str,
    variant_class: VariantClass,
    corpus_names: Sequence[str],
    controls_per_null: int = 5,
    seed: int = 0,
) -> dict[str, list[str]]:
    """Generate control names for one positive pair, grouped by null model."""
    controls: dict[str, list[str]] = {}

    for generator in nulls_for_class(variant_class):
        produced: list[str] = []

        for attempt in range(controls_per_null * 3):
            if len(produced) >= controls_per_null:
                break

            rng = np.random.default_rng(
                abs(hash((canonical, variant, generator.name, attempt)))
                % (2**32)
            )

            candidate = generator.generate(
                canonical, variant, corpus_names, rng
            )

            if (
                candidate
                and candidate.lower() != canonical.lower()
                and candidate.lower() != variant.lower()
                and candidate not in produced
            ):
                produced.append(candidate)

        controls[generator.name] = produced

    return controls
