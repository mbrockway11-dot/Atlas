"""Tests for R1 control quality, and the Saturn era regression gate.

Two things are pinned here.

The **structural rule**: a downstream coarsening may never certify balance in
an upstream representation. Translation normalization masks Saturn's era
signal by collapsing the classes that carry it, so a clean B2 balance check
is compatible with a badly confounded cohort. That is false assurance
produced by the representation itself, and the writer refuses it.

The **Saturn regression gate**: the measured era behaviour is now a fixture
of the framework. If Saturn stops separating well-separated decades in B3D,
or if B2 stops losing that information, something upstream changed and the
audit's conclusions no longer follow from the code.
"""

from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path

import numpy as np
import pytest

from atlas.validation.kamea_baselines import encode_cohort
from atlas.validation.kamea_era import (
    EARLY_ERA,
    LATE_ERA,
    binary_era_labels,
    blocked_accuracy,
)
from atlas.validation.r1_control_quality import (
    MAX_ERA_ACCURACY,
    EncodingBalance,
    R1ControlQualityError,
    build_r1_control_quality,
    dominant_share,
    support_overlap,
    total_variation,
    translation_masking,
    write_r1_result,
)
from atlas.validation.temporal_kamea import canonical_spec


def _balance(
    encoding: str,
    *,
    imbalance: float = 0.05,
    overlap: float = 0.9,
    dominant: float = 0.2,
    era_accuracy: float = 0.5,
    era_p: float = 0.6,
    unseen: float = 0.1,
) -> EncodingBalance:
    """Build a balance record with chosen diagnostics."""
    return EncodingBalance(
        body="saturn",
        encoding=encoding,
        class_imbalance=imbalance,
        support_overlap=overlap,
        dominant_share=dominant,
        era_accuracy=era_accuracy,
        era_p_value=era_p,
        unseen_class_rate=unseen,
    )


# ---------------------------------------------------------------------------
# The structural rule
# ---------------------------------------------------------------------------


def test_clean_b2_cannot_certify_a_confounded_cohort() -> None:
    """The failure mode this module exists to catch.

    Events and controls differ in Saturn phase, translation erases the
    distinction, and a B2-only balance check would pass.
    """
    masking = translation_masking(
        [
            _balance("B3", imbalance=0.7),
            _balance("B3D", imbalance=0.7),
            _balance("B2"),
        ]
    )

    assert masking["upstream_distinguishable_or_leaking"] is True
    assert masking["downstream_appears_clean"] is True
    assert masking["translation_masking_detected"] is True


def test_masking_blocks_the_write(tmp_path: Path) -> None:
    """No output at all, rather than a result carrying false assurance."""
    quality = build_r1_control_quality(
        [
            _balance("B3", imbalance=0.7),
            _balance("B3D", imbalance=0.7),
            _balance("B2"),
        ]
    )

    assert quality.usable is False

    with pytest.raises(R1ControlQualityError, match="masking detected"):
        write_r1_result(
            {"study": "x"},
            control_quality=quality,
            output_dir=tmp_path,
            result_name="result.json",
        )

    assert not list(tmp_path.iterdir())


def test_upstream_era_leakage_blocks_the_write(tmp_path: Path) -> None:
    """Saturn's measured failure mode, as a gate."""
    quality = build_r1_control_quality(
        [
            _balance("B3", era_accuracy=0.88, era_p=0.007),
            _balance("B3D", era_accuracy=0.89, era_p=0.007),
            _balance("B2", era_accuracy=0.51, era_p=0.29),
        ]
    )

    with pytest.raises(R1ControlQualityError):
        write_r1_result(
            {"study": "x"},
            control_quality=quality,
            output_dir=tmp_path,
            result_name="result.json",
        )


def test_a_sound_cohort_writes_with_its_interpretation_rule(
    tmp_path: Path,
) -> None:
    """A valid cohort produces output carrying the attribution rule."""
    quality = build_r1_control_quality(
        [_balance("B3"), _balance("B3D"), _balance("B2")]
    )

    assert quality.usable is True

    paths = write_r1_result(
        {"study": "x", "verdict": "no_association"},
        control_quality=quality,
        output_dir=tmp_path,
        result_name="result.json",
    )

    result = json.loads(paths["result"].read_text(encoding="utf-8"))

    assert result["r1_control_quality_summary"]["usable"] is True
    assert "differs robustly from B3D" in result["interpretation_rule"]


