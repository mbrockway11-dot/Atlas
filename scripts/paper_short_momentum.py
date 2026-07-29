"""Cost-aware paper test of the SHORT-momentum rule, out-of-sample.

Read-only. Trains the momentum threshold on the teacher registry, then paper-
trades it on a DISJOINT cohort of teachers (scanned with --exclude-registry, so
none overlap training). Each qualifying short is mirrored at a fixed paper
notional; realized return comes from the leg's entry/exit price, and round-trip
Hyperliquid taker fees (and optional funding) are subtracted. The question is
blunt: after costs, does filtering shorts by "enter only when momentum is low"
beat taking every short -- and is it net positive at all?

The +$21/leg lift measured earlier was in teachers' raw dollars across wildly
different sizes; this works in notional-return space instead, which is size-
independent and is what a paper account actually earns.

    .venv/Scripts/python.exe scripts/paper_short_momentum.py --taker-fee-bps 4.5
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import numpy as np

from atlas.investment.hyper_copytrade.analysis_pipeline import features_by_teacher
from atlas.investment.hyper_copytrade.client import HyperliquidReadClient
from atlas.investment.hyper_copytrade.strategy import derive_entry_rule, momentum_of
from atlas.investment.hyper_copytrade.teacher_registry import (
    DEFAULT_REGISTRY_PATH,
    iter_teacher_legs,
    load_teacher_records,
)


def _bps(x: float) -> str:
    return f"{x * 10000:+.1f}bps"


def _load_features(client, path, lookback):
    legs = dict(iter_teacher_legs(load_teacher_records(Path(path))))
    feats = features_by_teacher(client, legs, range_lookback_hours=lookback, progress=True)
    return [f for v in feats.values() for f in v]


def _summarize(name, net_returns, notional):
    if not net_returns:
        print(f"  {name}: no trades")
        return
    arr = np.array(net_returns)
    rng = np.random.default_rng(0)
    boots = np.array([rng.choice(arr, arr.size, replace=True).mean() for _ in range(3000)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    print(
        f"  {name}: n={arr.size}  mean net {_bps(arr.mean())} "
        f"[95% CI {_bps(lo)}..{_bps(hi)}]  "
        f"total ${arr.sum() * notional:,.0f} @ ${notional:,.0f}/trade  "
        f"profitable {100 * (arr > 0).mean():.0f}%"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument(
        "--cohort", default="output/investment_hyper_copytrade/paper_cohort.jsonl"
    )
    parser.add_argument("--range-lookback-hours", type=float, default=24.0)
    parser.add_argument("--taker-fee-bps", type=float, default=4.5)
    parser.add_argument(
        "--funding-bps-per-day", type=float, default=0.0,
        help="Optional funding cost/day (shorts often RECEIVE funding; default 0).",
    )
    parser.add_argument("--notional", type=float, default=1000.0)
    args = parser.parse_args(argv)

    client = HyperliquidReadClient()
    print(f"[provenance] {client.provenance()}")

    print("\nTraining momentum threshold on registry...")
    train_feats = _load_features(client, args.train_registry, args.range_lookback_hours)
    rule = derive_entry_rule(train_feats, momentum_of)
    side = rule.short_side
    direction_txt = "momentum <=" if not side.enter_high else "momentum >="
    print(
        f"  trained SHORT rule: take when {direction_txt} {side.threshold:+.4f}"
    )

    print("\nLoading disjoint paper cohort...")
    cohort_feats = _load_features(client, args.cohort, args.range_lookback_hours)
    shorts = [
        f
        for f in cohort_feats
        if f.direction == "SHORT" and f.momentum is not None and f.leg_return is not None
    ]
    print(f"  cohort SHORT legs with return+momentum: {len(shorts)}")
    if not shorts:
        print("No cohort shorts to simulate.", file=sys.stderr)
        return 1

    round_trip_fee = 2.0 * args.taker_fee_bps / 10000.0

    def net_return(f) -> float:
        funding = args.funding_bps_per_day / 10000.0 * (f.holding_minutes / 1440.0)
        return f.leg_return - round_trip_fee - funding

    all_net = [net_return(f) for f in shorts]
    taken = [f for f in shorts if side.takes(f.momentum)]
    taken_net = [net_return(f) for f in taken]
    skipped_net = [net_return(f) for f in shorts if not side.takes(f.momentum)]

    print("\n" + "=" * 70)
    print("COST-AWARE PAPER RESULT  (out-of-sample cohort, notional-return space)")
    print("=" * 70)
    print(f"round-trip taker fee: {_bps(round_trip_fee)}  "
          f"funding/day: {args.funding_bps_per_day:+.1f}bps")
    print(f"\ngross (pre-fee) mean short return: {_bps(statistics.fmean([f.leg_return for f in shorts]))}")
    _summarize("TAKE ALL shorts   ", all_net, args.notional)
    _summarize("FILTERED (rule)   ", taken_net, args.notional)
    _summarize("SKIPPED (anti-rule)", skipped_net, args.notional)

    if taken_net and all_net:
        edge = statistics.fmean(taken_net) - statistics.fmean(all_net)
        print(
            f"\nEdge of filter vs take-all: {_bps(edge)} per trade.  "
            f"Filtered net {'POSITIVE' if statistics.fmean(taken_net) > 0 else 'NEGATIVE'} "
            f"after costs."
        )
    print(
        "\nRead: filtered mean net must be >0 AND CI exclude 0 to be a real "
        "post-cost edge; if the CI straddles 0, costs ate it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
