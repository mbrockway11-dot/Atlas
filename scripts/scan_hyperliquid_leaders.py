"""Scan the live Hyperliquid leaderboard and read the best wallet's positions.

Read-only and keyless. Fetches the public leaderboard, ranks the top traders
under an explicit policy, and prints the leader's open longs and shorts with
leverage. No order is ever placed -- the client has no signing path.

    .venv/Scripts/python.exe scripts/scan_hyperliquid_leaders.py \
        --window week --metric roi --top-n 50 --min-account-value 25000
"""

from __future__ import annotations

import argparse
import sys

from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.contracts import (
    VALID_METRICS,
    VALID_WINDOWS,
)
from atlas.investment.hyper_copytrade.ranking import (
    DEFAULT_MINIMUM_ACCOUNT_VALUE,
    rank_traders,
)
from atlas.investment.hyper_copytrade.selection import (
    NoCopyableLeaderError,
    select_copyable_leader,
)


def _usd(value: float) -> str:
    return f"${value:,.0f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", choices=VALID_WINDOWS, default="week")
    parser.add_argument("--metric", choices=VALID_METRICS, default="roi")
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument(
        "--min-account-value",
        type=float,
        default=DEFAULT_MINIMUM_ACCOUNT_VALUE,
    )
    parser.add_argument("--show", type=int, default=10, help="Rows to print.")
    args = parser.parse_args(argv)

    client = HyperliquidReadClient()
    print(f"[provenance] {client.provenance()}")

    try:
        entries = client.fetch_leaderboard()
    except HyperliquidClientError as error:
        print(f"ERROR fetching leaderboard: {error}", file=sys.stderr)
        return 1
    print(f"Fetched {len(entries):,} leaderboard rows.")

    rankings = rank_traders(
        entries,
        window=args.window,
        metric=args.metric,
        top_n=args.top_n,
        minimum_account_value=args.min_account_value,
    )
    if not rankings:
        print("No traders matched the ranking policy.", file=sys.stderr)
        return 1

    print(
        f"\nTop {min(args.show, len(rankings))} of {len(rankings)} "
        f"by {args.metric} over '{args.window}' "
        f"(account >= {_usd(args.min_account_value)}):"
    )
    header = f"{'#':>3}  {'address':42}  {'acct_value':>14}  {'roi':>9}  {'pnl':>16}"
    print(header)
    print("-" * len(header))
    for ranking in rankings[: args.show]:
        print(
            f"{ranking.rank:>3}  {ranking.address:42}  "
            f"{_usd(ranking.account_value):>14}  "
            f"{ranking.roi * 100:>8.2f}%  {_usd(ranking.pnl):>16}"
        )

    try:
        selection = select_copyable_leader(rankings, client)
    except NoCopyableLeaderError as error:
        print(f"\n{error}", file=sys.stderr)
        return 1

    leader = selection.ranking
    state = selection.state
    if selection.skipped:
        print(
            f"\nProbed {selection.probed} wallet(s); skipped "
            f"{len(selection.skipped)} before the first copyable one:"
        )
        for candidate in selection.skipped:
            print(f"  rank {candidate.rank:>3} {candidate.address}  -> {candidate.reason}")

    print(
        f"\nBest COPYABLE wallet: rank {leader.rank} {leader.address} "
        f"({leader.roi * 100:.2f}% ROI, {_usd(leader.pnl)} PnL over "
        f"'{leader.window}')"
    )

    print(
        f"  account value {_usd(state.account_value)}  |  "
        f"account leverage {state.leverage_ratio:.2f}x  |  "
        f"{len(state.positions)} open position(s)"
    )
    if not state.positions:
        print("  (no open positions right now)")
        return 0

    print(
        f"  {'coin':>8}  {'dir':>5}  {'lev':>5}  "
        f"{'notional':>14}  {'entry':>12}  {'uPnL':>14}"
    )
    for position in sorted(
        state.positions, key=lambda p: p.position_value, reverse=True
    ):
        print(
            f"  {position.coin:>8}  {position.direction:>5}  "
            f"{position.leverage:>4.0f}x  {_usd(position.position_value):>14}  "
            f"{position.entry_price:>12,.4f}  {_usd(position.unrealized_pnl):>14}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
