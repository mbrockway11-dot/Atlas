"""Safety and sanitization tests for the paper execution dashboard."""

from __future__ import annotations

import pandas as pd

from atlas.investment.execution.dashboard import (
    dataframe_records,
    sanitize_mapping,
)


def test_sensitive_values_are_removed():
    payload = sanitize_mapping({
        "safe": "yes",
        "api_key": "never-display",
        "signature": "never-display",
        "nested": {
            "nonce": "never-display",
            "status": "PAPER",
        },
    })

    assert payload["safe"] == "yes"
    assert "api_key" not in payload
    assert "signature" not in payload
    assert "nonce" not in payload[
        "nested"
    ]
    assert (
        payload["nested"][
            "status"
        ]
        == "PAPER"
    )


def test_dataframe_nan_becomes_none():
    rows = dataframe_records(
        pd.DataFrame([
            {
                "asset": "BTC-USD",
                "reason": float("nan"),
            }
        ])
    )

    assert (
        rows[0]["reason"]
        is None
    )
