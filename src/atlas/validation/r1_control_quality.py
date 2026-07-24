"""Control quality for R1 event studies.

Temporal 2 v1 produced a significant result that was an artifact of its own
controls, and the R0 gate exists because nothing in the harness caught it. R1
introduces a second, subtler version of the same failure, and this module
exists to catch that one.

**The failure mode.** Translation normalization masks Saturn's era signal by
collapsing the classes that carry it -- measured at 88% blocked accuracy in
B3D against chance in B2. So::

    events and controls differ strongly in Saturn phase
            -> B2 erases the distinction
            -> a B2 balance check passes
            -> the study appears properly controlled

That is false assurance produced by the representation itself. Hence the
structural rule this module enforces:

    A downstream coarsening may not be used to certify balance in an
    upstream representation.

A cohort is rejected when events and controls are distinguishable in B3 or
B3D, **even when B2 looks balanced**. The general principle is worth stating
beyond R1: *a lossy representation can make a confounded dataset appear
balanced.*

Thresholds are deliberately asymmetric. The bodies fail in different ways --
Saturn by era leakage, the fast bodies by saturation, the slow bodies by
degeneracy -- and one global threshold would miss most of them.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Hashable, Sequence

import numpy as np

from atlas.validation.artifacts import write_json
from atlas.validation.kamea_era import era_association


R1_CONTROL_QUALITY_SCHEMA = "atlas.validation.r1-control-quality.v1"

# The encodings a cohort must be balanced in. B2 is checked too, but it can
# never certify the others -- see MASKING below.
UPSTREAM_ENCODINGS: tuple[str, ...] = ("B3", "B3D")
CHECKED_ENCODINGS: tuple[str, ...] = ("B3", "B3D", "B2")

# Era leakage. Saturn reached 0.88 blocked accuracy at p=0.007 separating
# decades forty years apart, so the threshold sits well below that and the
# permutation test remains authoritative.
MAX_ERA_ACCURACY = 0.70
ERA_SIGNIFICANCE = 0.05

# Saturation. Above this share of never-before-seen classes, mutual
# information is maximal by construction and carries no meaning.
MAX_UNSEEN_CLASS_RATE = 0.50

# Degeneracy. An encoding whose dominant class covers this much of the cohort
# is close to constant.
MAX_DOMINANT_CLASS_SHARE = 0.90

# Distribution imbalance between events and controls, as total-variation
# distance over class frequencies.
MAX_CLASS_IMBALANCE = 0.30

# Support mismatch: events and controls must largely occupy the same classes.
MIN_SUPPORT_OVERLAP = 0.50


class R1ControlQualityError(ValueError):
    """An R1 result was produced without valid upstream control evidence."""


def total_variation(
    left: Sequence[Hashable], right: Sequence[Hashable]
) -> float:
    """Return the total-variation distance between two class distributions."""
    if not left or not right:
        return 1.0

    left_counts = Counter(left)
    right_counts = Counter(right)

    return 0.5 * sum(
        abs(
            left_counts.get(key, 0) / len(left)
            - right_counts.get(key, 0) / len(right)
        )
        for key in set(left_counts) | set(right_counts)
    )


def support_overlap(
    left: Sequence[Hashable], right: Sequence[Hashable]
) -> float:
    """Return the Jaccard overlap of the classes two cohorts occupy."""
    first, second = set(left), set(right)
    union = first | second

    return len(first & second) / len(union) if union else 1.0


def dominant_share(signatures: Sequence[Hashable]) -> float:
    """Return the share held by the most common class."""
    if not signatures:
        return 1.0

    return Counter(signatures).most_common(1)[0][1] / len(signatures)


@dataclass(frozen=True, slots=True)
class EncodingBalance:
    """Balance evidence for one body in one encoding."""

    body: str
    encoding: str
    class_imbalance: float
    support_overlap: float
    dominant_share: float
    era_accuracy: float
    era_p_value: float
    unseen_class_rate: float

    @property
    def distinguishable(self) -> bool:
        """Return whether events and controls differ in this encoding."""
        return (
            self.class_imbalance > MAX_CLASS_IMBALANCE
            or self.support_overlap < MIN_SUPPORT_OVERLAP
        )

    @property
    def era_leaking(self) -> bool:
        """Return whether this encoding predicts era at held-out blocks."""
        return (
            self.era_accuracy >= MAX_ERA_ACCURACY
            and self.era_p_value < ERA_SIGNIFICANCE
        )

    @property
    def saturated(self) -> bool:
        """Return whether class coverage is too sparse to interpret."""
        return self.unseen_class_rate > MAX_UNSEEN_CLASS_RATE

    @property
    def degenerate(self) -> bool:
        """Return whether the encoding is close to constant."""
        return self.dominant_share > MAX_DOMINANT_CLASS_SHARE

    def failures(self) -> list[str]:
        """Return the failure categories this encoding exhibits."""
        problems: list[str] = []

        if self.distinguishable:
            problems.append("class_imbalance")

        if self.support_overlap < MIN_SUPPORT_OVERLAP:
            problems.append("support_mismatch")

        if self.era_leaking:
            problems.append("era_leakage")

        if self.saturated:
            problems.append("saturation")

        if self.degenerate:
            problems.append("degeneracy")

        return problems

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "body": self.body,
            "encoding": self.encoding,
            "failures": self.failures(),
            "class_imbalance": self.class_imbalance,
            "support_overlap": self.support_overlap,
            "dominant_share": self.dominant_share,
            "era_accuracy": self.era_accuracy,
            "era_p_value": self.era_p_value,
            "unseen_class_rate": self.unseen_class_rate,
            # Recorded because mutual information is uninterpretable above
            # the saturation threshold and must not be read alone.
            "mutual_information_interpretable": not self.saturated,
        }


def measure_balance(
    body: str,
    encoding: str,
    event_signatures: Sequence[Hashable],
    control_signatures: Sequence[Hashable],
    *,
    instants: Sequence[datetime] | None = None,
    era_labels: Sequence[str] | None = None,
    permutations: int = 100,
    seed: int = 20260801,
) -> EncodingBalance:
    """Measure one body's event/control balance in one encoding."""
    era_accuracy = float("nan")
    era_p = float("nan")
    unseen = 0.0

    if instants is not None and era_labels is not None:
        association = era_association(
            list(event_signatures) + list(control_signatures),
            list(instants),
            list(era_labels),
            permutations=permutations,
            seed=seed,
        )
        era_accuracy = association["balanced_accuracy"]
        era_p = association["mi_p_value"]
        unseen = association.get("unseen_class_rate", 0.0)

    return EncodingBalance(
        body=body,
        encoding=encoding,
        class_imbalance=total_variation(event_signatures, control_signatures),
        support_overlap=support_overlap(event_signatures, control_signatures),
        dominant_share=dominant_share(
            list(event_signatures) + list(control_signatures)
        ),
        era_accuracy=era_accuracy,
        era_p_value=era_p,
        unseen_class_rate=unseen,
    )


