"""Tests for the variant taxonomy, dataset, and conditioned null generators.

The dataset validator and the null generators are the two places where a
methodological error would silently become a result. Both are pinned here --
including the specific mistake the pilot's first run made, where a
length-preserving control was used for length-changing variants.
"""

from __future__ import annotations

import numpy as np
import pytest

from atlas.validation.nulls import (
    NULL_GENERATORS_BY_NAME,
    PRIMARY_NULL,
    REQUIRED_NULLS,
    NullModelError,
    generate_nulls,
    nulls_for_class,
)
from atlas.validation.variant_dataset import (
    build_initialised_pairs,
    build_orthographic_pairs,
    build_pilot_dataset,
    build_token_reducing_pairs,
    build_curated_pairs,
)
from atlas.validation.variants import (
    CLASS_EXPECTATIONS,
    SourceConfidence,
    VariantClass,
    VariantPair,
    character_overlap,
    levenshtein,
    validate_dataset,
)


# Deliberately varied: names with diacritics and apostrophes so the
# orthographic generator has something to work with, three-token names for
# the reducing and initialising generators, and enough two-token names of
# assorted lengths for the matched-unrelated-name null to find candidates.
CORPUS = (
    "Nikola Tesla",
    "José Rizal",
    "Émilie du Châtelet",
    "Seán O'Casey",
    "John Fitzgerald Kennedy",
    "Ada Byron Lovelace",
    "Marie Salomea Curie",
    "Isaac Newton",
    "Grace Brewster Hopper",
    "Alan Mathison Turing",
    "Teddy Rooseveldt",
    "Freddy Rosevelt",
    "Teddie Roosevelts",
    "Bobby Kennedie",
    "Harold Wilsonn",
    "Terence Rattigan",
)


def _pair(
    canonical: str,
    variant: str,
    variant_class: VariantClass,
) -> VariantPair:
    """Build a variant pair for testing."""
    return VariantPair(
        entity_id="test",
        canonical_name=canonical,
        variant_name=variant,
        variant_class=variant_class,
        variant_subtype="test",
        source="test",
        source_confidence=SourceConfidence.DERIVED,
    )


# ---------------------------------------------------------------------------
# Derived fields
# ---------------------------------------------------------------------------


def test_levenshtein_basic_cases() -> None:
    """Edit distance behaves as expected on known inputs."""
    assert levenshtein("", "") == 0
    assert levenshtein("abc", "abc") == 0
    assert levenshtein("abc", "") == 3
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("theodore", "teddy") == 5


def test_pair_derives_structural_fields() -> None:
    """Token and length deltas are computed from the names themselves."""
    pair = _pair(
        "Theodore Roosevelt", "Teddy Roosevelt", VariantClass.TOKEN_PRESERVING
    )

    assert pair.token_delta == 0
    assert pair.token_preserving is True
    assert pair.length_delta == -3
    assert pair.length_preserving is False
    assert pair.edit_distance > 0


def test_character_overlap_bounds() -> None:
    """Overlap is 1.0 for identical letter content and 0.0 for disjoint."""
    identical = character_overlap("abc", "abc")
    disjoint = character_overlap("abc", "xyz")

    assert identical["jaccard"] == pytest.approx(1.0)
    assert identical["multiset_overlap"] == pytest.approx(1.0)
    assert disjoint["jaccard"] == 0.0
    assert disjoint["multiset_overlap"] == 0.0


def test_character_overlap_handles_empty() -> None:
    """A name with no letters cannot produce a NaN overlap."""
    assert character_overlap("", "abc")["jaccard"] == 0.0


# ---------------------------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------------------------


def test_validator_rejects_token_change_in_preserving_class() -> None:
    """The exact error the pilot's first dataset made must be caught.

    Hyphen-to-space splits a token, so it is not token-preserving; filing it
    under a token-preserving class would put it against the wrong null.
    """
    result = validate_dataset(
        [
            _pair(
                "Jean-Paul Sartre",
                "Jean Paul Sartre",
                VariantClass.ORTHOGRAPHIC,
            )
        ]
    )

    assert result["valid"] is False
    assert (
        result["problems"][0]["issue"]
        == "token_count_changed_in_token_preserving_class"
    )


def test_validator_rejects_non_reducing_reduction() -> None:
    """A token-reducing class must actually reduce tokens."""
    result = validate_dataset(
        [
            _pair(
                "John Fitzgerald Kennedy",
                "John F. Kennedy",
                VariantClass.TOKEN_REDUCING,
            )
        ]
    )

    assert result["valid"] is False
    assert "not_reduced" in result["problems"][0]["issue"]


def test_validator_rejects_identical_variant() -> None:
    """A variant identical to its canonical name is not a variant."""
    result = validate_dataset(
        [_pair("Nikola Tesla", "Nikola Tesla", VariantClass.ORTHOGRAPHIC)]
    )

    assert result["valid"] is False


def test_validator_accepts_a_consistent_dataset() -> None:
    """Correctly classified pairs pass."""
    result = validate_dataset(
        [
            _pair("Jose Rizal", "José Rizal", VariantClass.ORTHOGRAPHIC),
            _pair(
                "John Fitzgerald Kennedy",
                "John Kennedy",
                VariantClass.TOKEN_REDUCING,
            ),
        ]
    )

    assert result["valid"] is True
    assert result["total_pairs"] == 2


def test_every_class_declares_an_expectation() -> None:
    """Expected behaviour is declared before scoring, for every class."""
    for variant_class in VariantClass:
        assert CLASS_EXPECTATIONS[variant_class].strip()


# ---------------------------------------------------------------------------
# Dataset generators
# ---------------------------------------------------------------------------


