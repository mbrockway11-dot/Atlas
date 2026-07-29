"""Preview the blended paper target book from the live Hyperliquid roster.

Read-only. Ranks the leaderboard, selects the top N copyable leaders, blends
their positions proportional-to-equity (netting longs/shorts), applies the risk
caps (per-coin concentration, gross leverage, net exposure), and scales to paper
capital. Prints the target book. No order is placed -- this is the translation
the paper-execution layer (2b) will consume.

Defaults favour breadth over the top few (validation: the copy-trade edge is the
teacher pool, not the highest-PnL names), with a wide roster and concentration /
net-exposure caps on by default so the book cannot become a one-way concentrated
bet. Pass ``--max-coin-weight`` / ``--max-net-leverage`` to tune, or a large value
to effectively disable.

    .venv/Scripts/python.exe scripts/preview_copytrade_book.py \
        --roster 12 --paper-capital 100000 --max-gross-leverage 3 \
        --max-coin-weight 0.25 --max-net-leverage 1.5
"""

from __future__ import annotations

import argparse
import sys

from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.contracts import VALID_METRICS, VALID_WINDOWS
from atlas.investment.hyper_copytrade.mirror import blend_targets
from atlas.investment.hyper_copytrade.ranking import rank_traders
from atlas.investment.hyper_copytrade.selection import (
    NoCopyableLeaderError,
    select_copyable_roster,
)


def _usd(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", choices=VALID_WINDOWS, default="week")
    parser.add_argument("--metric", choices=VALID_METRICS, default="pnl")
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--min-account-value", type=float, default=100000.0)
    parser.add_argument("--roster", type=int, default=12)
    parser.add_argument("--paper-capital", type=float, default=100000.0)
    parser.add_argument("--max-gross-leverage", type=float, default=3.0)
    parser.add_argument("--max-coin-weight", type=float, default=0.25)
    parser.add_argument("--max-net-leverage", type=float, default=1.5)
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
    try:
        roster = select_copyable_roster(rankings, client, size=args.roster)
    except NoCopyableLeaderError as error:
        print(f"\n{error}", file=sys.stderr)
        return 1

    print(
        f"\nRoster of {len(roster.members)} copyable leaders "
        f"(probed {roster.probed}, skipped {len(roster.skipped)}):"
    )
    for member in roster.members:
        state = member.state
        longs = sum(1 for p in state.positions if p.signed_size >= 0)
        shorts = len(state.positions) - longs
        print(
            f"  rank {member.ranking.rank:>3}  {member.ranking.address}  "
            f"{_usd(state.account_value):>14}  {state.leverage_ratio:>5.2f}x  "
            f"(L{longs}/S{shorts})  wk PnL {_usd(member.ranking.pnl)}"
        )

    book = blend_targets(
        [member.state for member in roster.members],
        paper_capital=args.paper_capital,
        maximum_gross_leverage=args.max_gross_leverage,
        maximum_coin_weight=args.max_coin_weight,
        maximum_net_leverage=args.max_net_leverage,
    )
    print(
        f"\nBlended target book on {_usd(args.paper_capital)} paper capital "
        f"(gross {book.gross_leverage_raw:.2f}x raw -> {book.gross_leverage_applied:.2f}x, "
        f"net {book.net_leverage_raw:.2f}x raw -> {book.net_leverage_applied:.2f}x, "
        f"per-coin cap {book.coin_weight_cap:g}, scale {book.scale_factor:.3f}):"
    )
    if not book.positions:
        print("  (blend netted to no positions above dust)")
        return 0
    print(f"  {'coin':>8}  {'dir':>5}  {'weight':>8}  {'target_notional':>16}")
    for position in book.positions:
        print(
            f"  {position.coin:>8}  {position.direction:>5}  "
            f"{position.signed_weight:>+7.3f}  {_usd(position.target_notional):>16}"
        )
    net = sum(p.target_notional for p in book.positions)
    gross = sum(abs(p.target_notional) for p in book.positions)
    print(f"\n  gross exposure {_usd(gross)}  |  net exposure {_usd(net)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
