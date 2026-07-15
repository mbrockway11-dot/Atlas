"""Build Morphology Portfolio Adapter V1 outputs."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.portfolio_adapter import (
    MorphologyPortfolioAdapterConfig,
    build_morphology_portfolio_targets,
    load_morphology_decisions,
    write_morphology_portfolio_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--decisions",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_portfolio"
        ),
    )

    parser.add_argument(
        "--maximum-total-exposure",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--maximum-asset-exposure",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--maximum-positions",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--minimum-confidence",
        type=float,
        default=0.70,
    )

    args = parser.parse_args()

    config = MorphologyPortfolioAdapterConfig(
        maximum_total_exposure=(
            args.maximum_total_exposure
        ),
        maximum_asset_exposure=(
            args.maximum_asset_exposure
        ),
        maximum_positions=(
            args.maximum_positions
        ),
        minimum_confidence=(
            args.minimum_confidence
        ),
        research_only=True,
        require_manual_approval=True,
    )

    decisions = load_morphology_decisions(
        args.decisions
    )

    targets = build_morphology_portfolio_targets(
        decisions,
        config=config,
    )

    outputs = write_morphology_portfolio_outputs(
        targets=targets,
        config=config,
        output_dir=args.output,
    )

    asset_targets = targets[
        ~targets["asset"].eq("CASH")
    ]

    print(
        "=== MORPHOLOGY PORTFOLIO ADAPTER V1 ==="
    )

    print(
        f"input_decisions={len(decisions)}"
    )

    print(
        f"asset_targets={len(asset_targets)}"
    )

    print(
        "gross_exposure="
        f"{asset_targets['target_weight'].abs().sum():.6f}"
    )

    for row in targets.itertuples(
        index=False
    ):
        print(
            f"{row.asset}: "
            f"direction={row.direction} "
            f"target_weight={row.target_weight:.6f} "
            f"confidence={row.confidence:.4f} "
            f"approval={row.requires_manual_approval} "
            f"live_authorized={row.live_authorized}"
        )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
