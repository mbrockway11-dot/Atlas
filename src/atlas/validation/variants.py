"""Same-person name variant taxonomy and pilot dataset schema.

A single "does Atlas recognize name variants" experiment would average over
phenomena that behave completely differently. The perturbation study showed
why: deleting one token moves a name further than replacing it with an
unrelated string of the same length. A cohort mixing nicknames with dropped
middle names would therefore report a null that is really an artefact of
token-count change.

So variants are split into four classes, each with its own expected behaviour
and -- critically -- its own null model, declared before any scoring happens.

Class D is deliberately open. Stage and pen names may share nothing
orthographically with a birth name, and a negative result there defines the
model's scope rather than indicting it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


VARIANT_DATASET_SCHEMA = "atlas.validation.variant-dataset.v1"


class VariantClass(str, Enum):
    """The four transformation classes, each with a distinct null."""

    ORTHOGRAPHIC = "orthographic_preserving"
    TOKEN_PRESERVING = "token_preserving_lexical"
    TOKEN_REDUCING = "token_reducing"
    STRUCTURE_CHANGING = "structure_changing_alias"


class SourceConfidence(str, Enum):
    """How well established a variant pair is.

    ``derived`` pairs are generated mechanically from a real corpus name and
    are true by construction. ``well_known`` pairs are widely documented
    identities recorded from general knowledge rather than checked against a
    citable authority -- stated plainly so the pilot's evidential weight is
    not overstated.
    """

    DERIVED = "derived"
    WELL_KNOWN = "well_known"
    UNCERTAIN = "uncertain"


# The declared expectation for each class, fixed before results are seen.
CLASS_EXPECTATIONS: dict[VariantClass, str] = {
    VariantClass.ORTHOGRAPHIC: (
        "High similarity. Token count preserved, length approximately "
        "preserved. The easiest positive control: if this class does not "
        "separate from matched controls, nothing will."
    ),
    VariantClass.TOKEN_PRESERVING: (
        "Moderate-to-high similarity, token count preserved, letter overlap "
        "variable. The most important test of real string-specific signal, "
        "because morphology is held fixed while the letters change."
    ),
    VariantClass.TOKEN_REDUCING: (
        "Token count reduced. Must be compared against deletion-conditioned "
        "controls, never the global population, or the known token-count "
        "effect will be mistaken for a failure to recognise the variant."
    ),
    VariantClass.STRUCTURE_CHANGING: (
        "No directional hypothesis. Exploratory: these test the scope of the "
        "encoding, not its invariance."
    ),
}


@dataclass(frozen=True, slots=True)
class VariantPair:
    """One canonical-name / variant-name pair."""

    entity_id: str
    canonical_name: str
    variant_name: str
    variant_class: VariantClass
    variant_subtype: str
    source: str
    source_confidence: SourceConfidence
    language: str = "en"
    script: str = "latin"

    @property
    def canonical_tokens(self) -> int:
        """Return the canonical name's token count."""
        return len(self.canonical_name.split())

    @property
    def variant_tokens(self) -> int:
        """Return the variant name's token count."""
        return len(self.variant_name.split())

    @property
    def token_delta(self) -> int:
        """Return variant minus canonical token count."""
        return self.variant_tokens - self.canonical_tokens

    @property
    def canonical_length(self) -> int:
        """Return canonical character count, excluding spaces."""
        return len(self.canonical_name.replace(" ", ""))

    @property
    def variant_length(self) -> int:
        """Return variant character count, excluding spaces."""
        return len(self.variant_name.replace(" ", ""))

    @property
    def length_delta(self) -> int:
        """Return variant minus canonical character count."""
        return self.variant_length - self.canonical_length

    @property
    def edit_distance(self) -> int:
        """Return Levenshtein distance between the two names."""
        return levenshtein(
            self.canonical_name.lower(), self.variant_name.lower()
        )

    @property
    def length_preserving(self) -> bool:
        """Return whether character count is unchanged."""
        return self.length_delta == 0

    @property
    def token_preserving(self) -> bool:
        """Return whether token count is unchanged."""
        return self.token_delta == 0

    def to_dict(self) -> dict[str, Any]:
        """Return the full JSON-safe row, including derived fields."""
        return {
            "entity_id": self.entity_id,
            "canonical_name": self.canonical_name,
            "variant_name": self.variant_name,
            "variant_class": self.variant_class.value,
            "variant_subtype": self.variant_subtype,
            "source": self.source,
            "source_confidence": self.source_confidence.value,
            "language": self.language,
            "script": self.script,
            "canonical_token_count": self.canonical_tokens,
            "variant_token_count": self.variant_tokens,
            "canonical_length": self.canonical_length,
            "variant_length": self.variant_length,
            "token_delta": self.token_delta,
            "length_delta": self.length_delta,
            "edit_distance": self.edit_distance,
            "length_preserving": self.length_preserving,
            "token_preserving": self.token_preserving,
            "expected_behavior": CLASS_EXPECTATIONS[self.variant_class],
        }


