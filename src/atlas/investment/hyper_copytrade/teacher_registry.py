"""Persistent style-first teacher registry.

Finding teachers is slow -- one leaderboard row is one fills fetch plus a
reconstruction, a few seconds each -- and the earlier harden+wire ran on only
11, far too few for statistical power. This module persists the scan so hundreds
of wallets accumulate across runs instead of being re-scanned every time.

Storage is JSONL, one scanned wallet per line, because a full registry of
teachers-with-legs is large and append-only writes make the build resumable:
re-running skips wallets already on disk and appends the rest. Every scanned
wallet is recorded -- teachers with their entry-observed legs, non-teachers as a
one-line marker -- so a wallet is never classified twice. Only entry-observed
legs are stored, since those are the only ones the entry-state analysis can use;
that also bounds the file size.

Each line is self-describing and carries the schema version; a line that fails
to parse is skipped rather than aborting the load, matching the batch rule that
one bad record must not lose the rest.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg


TEACHER_REGISTRY_SCHEMA = "atlas.investment.hyper-copytrade.teacher-registry.v2"
# v1 lacked exit_price; still loadable (exit_price defaults 0.0, unused for the
# momentum threshold). Only v2 records carry the exit price the paper cost model
# needs, so the paper simulator filters to legs with a real exit price.
_ACCEPTED_SCHEMAS = frozenset(
    {
        "atlas.investment.hyper-copytrade.teacher-registry.v1",
        "atlas.investment.hyper-copytrade.teacher-registry.v2",
    }
)

DEFAULT_REGISTRY_PATH = Path("output/investment_hyper_copytrade/teacher_registry.jsonl")


@dataclass(frozen=True, slots=True)
class RegisteredLeg:
    """A persisted entry-observed realized leg (candle join happens later)."""

    coin: str
    direction: str
    is_win: bool
    closed_pnl: float
    entry_price: float
    entry_time_ms: int
    exit_time_ms: int
    exit_price: float = 0.0  # 0.0 for legacy v1 records; real for v2

    @classmethod
    def from_realized(cls, leg: RealizedLeg) -> "RegisteredLeg":
        return cls(
            coin=leg.coin,
            direction=leg.direction,
            is_win=leg.is_win,
            closed_pnl=leg.closed_pnl,
            entry_price=leg.entry_price,
            entry_time_ms=leg.entry_time_ms,
            exit_time_ms=leg.exit_time_ms,
            exit_price=leg.exit_price,
        )

    def to_realized(self) -> RealizedLeg:
        """Rehydrate as a RealizedLeg (entry_observed by construction)."""
        return RealizedLeg(
            coin=self.coin,
            direction=self.direction,
            entry_price=self.entry_price,
            entry_time_ms=self.entry_time_ms,
            exit_price=self.exit_price,
            exit_time_ms=self.exit_time_ms,
            size=0.0,
            closed_pnl=self.closed_pnl,
            entry_observed=True,
        )

    def short_return(self) -> float | None:
        """Fractional return of the short leg, or None without a real exit price."""
        if self.direction != "SHORT" or self.entry_price <= 0.0 or self.exit_price <= 0.0:
            return None
        return (self.entry_price - self.exit_price) / self.entry_price

    def to_dict(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "direction": self.direction,
            "is_win": self.is_win,
            "closed_pnl": self.closed_pnl,
            "entry_price": self.entry_price,
            "entry_time_ms": self.entry_time_ms,
            "exit_time_ms": self.exit_time_ms,
            "exit_price": self.exit_price,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegisteredLeg":
        return cls(
            coin=str(data["coin"]),
            direction=str(data["direction"]),
            is_win=bool(data["is_win"]),
            closed_pnl=float(data["closed_pnl"]),
            entry_price=float(data["entry_price"]),
            entry_time_ms=int(data["entry_time_ms"]),
            exit_time_ms=int(data["exit_time_ms"]),
            exit_price=float(data.get("exit_price", 0.0)),
        )


@dataclass(frozen=True, slots=True)
class TeacherRecord:
    """One scanned wallet: its style verdict and (if a teacher) its legs."""

    address: str
    is_teacher: bool
    week_pnl: float
    account_value: float
    leg_count: int
    median_hold_minutes: float
    win_rate: float
    legs: tuple[RegisteredLeg, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TEACHER_REGISTRY_SCHEMA,
            "address": self.address,
            "is_teacher": self.is_teacher,
            "week_pnl": self.week_pnl,
            "account_value": self.account_value,
            "leg_count": self.leg_count,
            "median_hold_minutes": self.median_hold_minutes,
            "win_rate": self.win_rate,
            "legs": [leg.to_dict() for leg in self.legs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeacherRecord":
        if data.get("schema") not in _ACCEPTED_SCHEMAS:
            raise ValueError(f"Unknown teacher-record schema {data.get('schema')!r}.")
        return cls(
            address=str(data["address"]),
            is_teacher=bool(data["is_teacher"]),
            week_pnl=float(data["week_pnl"]),
            account_value=float(data["account_value"]),
            leg_count=int(data["leg_count"]),
            median_hold_minutes=float(data["median_hold_minutes"]),
            win_rate=float(data["win_rate"]),
            legs=tuple(
                RegisteredLeg.from_dict(leg) for leg in data.get("legs", ())
            ),
        )


def load_teacher_records(path: Path) -> list[TeacherRecord]:
    """Load all scanned-wallet records; skip any unparseable line."""
    if not path.exists():
        return []
    records: list[TeacherRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(TeacherRecord.from_dict(json.loads(line)))
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
    return records


def scanned_addresses(path: Path) -> set[str]:
    """Return the set of addresses already scanned (teachers and not)."""
    return {record.address for record in load_teacher_records(path)}


def append_teacher_record(path: Path, record: TeacherRecord) -> None:
    """Append one record as a JSONL line, creating the file/dir if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def teachers(records: Iterable[TeacherRecord]) -> list[TeacherRecord]:
    """Filter to records that passed the teacher gate."""
    return [record for record in records if record.is_teacher]


def iter_teacher_legs(
    records: Iterable[TeacherRecord],
) -> Iterator[tuple[str, list[RealizedLeg]]]:
    """Yield ``(address, realized_legs)`` for each teacher record."""
    for record in records:
        if record.is_teacher:
            yield record.address, [leg.to_realized() for leg in record.legs]
