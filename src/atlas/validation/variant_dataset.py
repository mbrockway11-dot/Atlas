"""The pilot same-person variant dataset.

Two provenance tiers, kept distinct because they carry different evidential
weight:

* **Derived** pairs are generated mechanically from real corpus names --
  diacritic normalisation, punctuation, middle-name removal. They are true
  by construction, so the only question is how the encoding responds.
* **Well-known** pairs are widely documented identities (Samuel Clemens /
  Mark Twain) recorded from general knowledge. They are *not* verified
  against a citable authority, and the pilot reports them as such rather
  than implying a level of sourcing that was not done.

A finding that rests only on the well-known tier should be treated as
provisional until those pairs are checked against real sources.
"""

from __future__ import annotations

import unicodedata
from typing import Sequence

import numpy as np

from atlas.validation.variants import (
    SourceConfidence,
    VariantClass,
    VariantPair,
)


# ---------------------------------------------------------------------------
# Curated pairs: token-preserving lexical variants (class B)
# ---------------------------------------------------------------------------
#
# Token count is held fixed while the letters change, which is what makes
# this the sharpest test of string-specific signal.

TOKEN_PRESERVING_PAIRS: tuple[tuple[str, str, str], ...] = (
    # (canonical, variant, subtype)
    ("Theodore Roosevelt", "Teddy Roosevelt", "nickname"),
    ("Abraham Lincoln", "Abe Lincoln", "nickname"),
    ("Benjamin Franklin", "Ben Franklin", "nickname"),
    ("William Shakespeare", "Will Shakespeare", "nickname"),
    ("Thomas Edison", "Tom Edison", "nickname"),
    ("Elizabeth Taylor", "Liz Taylor", "nickname"),
    ("Katharine Hepburn", "Kate Hepburn", "nickname"),
    ("Robert Kennedy", "Bobby Kennedy", "nickname"),
    ("James Carter", "Jimmy Carter", "nickname"),
    ("Margaret Thatcher", "Maggie Thatcher", "nickname"),
    ("Edward Kennedy", "Ted Kennedy", "nickname"),
    ("Frederick Douglass", "Fred Douglass", "nickname"),
    ("Alexander Hamilton", "Alex Hamilton", "nickname"),
    ("Daniel Boone", "Dan Boone", "nickname"),
    ("Samuel Johnson", "Sam Johnson", "nickname"),
    ("Lev Tolstoy", "Leo Tolstoy", "transliteration"),
    ("Pyotr Tchaikovsky", "Peter Tchaikovsky", "transliteration"),
    ("Aleksandr Solzhenitsyn", "Alexander Solzhenitsyn", "transliteration"),
    ("Muammar Gaddafi", "Moammar Qaddafi", "transliteration"),
    ("Nikolai Gogol", "Nicolai Gogol", "transliteration"),
    ("Fyodor Dostoevsky", "Feodor Dostoyevsky", "transliteration"),
    ("Mikhail Gorbachev", "Michail Gorbatchev", "transliteration"),
    ("Anton Chekhov", "Anton Tchekhov", "transliteration"),
    ("Sergei Rachmaninoff", "Sergey Rachmaninov", "transliteration"),
    ("Vladimir Nabokov", "Wladimir Nabokoff", "transliteration"),
    ("Genghis Khan", "Chinggis Khan", "transliteration"),
    ("Lao Tzu", "Lao Zi", "transliteration"),
    ("Mao Zedong", "Mao Tsetung", "transliteration"),
    ("Deng Xiaoping", "Teng Hsiaoping", "transliteration"),
    ("Omar Khayyam", "Umar Khayyaam", "transliteration"),
)


# ---------------------------------------------------------------------------
# Curated pairs: structure-changing aliases (class D)
# ---------------------------------------------------------------------------
#
# No directional hypothesis. These probe the scope of the encoding: a birth
# name and a stage name may share almost nothing orthographically.

