
"""Execution Engine v3 sequencing and idempotency."""

from __future__ import annotations

import pandas as pd

from atlas.investment.execution_engine.schema import stable_order_key


def sequence_orders(validated: list[dict], execution_log: pd.DataFrame, batch: dict) -> list[dict]:
    existing_keys = set()

    if not execution_log.empty and "stable_order_key" in execution_log.columns:
        existing_keys = set(execution_log["stable_order_key"].astype(str).tolist())

    sequenced = []

    valid_orders = [r for r in validated if r.get("validation_status") == "VALID"]

    for priority, row in enumerate(valid_orders, start=1):
        key = stable_order_key(
            str(row.get("asset")),
            str(row.get("action")),
            str(row.get("side")),
            float(row.get("requested_weight") or 0.0),
        )

        status = "DUPLICATE_TARGET" if key in existing_keys else "QUEUED"

        sequenced.append({
            **row,
            "execution_batch_id": batch["execution_batch_id"],
            "execution_id": f"{batch['execution_batch_id']}::{priority}",
            "stable_order_key": key,
            "execution_priority": priority,
            "execution_status": status,
        })

    invalid_orders = [r for r in validated if r.get("validation_status") != "VALID"]

    for row in invalid_orders:
        sequenced.append({
            **row,
            "execution_batch_id": batch["execution_batch_id"],
            "execution_id": None,
            "stable_order_key": None,
            "execution_priority": 999,
            "execution_status": "REJECTED_VALIDATION",
        })

    return sequenced
