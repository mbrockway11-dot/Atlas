"""What makes real names more similar than synthetic ones of the same shape?

The perturbation study found that a length-matched random name scores 0.967
against its original, above the 0.959 corpus mean. That comparison is
confounded: length matching alone raises the score, and the corpus mean
averages over all length differences. The honest control is **real name pairs
drawn from the same length stratum**.

This experiment holds gross morphology fixed and varies only how much real
linguistic structure a name retains:

    identical                 the ceiling
    real pair, same stratum   what real unrelated names score
    character shuffle         same letters, order destroyed
    letter-frequency match    same letter distribution, different letters
    length-matched random     same length and token shape only
    alphabet-frequency match  English letter frequencies, matched length

If synthetic names score the same as real ones from the same stratum, then
beyond gross morphology the encoding carries little, and identity claims
must narrow accordingly.

    python scripts/run_synthetic_name_decomposition.py
"""

from __future__ import annotations

import argparse
from collections import Counter
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
    name_strata,
    vector_for_name,
)
from atlas.validation.metrics import METRICS_BY_NAME, separation
from atlas.validation.models import load_config
from atlas.validation.perturbations import (
    length_matched_random,
    shuffle_characters,
)


# Rough English letter frequencies, for the frequency-matched synthetic arm.
ENGLISH_FREQUENCIES = {
    "a": 8.2, "b": 1.5, "c": 2.8, "d": 4.3, "e": 12.7, "f": 2.2,
    "g": 2.0, "h": 6.1, "i": 7.0, "j": 0.15, "k": 0.77, "l": 4.0,
    "m": 2.4, "n": 6.7, "o": 7.5, "p": 1.9, "q": 0.095, "r": 6.0,
    "s": 6.3, "t": 9.1, "u": 2.8, "v": 0.98, "w": 2.4, "x": 0.15,
    "y": 2.0, "z": 0.074,
}


def letter_frequency_match(name: str, rng: np.random.Generator) -> str:
    """Return a name drawn from *this name's own* letter distribution.

    Preserves the letter multiset's proportions but not their order or
    identity-bearing arrangement.
    """
    letters = [ch.lower() for ch in name if ch.isalpha()]

    if not letters:
        return name

    counts = Counter(letters)
    alphabet = list(counts)
    weights = np.array([counts[ch] for ch in alphabet], dtype=np.float64)
    weights /= weights.sum()

    return "".join(
        " "
        if ch == " "
        else str(rng.choice(alphabet, p=weights))
        for ch in name
    )


def alphabet_frequency_match(name: str, rng: np.random.Generator) -> str:
    """Return a name drawn from general English letter frequencies."""
    alphabet = list(ENGLISH_FREQUENCIES)
    weights = np.array(
        [ENGLISH_FREQUENCIES[ch] for ch in alphabet], dtype=np.float64
    )
    weights /= weights.sum()

    return "".join(
        " " if ch == " " else str(rng.choice(alphabet, p=weights))
        for ch in name
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Decompose the synthetic-name similarity floor."
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
        / "identity_synthetic_decomposition_v1",
    )
    parser.add_argument(
        "--sample-names",
        type=int,
        default=100,
        help="Names to decompose (default: 100).",
    )
    parser.add_argument(
        "--metric",
        default="cosine",
        choices=sorted(METRICS_BY_NAME),
        help="Geometry to report in (default: cosine).",
    )
    return parser


