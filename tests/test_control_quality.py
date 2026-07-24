"""Tests for the required control-quality artifact.

The enforcement is the point. Temporal 2 v1 produced a significant result
that was an artifact of its own controls, and the harness had nothing to say
about it -- the explanation was written afterwards, once the number looked
wrong. These tests pin that a study now cannot write a result at all without
control-quality evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import numpy as np
import pytest

from atlas.validation.control_quality import (
    CONTROL_QUALITY_SCHEMA,
    MAX_FEATURE_IMBALANCE,
    MAX_FRACTION_OUTSIDE_WINDOW,
    ControlQuality,
    ControlQualityError,
    FamilyQuality,
    build_control_quality,
    synthetic_era_leak_check,
    write_temporal_result,
)
from atlas.validation.temporal_controls import (
    ObservationWindow,
    window_random_controls,
)
from atlas.validation.temporal_state import (
    build_temporal_matrix,
    temporal_feature_layout,
)


WINDOW = ObservationWindow(
    earliest=datetime(1970, 1, 1, tzinfo=UTC),
    latest=datetime(2025, 12, 31, tzinfo=UTC),
)


def _family(
    *,
    outside: float = 0.0,
    imbalance: float = 0.05,
    year_distance: float = 0.05,
) -> FamilyQuality:
    """Build a family-quality record with chosen diagnostics."""
    return FamilyQuality(
        family="test",
        era_balance={
            "fraction_outside_event_window": outside,
            "year_distribution_distance": year_distance,
        },
        feature_imbalance={
            "max_absolute_standardized_difference": imbalance,
            "features": [],
            "body_ranking": [],
        },
    )


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------


def test_result_cannot_be_written_without_control_quality(
    tmp_path: Path,
) -> None:
    """The structural guarantee: no evidence, no output.

    v1's failure was possible because a result could be produced with
    nothing said about its controls.
    """
    with pytest.raises(ControlQualityError, match="cannot be written"):
        write_temporal_result(
            {"study": "x"},
            control_quality=None,
            output_dir=tmp_path,
            result_name="result.json",
        )

    assert not list(tmp_path.iterdir())


def test_result_cannot_be_written_with_empty_families(
    tmp_path: Path,
) -> None:
    """An artifact covering no families qualifies nothing."""
    empty = ControlQuality(
        schema_version=CONTROL_QUALITY_SCHEMA,
        families=(),
        synthetic_control_check={},
    )

    with pytest.raises(ControlQualityError, match="no families"):
        write_temporal_result(
            {"study": "x"},
            control_quality=empty,
            output_dir=tmp_path,
            result_name="result.json",
        )


def test_written_result_carries_its_control_verdict(tmp_path: Path) -> None:
    """A reader sees the control verdict without opening a second file."""
    quality = ControlQuality(
        schema_version=CONTROL_QUALITY_SCHEMA,
        families=(_family(), _family(outside=0.9)),
        synthetic_control_check={"diagnostic_working": True},
    )

    paths = write_temporal_result(
        {"study": "x", "verdict": "no_association"},
        control_quality=quality,
        output_dir=tmp_path,
        result_name="result.json",
    )

    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    summary = result["control_quality_summary"]

    assert summary["all_families_sound"] is False
    assert summary["diagnostic_working"] is True
    assert paths["control_quality"].name == "control_quality.json"


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------


def test_out_of_window_sampling_is_unsound() -> None:
    """The v1 matched family, at 35.7% outside, must fail."""
    family = _family(outside=0.357, imbalance=0.611)

    assert not family.sound
    assert "samples_outside_event_window" in family.failures()
    assert "excessive_feature_imbalance" in family.failures()


def test_v1_null_families_would_pass() -> None:
    """The families that were sound in v1 must still read as sound.

    nearby sampled 0.3% outside with imbalance 0.090; random 0.0% and 0.104.
    A threshold that failed these would be miscalibrated.
    """
    assert _family(outside=0.003, imbalance=0.090).sound
    assert _family(outside=0.0, imbalance=0.104).sound


def test_v2_families_would_pass() -> None:
    """Every v2 family sampled 0.0% outside with imbalance at most 0.114."""
    assert _family(outside=0.0, imbalance=0.114).sound


def test_thresholds_sit_between_the_observed_cases() -> None:
    """The thresholds separate v1's failures from its successes."""
    assert 0.003 < MAX_FRACTION_OUTSIDE_WINDOW < 0.126
    assert 0.114 < MAX_FEATURE_IMBALANCE < 0.419


def test_year_distribution_mismatch_is_caught() -> None:
    """A family may sit inside the window and still be era-skewed."""
    family = _family(year_distance=0.9)

    assert not family.sound
    assert "year_distribution_mismatch" in family.failures()


# ---------------------------------------------------------------------------
# The self-check
# ---------------------------------------------------------------------------


def test_synthetic_check_detects_era_leakage() -> None:
    """The diagnostic must still fire on a known confound.

    If it stops firing here it is not capable of catching a real one, so its
    silence about a study's own families would mean nothing.
    """
    check = synthetic_era_leak_check(
        build_matrix=build_temporal_matrix,
        layout=temporal_feature_layout(),
        sample=20,
    )

    assert check["leak_detected"] is True
    assert check["confinement_removes_leak"] is True
    assert check["diagnostic_working"] is True
    # Confinement must remove most of the leak, judged as a ratio: an
    # absolute bound would fail on small samples for reasons unrelated to
    # the diagnostic.
    assert check["leak_reduction_ratio"] < 0.5


def test_build_control_quality_covers_every_family() -> None:
    """Every supplied family appears in the artifact."""
    rng = np.random.default_rng(5)
    layout = temporal_feature_layout()

    # A realistic sample. The imbalance threshold assumes one: a handful of
    # events produces noisy standardized differences that can exceed it with
    # perfectly sound controls.
    events = [
        WINDOW.earliest + timedelta(days=int(rng.integers(0, 20_000)))
        for _ in range(120)
    ]
    controls = {
        "window_random": [
            control
            for event in events
            for control in window_random_controls(
                event, count=5, window=WINDOW, rng=rng
            )
        ]
    }

    event_matrix, _ = build_temporal_matrix(events)
    control_matrices = {
        name: build_temporal_matrix(instants)[0]
        for name, instants in controls.items()
    }

    quality = build_control_quality(
        events=events,
        controls_by_family=controls,
        event_matrix=event_matrix,
        control_matrices=control_matrices,
        layout=layout,
        window=WINDOW,
        build_matrix=build_temporal_matrix,
    )

    assert [f.family for f in quality.families] == ["window_random"]
    assert quality.all_sound
    assert quality.synthetic_control_check["diagnostic_working"] is True
