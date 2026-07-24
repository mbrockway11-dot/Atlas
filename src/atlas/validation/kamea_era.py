"""Blocked era predictability for R1 encodings.

Accepting static slow bodies made a static cell an era marker: Saturn crosses
one cell of its own square in 3.27 years, so its cell is approximately a
decade label. That is Temporal 2 v1's era leakage in R1 form, and it must be
measured before any R1 event study, not after one produces a number.

The partition decomposition makes the measurement diagnostic rather than
merely descriptive. Each encoding isolates one operation, so era association
can be attributed::

    B3    quantized orbital state
    B3D   after removing repeat visits          -> dedup's contribution
    B2    after translation normalization       -> the square's contribution

Two quantities are reported, and conflating them would be an error:

* **Mutual information** -- population association. B2 is a coarsening of
  B3D, so it *cannot* add information about era; MI must fall or hold.
* **Blocked predictive accuracy** -- usable separability in a finite sample.
  This can rise under coarsening, because merging classes is regularization.

If accuracy rises while MI falls, that is a compression effect, not newly
created temporal information. The report says so explicitly rather than
leaving the reader to notice.

Validation is blocked by calendar year. A random split would put adjacent
timestamps -- with near-identical slow-body states -- in both train and test,
which inflates accuracy for exactly the bodies whose leakage is at issue.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any, Hashable, Sequence

import numpy as np

from atlas.validation.kamea_baselines import mutual_information


ERA_SCHEMA = "atlas.validation.kamea-era.v1"

# Two well-separated decades, the analogue of the synthetic control check.
# Separated rather than adjacent so that a failure to distinguish them is
# strong evidence of no era dependence.
EARLY_ERA = (datetime(1970, 1, 1, tzinfo=UTC), datetime(1980, 1, 1, tzinfo=UTC))
LATE_ERA = (datetime(2010, 1, 1, tzinfo=UTC), datetime(2020, 1, 1, tzinfo=UTC))

DEFAULT_FOLDS = 4


class EraError(ValueError):
    """An era study could not be constructed as specified."""


def binary_era_labels(
    instants: Sequence[datetime],
) -> tuple[list[datetime], list[str]]:
    """Return instants falling in either era, with their labels."""
    kept: list[datetime] = []
    labels: list[str] = []

    for instant in instants:
        if EARLY_ERA[0] <= instant < EARLY_ERA[1]:
            kept.append(instant)
            labels.append("early")
        elif LATE_ERA[0] <= instant < LATE_ERA[1]:
            kept.append(instant)
            labels.append("late")

    return kept, labels


def decade_labels(instants: Sequence[datetime]) -> list[str]:
    """Return a decade label per instant, for the multi-era task."""
    return [f"{instant.year // 10 * 10}s" for instant in instants]


def year_blocked_folds(
    instants: Sequence[datetime],
    labels: Sequence[str],
    folds: int = DEFAULT_FOLDS,
) -> list[list[int]]:
    """Assign indices to folds so that no calendar year spans a split.

    Years are chunked contiguously *within* each label, so every fold holds
    every label while adjacent timestamps stay on the same side of the
    split. Random splitting would let two instants a day apart -- with
    effectively identical Saturn and Jupiter state -- land in train and test,
    which is precisely the leakage being measured.
    """
    if folds < 2:
        raise EraError("Blocked validation needs at least two folds.")

    by_label: dict[str, dict[int, list[int]]] = {}

    for index, (instant, label) in enumerate(zip(instants, labels)):
        by_label.setdefault(label, {}).setdefault(instant.year, []).append(
            index
        )

    assigned: list[list[int]] = [[] for _ in range(folds)]

    for years in by_label.values():
        ordered = sorted(years)
        chunks = np.array_split(np.array(ordered, dtype=int), folds)

        for fold, chunk in enumerate(chunks):
            for year in chunk.tolist():
                assigned[fold].extend(years[year])

    return assigned


def balanced_accuracy(
    truth: Sequence[str], predicted: Sequence[str]
) -> float:
    """Return accuracy averaged over classes, so imbalance cannot flatter."""
    if not truth:
        return float("nan")

    per_class: dict[str, list[int]] = {}

    for actual, guess in zip(truth, predicted):
        per_class.setdefault(actual, []).append(1 if actual == guess else 0)

    return float(np.mean([np.mean(hits) for hits in per_class.values()]))


def _majority_map(
    signatures: Sequence[Hashable], labels: Sequence[str]
) -> tuple[dict[Hashable, str], str]:
    """Learn the most common label per signature, plus a fallback."""
    grouped: dict[Hashable, Counter] = {}

    for signature, label in zip(signatures, labels):
        grouped.setdefault(signature, Counter())[label] += 1

    fallback = Counter(labels).most_common(1)[0][0]

    return (
        {
            signature: counts.most_common(1)[0][0]
            for signature, counts in grouped.items()
        },
        fallback,
    )


def blocked_accuracy(
    signatures: Sequence[Hashable],
    instants: Sequence[datetime],
    labels: Sequence[str],
    folds: int = DEFAULT_FOLDS,
) -> dict[str, Any]:
    """Return year-blocked predictive accuracy for one encoding.

    The classifier is deliberately the simplest one that can express the
    hypothesis -- majority label per signature class -- because the question
    is whether the *representation* separates eras, not whether a flexible
    model can be fitted on top of it.
    """
    assignment = year_blocked_folds(instants, labels, folds)

    scores: list[float] = []
    unseen: list[float] = []

    for held_out in assignment:
        if not held_out:
            continue

        train = [
            index
            for fold in assignment
            for index in fold
            if fold is not held_out
        ]

        if not train:
            continue

        mapping, fallback = _majority_map(
            [signatures[i] for i in train], [labels[i] for i in train]
        )

        predicted = [
            mapping.get(signatures[i], fallback) for i in held_out
        ]
        truth = [labels[i] for i in held_out]

        scores.append(balanced_accuracy(truth, predicted))
        unseen.append(
            float(
                np.mean(
                    [signatures[i] not in mapping for i in held_out]
                )
            )
        )

    if not scores:
        return {"balanced_accuracy": float("nan"), "folds": 0}

    return {
        "balanced_accuracy": float(np.mean(scores)),
        "fold_scores": [float(value) for value in scores],
        "folds": len(scores),
        # A class never seen in training cannot inform a prediction, so a
        # high rate means the accuracy reflects the fallback, not the
        # representation.
        "unseen_class_rate": float(np.mean(unseen)),
    }


def era_association(
    signatures: Sequence[Hashable],
    instants: Sequence[datetime],
    labels: Sequence[str],
    *,
    folds: int = DEFAULT_FOLDS,
    permutations: int = 200,
    seed: int = 20260801,
) -> dict[str, Any]:
    """Measure one encoding's era dependence, both ways.

    Mutual information answers "is there population association"; blocked
    accuracy answers "is it usable in a finite sample". They can disagree,
    and the disagreement is itself informative.
    """
    observed_mi = mutual_information(signatures, labels)
    accuracy = blocked_accuracy(signatures, instants, labels, folds)

    # The null permutes labels within year blocks rather than freely, so the
    # null preserves the temporal autocorrelation that makes era prediction
    # easy in the first place.
    rng = np.random.default_rng(seed)
    years = np.array([instant.year for instant in instants])
    unique_years = np.unique(years)

    null_mi: list[float] = []

    for _ in range(permutations):
        shuffled_years = rng.permutation(unique_years)
        remap = dict(zip(unique_years.tolist(), shuffled_years.tolist()))
        by_year: dict[int, list[str]] = {}

        for year, label in zip(years.tolist(), labels):
            by_year.setdefault(year, []).append(label)

        permuted: list[str] = []
        cursors: dict[int, int] = {}

        for year in years.tolist():
            source = remap[year]
            pool = by_year[source]
            position = cursors.get(source, 0) % len(pool)
            cursors[source] = position + 1
            permuted.append(pool[position])

        null_mi.append(mutual_information(signatures, permuted))

    null_array = np.array(null_mi, dtype=np.float64)
    extreme = int((null_array >= observed_mi).sum())

    return {
        "mutual_information_nats": observed_mi,
        "null_mean_mi": float(null_array.mean()),
        "mi_p_value": (extreme + 1) / (permutations + 1),
        "permutations": permutations,
        **accuracy,
    }


def era_decomposition(
    encodings: Sequence[dict[str, tuple[Hashable, ...]]],
    instants: Sequence[datetime],
    labels: Sequence[str],
    *,
    folds: int = DEFAULT_FOLDS,
    permutations: int = 200,
    seed: int = 20260801,
) -> dict[str, Any]:
    """Attribute era association to each operation in the pipeline."""
    results = {
        name: era_association(
            [item[name] for item in encodings],
            instants,
            labels,
            folds=folds,
            permutations=permutations,
            seed=seed,
        )
        for name in ("B3", "B3D", "B2")
    }

    mi = {name: block["mutual_information_nats"] for name, block in results.items()}
    accuracy = {
        name: block["balanced_accuracy"] for name, block in results.items()
    }

    # A coarsening cannot add population information, so a rise here is a
    # harness fault or a finite-sample estimator artifact, never a finding.
    translation_added_information = mi["B2"] > mi["B3D"] + 1e-9

    return {
        "encodings": results,
        "era_information_removed_by_dedup": mi["B3"] - mi["B3D"],
        "era_information_removed_by_translation": mi["B3D"] - mi["B2"],
        "accuracy_change_from_dedup": accuracy["B3D"] - accuracy["B3"],
        "accuracy_change_from_translation": accuracy["B2"] - accuracy["B3D"],
        "translation_added_information": translation_added_information,
        # The distinction that must not be collapsed: coarsening can raise
        # finite-sample accuracy purely by regularizing, while removing
        # information.
        "compression_regularization_effect": (
            accuracy["B2"] > accuracy["B3D"] and mi["B2"] < mi["B3D"]
        ),
        "interpretation": (
            "B2 is a coarsening of B3D, so mutual information cannot rise. "
            "If blocked accuracy rises while mutual information falls, that "
            "is regularization from merging classes, not newly created "
            "temporal information."
        ),
    }
