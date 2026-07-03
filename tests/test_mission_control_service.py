"""Tests for Mission Control service."""

from __future__ import annotations

from atlas.services.mission_control_service import build_mission_control_status


def test_mission_control_status_builds():
    status = build_mission_control_status()

    assert status["architecture"] == "Service-backed"
    assert status["tests"]["count"] >= 551
    assert status["systems"]["kernel"] == "Healthy"
    assert status["systems"]["ive"] == "Integrated"
    assert status["engines"]["single_profile_intelligence"] == "Online"