def translation_masking(
    balances: Sequence[EncodingBalance],
) -> dict[str, Any]:
    """Detect a coarsening concealing an upstream imbalance.

    The structural rule, enforced. If B3 or B3D distinguishes events from
    controls -- or predicts era -- while B2 does not, then B2's apparent
    balance is an artifact of the classes it collapsed, and it may not be
    used to certify the cohort.
    """
    by_encoding = {balance.encoding: balance for balance in balances}

    upstream_problem = any(
        by_encoding[name].distinguishable or by_encoding[name].era_leaking
        for name in UPSTREAM_ENCODINGS
        if name in by_encoding
    )

    downstream = by_encoding.get("B2")
    downstream_clean = downstream is not None and not (
        downstream.distinguishable or downstream.era_leaking
    )

    masked = upstream_problem and downstream_clean

    return {
        "upstream_distinguishable_or_leaking": upstream_problem,
        "downstream_appears_clean": downstream_clean,
        "translation_masking_detected": masked,
        "note": (
            "Translation normalization masks an upstream difference by "
            "collapsing the classes that carry it -- it does not adjust for "
            "one. A clean B2 therefore cannot certify B3 or B3D."
        ),
    }


@dataclass(frozen=True, slots=True)
class R1ControlQuality:
    """The required control-quality artifact for an R1 study."""

    schema_version: str
    balances: tuple[EncodingBalance, ...]
    masking: dict[str, Any]

    @property
    def upstream_sound(self) -> bool:
        """Return whether B3 and B3D are both balanced and leak-free."""
        return not any(
            balance.failures()
            for balance in self.balances
            if balance.encoding in UPSTREAM_ENCODINGS
        )

    @property
    def masking_detected(self) -> bool:
        """Return whether a coarsening concealed an upstream difference."""
        return bool(self.masking.get("translation_masking_detected"))

    @property
    def usable(self) -> bool:
        """Return whether an R1 result may be interpreted at all."""
        return self.upstream_sound and not self.masking_detected

    def failures_by_category(self) -> dict[str, list[str]]:
        """Return failing body/encoding pairs, grouped by category."""
        grouped: dict[str, list[str]] = {}

        for balance in self.balances:
            for category in balance.failures():
                grouped.setdefault(category, []).append(
                    f"{balance.body}/{balance.encoding}"
                )

        if self.masking_detected:
            grouped.setdefault("translation_masking", []).append("B3D->B2")

        return grouped

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "usable": self.usable,
            "upstream_sound": self.upstream_sound,
            "translation_masking_detected": self.masking_detected,
            "failures_by_category": self.failures_by_category(),
            "thresholds": {
                "max_era_accuracy": MAX_ERA_ACCURACY,
                "era_significance": ERA_SIGNIFICANCE,
                "max_unseen_class_rate": MAX_UNSEEN_CLASS_RATE,
                "max_dominant_class_share": MAX_DOMINANT_CLASS_SHARE,
                "max_class_imbalance": MAX_CLASS_IMBALANCE,
                "min_support_overlap": MIN_SUPPORT_OVERLAP,
            },
            "masking": self.masking,
            "balances": [balance.to_dict() for balance in self.balances],
            "principle": (
                "A lossy representation can make a confounded dataset appear "
                "balanced. A downstream coarsening may therefore never be "
                "used to certify balance in an upstream representation."
            ),
        }


