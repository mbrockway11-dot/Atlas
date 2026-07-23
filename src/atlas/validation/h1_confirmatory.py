"""Held-out H1 confirmatory dataset: orthographic-preserving variants.

The pilot found H1 the only class trending positive (d ~ +0.43, AUC 0.67)
under a correctly conditioned null, but at n = 35 could not resolve it. This
builds a larger, held-out cohort to test that one hypothesis properly.

Held out means exactly that: the profiles used here are disjoint from the
ones the pilot sampled. Extending the pilot and reanalysing everything
together would reuse the data that generated the hypothesis.

The class is subdivided because its members do not behave alike:

* **A1** -- case, spacing, punctuation. The encoder is exactly invariant to
  these, so similarity is 1.0 by construction. Reported as preprocessing
  verification and **excluded from the confirmatory endpoint**: counting a
  built-in invariance as evidence of variant recognition would be circular.
* **A2** -- accent removal (ö -> o). Length-preserving, and a real-world
  phenomenon: ASCII-folded forms of the same name are widely attested.
* **A3** -- orthographic convention expansion (ö -> oe, ß -> ss, æ -> ae).
  Length-*changing*, and documented convention rather than mere stripping.
  The contrast with A2 is deliberate: it separates "changed letters" from
  "changed length" within the same hypothesis.

Every pair here is derived mechanically from a real corpus name, so all are
``derived_by_construction``. No provisional rows are admitted.
"""

from __future__ import annotations

import unicodedata
from typing import Sequence

import numpy as np

from atlas.validation.variants import (
    OrthographicSubclass,
    SourceConfidence,
    VariantClass,
    VariantPair,
)


# Documented orthographic conventions: the standard expansions used when a
# character is unavailable. These are real alternate spellings, not damage.
CONVENTION_EXPANSIONS: tuple[tuple[str, str], ...] = (
    ("ä", "ae"), ("ö", "oe"), ("ü", "ue"),
    ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"),
    ("ß", "ss"),
    ("æ", "ae"), ("Æ", "Ae"),
    ("ø", "oe"), ("Ø", "Oe"),
    ("å", "aa"), ("Å", "Aa"),
    ("œ", "oe"), ("Œ", "Oe"),
)


def strip_accents(value: str) -> str:
    """Return the string with combining marks removed (A2)."""
    decomposed = unicodedata.normalize("NFD", value)

    return unicodedata.normalize(
        "NFC",
        "".join(ch for ch in decomposed if not unicodedata.combining(ch)),
    )


def expand_conventions(value: str) -> str:
    """Return the string with characters expanded by convention (A3)."""
    result = value

    for character, expansion in CONVENTION_EXPANSIONS:
        result = result.replace(character, expansion)

    return result


def build_h1_confirmatory_dataset(
    corpus_names: Sequence[str],
    *,
    excluded_names: Sequence[str] = (),
    target_per_subclass: int = 50,
    seed: int = 20260801,
) -> list[VariantPair]:
    """Build the held-out H1 dataset, disjoint from the supplied exclusions."""
    excluded = {name.strip().lower() for name in excluded_names}

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(corpus_names))

    a1: list[VariantPair] = []
    a2: list[VariantPair] = []
    a3: list[VariantPair] = []

    for position in order:
        name = str(corpus_names[int(position)])

        if name.strip().lower() in excluded or len(name.split()) < 2:
            continue

        # A2: accent removal. Only names that actually carry accents.
        if len(a2) < target_per_subclass:
            folded = strip_accents(name)

            if folded != name:
                a2.append(
                    VariantPair(
                        entity_id=f"h1a2_{len(a2):03d}",
                        canonical_name=name,
                        variant_name=folded,
                        variant_class=VariantClass.ORTHOGRAPHIC,
                        variant_subtype="accent_removal",
                        source="derived_from_corpus",
                        source_confidence=(
                            SourceConfidence.DERIVED_BY_CONSTRUCTION
                        ),
                        script="latin_extended",
                        subclass=OrthographicSubclass.A2_DIACRITIC,
                    )
                )
                continue

        # A3: convention expansion. Only names containing an expandable
        # character, and only where expansion genuinely differs from folding.
        if len(a3) < target_per_subclass:
            expanded = expand_conventions(name)

            if expanded != name and expanded != strip_accents(name):
                a3.append(
                    VariantPair(
                        entity_id=f"h1a3_{len(a3):03d}",
                        canonical_name=name,
                        variant_name=expanded,
                        variant_class=VariantClass.ORTHOGRAPHIC,
                        variant_subtype="convention_expansion",
                        source="derived_from_corpus",
                        source_confidence=(
                            SourceConfidence.DERIVED_BY_CONSTRUCTION
                        ),
                        script="latin_extended",
                        subclass=(
                            OrthographicSubclass.A3_ORTHOGRAPHIC_CONVENTION
                        ),
                    )
                )
                continue

        # A1: the preprocessing cohort. Any name will do.
        if len(a1) < target_per_subclass:
            a1.append(
                VariantPair(
                    entity_id=f"h1a1_{len(a1):03d}",
                    canonical_name=name,
                    variant_name=name.lower(),
                    variant_class=VariantClass.ORTHOGRAPHIC,
                    variant_subtype="case_folding",
                    source="derived_from_corpus",
                    source_confidence=(
                        SourceConfidence.DERIVED_BY_CONSTRUCTION
                    ),
                    subclass=OrthographicSubclass.A1_ENCODER_INVARIANCE,
                )
            )

        if (
            len(a1) >= target_per_subclass
            and len(a2) >= target_per_subclass
            and len(a3) >= target_per_subclass
        ):
            break

    return [*a1, *a2, *a3]
