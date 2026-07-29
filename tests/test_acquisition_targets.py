"""Tests for the canonical acquisition corpus and catalog roles.

The corpus is mostly a plan: two targets are still NOT_ACQUIRED, and one --
numerology's denotation -- has been acquired and admitted (1E-N-SOURCE-A).
These tests pin that the plan is coherent (each target's tier can license its
claim), that the report names exactly what has been admitted, and that the
catalog/repository role distinction holds -- including the refined rule that
repository access alone is not copy verification, though completed copy-level
checks against a repository-hosted surrogate are.
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


def test_targets_reflect_their_real_acquisition_state() -> None:
    """Two targets acquired, one still a plan.

    Numerology's denotation (1E-N-SOURCE-A, Jordan) and the Vedic ayanamsa
    (1E-V-SOURCE-A, Calendar Reform Committee) are admitted; the gematria value
    method is still plan, not evidence. A target advances only by running the
    protocol against a verified copy, so the report's admitted list names
    exactly what has -- no more.
    """
    by_id = {t.target_id: t for t in CANONICAL_ACQUISITION_CORPUS}

    assert by_id["numerology-denotation"].status is (
        AcquisitionStatus.ADMITTED
    )
    assert by_id["vedic-ayanamsa-authority"].status is (
        AcquisitionStatus.ADMITTED
    )
    assert by_id["gematria-value-method"].status is (
        AcquisitionStatus.NOT_ACQUIRED
    )

    assert acquisition_report()["admitted"] == [
        "numerology-denotation",
        "vedic-ayanamsa-authority",
    ]


def test_every_target_tier_can_license_its_claim() -> None:
    """The plan cannot name a source that could not license its claim.

    Source-neutral coherence: caught now, not after a copy is in hand.
    """
    for target in CANONICAL_ACQUISITION_CORPUS:
        assert target.plan_is_coherent
        assert can_license(target.required_tier, target.licenses_claim)

    assert acquisition_report()["all_coherent"] is True


def test_named_works_are_classified_to_license_their_claim() -> None:
    """A named target's actual work tier must license the claim its gate needs.

    Juno Jordan is primary_traditional (licenses a meaning); the Calendar
    Reform Committee Report is a governmental normative standard (licenses the
    ayanamsa computation). The gematria work stays an honest placeholder,
    exempt from this check.
    """
    tiers: dict[str, SourceTier] = {}

    for target in CANONICAL_ACQUISITION_CORPUS:
        if target.work_id.endswith("_pending"):
            continue

        tier = tier_of(target.work_id)

        assert tier is not SourceTier.INADMISSIBLE
        assert can_license(tier, target.licenses_claim)
        tiers[target.work_id] = tier

    assert tiers["juno_jordan_romance_in_your_name"] is (
        SourceTier.PRIMARY_TRADITIONAL
    )
    assert tiers["calendar_reform_committee_report"] is (
        SourceTier.NORMATIVE_STANDARD
    )


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
    """Finding a scan is not verifying a copy -- but completing the checks is.

    A repository provides something to verify; the title-page, copyright-page
    and pagination checks still have to be made. The refined rule keeps that
    tooth: a repository-located target may advance past NOT_ACQUIRED only when
    its finding records that those copy-level checks were completed against the
    copy. Access alone never advances it -- so an advanced target must show the
    verification in its finding, not merely that a scan was located.
    """
    located_via_repository = [
        target
        for target in CANONICAL_ACQUISITION_CORPUS
        if catalog_role(target.located_via) is CatalogRole.REPOSITORY
    ]

    assert located_via_repository
    for target in located_via_repository:
        if target.status is AcquisitionStatus.NOT_ACQUIRED:
            continue

        # Advanced past NOT_ACQUIRED: the finding must document copy-level
        # verification against the actual pages, not just repository access.
        finding = target.finding.lower()

        assert "copy verified" in finding
        assert "page image" in finding
