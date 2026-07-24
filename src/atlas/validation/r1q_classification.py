"""The R1-Q decision rule, preregistered before the large cohort runs.

1D's remaining job is narrow: determine whether any substantial nondegenerate
regime contradicts quantization dominance. Writing the rule first is what
stops the large cohort from being read as whatever it happens to show.

Four translation outcomes are reported separately, because they are different
phenomena and collapsing them has already caused one misreading in this
milestone::

    translation_active                            signature changes at all
    translation_merges_classes                    distinct B3D classes merge
    translation_removes_empirical_era_association distributional, MI-based
    translation_changes_blocked_era_predictability held-out, accuracy-based

The last two stay apart because translation can reduce empirical association
without producing a reliable change in held-out predictability -- exactly the
distinction the saturated Moon case forced.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Hashable, Sequence

from atlas.validation.kamea_baselines import (
    mutual_information,
    occupancy_estimates,
    partition_comparison,
    shannon_entropy,
)
from atlas.validation.kamea_era import blocked_accuracy


R1Q_SCHEMA = "atlas.validation.r1q-classification.v1"

# A regime must clear this to count as nondegenerate. Below it, any
# translation effect is an effect on near-constant paths.
MIN_EFFECTIVE_SUPPORT = 5.0

# Below this, translation is doing nothing worth attributing to geometry.
MIN_TRANSLATION_ACTIVITY = 0.10

# Saturation ceiling: above it, capacity is a property of the cohort.
MAX_UNSEEN_FOR_CAPACITY = 0.50

# A change in held-out era predictability worth calling a change.
MIN_ACCURACY_CHANGE = 0.10


@dataclass(frozen=True, slots=True)
class RegimeRow:
    """One body-scale row of the R1-Q decision table."""

    body: str
    scale: str
    cohort: str
    capacity: dict[str, Any]
    translation: dict[str, Any]
    partition: dict[str, Any]
    era: dict[str, Any]

    @property
    def adequate_capacity(self) -> bool:
        """Return whether B3D is measurably nondegenerate."""
        return (
            self.capacity["effective_support"] >= MIN_EFFECTIVE_SUPPORT
            and self.capacity["capacity_measurable"]
        )

    @property
    def translation_active(self) -> bool:
        """Return whether B2 differs from B3D at all."""
        return (
            self.translation["translation_activity"]
            >= MIN_TRANSLATION_ACTIVITY
        )

    @property
    def merges_classes(self) -> bool:
        """Return whether distinct B3D classes were merged."""
        return self.partition["merges_added_by_right"] > 0

    @property
    def outside_degenerate_paths(self) -> bool:
        """Return whether the effect survives excluding stationary paths.

        The measured mechanism is that translation merges only when core
        figures are small enough to coincide, which is where paths are
        already degenerate. A geometry-specific claim has to hold where they
        are not.
        """
        return self.translation["stationary_fraction"] < 0.5

    def contradicts_r1q(self) -> bool:
        """Return whether this regime is evidence against R1-Q.

        Preregistered conjunction: anything less remains consistent with
        quantization dominance.
        """
        return (
            self.adequate_capacity
            and self.translation_active
            and self.merges_classes
            and self.outside_degenerate_paths
            and not self.capacity["saturated"]
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "body": self.body,
            "scale": self.scale,
            "cohort": self.cohort,
            "adequate_capacity": self.adequate_capacity,
            "translation_active": self.translation_active,
            "merges_classes": self.merges_classes,
            "outside_degenerate_paths": self.outside_degenerate_paths,
            "contradicts_r1q": self.contradicts_r1q(),
            "capacity": self.capacity,
            "translation": self.translation,
            "partition": self.partition,
            "era": self.era,
        }


def translation_outcomes(
    encodings: Sequence[dict[str, tuple[Hashable, ...]]],
    instants: Sequence[datetime],
    era_labels: Sequence[str],
) -> dict[str, Any]:
    """Return the four translation outcomes, kept separate."""
    b3d = [item["B3D"] for item in encodings]
    b2 = [item["B2"] for item in encodings]

    changed = sum(1 for left, right in zip(b3d, b2) if left != right)

    classes_b3d = len(set(b3d))
    classes_b2 = len(set(b2))

    mi_b3d = mutual_information(b3d, era_labels)
    mi_b2 = mutual_information(b2, era_labels)

    accuracy_b3d = blocked_accuracy(b3d, instants, era_labels)
    accuracy_b2 = blocked_accuracy(b2, instants, era_labels)

    accuracy_delta = (
        accuracy_b3d["balanced_accuracy"] - accuracy_b2["balanced_accuracy"]
    )

    return {
        # 1. Does the signature change at all? Note this is nearly always
        # true, since translation rewrites coordinates even when it merges
        # nothing -- which is why it is reported apart from merging.
        "signature_changed_fraction": changed / len(encodings),
        # 2. Does it merge distinct classes? The partition-level question.
        "translation_activity": (
            1.0 - classes_b2 / classes_b3d if classes_b3d else 0.0
        ),
        "classes_b3d": classes_b3d,
        "classes_b2": classes_b2,
        # 3. Distributional: association with era, which a coarsening
        # cannot increase.
        "era_mi_b3d_nats": mi_b3d,
        "era_mi_b2_nats": mi_b2,
        "removes_empirical_era_association": mi_b3d - mi_b2 > 0.01,
        "era_association_removed": mi_b3d - mi_b2,
        # 4. Held-out: reusable predictability, which can move independently
        # of the distributional measure.
        "era_accuracy_b3d": accuracy_b3d["balanced_accuracy"],
        "era_accuracy_b2": accuracy_b2["balanced_accuracy"],
        "changes_blocked_era_predictability": (
            abs(accuracy_delta) >= MIN_ACCURACY_CHANGE
        ),
        "era_accuracy_change": accuracy_delta,
        "unseen_class_rate_b3d": accuracy_b3d.get("unseen_class_rate", 0.0),
        "entropy_b3d_nats": shannon_entropy(b3d),
        "entropy_b2_nats": shannon_entropy(b2),
        "stationary_fraction": sum(
            1 for item in encodings if len(set(item["B1"])) == 1
        )
        / len(encodings),
    }


def build_regime_row(
    body: str,
    scale: str,
    cohort: str,
    encodings: Sequence[dict[str, tuple[Hashable, ...]]],
    instants: Sequence[datetime],
    era_labels: Sequence[str],
) -> RegimeRow:
    """Assemble one decision-table row."""
    b3d = [item["B3D"] for item in encodings]
    b2 = [item["B2"] for item in encodings]

    return RegimeRow(
        body=body,
        scale=scale,
        cohort=cohort,
        capacity=occupancy_estimates(b3d),
        translation=translation_outcomes(encodings, instants, era_labels),
        partition=partition_comparison(b3d, b2),
        era={
            "mi_b3d_nats": mutual_information(b3d, era_labels),
            "mi_b2_nats": mutual_information(b2, era_labels),
        },
    )


def classify_r1q(
    rows: Sequence[RegimeRow],
    *,
    require_cross_cohort_stability: bool = True,
) -> dict[str, Any]:
    """Apply the preregistered rule across every measured regime.

    The stated conjunction includes *stable class merges across cohorts*, so
    it is enforced here rather than reported alongside: a body-scale regime
    counts as evidence only when every cohort's row qualifies **and** its
    translation activity agrees across cadences. The first version of this
    function checked the per-row clauses only, which admitted regimes whose
    activity was a lattice artifact -- exactly the failure the Mercury
    aliasing result warned about.
    """
    qualifying_rows = [
        f"{row.body}/{row.scale}/{row.cohort}"
        for row in rows
        if row.contradicts_r1q()
    ]

    grouped: dict[tuple[str, str], list[RegimeRow]] = {}

    for row in rows:
        grouped.setdefault((row.body, row.scale), []).append(row)

    stability = robustness_across_cohorts(rows)
    unstable = set(stability["unstable_across_cohorts"])

    contradicting: list[str] = []
    rejected_for_instability: list[str] = []

    for (body, scale), group in sorted(grouped.items()):
        if not all(row.contradicts_r1q() for row in group):
            continue

        label = f"{body}/{scale}"

        if require_cross_cohort_stability and label in unstable:
            rejected_for_instability.append(label)
            continue

        contradicting.append(label)

    return {
        "schema": R1Q_SCHEMA,
        "regimes": len(rows),
        "body_scale_regimes": len(grouped),
        "qualifying_rows": qualifying_rows,
        "contradicting_regimes": contradicting,
        "rejected_for_instability": rejected_for_instability,
        "cross_cohort_stability_enforced": require_cross_cohort_stability,
        "r1q_holds": not contradicting,
        "rule": {
            "min_effective_support": MIN_EFFECTIVE_SUPPORT,
            "min_translation_activity": MIN_TRANSLATION_ACTIVITY,
            "max_unseen_for_capacity": MAX_UNSEEN_FOR_CAPACITY,
            "min_accuracy_change": MIN_ACCURACY_CHANGE,
            "conjunction": (
                "adequate B3D capacity AND nontrivial translation activity "
                "AND stable class merges AND effect outside near-stationary "
                "paths AND not explained by saturation"
            ),
        },
        "classification": (
            "R1-Q: quantization-dominant"
            if not contradicting
            else "R1-G: geometrically active in at least one regime"
        ),
    }


def threshold_sensitivity(
    rows: Sequence[RegimeRow],
    *,
    activity_grid: Sequence[float] = (0.05, 0.10, 0.15, 0.20, 0.30),
    stationary_grid: Sequence[float] = (0.4, 0.5, 0.6),
) -> dict[str, Any]:
    """Return which regimes survive over a grid of the two soft thresholds.

    The frozen rule is one point on this grid. A finding that holds only at
    its own cutoff is threshold-dependent; one that holds across the grid is
    a property of the data. Reported so the distinction is visible rather
    than assumed. Capacity, merges and stability are structural clauses and
    are held fixed -- only the two tunable cutoffs are swept.
    """
    grouped: dict[tuple[str, str], list[RegimeRow]] = {}

    for row in rows:
        grouped.setdefault((row.body, row.scale), []).append(row)

    stability = robustness_across_cohorts(rows)
    unstable = set(stability["unstable_across_cohorts"])

    cells: list[dict[str, Any]] = []
    survival: dict[str, int] = {}
    combinations = 0

    for activity_min in activity_grid:
        for stationary_max in stationary_grid:
            combinations += 1
            contradicting: list[str] = []

            for (body, scale), group in sorted(grouped.items()):
                label = f"{body}/{scale}"

                if label in unstable:
                    continue

                qualifies = all(
                    row.adequate_capacity
                    and not row.capacity["saturated"]
                    and row.merges_classes
                    and row.translation["translation_activity"]
                    >= activity_min
                    and row.translation["stationary_fraction"]
                    < stationary_max
                    for row in group
                )

                if qualifies:
                    contradicting.append(label)
                    survival[label] = survival.get(label, 0) + 1

            cells.append(
                {
                    "activity_min": activity_min,
                    "stationary_max": stationary_max,
                    "contradicting": contradicting,
                    "r1q_holds": not contradicting,
                }
            )

    always = sorted(
        label for label, count in survival.items() if count == combinations
    )
    sometimes = sorted(
        label
        for label, count in survival.items()
        if 0 < count < combinations
    )

    return {
        "grid": {
            "activity_min": list(activity_grid),
            "stationary_max": list(stationary_grid),
            "combinations": combinations,
        },
        "survives_every_threshold": always,
        "threshold_dependent": {
            label: survival[label] for label in sometimes
        },
        # R1-G is robust if at least one regime contradicts everywhere on the
        # grid; the classification does not hinge on a single cutoff.
        "r1g_threshold_robust": bool(always),
        "cells": cells,
    }


def robustness_across_cohorts(
    rows: Sequence[RegimeRow],
) -> dict[str, Any]:
    """Check whether translation activity is stable across cohorts.

    A merge count that appears under one cadence and vanishes under another
    is a sampling artifact, not a property of the representation -- the
    Mercury aliasing result showed this is not hypothetical.
    """
    grouped: dict[tuple[str, str], list[float]] = {}

    for row in rows:
        grouped.setdefault((row.body, row.scale), []).append(
            row.translation["translation_activity"]
        )

    unstable = [
        f"{body}/{scale}"
        for (body, scale), values in grouped.items()
        if len(values) > 1
        and max(values) > 0
        and (max(values) - min(values)) / max(values) > 0.25
    ]

    return {
        "regimes_compared": len(grouped),
        "unstable_across_cohorts": unstable,
        "stable": not unstable,
    }