ALIAS_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("Samuel Clemens", "Mark Twain", "pen_name"),
    ("Eric Blair", "George Orwell", "pen_name"),
    ("Charles Dodgson", "Lewis Carroll", "pen_name"),
    ("Mary Ann Evans", "George Eliot", "pen_name"),
    ("Theodor Geisel", "Doctor Seuss", "pen_name"),
    ("Norma Jeane Mortenson", "Marilyn Monroe", "stage_name"),
    ("Archibald Leach", "Cary Grant", "stage_name"),
    ("Frances Gumm", "Judy Garland", "stage_name"),
    ("Marion Morrison", "John Wayne", "stage_name"),
    ("Issur Danielovitch", "Kirk Douglas", "stage_name"),
    ("Farrokh Bulsara", "Freddie Mercury", "stage_name"),
    ("Reginald Dwight", "Elton John", "stage_name"),
    ("Stefani Germanotta", "Lady Gaga", "stage_name"),
    ("Anna Mae Bullock", "Tina Turner", "stage_name"),
    ("Paul Hewson", "Bono Vox", "stage_name"),
    ("Gordon Sumner", "Sting Sumner", "stage_name"),
    ("Ehrich Weiss", "Harry Houdini", "stage_name"),
    ("Malcolm Little", "Malcolm X", "adopted_name"),
    ("Cassius Clay", "Muhammad Ali", "adopted_name"),
    ("Karol Wojtyla", "John Paul", "religious_name"),
    ("Jorge Bergoglio", "Pope Francis", "religious_name"),
    ("Agnes Bojaxhiu", "Mother Teresa", "religious_name"),
)


# ---------------------------------------------------------------------------
# Derived generators (classes A and C)
# ---------------------------------------------------------------------------


def _strip_diacritics(value: str) -> str:
    """Return the name with combining marks removed."""
    decomposed = unicodedata.normalize("NFD", value)

    return unicodedata.normalize(
        "NFC",
        "".join(ch for ch in decomposed if not unicodedata.combining(ch)),
    )


def build_orthographic_pairs(
    corpus_names: Sequence[str],
    *,
    limit: int = 35,
    seed: int = 20260723,
) -> list[VariantPair]:
    """Derive orthographic-preserving variants from real corpus names.

    Only transformations that genuinely change the string are kept: a name
    with no diacritics yields no diacritic variant, and silently emitting an
    identical pair would inflate the class with guaranteed perfect scores.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(corpus_names))

    pairs: list[VariantPair] = []

    for position in order:
        if len(pairs) >= limit:
            break

        name = str(corpus_names[int(position)])

        if len(name.split()) < 2:
            continue

        # Hyphen-to-space is deliberately absent. It is a real orthographic
        # variant, but under whitespace tokenization it splits one token into
        # two, which makes it token-changing and so incompatible with this
        # class's token-preserving nulls. Including it would contaminate the
        # comparison with the known token-count effect.
        candidates = [
            (_strip_diacritics(name), "diacritic_normalisation"),
            (name.replace("'", "").replace("’", ""), "apostrophe"),
            (name.replace(".", ""), "punctuation"),
            (name.replace("  ", " ").strip(), "whitespace"),
        ]

        for variant, subtype in candidates:
            if variant == name or len(pairs) >= limit:
                continue

            pairs.append(
                VariantPair(
                    entity_id=f"orth_{len(pairs):03d}",
                    canonical_name=name,
                    variant_name=variant,
                    variant_class=VariantClass.ORTHOGRAPHIC,
                    variant_subtype=subtype,
                    source="derived_from_corpus",
                    source_confidence=SourceConfidence.DERIVED,
                    script="latin" if name.isascii() else "latin_extended",
                )
            )
            break

    return pairs


def build_token_reducing_pairs(
    corpus_names: Sequence[str],
    *,
    limit: int = 35,
    seed: int = 20260724,
) -> list[VariantPair]:
    """Derive token-reducing variants by dropping or initialising a middle name."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(corpus_names))

    pairs: list[VariantPair] = []

    for position in order:
        if len(pairs) >= limit:
            break

        name = str(corpus_names[int(position)])
        tokens = name.split()

        if len(tokens) < 3:
            continue

        # Only removal belongs here. Initialising a middle name ("John
        # Fitzgerald Kennedy" -> "John F. Kennedy") keeps the token count,
        # so it is a token-*preserving* lexical variant and is generated
        # separately; filing it here would put a token-preserving pair
        # against deletion-conditioned nulls.
        variant = " ".join([tokens[0], tokens[-1]])
        subtype = "middle_name_removed"

        if variant == name or len(variant.split()) >= len(tokens):
            continue

        pairs.append(
            VariantPair(
                entity_id=f"reduce_{len(pairs):03d}",
                canonical_name=name,
                variant_name=variant,
                variant_class=VariantClass.TOKEN_REDUCING,
                variant_subtype=subtype,
                source="derived_from_corpus",
                source_confidence=SourceConfidence.DERIVED,
                script="latin" if name.isascii() else "latin_extended",
            )
        )

    return pairs


