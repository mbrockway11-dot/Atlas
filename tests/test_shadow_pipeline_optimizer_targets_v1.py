from __future__ import annotations

import json

from atlas.investment.execution.shadow_pipeline import (
    load_target_allocations,
)


def test_loads_portfolio_optimizer_report_shape(tmp_path) -> None:
    report_path = tmp_path / "portfolio_optimizer_report.json"

    report_path.write_text(
        json.dumps(
            {
                "success": True,
                "version": "portfolio_optimizer_v2",
                "portfolio": [
                    {
                        "asset": "BTC-USD",
                        "weight": 0.20,
                    },
                    {
                        "asset": "SOL-USD",
                        "weight": 0.10,
                    },
                    {
                        "asset": "CASH",
                        "weight": 0.70,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    allocations = load_target_allocations(
        report_path
    )

    assert allocations == {
        "BTC-USD": 0.20,
        "SOL-USD": 0.10,
        "CASH": 0.70,
    }