def test_missing_evidence_blocks_the_write(tmp_path: Path) -> None:
    """The R0 gate's rule, carried forward."""
    with pytest.raises(R1ControlQualityError, match="cannot be written"):
        write_r1_result(
            {"study": "x"},
            control_quality=None,
            output_dir=tmp_path,
            result_name="result.json",
        )


def test_balanced_downstream_does_not_hide_upstream_in_the_report() -> None:
    """Failures are grouped by category so each mode stays visible."""
    quality = build_r1_control_quality(
        [
            _balance("B3", overlap=0.1),
            _balance("B3D", unseen=0.9),
            _balance("B2", dominant=0.99),
        ]
    )

    categories = quality.failures_by_category()

    assert "support_mismatch" in categories
    assert "saturation" in categories
    assert "degeneracy" in categories


# ---------------------------------------------------------------------------
# Component measures
# ---------------------------------------------------------------------------


def test_total_variation_bounds() -> None:
    """Identical cohorts differ by zero; disjoint ones by one."""
    assert total_variation(["a", "b"], ["a", "b"]) == pytest.approx(0.0)
    assert total_variation(["a", "a"], ["b", "b"]) == pytest.approx(1.0)


def test_support_overlap_detects_disjoint_classes() -> None:
    """Cohorts occupying different classes cannot be compared."""
    assert support_overlap(["a", "b"], ["a", "b"]) == pytest.approx(1.0)
    assert support_overlap(["a"], ["b"]) == pytest.approx(0.0)


def test_dominant_share_detects_a_near_constant_encoding() -> None:
    """Saturn at the shortest scale is close to constant."""
    assert dominant_share(["x"] * 99 + ["y"]) == pytest.approx(0.99)


# ---------------------------------------------------------------------------
# The Saturn era regression gate
# ---------------------------------------------------------------------------


def _era_cohort(per_era: int = 45, seed: int = 20260801):
    """Draw a deterministic cohort inside the two declared eras."""
    rng = np.random.default_rng(seed)
    instants = []

    for start, end in (EARLY_ERA, LATE_ERA):
        span = int((end - start).total_seconds())
        instants.extend(
            start + timedelta(seconds=int(rng.integers(0, span)))
            for _ in range(per_era)
        )

    return binary_era_labels(sorted(instants))


def test_saturn_still_leaks_era_upstream() -> None:
    """Saturn's quantized trajectory separates decades forty years apart.

    The measured fixture: 88% blocked accuracy at p=0.007. If this stops
    holding, the representation changed and the audit's conclusions no
    longer follow from the code.
    """
    instants, labels = _era_cohort()
    encodings = encode_cohort(instants, "saturn", canonical_spec("R1-W3D"))

    accuracy = blocked_accuracy(
        [item["B3D"] for item in encodings], instants, labels
    )

    assert accuracy["balanced_accuracy"] >= MAX_ERA_ACCURACY
    assert accuracy["unseen_class_rate"] < 0.25


def test_translation_masks_saturn_era_information() -> None:
    """B2 conceals the leak by collapsing the classes that carry it.

    Not a correction. Translation discards distinctions, and the nuisance
    association disappears as a consequence -- so a null B2 diagnostic
    cannot certify a clean control design.
    """
    instants, labels = _era_cohort()
    encodings = encode_cohort(instants, "saturn", canonical_spec("R1-W3D"))

    upstream = blocked_accuracy(
        [item["B3D"] for item in encodings], instants, labels
    )["balanced_accuracy"]
    downstream = blocked_accuracy(
        [item["B2"] for item in encodings], instants, labels
    )["balanced_accuracy"]

    assert upstream >= MAX_ERA_ACCURACY
    assert downstream < MAX_ERA_ACCURACY
    assert upstream - downstream > 0.2


def test_fast_bodies_do_not_spuriously_leak() -> None:
    """Only Saturn exceeded the threshold, and that must stay true."""
    instants, labels = _era_cohort()

    for key in ("moon", "mercury"):
        encodings = encode_cohort(instants, key, canonical_spec("R1-W3D"))
        accuracy = blocked_accuracy(
            [item["B3D"] for item in encodings], instants, labels
        )

        assert accuracy["balanced_accuracy"] < MAX_ERA_ACCURACY
