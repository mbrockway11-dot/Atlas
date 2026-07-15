"""Build V32-Morphology Ensemble Bridge V1 outputs."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.v32_ensemble import (
    V32MorphologyEnsembleConfig,
    build_v32_morphology_ensemble,
    load_morphology_execution_decisions,
    load_v32_combined_decisions,
    write_v32_morphology_ensemble_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--v32-decisions",
        required=True,
    )

    parser.add_argument(
        "--morphology-decisions",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_v32_morphology_ensemble"
        ),
    )

    parser.add_argument(
        "--maximum-target-exposure",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--neutral-exposure-multiplier",
        type=float,
        default=0.50,
    )

    parser.add_argument(
        "--unavailable-exposure-multiplier",
        type=float,
        default=0.25,
    )

    parser.add_argument(
        "--minimum-supportive-confidence",
        type=float,
        default=0.70,
    )

    args = parser.parse_args()

    config = V32MorphologyEnsembleConfig(
        maximum_target_exposure=(
            args.maximum_target_exposure
        ),
        neutral_exposure_multiplier=(
            args.neutral_exposure_multiplier
        ),
        unavailable_exposure_multiplier=(
            args.unavailable_exposure_multiplier
        ),
        minimum_supportive_confidence=(
            args.minimum_supportive_confidence
        ),
    )

    v32 = load_v32_combined_decisions(
        args.v32_decisions
    )

    morphology = (
        load_morphology_execution_decisions(
            args.morphology_decisions
        )
    )

    decisions = build_v32_morphology_ensemble(
        v32_decisions=v32,
        morphology_decisions=morphology,
        config=config,
    )

    outputs = (
        write_v32_morphology_ensemble_outputs(
            decisions=decisions,
            config=config,
            output_dir=args.output,
        )
    )

    print(
        "=== V32-MORPHOLOGY ENSEMBLE V1 ==="
    )

    print(
        f"decisions={len(decisions)}"
    )

    print(
        "v32_entries="
        f"{int(decisions['v32_entry_ready'].astype(bool).sum()) if not decisions.empty else 0}"
    )

    print(
        "ensemble_entries="
        f"{int(decisions['entry_ready'].astype(bool).sum()) if not decisions.empty else 0}"
    )

    print(
        "morphology_vetoes="
        f"{int(decisions['morphology_veto'].astype(bool).sum()) if not decisions.empty else 0}"
    )

    for row in (
        decisions.tail(20).itertuples(
            index=False
        )
    ):
        print(
            f"{row.timestamp} "
            f"{row.asset}: "
            f"v32={row.v32_action} "
            f"morphology={row.morphology_state} "
            f"ensemble={row.combined_action} "
            f"exposure={row.combined_target_exposure:.4f}"
        )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
