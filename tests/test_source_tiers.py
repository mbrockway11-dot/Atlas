"""Tests for the source-tier licensing matrix.

Turns "use good sources" into a constraint: a source may license only the
claim types its tier covers. These tests pin the boundary and confirm it
validates every licensing decision the project has already made.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.source_tiers import (
    ClaimType,
    SourceTier,
    SourceTierError,
    can_license,
    require_licensing,
    tier_of,
)


# ---------------------------------------------------------------------------
# The matrix validates prior decisions
# ---------------------------------------------------------------------------


def test_unicode_licensed_identity_not_meaning() -> None:
    """1E-G-SOURCE-A, retroactively checked.

    Unicode is a normative standard: it fixed Hebrew letter identity, and it
    was correctly unable to license a value or a meaning.
    """
    unicode = tier_of("unicode_standard")

    assert can_license(unicode, ClaimType.IDENTITY)
    assert not can_license(unicode, ClaimType.MEANING)
    assert not can_license(unicode, ClaimType.METHOD)


def test_swiss_ephemeris_licensed_computation_not_meaning() -> None:
    """The ayanamsa offset is normative computation, not a licensed choice."""
    swe = tier_of("swiss_ephemeris")

    assert can_license(swe, ClaimType.COMPUTATION)
    assert not can_license(swe, ClaimType.MEANING)
    assert not can_license(swe, ClaimType.RULE)


def test_catalogs_license_provenance_only() -> None:
    """Open Library and WorldCat established editions, nothing more."""
    for catalog in ("open_library", "worldcat", "hathitrust"):
        tier = tier_of(catalog)

        assert tier is SourceTier.CATALOG_ARCHIVE
        assert can_license(tier, ClaimType.PROVENANCE)
        assert not can_license(tier, ClaimType.MEANING)
        assert not can_license(tier, ClaimType.METHOD)


def test_only_primary_traditional_licenses_meaning() -> None:
    """A denotation needs a primary traditional source, nothing weaker."""
    for tier in SourceTier:
        expected = tier is SourceTier.PRIMARY_TRADITIONAL

        assert can_license(tier, ClaimType.MEANING) is expected
        assert can_license(tier, ClaimType.METHOD) is expected


# ---------------------------------------------------------------------------
# The avoid-list licenses nothing
# ---------------------------------------------------------------------------


def test_inadmissible_sources_license_nothing() -> None:
    """The avoid-list, structurally unable to license anything."""
    for source in (
        "wikipedia",
        "ai_generated_summary",
        "numerology_website",
        "angel_number_site",
        "unsourced_gematria_calculator",
        "astrology_blog",
        "social_media_post",
    ):
        tier = tier_of(source)

        assert tier is SourceTier.INADMISSIBLE

        for claim in ClaimType:
            assert not can_license(tier, claim)


def test_an_unknown_source_is_inadmissible_by_default() -> None:
    """Silent unless admitted, at the source level."""
    assert tier_of("some_random_blog_2026") is SourceTier.INADMISSIBLE


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------


def test_a_catalog_cannot_be_made_to_license_a_meaning() -> None:
    """The enforcement point raises rather than allowing the crossing."""
    with pytest.raises(SourceTierError, match="cannot license a meaning"):
        require_licensing(SourceTier.CATALOG_ARCHIVE, ClaimType.MEANING)


def test_a_normative_standard_cannot_license_a_method() -> None:
    with pytest.raises(SourceTierError, match="cannot license a method"):
        require_licensing(
            SourceTier.NORMATIVE_STANDARD, ClaimType.METHOD
        )


def test_a_permitted_claim_passes() -> None:
    """The matrix is not merely always-refusing."""
    require_licensing(SourceTier.NORMATIVE_STANDARD, ClaimType.IDENTITY)
    require_licensing(SourceTier.PRIMARY_TRADITIONAL, ClaimType.MEANING)
    require_licensing(SourceTier.CATALOG_ARCHIVE, ClaimType.PROVENANCE)


def test_transliteration_standards_are_normative_not_gematria_authority() -> (
    None
):
    """ISO 259 and friends license orthography, never gematria values.

    A transliteration convention fixes letter correspondence (identity); it
    cannot license what a letter is worth or what a value means.
    """
    for standard in (
        "iso_259",
        "ala_lc_hebrew_romanization",
        "sbl_hebrew_transliteration",
    ):
        tier = tier_of(standard)

        assert tier is SourceTier.NORMATIVE_STANDARD
        assert can_license(tier, ClaimType.IDENTITY)
        assert not can_license(tier, ClaimType.METHOD)
        assert not can_license(tier, ClaimType.MEANING)
