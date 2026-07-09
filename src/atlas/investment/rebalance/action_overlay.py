
"""Apply Action Engine v3 requests to target weights."""

from __future__ import annotations

import pandas as pd


def apply_action_requests(targets: dict[str, float], current: dict[str, float], requests: pd.DataFrame) -> dict[str, float]:
    adjusted = dict(targets)

    if requests.empty:
        return adjusted

    for _, row in requests.iterrows():
        asset = str(row.get("asset"))
        action = str(row.get("portfolio_action") or "")
        delta = float(row.get("requested_weight_delta") or 0.0)

        current_weight = float(current.get(asset, adjusted.get(asset, 0.0)))

        if action == "REQUEST_CLOSE":
            adjusted[asset] = 0.0
        elif action in {"REQUEST_REDUCE", "REQUEST_TAKE_PROFIT"}:
            adjusted[asset] = max(0.0, current_weight + delta)
        elif action in {"UPDATE_TRAILING_STOP", "REQUEST_EXIT_REVIEW"}:
            adjusted[asset] = current_weight

    return adjusted
