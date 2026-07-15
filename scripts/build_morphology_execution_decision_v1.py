"""Build Morphology Execution Decision Engine V1 outputs."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.execution_decision import (
    MorphologyExecutionConfig,
    build_morphology_execution_decisions,
    load_latest_evolution,
    load_latest_field,
    load_latest_trajectories,
    load_validated_discovery,
    write_morphology_execution_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--trajectories",
        required=True,
    )

    parser.add_argument(
        "--evolution",
        required=True,
    )

    parser.add_argument(
        "--field",
        required=True,
    )

    parser.add_argument(
        "--discovery",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_execution"
        ),
    )

    parser.add_argument(
        "--maximum-target-exposure",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--minimum-entry-confidence",
        type=float,
        default=0.70,
    )

    parser.add_argument(
        "--allow-short",
        action="store_true",
    )

    args = parser.parse_args()

    config = MorphologyExecutionConfig(
        maximum_target_exposure=(
            args.maximum_target_exposure
        ),
        minimum_entry_confidence=(
            args.minimum_entry_confidence
        ),
        allow_short=(
            args.allow_short
        ),
        research_only=True,
    )

    decisions = (
        build_morphology_execution_decisions(
            latest_trajectories=(
                load_latest_trajectories(
                    args.trajectories
                )
            ),
            latest_evolution=(
                load_latest_evolution(
                    args.evolution
                )
            ),
            latest_field=(
                load_latest_field(
                    args.field
                )
            ),
            validated_discovery=(
                load_validated_discovery(
                    args.discovery
                )
            ),
            config=config,
        )
    )

    outputs = (
        write_morphology_execution_outputs(
            decisions=decisions,
            config=config,
            output_dir=args.output,
        )
    )

    print(
        "=== MORPHOLOGY EXECUTION DECISION V1 ==="
    )

    print(
        f"decisions={len(decisions)}"
    )

    print(
        "entry_ready="
        f"{int(decisions['entry_ready'].astype(bool).sum()) if not decisions.empty else 0}"
    )

    for row in decisions.itertuples(
        index=False
    ):
        print(
            f"{row.asset}: "
            f"action={row.action} "
            f"direction={row.direction} "
            f"confidence={row.confidence:.4f} "
            f"exposure={row.target_exposure:.4f} "
            f"entry_ready={row.entry_ready} "
            f"live_authorized={row.live_authorized}"
        )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