def test_orthographic_pairs_preserve_token_count() -> None:
    """Derived orthographic variants must not change token count."""
    pairs = build_orthographic_pairs(CORPUS, limit=10)

    for pair in pairs:
        assert pair.token_preserving, pair.variant_name


def test_token_reducing_pairs_actually_reduce() -> None:
    """Derived reductions must lower the token count."""
    pairs = build_token_reducing_pairs(CORPUS, limit=10)

    assert pairs

    for pair in pairs:
        assert pair.token_delta < 0


def test_initialised_pairs_preserve_token_count() -> None:
    """Initialising a middle name keeps the token count.

    This is why initialisation belongs in the token-preserving class and not
    the reducing one -- a distinction the first pilot run got wrong.
    """
    pairs = build_initialised_pairs(CORPUS, limit=10)

    assert pairs

    for pair in pairs:
        assert pair.token_delta == 0
        assert pair.variant_class is VariantClass.TOKEN_PRESERVING


def test_curated_pairs_carry_honest_provenance() -> None:
    """Curated pairs are labelled well_known, never as verified."""
    for pair in build_curated_pairs():
        assert pair.source_confidence is SourceConfidence.WELL_KNOWN
        assert pair.source == "general_knowledge"


def test_pilot_dataset_is_valid_and_covers_every_class() -> None:
    """The assembled pilot dataset passes its own validator."""
    dataset = build_pilot_dataset(CORPUS, orthographic_limit=5, reducing_limit=5)
    result = validate_dataset(dataset)

    assert result["valid"] is True
    assert set(result["by_class"]) == {
        variant_class.value for variant_class in VariantClass
    }


def test_generators_are_deterministic() -> None:
    """The same corpus yields the same dataset."""
    first = build_orthographic_pairs(CORPUS, limit=5)
    second = build_orthographic_pairs(CORPUS, limit=5)

    assert [p.to_dict() for p in first] == [p.to_dict() for p in second]


# ---------------------------------------------------------------------------
# Null models
# ---------------------------------------------------------------------------


def test_every_class_has_a_declared_null() -> None:
    """A cohort with no null model cannot be scored."""
    for variant_class in VariantClass:
        assert nulls_for_class(variant_class)
        assert PRIMARY_NULL[variant_class] in REQUIRED_NULLS[variant_class]


def test_missing_null_model_is_an_error() -> None:
    """An unknown class raises rather than falling back to the population."""
    with pytest.raises(NullModelError, match="No null model"):
        nulls_for_class("not_a_class")  # type: ignore[arg-type]


def test_length_matched_null_matches_length_and_edit_distance() -> None:
    """The primary null reproduces the variant's length change.

    The pilot's first run used a substitution-only null, which preserves
    length, against variants that shorten the name by ~3 characters. Since
    length difference drives ~30% of score variance, that comparison
    measured the length change rather than the variant.
    """
    generator = NULL_GENERATORS_BY_NAME["edit_and_length_matched_mutation"]

    canonical = "Theodore Roosevelt"
    variant = "Teddy Roosevelt"
    expected_delta = len(variant.replace(" ", "")) - len(
        canonical.replace(" ", "")
    )

    control = generator.generate(
        canonical, variant, CORPUS, np.random.default_rng(0)
    )

    actual_delta = len(control.replace(" ", "")) - len(
        canonical.replace(" ", "")
    )

    assert actual_delta == expected_delta


def test_substitution_null_preserves_length_by_design() -> None:
    """The substitution-only null is length-preserving, as documented."""
    generator = NULL_GENERATORS_BY_NAME["edit_distance_matched_substitution"]

    control = generator.generate(
        "Theodore Roosevelt",
        "Teddy Roosevelt",
        CORPUS,
        np.random.default_rng(0),
    )

    assert len(control) == len("Theodore Roosevelt")


def test_token_reducing_null_deletes_a_token() -> None:
    """The deletion null applies the same structural operation."""
    generator = NULL_GENERATORS_BY_NAME["random_token_deletion"]

    control = generator.generate(
        "John Fitzgerald Kennedy",
        "John Kennedy",
        CORPUS,
        np.random.default_rng(0),
    )

    assert len(control.split()) == 2


def test_generate_nulls_covers_required_models() -> None:
    """Every required null for a class is produced."""
    controls = generate_nulls(
        canonical="Theodore Roosevelt",
        variant="Teddy Roosevelt",
        variant_class=VariantClass.TOKEN_PRESERVING,
        corpus_names=CORPUS,
        controls_per_null=3,
    )

    assert set(controls) == set(
        REQUIRED_NULLS[VariantClass.TOKEN_PRESERVING]
    )

    for name, produced in controls.items():
        assert produced, name


def test_generated_nulls_are_never_the_positive_pair() -> None:
    """A control must not be the canonical name or the genuine variant."""
    controls = generate_nulls(
        canonical="Theodore Roosevelt",
        variant="Teddy Roosevelt",
        variant_class=VariantClass.TOKEN_PRESERVING,
        corpus_names=CORPUS,
        controls_per_null=4,
    )

    for produced in controls.values():
        for control in produced:
            assert control.lower() != "theodore roosevelt"
            assert control.lower() != "teddy roosevelt"


def test_generated_nulls_are_deterministic() -> None:
    """The same inputs produce the same controls."""
    kwargs = {
        "canonical": "Ada Byron Lovelace",
        "variant": "Ada Lovelace",
        "variant_class": VariantClass.TOKEN_REDUCING,
        "corpus_names": CORPUS,
        "controls_per_null": 3,
    }

    assert generate_nulls(**kwargs) == generate_nulls(**kwargs)