def build_initialised_pairs(
    corpus_names: Sequence[str],
    *,
    limit: int = 30,
    seed: int = 20260725,
) -> list[VariantPair]:
    """Derive token-preserving variants by initialising middle names.

    "John Fitzgerald Kennedy" -> "John F. Kennedy" keeps the token count and
    changes only the letters, which is exactly the token-preserving case the
    curated nickname and transliteration pairs also test -- but derived, so
    true by construction.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(corpus_names))

    pairs: list[VariantPair] = []

    for position in order:
        if len(pairs) >= limit:
            break

        name = str(corpus_names[int(position)])
        tokens = name.split()

        if len(tokens) < 3:
            continue

        middle = [f"{token[0]}." for token in tokens[1:-1] if token]
        variant = " ".join([tokens[0], *middle, tokens[-1]])

        if variant == name or len(variant.split()) != len(tokens):
            continue

        pairs.append(
            VariantPair(
                entity_id=f"init_{len(pairs):03d}",
                canonical_name=name,
                variant_name=variant,
                variant_class=VariantClass.TOKEN_PRESERVING,
                variant_subtype="middle_name_initialised",
                source="derived_from_corpus",
                source_confidence=SourceConfidence.DERIVED,
                script="latin" if name.isascii() else "latin_extended",
            )
        )

    return pairs


def build_curated_pairs() -> list[VariantPair]:
    """Return the curated token-preserving and alias pairs."""
    pairs: list[VariantPair] = []

    for index, (canonical, variant, subtype) in enumerate(
        TOKEN_PRESERVING_PAIRS
    ):
        pairs.append(
            VariantPair(
                entity_id=f"lex_{index:03d}",
                canonical_name=canonical,
                variant_name=variant,
                variant_class=VariantClass.TOKEN_PRESERVING,
                variant_subtype=subtype,
                source="general_knowledge",
                source_confidence=SourceConfidence.WELL_KNOWN,
            )
        )

    for index, (canonical, variant, subtype) in enumerate(ALIAS_PAIRS):
        pairs.append(
            VariantPair(
                entity_id=f"alias_{index:03d}",
                canonical_name=canonical,
                variant_name=variant,
                variant_class=VariantClass.STRUCTURE_CHANGING,
                variant_subtype=subtype,
                source="general_knowledge",
                source_confidence=SourceConfidence.WELL_KNOWN,
            )
        )

    return pairs


def build_pilot_dataset(
    corpus_names: Sequence[str],
    *,
    orthographic_limit: int = 35,
    reducing_limit: int = 35,
) -> list[VariantPair]:
    """Assemble the full pilot dataset across all four variant classes."""
    return [
        *build_orthographic_pairs(corpus_names, limit=orthographic_limit),
        *build_curated_pairs(),
        *build_initialised_pairs(corpus_names, limit=30),
        *build_token_reducing_pairs(corpus_names, limit=reducing_limit),
    ]
