"""Run one validation experiment from a versioned configuration.

    python scripts/run_validation_experiment.py \
        configs/validation/identity_random_pair_baseline_v1.yaml

The config is validated before any work starts, so a domain/input mismatch
fails immediately rather than after producing a meaningless number.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from atlas.validation.artifacts import (
    build_provenance,
    experiment_dir,
    write_json,
    write_pairs,
)
from atlas.validation.datasets import load_corpus_matrix, name_strata
from atlas.validation.models import (
    ExperimentConfigError,
    ExperimentKind,
    load_config,
)
from atlas.validation.reporting import render_baseline_report
from atlas.validation.runner import (
    Checkpoint,
    compute_group_scores,
    expected_block_count,
    load_checkpoint,
    run_all_pairs,
    save_checkpoint,
)
from atlas.validation.statistics import summarize, top_and_bottom


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run one Atlas validation experiment."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the experiment configuration (YAML or JSON).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output") / "validation",
        metavar="PATH",
        help="Where experiment directories are written.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from an existing checkpoint if one is present.",
    )
    parser.add_argument(
        "--limit-profiles",
        type=int,
        default=None,
        metavar="N",
        help="Use only the first N profiles. For smoke tests.",
    )
    return parser


def _stratify(
    scores: np.ndarray,
    pair_indices: np.ndarray,
    strata: dict[str, np.ndarray],
    profile_names: tuple[str, ...],
) -> dict[str, list[dict[str, object]]]:
    """Return mean scores grouped by name-shape strata."""
    left = pair_indices[:, 0]
    right = pair_indices[:, 1]

    out: dict[str, list[dict[str, object]]] = {}

    # Token-count combination, e.g. "2+3" for a two-token and three-token name.
    tokens = strata["token_count"]
    combo = np.char.add(
        np.char.add(
            np.minimum(tokens[left], tokens[right]).astype(str), "+"
        ),
        np.maximum(tokens[left], tokens[right]).astype(str),
    )
    out["Token-count combination"] = _group_rows(combo, scores, limit=12)

    # Absolute difference in name length, bucketed.
    lengths = strata["character_length"]
    delta = np.abs(lengths[left] - lengths[right])
    buckets = np.select(
        [delta <= 2, delta <= 5, delta <= 10, delta <= 20],
        ["0-2", "3-5", "6-10", "11-20"],
        default="21+",
    )
    out["Name-length difference"] = _group_rows(buckets, scores, limit=12)

    # Same vs different script family, approximated by ASCII-ness.
    ascii_flags = strata["is_ascii"]
    same_script = np.where(
        ascii_flags[left] == ascii_flags[right],
        "same script family",
        "different script family",
    )
    out["Script family"] = _group_rows(same_script, scores, limit=4)

    return out


def _group_rows(
    labels: np.ndarray,
    scores: np.ndarray,
    *,
    limit: int,
) -> list[dict[str, object]]:
    """Return per-stratum count/mean/stddev, largest strata first."""
    unique, inverse, counts = np.unique(
        labels, return_inverse=True, return_counts=True
    )

    rows: list[dict[str, object]] = []

    for index, label in enumerate(unique):
        selected = scores[inverse == index]

        rows.append(
            {
                "stratum": str(label),
                "count": int(counts[index]),
                "mean": float(selected.mean()),
                "stddev": float(selected.std()),
            }
        )

    rows.sort(key=lambda row: row["count"], reverse=True)

    return rows[:limit]


def _confounders(
    scores: np.ndarray,
    pair_indices: np.ndarray,
    strata: dict[str, np.ndarray],
) -> list[dict[str, object]]:
    """Return correlations between name shape and score, strongest first.

    A cohort study is only interpretable once these are known: if similarity
    tracks name length, then any group whose names happen to be similarly
    sized will score high for reasons having nothing to do with the group.
    """
    left = pair_indices[:, 0]
    right = pair_indices[:, 1]

    lengths = strata["character_length"].astype(float)
    tokens = strata["token_count"].astype(float)

    candidates = {
        "absolute name-length difference": np.abs(
            lengths[left] - lengths[right]
        ),
        "absolute token-count difference": np.abs(
            tokens[left] - tokens[right]
        ),
        "mean name length": (lengths[left] + lengths[right]) / 2.0,
        "mean token count": (tokens[left] + tokens[right]) / 2.0,
    }

    rows: list[dict[str, object]] = []

    for label, values in candidates.items():
        if values.std() == 0:
            continue

        correlation = float(np.corrcoef(values, scores)[0, 1])

        rows.append(
            {
                "variable": label,
                "pearson_r": correlation,
                "variance_explained": correlation**2,
            }
        )

    rows.sort(key=lambda row: abs(row["pearson_r"]), reverse=True)

    return rows


def main() -> int:
    """Execute one experiment."""
    args = build_parser().parse_args()

    try:
        config = load_config(args.config)
    except ExperimentConfigError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    if config.kind is not ExperimentKind.ALL_PAIRS_BASELINE:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        f"Runner does not yet implement kind "
                        f"{config.kind.value!r}."
                    ),
                },
                indent=2,
            )
        )
        return 2

    options = config.options
    block_size = int(options.get("block_size", 256))
    destination = experiment_dir(config.experiment_id, root=args.output_root)
    destination.mkdir(parents=True, exist_ok=True)
    checkpoint_path = destination / "checkpoint.json"

    started = perf_counter()

    corpus = load_corpus_matrix(
        normalization_mode=config.normalization_mode,
    )

    if args.limit_profiles is not None:
        keys = corpus.profile_keys[: args.limit_profiles]
        corpus = load_corpus_matrix(
            normalization_mode=config.normalization_mode,
            profile_keys=keys,
        )

    if corpus.profile_count < 2:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        "Need at least two compiled profiles. Run "
                        "scripts/compile_identity_vectors_batch.py."
                    ),
                },
                indent=2,
            )
        )
        return 1

    total_blocks = expected_block_count(corpus.profile_count, block_size)
    fingerprint = f"{corpus.profile_count}:{config.normalization_mode}"

    start_block = 0

    if args.resume:
        existing = load_checkpoint(checkpoint_path)

        if (
            existing is not None
            and existing.corpus_fingerprint == fingerprint
            and existing.block_size == block_size
        ):
            start_block = existing.completed_blocks

    pair_indices, scores, elapsed = run_all_pairs(
        corpus,
        block_size=block_size,
        start_block=start_block,
        on_block=lambda index, block: save_checkpoint(
            Checkpoint(
                experiment_id=config.experiment_id,
                corpus_fingerprint=fingerprint,
                block_size=block_size,
                completed_blocks=index + 1,
                total_blocks=total_blocks,
                pairs_written=int(block.pair_indices.shape[0]),
            ),
            checkpoint_path,
        ),
    )

    summary = summarize(
        scores,
        bins=int(options.get("histogram_bins", 100)),
    )

    extremes_raw = top_and_bottom(
        scores,
        pair_indices,
        limit=int(options.get("extremes_limit", 25)),
    )
    extremes = {
        key: [
            {
                "profile_a": corpus.profile_keys[a],
                "profile_b": corpus.profile_keys[b],
                "profile_a_name": corpus.profile_names[a],
                "profile_b_name": corpus.profile_names[b],
                "score": score,
            }
            for a, b, score in rows
        ]
        for key, rows in extremes_raw.items()
    }

    # Per-cipher and per-planet decomposition on a deterministic sample.
    sample_size = min(
        int(options.get("group_sample_size", 200_000)), scores.size
    )
    rng = np.random.default_rng(config.random_seed)
    sample = rng.choice(scores.size, size=sample_size, replace=False)
    sample.sort()

    group_scores = compute_group_scores(
        corpus, sample_pairs=pair_indices[sample]
    )
    group_summaries = {
        label: summarize(values, bins=40).to_dict()
        for label, values in group_scores.items()
    }

    profile_strata = name_strata(corpus.profile_names)

    strata = _stratify(
        scores, pair_indices, profile_strata, corpus.profile_names,
    )
    confounders = _confounders(scores, pair_indices, profile_strata)

    provenance = build_provenance(
        config,
        profile_count=corpus.profile_count,
        pair_count=int(scores.size),
        block_size=block_size,
    ).to_dict()

    exact_collisions = int(
        np.count_nonzero(scores >= 1.0 - 1e-12)
    )

    write_json(config.to_dict(), destination / "experiment.json")
    write_json(provenance, destination / "provenance.json")
    write_json(
        {
            **summary.to_dict(),
            "exact_collision_pairs": exact_collisions,
            "corpus": corpus.provenance(),
        },
        destination / "distribution.json",
    )
    write_json(
        {"percentiles": summary.percentiles},
        destination / "quantiles.json",
    )
    write_json(extremes, destination / "extremes.json")
    write_json(
        {"groups": group_summaries, "sample_size": sample_size},
        destination / "group_distributions.json",
    )
    write_json(
        {"strata": strata, "confounders": confounders},
        destination / "strata.json",
    )

    pairs_path = write_pairs(
        profile_keys=corpus.profile_keys,
        pair_indices=pair_indices,
        scores=scores,
        path=destination / "pairs.parquet",
        metric=config.metric,
        normalization_mode=config.normalization_mode,
    )

    total_elapsed = perf_counter() - started

    report = render_baseline_report(
        config=config,
        provenance=provenance,
        summary=summary,
        extremes=extremes,
        strata=strata,
        confounders=confounders,
        group_summaries=group_summaries,
        elapsed_seconds=total_elapsed,
        skipped=list(corpus.skipped),
    )
    (destination / "report.md").write_text(report, encoding="utf-8")

    save_checkpoint(
        Checkpoint(
            experiment_id=config.experiment_id,
            corpus_fingerprint=fingerprint,
            block_size=block_size,
            completed_blocks=total_blocks,
            total_blocks=total_blocks,
            pairs_written=int(scores.size),
        ),
        checkpoint_path,
    )

    print(
        json.dumps(
            {
                "success": True,
                "experiment_id": config.experiment_id,
                "domain": config.domain.value,
                "profile_count": corpus.profile_count,
                "pair_count": int(scores.size),
                "skipped_profiles": len(corpus.skipped),
                "mean": summary.mean,
                "median": summary.median,
                "stddev": summary.stddev,
                "minimum": summary.minimum,
                "maximum": summary.maximum,
                "exact_collision_pairs": exact_collisions,
                "distinct_scores": summary.distinct_scores,
                "strongest_confounder": confounders[0] if confounders else None,
                "compute_seconds": round(elapsed, 2),
                "total_seconds": round(total_elapsed, 2),
                "output_dir": str(destination),
                "pairs_bytes": pairs_path.stat().st_size,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
