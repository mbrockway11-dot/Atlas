from __future__ import annotations

from atlas.investment.brokers import (
    BrokerHealthState,
    FixtureRestTransport,
    GenericRestPaperAdapter,
    GenericRestPaperConfig,
)


def test_recorded_fixture_transport_never_uses_network() -> None:
    transport = FixtureRestTransport(
        {
            ("GET", "/paper/health"): {
                "state": "HEALTHY",
                "message": "recorded fixture",
                "latency_ms": 0,
            }
        }
    )
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture"),
        transport=transport,
    )

    result = broker.health_check()

    assert result.state == BrokerHealthState.HEALTHY
    assert result.message == "recorded fixture"
    assert transport.requests == [
        {
            "method": "GET",
            "path": "/paper/health",
            "json_body": None,
            "headers": None,
        }
    ]


def test_transport_failure_degrades_health_without_live_call() -> None:
    transport = FixtureRestTransport(
        {
            ("GET", "/paper/health"): {
                "__raise__": "transport",
                "message": "offline fixture",
            }
        }
    )
    broker = GenericRestPaperAdapter(
        config=GenericRestPaperConfig(provider="fixture"),
        transport=transport,
    )

    result = broker.health_check()

    assert result.state == BrokerHealthState.UNAVAILABLE
    assert result.paper_only is True
    assert result.live_execution is False
