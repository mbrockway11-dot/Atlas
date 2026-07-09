
"""Portfolio Lifecycle v2 transition logic."""

from __future__ import annotations

from atlas.investment.lifecycle import states


def transition_for_position(position: dict, action_lookup: dict[str, dict]) -> tuple[str, str]:
    asset = str(position.get("asset"))
    side = str(position.get("side") or "LONG")
    position_id = f"paper::{asset}::{side}"

    action = action_lookup.get(position_id, {}).get("final_action", "HOLD")

    unrealized = float(position.get("unrealized_pnl_pct") or 0.0)

    if action == "EXIT_REVIEW":
        return states.EXIT_REQUESTED, "Action Engine requested exit review."

    if action == "REDUCE":
        return states.REDUCE_REQUESTED, "Action Engine requested position reduction."

    if unrealized <= -0.05:
        return states.WATCH, "Position is below -5% unrealized; watch closely."

    return states.ACTIVE, "Position is active and within lifecycle limits."
