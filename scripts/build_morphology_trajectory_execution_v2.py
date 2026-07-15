"""Run Morphology Trajectory Execution Engine V2."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.trajectory_execution_v2 import (
    TrajectoryExecutionConfig,
    build_trajectory_execution_signals,
    load_trajectory_observations,
    write_trajectory_execution_outputs,
)


def parse_horizons(value: str) -> tuple[int, ...]:
    return tuple(
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--observations",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_trajectory_execution_v2"
        ),
    )

    parser.add_argument(
        "--horizons",
        default="8,16,32",
    )

    parser.add_argument(
        "--minimum-observations",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--confidence-target",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--transaction-cost-bps",
        type=float,
        default=8.0,
    )

    parser.add_argument(
        "--risk-penalty",
        type=float,
        default=0.50,
    )

    parser.add_argument(
        "--minimum-win-rate",
        type=float,
        default=0.52,
    )

    parser.add_argument(
        "--minimum-profit-factor",
        type=float,
        default=1.05,
    )

    parser.add_argument(
        "--maximum-target-exposure",
        type=float,
        default=0.10,
    )

    args = parser.parse_args()

    config = TrajectoryExecutionConfig(
        horizons=parse_horizons(
            args.horizons
        ),
        minimum_observations=(
            args.minimum_observations
        ),
        confidence_target=(
            args.confidence_target
        ),
        transaction_cost_bps=(
            args.transaction_cost_bps
        ),
        risk_penalty=(
            args.risk_penalty
        ),
        minimum_win_rate=(
            args.minimum_win_rate
        ),
        minimum_profit_factor=(
            args.minimum_profit_factor
        ),
        maximum_target_exposure=(
            args.maximum_target_exposure
        ),
    )

    observations = load_trajectory_observations(
        args.observations,
        config=config,
    )

    signals = build_trajectory_execution_signals(
        observations,
        config=config,
    )

    outputs = write_trajectory_execution_outputs(
        signals=signals,
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY TRAJECTORY EXECUTION V2 ==="
    )

    print(
        f"observation_rows={len(observations)}"
    )

    print(
        f"signal_rows={len(signals)}"
    )

    print(
        "entry_rows="
        f"{int(signals['entry_ready'].astype(bool).sum()) if not signals.empty else 0}"
    )

    print(
        "long_entries="
        f"{int((signals['entry_ready'].astype(bool) & signals['recommended_direction'].eq('LONG')).sum()) if not signals.empty else 0}"
    )

    print(
        "short_entries="
        f"{int((signals['entry_ready'].astype(bool) & signals['recommended_direction'].eq('SHORT')).sum()) if not signals.empty else 0}"
    )

    print(
        "insufficient_evidence="
        f"{int(signals['recommended_action'].eq('INSUFFICIENT_EVIDENCE').sum()) if not signals.empty else 0}"
    )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