def levenshtein(left: str, right: str) -> int:
    """Return the Levenshtein edit distance between two strings.

    Written out rather than pulled in as a dependency: it is short, and the
    null generators need an exact edit distance to match controls against.
    """
    if left == right:
        return 0

    if not left:
        return len(right)

    if not right:
        return len(left)

    previous = list(range(len(right) + 1))

    for i, left_char in enumerate(left, start=1):
        current = [i]

        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (left_char != right_char),
                )
            )

        previous = current

    return previous[-1]


def character_overlap(left: str, right: str) -> dict[str, float]:
    """Return set and multiset letter overlap between two names.

    Used by the neighbour audit to ask whether an extreme pair simply shares
    its letters.
    """
    a = [ch.lower() for ch in left if ch.isalpha()]
    b = [ch.lower() for ch in right if ch.isalpha()]

    if not a or not b:
        return {"jaccard": 0.0, "multiset_overlap": 0.0}

    set_a, set_b = set(a), set(b)
    union = set_a | set_b

    from collections import Counter

    counts_a, counts_b = Counter(a), Counter(b)
    shared = sum((counts_a & counts_b).values())

    return {
        "jaccard": len(set_a & set_b) / len(union) if union else 0.0,
        "multiset_overlap": 2.0 * shared / (len(a) + len(b)),
    }


def validate_dataset(pairs: Iterable[VariantPair]) -> dict[str, Any]:
    """Summarize a variant dataset and flag rows inconsistent with their class.

    A pair filed under a token-preserving class that actually changes token
    count would silently contaminate that class's null comparison, so the
    mismatch is surfaced rather than tolerated.
    """
    rows = list(pairs)
    by_class: dict[str, int] = {}
    problems: list[dict[str, Any]] = []

    for pair in rows:
        by_class[pair.variant_class.value] = (
            by_class.get(pair.variant_class.value, 0) + 1
        )

        if (
            pair.variant_class
            in {VariantClass.ORTHOGRAPHIC, VariantClass.TOKEN_PRESERVING}
            and not pair.token_preserving
        ):
            problems.append(
                {
                    "entity_id": pair.entity_id,
                    "issue": "token_count_changed_in_token_preserving_class",
                    "token_delta": pair.token_delta,
                }
            )

        if (
            pair.variant_class is VariantClass.TOKEN_REDUCING
            and pair.token_delta >= 0
        ):
            problems.append(
                {
                    "entity_id": pair.entity_id,
                    "issue": "token_count_not_reduced_in_reducing_class",
                    "token_delta": pair.token_delta,
                }
            )

        if pair.canonical_name.strip() == pair.variant_name.strip():
            problems.append(
                {
                    "entity_id": pair.entity_id,
                    "issue": "variant_identical_to_canonical",
                }
            )

    return {
        "schema_version": VARIANT_DATASET_SCHEMA,
        "total_pairs": len(rows),
        "by_class": dict(sorted(by_class.items())),
        "by_confidence": {
            level.value: sum(
                1 for pair in rows if pair.source_confidence is level
            )
            for level in SourceConfidence
        },
        "problems": problems,
        "valid": not problems,
    }
