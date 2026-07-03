"""Tests for single profile intelligence service."""

from __future__ import annotations

from atlas.services.single_profile_intelligence_service import (
    build_single_profile_intelligence_payload,
)


def test_single_profile_intelligence_payload_builds():
    payload = build_single_profile_intelligence_payload(
        "nikola_tesla",
        evaluation_date="2026-07-02",
        forecast_days=3,
    )

    assert payload["success"] is True
    assert payload["profile_key"] == "nikola_tesla"
    assert payload["evaluation_date"] == "2026-07-02"
    assert payload["css"]
    assert payload["temporal_runtime"]["success"] is True
    assert payload["forecast"]["count"] == 3
    assert payload["semantic_graph"]["summary"]["node_count"] > 0
    assert payload["graph_metrics"]["node_count"] > 0
    assert payload["graph_activation"]["summary"]["activated_node_count"] > 0
    assert payload["graph_propagation"]["summary"]["propagation_status"] == "computed"
    assert len(payload["structural_fingerprint"]["structural_hash"]) == 64


def test_single_profile_intelligence_payload_has_dashboard_integration_status():
    payload = build_single_profile_intelligence_payload(
        "nikola_tesla",
        evaluation_date="2026-07-02",
    )

    assert payload["ive"]["metadata"]["status"] == "integrated"
    assert payload["ive"]["quality"]["source"] == "graph_intelligence"
    assert payload["population"]["status"] == "not_integrated"
    assert "warnings" in payload
    assert "errors" in payload
