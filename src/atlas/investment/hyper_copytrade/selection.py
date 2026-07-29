"""Select the best *copyable* Hyperliquid trader from a ranking.

Ranking (`ranking.py`) is pure and offline-testable: it orders leaderboard
rows by a metric. But the top-ranked row is frequently not copyable -- live
probing of the leaderboard shows the highest wallets are commonly vaults,
spot-heavy, sub-account-routed or simply flat, so their perpetual clearinghouse
is empty. Copying an empty wallet mirrors nothing.

This module walks the ranking in order, fetches each wallet's live state, and
returns the first (highest-ranked) trader that satisfies a copyability policy:
open positions, a meaningful clearinghouse balance, and -- since the point is
to copy *leveraged* longs and shorts -- actual leverage in use. Each rejected
candidate is recorded with a reason, so the selection is auditable rather than
a silent walk.

Fetching is bounded by ``maximum_candidates_to_probe`` so one selection cannot
issue an unbounded number of API calls.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from atlas.investment.hyper_copytrade.contracts import (
    TraderRanking,
    WalletState,
)
from atlas.investment.hyper_copytrade.ranking import per_leg_sharpe
from atlas.investment.hyper_copytrade.teacher_registry import (
    TeacherRecord,
    teachers,
)


DEFAULT_MINIMUM_POSITIONS = 1
DEFAULT_MINIMUM_CLEARINGHOUSE_VALUE = 50_000.0
DEFAULT_MINIMUM_ACCOUNT_LEVERAGE = 1.05
DEFAULT_MAXIMUM_CANDIDATES = 25
DEFAULT_MINIMUM_LEGS_FOR_SKILL = 20


class WalletStateSource(Protocol):
    """The read-only capability selection needs from the client."""

    def fetch_wallet_state(self, address: str) -> WalletState:
        ...


@dataclass(frozen=True, slots=True)
class CopyabilityPolicy:
    """Thresholds a wallet must meet to be worth mirroring."""

    minimum_positions: int = DEFAULT_MINIMUM_POSITIONS
    minimum_clearinghouse_value: float = DEFAULT_MINIMUM_CLEARINGHOUSE_VALUE
    minimum_account_leverage: float = DEFAULT_MINIMUM_ACCOUNT_LEVERAGE
    maximum_candidates_to_probe: int = DEFAULT_MAXIMUM_CANDIDATES

    def rejection_reason(self, state: WalletState) -> str | None:
        """Return why ``state`` is not copyable, or ``None`` if it is."""
        if len(state.positions) < self.minimum_positions:
            return "no_open_positions"
        if state.account_value < self.minimum_clearinghouse_value:
            return "clearinghouse_below_floor"
        if state.leverage_ratio < self.minimum_account_leverage:
            return "insufficient_leverage"
        return None


@dataclass(frozen=True, slots=True)
class SkippedCandidate:
    """A ranked trader that was probed and rejected, with the reason."""

    rank: int
    address: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"rank": self.rank, "address": self.address, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class LeaderSelection:
    """The chosen copyable leader plus the audit trail of what was skipped."""

    ranking: TraderRanking
    state: WalletState
    skipped: tuple[SkippedCandidate, ...]
    probed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranking": self.ranking.to_dict(),
            "state": self.state.to_dict(),
            "skipped": [candidate.to_dict() for candidate in self.skipped],
            "probed": self.probed,
        }


class NoCopyableLeaderError(RuntimeError):
    """No ranked trader within the probe budget was copyable."""


def select_copyable_leader(
    rankings: list[TraderRanking],
    source: WalletStateSource,
    *,
    policy: CopyabilityPolicy | None = None,
) -> LeaderSelection:
    """Return the highest-ranked trader that satisfies the copyability policy.

    Walks ``rankings`` in order, fetching live state for at most
    ``policy.maximum_candidates_to_probe`` wallets. A wallet whose state cannot
    be fetched is treated as a skip (reason ``fetch_failed``), not a hard
    error, so one unreachable wallet does not abort the selection.
    """
    policy = policy or CopyabilityPolicy()
    skipped: list[SkippedCandidate] = []
    probed = 0

    for ranking in rankings:
        if probed >= policy.maximum_candidates_to_probe:
            break
        probed += 1

        try:
            state = source.fetch_wallet_state(ranking.address)
        except Exception:
            skipped.append(
                SkippedCandidate(ranking.rank, ranking.address, "fetch_failed")
            )
            continue

        reason = policy.rejection_reason(state)
        if reason is None:
            return LeaderSelection(
                ranking=ranking,
                state=state,
                skipped=tuple(skipped),
                probed=probed,
            )
        skipped.append(
            SkippedCandidate(ranking.rank, ranking.address, reason)
        )

    raise NoCopyableLeaderError(
        f"No copyable leader in the top {probed} probed "
        f"(of {len(rankings)} ranked)."
    )


@dataclass(frozen=True, slots=True)
class RosterSelection:
    """A blended roster of copyable leaders, with the skip audit trail."""

    members: tuple[LeaderSelection, ...]
    skipped: tuple[SkippedCandidate, ...]
    probed: int

    @property
    def addresses(self) -> tuple[str, ...]:
        return tuple(member.ranking.address for member in self.members)

    def to_dict(self) -> dict[str, Any]:
        return {
            "members": [member.to_dict() for member in self.members],
            "skipped": [candidate.to_dict() for candidate in self.skipped],
            "probed": self.probed,
        }


def select_copyable_roster(
    rankings: list[TraderRanking],
    source: WalletStateSource,
    *,
    size: int,
    policy: CopyabilityPolicy | None = None,
) -> RosterSelection:
    """Return the top ``size`` copyable traders, walking past uncopyable ones.

    Same walk as :func:`select_copyable_leader`, but collects ``size`` members
    instead of stopping at the first. Raises :class:`NoCopyableLeaderError` if
    the probe budget is exhausted before ``size`` copyable wallets are found;
    the partial roster is not returned, because a blend sized for ``size``
    members should not silently run on fewer.
    """
    if size < 1:
        raise ValueError("Roster size must be at least 1.")
    policy = policy or CopyabilityPolicy()
    members: list[LeaderSelection] = []
    skipped: list[SkippedCandidate] = []
    probed = 0

    for ranking in rankings:
        if len(members) >= size:
            break
        if probed >= policy.maximum_candidates_to_probe:
            break
        probed += 1

        try:
            state = source.fetch_wallet_state(ranking.address)
        except Exception:
            skipped.append(
                SkippedCandidate(ranking.rank, ranking.address, "fetch_failed")
            )
            continue

        reason = policy.rejection_reason(state)
        if reason is None:
            members.append(
                LeaderSelection(
                    ranking=ranking,
                    state=state,
                    skipped=(),
                    probed=probed,
                )
            )
        else:
            skipped.append(
                SkippedCandidate(ranking.rank, ranking.address, reason)
            )

    if len(members) < size:
        raise NoCopyableLeaderError(
            f"Found only {len(members)} copyable of {size} requested "
            f"in the top {probed} probed (of {len(rankings)} ranked)."
        )
    return RosterSelection(
        members=tuple(members),
        skipped=tuple(skipped),
        probed=probed,
    )


@dataclass(frozen=True, slots=True)
class SkillRankedTeacher:
    """A registry teacher scored by risk-adjusted skill."""

    address: str
    leg_count: int
    per_leg_sharpe: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "leg_count": self.leg_count,
            "per_leg_sharpe": self.per_leg_sharpe,
        }


def select_registry_roster_by_skill(
    records: Sequence[TeacherRecord],
    *,
    size: int,
    minimum_legs: int = DEFAULT_MINIMUM_LEGS_FOR_SKILL,
) -> list[SkillRankedTeacher]:
    """Return the top ``size`` teachers by per-leg Sharpe, from stored legs.

    The registry-backed, network-free counterpart to :func:`select_copyable_roster`:
    it ranks already-scanned teachers on the validated risk-adjusted skill metric
    (per-leg Sharpe persists out-of-sample better than raw PnL, and unlike raw-PnL
    selection its top slice beats the field), using the legs already on disk --
    no leaderboard fetch, no per-candidate reconstruction. Teachers with fewer
    than ``minimum_legs`` legs are excluded so the score is stable. Members are
    returned highest-skill first; the caller fetches each address's live wallet
    state to blend. Pair with a wide roster and the concentration/net caps in
    ``mirror.blend_targets`` -- the edge is breadth, not the single top name.
    """
    if size < 1:
        raise ValueError("Roster size must be at least 1.")
    scored = [
        SkillRankedTeacher(
            address=record.address,
            leg_count=record.leg_count,
            per_leg_sharpe=per_leg_sharpe(
                [leg.closed_pnl for leg in record.legs]
            ),
        )
        for record in teachers(records)
        if record.leg_count >= minimum_legs and record.legs
    ]
    scored.sort(key=lambda member: member.per_leg_sharpe, reverse=True)
    return scored[:size]
