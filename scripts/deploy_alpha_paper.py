"""Deploy the validated alpha config to paper execution.

Turns the two PROMOTED engines' current LONG signals (drawdown_recovery_v1 +
defensive_risk_off_v1, walk-forward-confirmed) into conviction-weighted target
allocations and runs one cycle through the provably paper-only shadow pipeline.

Long-only by construction: the portfolio bridge rejects negative weights, so the
defensive engine's short/hedge leg is NOT executed here -- a known limitation.
This deploys the long side of the validated ensemble; the hedge leg needs the
short-capable execution path.

    .venv/Scripts/python.exe scripts/deploy_alpha_paper.py --initial-cash 10000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from atlas.investment.execution.shadow_pipeline import run_shadow_pipeline

PROMOTED = ("drawdown_recovery_v1", "defensive_risk_off_v1")
LATEST = Path("output/investment_alpha_engines/alpha_engine_latest.csv")
TARGETS_OUT = Path("output/investment_alpha_portfolio/promoted_engine_targets.json")


def priced_universe(snapshot_path: Path) -> set[str]:
    """Assets the market snapshot can price (targets must be a subset)."""
    if not snapshot_path.exists():
        return set()
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assets: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("asset", "symbol", "product_id") and isinstance(value, str):
                    assets.add(value.strip().upper())
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return assets


def build_targets(
    latest_csv: Path, *, invested: float, max_weight: float, universe: set[str]
) -> list[dict]:
    signals = pd.read_csv(latest_csv)
    signals = signals[signals["engine_id"].isin(PROMOTED)]
    longs = signals[signals["direction"] == "LONG"].copy()
    if universe:
        longs = longs[longs["asset"].str.upper().isin(universe)]
    if longs.empty:
        return []
    # Equal engine weight: sum LONG conviction per asset across the two engines.
    conviction = longs.groupby("asset")["conviction"].sum()
    weights = conviction / conviction.sum() * invested
    weights = weights.clip(upper=max_weight)
    # Renormalize back toward the invested fraction after capping.
    if weights.sum() > 0:
        weights = weights / weights.sum() * min(invested, 1.0)
    return [
        {"asset": str(asset), "target_weight": round(float(w), 6)}
        for asset, w in weights.sort_values(ascending=False).items()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latest", default=str(LATEST))
    parser.add_argument(
        "--snapshot",
        default="output/investment_market_data/latest_market_snapshot.json",
    )
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    parser.add_argument("--invested-fraction", type=float, default=0.90)
    parser.add_argument("--max-weight", type=float, default=0.30)
    args = parser.parse_args(argv)

    universe = priced_universe(Path(args.snapshot))
    targets = build_targets(
        Path(args.latest),
        invested=args.invested_fraction,
        max_weight=args.max_weight,
        universe=universe,
    )
    if not targets:
        print("No LONG signals from the promoted engines.", file=sys.stderr)
        return 1

    print("Deploying validated config (promoted engines, long side):")
    for t in targets:
        print(f"  {t['asset']:10} target_weight {t['target_weight']:.3f}")
    print(f"  cash buffer ~{1 - sum(t['target_weight'] for t in targets):.3f}")

    TARGETS_OUT.parent.mkdir(parents=True, exist_ok=True)
    TARGETS_OUT.write_text(
        json.dumps(
            {
                "source": "promoted_alpha_engines",
                "engines": list(PROMOTED),
                "targets": targets,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"\nRunning one paper cycle through the shadow pipeline...")
    report = run_shadow_pipeline(
        targets_path=TARGETS_OUT,
        initial_cash=args.initial_cash,
        maximum_intents=None,
        resume=True,
        write_outputs=True,
    )

    print(
        f"\nstatus={report.get('status')}  success={report.get('success')}"
    )
    perf = report.get("performance", {})
    cyc = report.get("shadow_cycle", {})
    plan = report.get("intent_plan", {})
    print(f"  provenance: {report.get('provenance', {})}")
    print(f"  intents generated: {plan.get('generated_intents', plan.get('intent_count', '?'))}")
    print(f"  net liquidation: {perf.get('net_liquidation_value', perf.get('equity', '?'))}")
    if report.get("errors"):
        print(f"  errors: {report['errors']}")
    return 0 if report.get("success", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
