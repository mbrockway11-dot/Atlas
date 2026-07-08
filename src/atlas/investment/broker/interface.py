
"""Broker interface."""

from __future__ import annotations

from atlas.investment.broker.loader import load_orders, load_safety
from atlas.investment.broker.paper_broker import build_paper_broker_orders


def build_broker_interface_payload() -> dict:
    safety = load_safety()
    orders = load_orders()

    paper_orders = build_paper_broker_orders(orders, safety)

    return {
        "success": True,
        "safety_status": safety.get("safety_status"),
        "approved": bool(safety.get("approved")),
        "broker": "paper",
        "order_count": len(paper_orders),
        "orders": [o.to_dict() for o in paper_orders],
        "summary": (
            f"Broker Interface prepared {len(paper_orders)} paper broker order(s). "
            f"Safety status: {safety.get('safety_status')}."
        ),
    }
