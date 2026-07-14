"""Reconcile canonical ledger state against broker state."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

from atlas.investment.brokers import BrokerAccountSnapshot, BrokerPosition

from .contracts import PortfolioSnapshot


@dataclass(frozen=True)
class LedgerReconciliationIssue:
    code: str
    severity: str
    message: str
    symbol: str | None = None


@dataclass(frozen=True)
class LedgerReconciliationReport:
    status: str
    issues: list[dict]
    cash_difference: float
    equity_difference: float
    position_quantity_differences: dict[str, float]
    paper_only: bool
    live_execution: bool


def reconcile_snapshot(
    snapshot: PortfolioSnapshot,
    broker_account: BrokerAccountSnapshot,
    broker_positions: Iterable[BrokerPosition],
    *,
    tolerance: float = 1e-9,
) -> LedgerReconciliationReport:
    issues: list[LedgerReconciliationIssue] = []

    ledger_cash = sum(item.balance for item in snapshot.cash)
    cash_difference = ledger_cash - broker_account.cash
    equity_difference = snapshot.equity - broker_account.equity

    ledger_positions = {
        item.symbol: item.quantity for item in snapshot.positions
    }
    broker_position_map = {
        item.symbol: item.quantity for item in broker_positions
    }

    symbols = sorted(set(ledger_positions) | set(broker_position_map))
    position_differences = {
        symbol: ledger_positions.get(symbol, 0.0)
        - broker_position_map.get(symbol, 0.0)
        for symbol in symbols
    }

    if abs(cash_difference) > tolerance:
        issues.append(
            LedgerReconciliationIssue(
                code="CASH_MISMATCH",
                severity="ERROR",
                message=f"Cash differs by {cash_difference}",
            )
        )
    if abs(equity_difference) > tolerance:
        issues.append(
            LedgerReconciliationIssue(
                code="EQUITY_MISMATCH",
                severity="ERROR",
                message=f"Equity differs by {equity_difference}",
            )
        )
    for symbol, difference in position_differences.items():
        if abs(difference) > tolerance:
            issues.append(
                LedgerReconciliationIssue(
                    code="POSITION_MISMATCH",
                    severity="ERROR",
                    message=f"Position quantity differs by {difference}",
                    symbol=symbol,
                )
            )

    paper_only = snapshot.paper_only and broker_account.paper_only
    live_execution = snapshot.live_execution or broker_account.live_execution
    if not paper_only or live_execution:
        issues.append(
            LedgerReconciliationIssue(
                code="SAFETY_BOUNDARY_VIOLATION",
                severity="CRITICAL",
                message="Ledger or broker state violates paper-only boundary",
            )
        )

    return LedgerReconciliationReport(
        status="PASS" if not issues else "FAIL",
        issues=[asdict(issue) for issue in issues],
        cash_difference=cash_difference,
        equity_difference=equity_difference,
        position_quantity_differences=position_differences,
        paper_only=paper_only,
        live_execution=live_execution,
    )


__all__ = [
    "LedgerReconciliationIssue",
    "LedgerReconciliationReport",
    "reconcile_snapshot",
]
