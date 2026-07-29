"""Hyperliquid copy-trading tracker (paper-only).

Tracks the Hyperliquid perpetuals leaderboard, ranks traders by leveraged
PnL over a window, and reads the leader's live positions (longs and shorts,
with leverage). This package is **read-only and keyless**: it fetches public
market data and never signs, funds, or transmits an order. Mirrored positions
are handed to the existing paper execution plane, which is provably paper-only.

Nothing here touches live execution. The client cannot place an order because
it has no signing path; the only outputs are rankings and position snapshots.
"""

from __future__ import annotations

from atlas.investment.hyper_copytrade.contracts import (
    HYPER_COPYTRADE_CONTRACT_VERSION,
    LeaderPosition,
    LeaderboardEntry,
    TraderRanking,
    WalletState,
    WindowPerformance,
)

__all__ = [
    "HYPER_COPYTRADE_CONTRACT_VERSION",
    "LeaderPosition",
    "LeaderboardEntry",
    "TraderRanking",
    "WalletState",
    "WindowPerformance",
]
