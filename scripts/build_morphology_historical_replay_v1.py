"""Run Morphology Historical Replay Engine V1."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.historical_replay import (
    MorphologyHistoricalReplayConfig,
    assemble_historical_morphology_state,
    build_morphology_historical_replay,
    load_replay_calendar,
    load_replay_evolution,
    load_replay_field,
    load_replay_trajectories,
    write_morphology_historical_replay_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--calendar",
        required=True,
    )

    parser.add_argument(
        "--field",
        required=True,
    )

    parser.add_argument(
        "--evolution",
        required=True,
    )

    parser.add_argument(
        "--trajectories",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_historical_replay"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=[
            "shadow",
            "strict",
        ],
        default="shadow",
    )

    parser.add_argument(
        "--maximum-asof-age-bars",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--bar-minutes",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--minimum-field-predictability",
        type=float,
        default=0.25,
    )

    parser.add_argument(
        "--supportive-field-predictability",
        type=float,
        default=0.55,
    )

    parser.add_argument(
        "--supportive-confidence",
        type=float,
        default=0.65,
    )

    parser.add_argument(
        "--neutral-confidence",
        type=float,
        default=0.40,
    )

    args = parser.parse_args()

    config = MorphologyHistoricalReplayConfig(
        mode=args.mode,
        maximum_asof_age_bars=(
            args.maximum_asof_age_bars
        ),
        bar_minutes=args.bar_minutes,
        minimum_field_predictability=(
            args.minimum_field_predictability
        ),
        supportive_field_predictability=(
            args.supportive_field_predictability
        ),
        supportive_confidence=(
            args.supportive_confidence
        ),
        neutral_confidence=(
            args.neutral_confidence
        ),
    )

    calendar = load_replay_calendar(
        args.calendar
    )

    field = load_replay_field(
        args.field
    )

    evolution = load_replay_evolution(
        args.evolution
    )

    trajectories = load_replay_trajectories(
        args.trajectories
    )

    assembled = (
        assemble_historical_morphology_state(
            calendar=calendar,
            field=field,
            evolution=evolution,
            trajectories=trajectories,
            config=config,
        )
    )

    decisions = (
        build_morphology_historical_replay(
            assembled_state=assembled,
            config=config,
        )
    )

    outputs = (
        write_morphology_historical_replay_outputs(
            decisions=decisions,
            config=config,
            output_dir=args.output,
        )
    )

    print(
        "=== MORPHOLOGY HISTORICAL REPLAY V1 ==="
    )

    print(
        f"calendar_rows={len(calendar)}"
    )

    print(
        f"assembled_rows={len(assembled)}"
    )

    print(
        f"decision_rows={len(decisions)}"
    )

    if not decisions.empty:
        counts = (
            decisions[
                "morphology_state"
            ]
            .value_counts()
            .sort_index()
        )

        for state, count in counts.items():
            print(
                f"{state.lower()}={count}"
            )

        print(
            "entry_ready="
            f"{int(decisions['entry_ready'].astype(bool).sum())}"
        )

        for row in (
            decisions.tail(20)
            .itertuples(index=False)
        ):
            print(
                f"{row.timestamp} "
                f"{row.asset}: "
                f"calendar={row.calendar_action} "
                f"morphology={row.morphology_state} "
                f"action={row.action} "
                f"direction={row.direction} "
                f"confidence={row.confidence:.4f}"
            )

    for name, path in outputs.items():
        print(
            f"{name}={path}"
        )


if __name__ == "__main__":
    main()