def build_r1_control_quality(
    balances: Sequence[EncodingBalance],
) -> R1ControlQuality:
    """Assemble the artifact, including the masking check."""
    return R1ControlQuality(
        schema_version=R1_CONTROL_QUALITY_SCHEMA,
        balances=tuple(balances),
        masking=translation_masking(balances),
    )


def write_r1_result(
    result: dict[str, Any],
    *,
    control_quality: R1ControlQuality | None,
    output_dir: Path,
    result_name: str,
) -> dict[str, Path]:
    """Write an R1 result, refusing without valid upstream evidence.

    Stricter than the R0 gate. Presence of the artifact is not enough: a
    cohort whose upstream encodings are imbalanced, or whose B2 balance is
    the product of masking, produces no output at all.
    """
    if control_quality is None:
        raise R1ControlQualityError(
            "An R1 result cannot be written without control-quality "
            "evidence covering B3, B3D and B2. Build one with "
            "build_r1_control_quality()."
        )

    if not control_quality.balances:
        raise R1ControlQualityError(
            "R1 control quality carries no encodings; there is nothing to "
            "qualify the result with."
        )

    if control_quality.masking_detected:
        raise R1ControlQualityError(
            "Translation masking detected: events and controls are "
            "distinguishable in B3 or B3D while B2 appears balanced. B2's "
            "balance is an artifact of the classes it collapsed, so it "
            "cannot certify this cohort. Fix the control design upstream."
        )

    if not control_quality.upstream_sound:
        raise R1ControlQualityError(
            "Upstream encodings are not sound: "
            f"{control_quality.failures_by_category()}. A downstream "
            "coarsening may not be used to certify balance in an upstream "
            "representation."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    annotated = {
        **result,
        "r1_control_quality_summary": {
            "usable": control_quality.usable,
            "upstream_sound": control_quality.upstream_sound,
            "translation_masking_detected": (
                control_quality.masking_detected
            ),
        },
        "interpretation_rule": (
            "No B2 event result may be attributed to Kamea geometry unless "
            "it differs robustly from B3D under controls that pass upstream "
            "era and support diagnostics."
        ),
    }

    return {
        "result": write_json(annotated, output_dir / result_name),
        "control_quality": write_json(
            control_quality.to_dict(), output_dir / "r1_control_quality.json"
        ),
    }
