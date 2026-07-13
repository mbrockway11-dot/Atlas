"""Persistent account storage for autonomous paper shadow trading."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from atlas.investment.execution.contracts import (
    AccountSnapshot,
    PositionSnapshot,
)


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

PAPER_ACCOUNT_JSON = (
    OUTPUT_DIR
    / "paper_account_state.json"
)

ACCOUNT_STORE_VERSION = "1.0.0"


def load_paper_account(
    *,
    path: Path = PAPER_ACCOUNT_JSON,
    initial_cash: float = 10_000.0,
) -> AccountSnapshot:
    """Load the authoritative paper account or create an empty account."""
    if not path.exists():
        return AccountSnapshot(
            cash=float(initial_cash)
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        raise RuntimeError(
            "PAPER_ACCOUNT_STATE_UNREADABLE"
        )

    account_data = payload.get(
        "account",
        payload,
    )

    if not isinstance(
        account_data,
        Mapping,
    ):
        raise RuntimeError(
            "PAPER_ACCOUNT_STATE_INVALID"
        )

    positions_payload = (
        account_data.get(
            "positions",
            {},
        )
    )

    positions: dict[
        str,
        PositionSnapshot,
    ] = {}

    if isinstance(
        positions_payload,
        Mapping,
    ):
        for asset, raw in (
            positions_payload.items()
        ):
            if not isinstance(
                raw,
                Mapping,
            ):
                continue

            positions[
                str(asset).upper()
            ] = PositionSnapshot(
                asset=str(
                    raw.get(
                        "asset",
                        asset,
                    )
                ).upper(),
                quantity=float(
                    raw.get(
                        "quantity",
                        0.0,
                    )
                ),
                average_price=float(
                    raw.get(
                        "average_price",
                        0.0,
                    )
                ),
                mark_price=float(
                    raw.get(
                        "mark_price",
                        0.0,
                    )
                ),
            )

    return AccountSnapshot(
        cash=float(
            account_data.get(
                "cash",
                initial_cash,
            )
        ),
        positions=positions,
        realized_pnl=float(
            account_data.get(
                "realized_pnl",
                0.0,
            )
        ),
        daily_pnl=float(
            account_data.get(
                "daily_pnl",
                0.0,
            )
        ),
    )


def write_paper_account(
    account: AccountSnapshot,
    *,
    path: Path = PAPER_ACCOUNT_JSON,
    source_execution_id: str = "",
) -> None:
    """Atomically persist one authoritative paper account snapshot."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "version": (
            ACCOUNT_STORE_VERSION
        ),
        "updated_at": (
            datetime.now(
                UTC
            ).isoformat()
        ),
        "source_execution_id": (
            source_execution_id
        ),
        "account": (
            account.to_dict()
        ),
    }

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def account_from_mapping(
    payload: Mapping[str, Any],
) -> AccountSnapshot:
    """Reconstruct an immutable account from an execution report."""
    positions_payload = payload.get(
        "positions",
        {},
    )

    positions = {}

    if isinstance(
        positions_payload,
        Mapping,
    ):
        for asset, row in (
            positions_payload.items()
        ):
            if not isinstance(
                row,
                Mapping,
            ):
                continue

            positions[
                str(asset).upper()
            ] = PositionSnapshot(
                asset=str(
                    row.get(
                        "asset",
                        asset,
                    )
                ).upper(),
                quantity=float(
                    row.get(
                        "quantity",
                        0.0,
                    )
                ),
                average_price=float(
                    row.get(
                        "average_price",
                        0.0,
                    )
                ),
                mark_price=float(
                    row.get(
                        "mark_price",
                        0.0,
                    )
                ),
            )

    return AccountSnapshot(
        cash=float(
            payload.get(
                "cash",
                0.0,
            )
        ),
        positions=positions,
        realized_pnl=float(
            payload.get(
                "realized_pnl",
                0.0,
            )
        ),
        daily_pnl=float(
            payload.get(
                "daily_pnl",
                0.0,
            )
        ),
    )


__all__ = [
    "ACCOUNT_STORE_VERSION",
    "PAPER_ACCOUNT_JSON",
    "account_from_mapping",
    "load_paper_account",
    "write_paper_account",
]
