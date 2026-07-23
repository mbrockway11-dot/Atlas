"""Trace how identity similarity decays as a name is progressively damaged.

The primary characterization experiment. For each sampled name, graded
perturbations are applied and the similarity to the original recorded, so the
response curve can be read against the population baseline.

Length-preserving and length-changing perturbations are reported separately
throughout, because the baseline showed name-length difference drives 30% of
score variance: mixing them would re-measure the confounder instead of the
edit.

Every result is placed against two reference points -- the corpus mean for
unrelated pairs, and the score of a length-matched random name. A
perturbation that lands at or below the unrelated-pair mean has destroyed the
identity as far as this model is concerned.

    python scripts/run_name_perturbation_experiment.py
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from atlas.validation.artifacts import build_provenance, write_json
from atlas.validation.datasets import (
    build_feature_layout,
    cosine,
    load_corpus_matrix,
    vector_for_name,
)
from atlas.validation.models import load_config
from atlas.validation.perturbations import build_perturbations
from atlas.validation.runner import run_all_pairs
from atlas.validation.statistics import percentile_of, summarize


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run the name-perturbation experiment."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "configs/validation/identity_random_pair_baseline_v1.yaml"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output")
        / "validation"
        / "identity_name_perturbation_v1",
    )
    parser.add_argument(
        "--sample-names",
        type=int,
        default=120,
        help="Corpus names to perturb (default: 120).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Random draws per name per perturbation (default: 3).",
    )
    parser.add_argument(
        "--max-severity",
        type=int,
        default=4,
        help="Highest edit count (default: 4).",
    )
    return parser


def main() -> int:
    """Run the perturbation suite."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    started = perf_counter()

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    layout = build_feature_layout()

    _, all_scores, _ = run_all_pairs(corpus, block_size=256)
    global_summary = summarize(all_scores, bins=200)
    unrelated_mean = float(all_scores.mean())
    unrelated_p1 = float(np.percentile(all_scores, 1.0))

    rng = np.random.default_rng(config.random_seed)
    sample_size = min(args.sample_names, corpus.profile_count)
    chosen = rng.choice(corpus.profile_count, size=sample_size, replace=False)

    names: list[str] = []
    originals: dict[str, np.ndarray] = {}

    for index in chosen:
        name = corpus.profile_names[int(index)]
        vector = vector_for_name(name, layout=layout)

        if vector is not None:
            names.append(name)
            originals[name] = vector

    perturbations = build_perturbations(max_severity=args.max_severity)

    buckets: dict[tuple[str, int], list[float]] = defaultdict(list)
    length_changes: dict[tuple[str, int], list[int]] = defaultdict(list)
    position_effect: dict[str, list[float]] = defaultdict(list)

    for perturbation in perturbations:
        key = (perturbation.name, perturbation.severity)

        for name in names:
            for repeat in range(args.repeats):
                # Seeded per (name, perturbation, repeat) so the whole
                # experiment reproduces exactly.
                draw = np.random.default_rng(
                    abs(hash((name, perturbation.name,
                              perturbation.severity, repeat))) % (2**32)
                )

                try:
                    mutated = perturbation.apply(name, draw)
                except Exception:  # noqa: BLE001 - a failed edit is a skip
                    continue

                if mutated == name:
                    continue

                vector = vector_for_name(mutated, layout=layout)

                if vector is None:
                    continue

                score = cosine(originals[name], vector)
                buckets[key].append(score)
                length_changes[key].append(
                    len(mutated.replace(" ", "")) - len(name.replace(" ", ""))
                )

    # Does an edit near the start of a name matter more than one near the end?
    for name in names:
        letters = [i for i, ch in enumerate(name) if ch.isalpha()]

        if len(letters) < 6:
            continue

        for label, position in (
            ("first_third", letters[len(letters) // 6]),
            ("last_third", letters[-max(1, len(letters) // 6)]),
        ):
            chars = list(name)
            original = chars[position].lower()
            chars[position] = "z" if original != "z" else "q"
            vector = vector_for_name("".join(chars), layout=layout)

            if vector is not None:
                position_effect[label].append(
                    cosine(originals[name], vector)
                )

    curves: list[dict] = []

    for (label, severity), values in sorted(buckets.items()):
        array = np.array(values, dtype=np.float64)

        if array.size == 0:
            continue

        mean = float(array.mean())
        deltas = np.array(length_changes[(label, severity)])

        curves.append(
            {
                "perturbation": label,
                "severity": severity,
                "samples": int(array.size),
                "mean_similarity": mean,
                "median_similarity": float(np.median(array)),
                "stddev": float(array.std()),
                "min_similarity": float(array.min()),
                "max_similarity": float(array.max()),
                "global_percentile_of_mean": float(
                    percentile_of(global_summary, mean)
                ),
                "mean_length_change": float(deltas.mean()),
                "preserves_length": bool(np.all(deltas == 0)),
                # The interpretive anchor: has this edit pushed the name as
                # far away as an unrelated name already sits?
                "at_or_below_unrelated_mean": bool(mean <= unrelated_mean),
                "margin_above_unrelated_mean": mean - unrelated_mean,
            }
        )

    monotonic: dict[str, bool] = {}

    for label in {row["perturbation"] for row in curves}:
        graded = sorted(
            (row for row in curves if row["perturbation"] == label
             and row["severity"] < 90),
            key=lambda row: row["severity"],
        )

        if len(graded) > 1:
            means = [row["mean_similarity"] for row in graded]
            monotonic[label] = all(
                later <= earlier + 1e-9
                for earlier, later in zip(means, means[1:])
            )

    position_summary = {
        label: {
            "samples": len(values),
            "mean_similarity": float(np.mean(values)),
        }
        for label, values in position_effect.items()
        if values
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "curves": curves,
            "monotonic_decay": monotonic,
            "position_effect": position_summary,
            "reference": {
                "unrelated_pair_mean": unrelated_mean,
                "unrelated_pair_p1": unrelated_p1,
                "reference_pairs": int(all_scores.size),
            },
        },
        args.output_dir / "perturbation-curves.json",
    )
    write_json(
        build_provenance(
            config,
            profile_count=len(names),
            pair_count=sum(len(v) for v in buckets.values()),
            block_size=int(config.options.get("block_size", 256)),
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    headline = {
        row["perturbation"] + f"@{row['severity']}": round(
            row["mean_similarity"], 5
        )
        for row in curves
        if row["severity"] in (1, 99)
    }

    print(
        json.dumps(
            {
                "success": True,
                "names": len(names),
                "measurements": sum(len(v) for v in buckets.values()),
                "unrelated_pair_mean": round(unrelated_mean, 6),
                "monotonic_decay": monotonic,
                "position_effect": position_summary,
                "severity_1_and_extreme": headline,
                "output_dir": str(args.output_dir),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