def main() -> int:
    """Run the synthetic-name decomposition."""
    args = build_parser().parse_args()
    config = load_config(args.config)
    started = perf_counter()

    corpus = load_corpus_matrix(normalization_mode=config.normalization_mode)
    layout = build_feature_layout()
    strata = name_strata(corpus.profile_names)
    lengths = strata["character_length"]
    tokens = strata["token_count"]

    rng = np.random.default_rng(config.random_seed)
    sample_size = min(args.sample_names, corpus.profile_count)
    chosen = rng.choice(corpus.profile_count, size=sample_size, replace=False)

    arms: dict[str, list[float]] = {
        "real_pair_same_stratum": [],
        "character_shuffle": [],
        "letter_frequency_match": [],
        "length_matched_random": [],
        "alphabet_frequency_match": [],
    }

    for position in chosen:
        index = int(position)
        name = corpus.profile_names[index]
        original = vector_for_name(name, layout=layout)

        if original is None:
            continue

        draw = np.random.default_rng(abs(hash(name)) % (2**32))

        # The honest control: a different REAL name with the same token
        # count and near-identical length.
        candidates = np.flatnonzero(
            (tokens == tokens[index])
            & (np.abs(lengths.astype(int) - int(lengths[index])) <= 1)
        )
        candidates = candidates[candidates != index]

        if candidates.size:
            partner = int(draw.choice(candidates))
            arms["real_pair_same_stratum"].append(
                cosine(original, corpus.matrix[partner])
            )

        synthetics = {
            "character_shuffle": shuffle_characters(name, rng=draw),
            "letter_frequency_match": letter_frequency_match(name, draw),
            "length_matched_random": length_matched_random(name, rng=draw),
            "alphabet_frequency_match": alphabet_frequency_match(name, draw),
        }

        for label, synthetic in synthetics.items():
            vector = vector_for_name(synthetic, layout=layout)

            if vector is not None:
                arms[label].append(cosine(original, vector))

    summaries: dict[str, dict] = {}

    for label, values in arms.items():
        if not values:
            continue

        array = np.array(values, dtype=np.float64)
        summaries[label] = {
            "samples": int(array.size),
            "mean": float(array.mean()),
            "median": float(np.median(array)),
            "stddev": float(array.std()),
            "minimum": float(array.min()),
            "maximum": float(array.max()),
        }

    # The decisive comparison: does a real same-stratum name score higher
    # than a synthetic with the same gross morphology?
    comparisons: dict[str, dict] = {}
    real = np.array(arms["real_pair_same_stratum"], dtype=np.float64)

    for label in (
        "character_shuffle",
        "letter_frequency_match",
        "length_matched_random",
        "alphabet_frequency_match",
    ):
        synthetic = np.array(arms[label], dtype=np.float64)

        if real.size and synthetic.size:
            # Bootstrap the difference in means. A confidence interval that
            # straddles zero is the whole answer here: it says the two arms
            # are indistinguishable, which is a result, not a failure.
            boot = np.random.default_rng(config.random_seed)
            differences = np.empty(10_000, dtype=np.float64)

            for iteration in range(differences.size):
                differences[iteration] = (
                    real[boot.integers(0, real.size, real.size)].mean()
                    - synthetic[
                        boot.integers(0, synthetic.size, synthetic.size)
                    ].mean()
                )

            lower = float(np.percentile(differences, 2.5))
            upper = float(np.percentile(differences, 97.5))

            comparisons[f"real_vs_{label}"] = {
                **separation(real, synthetic),
                "real_mean": float(real.mean()),
                "synthetic_mean": float(synthetic.mean()),
                "difference": float(real.mean() - synthetic.mean()),
                "bootstrap_ci_95": [lower, upper],
                "ci_includes_zero": bool(lower <= 0.0 <= upper),
                "bootstrap_iterations": int(differences.size),
            }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        {
            "metric": args.metric,
            "arms": summaries,
            "comparisons": comparisons,
            "interpretation": (
                "Each synthetic arm holds gross morphology fixed and removes "
                "a different kind of real linguistic structure. Where a "
                "synthetic arm matches the real same-stratum arm, that kind "
                "of structure is not contributing to the score."
            ),
        },
        args.output_dir / "synthetic-decomposition.json",
    )
    write_json(
        build_provenance(
            config,
            profile_count=sample_size,
            pair_count=sum(len(v) for v in arms.values()),
            block_size=int(config.options.get("block_size", 256)),
        ).to_dict(),
        args.output_dir / "provenance.json",
    )

    print(
        json.dumps(
            {
                "success": True,
                "arms": {
                    label: {
                        "n": body["samples"],
                        "mean": round(body["mean"], 5),
                        "sd": round(body["stddev"], 5),
                    }
                    for label, body in summaries.items()
                },
                "comparisons": {
                    label: {
                        "difference": round(body["difference"], 5),
                        "ci95": [
                            round(body["bootstrap_ci_95"][0], 5),
                            round(body["bootstrap_ci_95"][1], 5),
                        ],
                        "ci_includes_zero": body["ci_includes_zero"],
                        "cohens_d": round(body["cohens_d"], 3),
                        "p_superior": round(body["probability_superior"], 3),
                    }
                    for label, body in comparisons.items()
                },
                "output_dir": str(args.output_dir),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
