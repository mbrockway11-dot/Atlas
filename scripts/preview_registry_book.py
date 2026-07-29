"""Preview the paper book from the REGISTRY, ranked by risk-adjusted skill.

The registry-backed counterpart to ``preview_copytrade_book.py``. Instead of
ranking the live leaderboard by weekly PnL, it ranks the already-scanned teacher
registry by per-leg Sharpe -- the validated metric that persists out-of-sample
(rho 0.25 vs raw PnL 0.18) and whose top slice beats the field, unlike raw-PnL
selection. Selection uses only the legs already on disk (no probing); the sole
network calls are one live wallet-state fetch per *selected* teacher, to read
their current positions for the blend. Read-only, paper-only, no orders.

    .venv/Scripts/python.exe scripts/preview_registry_book.py \
        --roster 12 --paper-capital 100000 --min-legs 20 \
        --max-coin-weight 0.25 --max-net-leverage 1.5
"""

from __future__ import annotations

import argparse
import sys

from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.mirror import blend_targets
from atlas.investment.hyper_copytrade.selection import (
    select_registry_roster_by_skill,
)
from atlas.investment.hyper_copytrade.teacher_registry import (
    DEFAULT_REGISTRY_PATH,
    load_teacher_records,
)
from pathlib import Path


def _usd(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--roster", type=int, default=12)
    parser.add_argument("--min-legs", type=int, default=20)
    parser.add_argument("--paper-capital", type=float, default=100000.0)
    parser.add_argument("--max-gross-leverage", type=float, default=3.0)
    parser.add_argument("--max-coin-weight", type=float, default=0.25)
    parser.add_argument("--max-net-leverage", type=float, default=1.5)
    args = parser.parse_args(argv)

    if not args.registry_path.exists():
        print(f"No registry at {args.registry_path}. Run build_teacher_registry.py "
              "first.", file=sys.stderr)
        return 1
    records = load_teacher_records(args.registry_path)
    roster = select_registry_roster_by_skill(
        records, size=args.roster, minimum_legs=args.min_legs
    )
    if not roster:
        print(f"No teachers with >= {args.min_legs} legs in the registry.",
              file=sys.stderr)
        return 1

    print(f"Registry: {len(records)} scanned. Top {len(roster)} by per-leg Sharpe "
          f"(>= {args.min_legs} legs):")
    for member in roster:
        print(f"  {member.address}  legs {member.leg_count:>5}  "
              f"sharpe {member.per_leg_sharpe:+.3f}")

    client = HyperliquidReadClient()
    print(f"\n[provenance] {client.provenance()}")
    states = []
    for member in roster:
        try:
            state = client.fetch_wallet_state(member.address)
        except HyperliquidClientError:
            print(f"  (skip {member.address[:12]}: wallet-state fetch failed)")
            continue
        if state.account_value > 0.0 and state.positions:
            states.append(state)
    if not states:
        print("None of the skilled teachers hold open positions right now.")
        return 0

    book = blend_targets(
        states,
        paper_capital=args.paper_capital,
        maximum_gross_leverage=args.max_gross_leverage,
        maximum_coin_weight=args.max_coin_weight,
        maximum_net_leverage=args.max_net_leverage,
    )
    print(
        f"\nSkill-ranked book on {_usd(args.paper_capital)} paper capital, "
        f"{len(states)} live rosters "
        f"(gross {book.gross_leverage_raw:.2f}x -> {book.gross_leverage_applied:.2f}x, "
        f"net {book.net_leverage_raw:.2f}x -> {book.net_leverage_applied:.2f}x, "
        f"per-coin cap {book.coin_weight_cap:g}, scale {book.scale_factor:.3f}):"
    )
    print(f"  {'coin':>8}  {'dir':>5}  {'weight':>8}  {'target_notional':>16}")
    for position in book.positions:
        print(
            f"  {position.coin:>8}  {position.direction:>5}  "
            f"{position.signed_weight:>+7.3f}  {_usd(position.target_notional):>16}"
        )
    print(f"\n  gross exposure {_usd(book.gross_leverage_applied * args.paper_capital)}"
          f"  |  net exposure {_usd(sum(p.target_notional for p in book.positions))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
