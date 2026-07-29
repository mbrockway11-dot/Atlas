"""Harden + wire at scale: run the OOS entry-rule test over the teacher registry.

Read-only (candles only; legs come from disk). Loads all teachers from the
persistent registry, joins candles, and runs both the significance hardening and
the two-fold cross-teacher out-of-sample rule evaluation over the full pool --
the underpowered 11-teacher run is what this replaces.

    .venv/Scripts/python.exe scripts/evaluate_registry_rule.py
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

from atlas.investment.hyper_copytrade.analysis_pipeline import features_by_teacher
from atlas.investment.hyper_copytrade.client import HyperliquidReadClient
from atlas.investment.hyper_copytrade.significance import test_gap
from atlas.investment.hyper_copytrade.strategy import (
    derive_entry_rule,
    evaluate_rule,
    momentum_of,
    range_position_of,
)
from atlas.investment.hyper_copytrade.teacher_registry import (
    DEFAULT_REGISTRY_PATH,
    iter_teacher_legs,
    load_teacher_records,
)


def _pct(v: float) -> str:
    return f"{v * 100:5.1f}%"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--range-lookback-hours", type=float, default=24.0)
    parser.add_argument("--permutation-iterations", type=int, default=5000)
    parser.add_argument(
        "--feature",
        choices=("range_position", "momentum"),
        default="range_position",
    )
    args = parser.parse_args(argv)
    selector = range_position_of if args.feature == "range_position" else momentum_of
    feat = args.feature

    records = load_teacher_records(Path(args.registry))
    teacher_legs = dict(iter_teacher_legs(records))
    print(
        f"Registry {args.registry}: {len(records)} scanned, "
        f"{len(teacher_legs)} teachers, "
        f"{sum(len(v) for v in teacher_legs.values()):,} legs."
    )
    if len(teacher_legs) < 4:
        print("Need >=4 teachers; build the registry further.", file=sys.stderr)
        return 1

    client = HyperliquidReadClient()
    teacher_features = features_by_teacher(
        client,
        teacher_legs,
        range_lookback_hours=args.range_lookback_hours,
        progress=True,
    )
    features = [f for feats in teacher_features.values() for f in feats]

    # --- Hardening: significance of the pooled gaps, direction-conditioned. ---
    print("\n" + "=" * 70)
    print(f"HARDENING  feature={feat}  (pooled, {len(teacher_features)} teachers)")
    print("=" * 70)
    for direction in ("LONG", "SHORT"):
        wins = [
            v
            for f in features
            if f.is_win and f.direction == direction and (v := selector(f)) is not None
        ]
        losses = [
            v
            for f in features
            if not f.is_win and f.direction == direction and (v := selector(f)) is not None
        ]
        sig = test_gap(wins, losses, permutation_iterations=args.permutation_iterations)
        if sig is None:
            print(f"  {feat} [{direction}]: insufficient data")
            continue
        verdict = "SIGNIFICANT" if sig.significant else "not significant"
        print(
            f"  {feat} [{direction}]: win {sig.winner_median:.3f} vs "
            f"loss {sig.loser_median:.3f}  gap {sig.median_gap:+.3f}  "
            f"r={sig.rank_biserial:+.2f}  MWU p={sig.p_value:.1e} -> {verdict}"
        )

    # --- Wiring: two-fold cross-teacher OOS on the direction-conditioned rule. ---
    addresses = sorted(teacher_features)
    fold_a, fold_b = addresses[0::2], addresses[1::2]
    print("\n" + "=" * 70)
    print(f"OUT-OF-SAMPLE  (fold A={len(fold_a)}, B={len(fold_b)} teachers)")
    print("=" * 70)
    lifts = []
    for train, test, name in ((fold_a, fold_b, "A->B"), (fold_b, fold_a, "B->A")):
        train_feats = [f for a in train for f in teacher_features[a]]
        test_feats = [f for a in test for f in teacher_features[a]]
        rule = derive_entry_rule(train_feats, selector)
        result = evaluate_rule(rule, test_feats, selector)
        if result is None:
            print(f"\n[{name}] no scorable test legs.")
            continue
        lifts.append(result.win_rate_lift)
        def side_str(side):
            return f"{'>=' if side.enter_high else '<='} {side.threshold:+.3f}"
        print(
            f"\n[{name}] rule (train-fit)  LONG {side_str(rule.long_side)}  "
            f"SHORT {side_str(rule.short_side)}"
        )
        # Per-direction: win-rate AND PnL lift (win rate != profitability).
        for subset_name, subset in (
            ("ALL  ", test_feats),
            ("LONG ", [f for f in test_feats if f.direction == "LONG"]),
            ("SHORT", [f for f in test_feats if f.direction == "SHORT"]),
        ):
            r = evaluate_rule(rule, subset, selector)
            if r is None:
                continue
            print(
                f"    {subset_name}: win {_pct(r.base_win_rate)}->{_pct(r.taken_win_rate)} "
                f"({r.win_rate_lift * 100:+.1f}pp, n={r.taken})   "
                f"PnL/leg ${r.base_mean_pnl:,.0f}->${r.taken_mean_pnl:,.0f} "
                f"({r.taken_mean_pnl - r.base_mean_pnl:+,.0f})"
            )

    if lifts:
        print(
            f"\nMean pooled OOS win-rate lift: {statistics.fmean(lifts) * 100:+.1f}pp. "
            f"Judge SHORT on PnL/leg lift, not win rate (they can diverge)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
