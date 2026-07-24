"""Tests for the canonical acquisition corpus and catalog roles.

The corpus is a plan, not evidence: every target is NOT_ACQUIRED. These tests
pin that the plan is coherent (each target's tier can license its claim), that
nothing is admitted, and that the catalog/repository role distinction holds --
including that repository access is not copy verification.
"""

from __future__ import annotations

from atlas.validation.denotation.acquisition_targets import (
    CANONICAL_ACQUISITION_CORPUS,
    AcquisitionStatus,
    acquisition_report,
)
from atlas.validation.denotation.source_tiers import (
    CatalogRole,
    ClaimType,
    SourceTier,
    can_license,
    catalog_role,
    tier_of,
)


# ---------------------------------------------------------------------------
# The plan is coherent, and unacquired
# ---------------------------------------------------------------------------


def test_every_target_is_not_acquired() -> None:
    """A plan, not evidence. Nothing here has been acquired or admitted."""
    for target in CANONICAL_ACQUISITION_CORPUS:
        assert target.status is AcquisitionStatus.NOT_ACQUIRED

    assert acquisition_report()["admitted"] == []


def test_every_target_tier_can_license_its_claim() -> None:
    """The plan cannot name a source that could not license its claim.

    Source-neutral coherence: caught now, not after a copy is in hand.
    """
    for target in CANONICAL_ACQUISITION_CORPUS:
        assert target.plan_is_coherent
        assert can_license(target.required_tier, target.licenses_claim)

    assert acquisition_report()["all_coherent"] is True


def test_named_works_are_classified_to_license_their_claim() -> None:
    """A named target's actual work tier must match what its gate needs.

    Pardes Rimmonim and Juno Jordan are primary_traditional and can license a
    method / a meaning. The ayanamsa authority is an honest placeholder
    (unnamed), so it is exempt from this check.
    """
    for target in CANONICAL_ACQUISITION_CORPUS:
        if target.work_id.endswith("_pending"):
            continue

        assert tier_of(target.work_id) is SourceTier.PRIMARY_TRADITIONAL
        assert can_license(tier_of(target.work_id), target.licenses_claim)


def test_the_corpus_is_one_source_per_phase_in_order() -> None:
    """Three works, phases 1-2-3, in dependency order."""
    phases = [target.phase for target in CANONICAL_ACQUISITION_CORPUS]

    assert phases == [1, 2, 3]
    assert len(CANONICAL_ACQUISITION_CORPUS) == 3


def test_each_target_names_the_gate_it_unlocks() -> None:
    """Value proportional to gates unlocked, not pages contained."""
    for target in CANONICAL_ACQUISITION_CORPUS:
        assert target.unlocks

    gematria = CANONICAL_ACQUISITION_CORPUS[0]

    assert gematria.system == "gematria"
    # Re-scoped by the P1 integration test: the value table is a normative
    # convention (Hebrew alphabetic numeral system), not a primary-text
    # method claim. See docs/GEMATRIA_P1_INTEGRATION_FINDINGS.md.
    assert gematria.licenses_claim is ClaimType.COMPUTATION
    assert gematria.required_tier is SourceTier.NORMATIVE_STANDARD
    assert gematria.finding
    assert "numeric_evaluation_available" in gematria.unlocks


# ---------------------------------------------------------------------------
# Catalog vs repository role
# ---------------------------------------------------------------------------


def test_catalogs_are_discovery_repositories_are_access() -> None:
    """The role distinction within the catalog_archive tier."""
    assert catalog_role("worldcat") is CatalogRole.CATALOG
    assert catalog_role("library_of_congress") is CatalogRole.CATALOG

    for repository in ("internet_archive", "sefaria", "gretil", "hathitrust"):
        assert catalog_role(repository) is CatalogRole.REPOSITORY


def test_a_non_catalog_source_has_no_catalog_role() -> None:
    """Unicode and primary works are not catalog-tier."""
    assert catalog_role("unicode_standard") is None
    assert catalog_role("pardes_rimmonim") is None


def test_both_roles_still_license_provenance_only() -> None:
    """The role distinction does not change the tier: no new fifth tier."""
    for source in ("worldcat", "internet_archive", "sefaria"):
        tier = tier_of(source)

        assert tier is SourceTier.CATALOG_ARCHIVE
        assert can_license(tier, ClaimType.PROVENANCE)
        assert not can_license(tier, ClaimType.MEANING)


def test_repository_access_is_not_copy_verification() -> None:
    """Finding a scan is not verifying a copy.

    A repository provides something to verify; the title-page, copyright-page
    and pagination checks still have to be made. Modelled by targets located
    via a repository still sitting at NOT_ACQUIRED, never COPY_VERIFIED.
    """
    located_via_repository = [
        target
        for target in CANONICAL_ACQUISITION_CORPUS
        if catalog_role(target.located_via) is CatalogRole.REPOSITORY
    ]

    assert located_via_repository
    for target in located_via_repository:
        assert target.status is AcquisitionStatus.NOT_ACQUIRED
