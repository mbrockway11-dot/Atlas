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


# ---------------------------------------------------------------------------
# The named acquisition queue (Sefaria, Jewish Encyclopedia, GRETIL, ...)
# ---------------------------------------------------------------------------


def test_jewish_encyclopedia_cannot_license_the_value_table() -> None:
    """A scholarly reference describes mispar hechrachi; it cannot license it.

    The user's own caveat, enforced: the Jewish Encyclopedia is excellent for
    context and bibliography, but the value method needs a primary source.
    """
    je = tier_of("jewish_encyclopedia_1906")

    assert je is SourceTier.SCHOLARLY_REFERENCE
    assert not can_license(je, ClaimType.METHOD)
    assert not can_license(je, ClaimType.MEANING)
    assert can_license(je, ClaimType.CONTEXT)


def test_a_text_platform_is_an_access_route_not_a_meaning_licence() -> None:
    """Sefaria hosts primary texts but does not inherit their tier.

    'The value is on Sefaria' cannot license a value. The hosted work does,
    and only through a verified edition and copy.
    """
    from atlas.validation.denotation.source_tiers import ACCESS_ROUTES

    for platform in ("sefaria", "gretil", "sanskrit_documents"):
        tier = tier_of(platform)

        assert platform in ACCESS_ROUTES
        assert tier is SourceTier.CATALOG_ARCHIVE
        assert can_license(tier, ClaimType.PROVENANCE)
        assert not can_license(tier, ClaimType.MEANING)
        assert not can_license(tier, ClaimType.METHOD)


def test_the_hosted_primary_work_may_license_a_meaning() -> None:
    """Pardes Rimmonim is primary_traditional -- the platform is not.

    Classification is not admission: the tier permits the claim, but a
    specific verified passage is still required to make it.
    """
    work = tier_of("pardes_rimmonim")

    assert work is SourceTier.PRIMARY_TRADITIONAL
    assert can_license(work, ClaimType.METHOD)
    assert can_license(work, ClaimType.MEANING)
    assert can_license(work, ClaimType.EQUIVALENCE)


def test_classical_jyotisha_texts_are_primary_traditional() -> None:
    """BPHS and the rest may license rules and meanings; a catalog cannot."""
    for work in (
        "brihat_parasara_hora_shastra",
        "brihat_jataka",
        "phaladipika",
        "jataka_parijata",
    ):
        assert tier_of(work) is SourceTier.PRIMARY_TRADITIONAL
        assert can_license(tier_of(work), ClaimType.RULE)
