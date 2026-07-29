"""Build/extend the persistent teacher registry by scanning the leaderboard.

Read-only. Ranks funded, profitable wallets, scans those not yet in the
registry, classifies each with the leg-based teacher gate, and appends the
result. Resumable: re-run to extend the registry (already-scanned wallets are
skipped). Slow by nature -- one fills fetch per wallet -- so it caps new scans
per run and persists incrementally, so a kill mid-run loses nothing.

    .venv/Scripts/python.exe scripts/build_teacher_registry.py \
        --candidate-pool 600 --max-new 200
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time

from atlas.investment.hyper_copytrade.basis_reconstruction import (
    reconstruct_realized_legs,
)
from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.teacher_registry import (
    DEFAULT_REGISTRY_PATH,
    RegisteredLeg,
    TeacherRecord,
    append_teacher_record,
    load_teacher_records,
    scanned_addresses,
)
from atlas.investment.hyper_copytrade.trader_style import profile_realized_legs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-pool", type=int, default=600)
    parser.add_argument("--max-new", type=int, default=200)
    parser.add_argument("--min-account-value", type=float, default=50000.0)
    parser.add_argument("--window", default="week")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument(
        "--exclude-registry",
        default=None,
        help="Also skip addresses already in this registry (for a disjoint cohort).",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.4,
        help="Throttle between wallet fetches to avoid rate limits.",
    )
    args = parser.parse_args(argv)

    from pathlib import Path

    registry_path = Path(args.registry)
    client = HyperliquidReadClient()
    print(f"[provenance] {client.provenance()}")

    try:
        entries = client.fetch_leaderboard()
    except HyperliquidClientError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    # Candidate pool: funded + profitable this window, ranked by PnL. PnL is only
    # a "is a real, active, profitable account" gate here -- style decides who is
    # a teacher, so the pool is intentionally broad.
    candidates = [
        e
        for e in rank_traders(
            entries,
            window=args.window,
            metric="pnl",
            top_n=args.candidate_pool,
            minimum_account_value=args.min_account_value,
        )
    ]
    already = scanned_addresses(registry_path)
    if args.exclude_registry:
        already = already | scanned_addresses(Path(args.exclude_registry))
    todo = [c for c in candidates if c.address not in already]
    print(
        f"Candidate pool {len(candidates)} | already scanned {len(already)} | "
        f"to scan this run {min(len(todo), args.max_new)}"
    )

    scanned = 0
    new_teachers = 0
    for ranking in todo[: args.max_new]:
        if args.delay_seconds > 0:
            time.sleep(args.delay_seconds)
        try:
            fills = client.fetch_user_fills(ranking.address)
        except HyperliquidClientError:
            continue  # transient; retry on a later run (not recorded)
        legs = reconstruct_realized_legs(fills)
        profile = profile_realized_legs(legs)
        observed = [leg for leg in legs if leg.entry_observed]
        record = TeacherRecord(
            address=ranking.address,
            is_teacher=profile.is_teacher,
            week_pnl=ranking.pnl,
            account_value=ranking.account_value,
            leg_count=profile.leg_count,
            median_hold_minutes=profile.median_hold_minutes,
            win_rate=profile.win_rate,
            legs=tuple(RegisteredLeg.from_realized(leg) for leg in observed)
            if profile.is_teacher
            else (),
        )
        append_teacher_record(registry_path, record)
        scanned += 1
        if profile.is_teacher:
            new_teachers += 1
        if scanned % 20 == 0:
            print(f"  scanned {scanned}/{min(len(todo), args.max_new)}, "
                  f"{new_teachers} new teachers...")

    records = load_teacher_records(registry_path)
    teacher_records = [r for r in records if r.is_teacher]
    total_legs = sum(len(r.legs) for r in teacher_records)
    holds = [r.median_hold_minutes for r in teacher_records if r.median_hold_minutes > 0]
    print(
        f"\nRegistry: {registry_path}\n"
        f"  scanned this run: {scanned}  (new teachers: {new_teachers})\n"
        f"  total scanned:    {len(records)}\n"
        f"  total teachers:   {len(teacher_records)}\n"
        f"  total legs:       {total_legs:,}\n"
        f"  median teacher hold: "
        f"{statistics.median(holds):.0f}m" if holds else "  (no teachers yet)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
