"""Execution metrics for Atlas kernel runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class PluginTiming:
    """Timing record for one plugin."""

    plugin: str
    elapsed_ms: float
    status: str
    warning: str | None = None


@dataclass(frozen=True)
class KernelMetrics:
    """Execution metrics for one kernel run."""

    total_ms: float
    plugin_timings: list[PluginTiming] = field(default_factory=list)
    cache_status: str = "unknown"
    warning_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe metrics."""
        return asdict(self)


class Timer:
    """Small perf-counter timer."""

    def __init__(self) -> None:
        self.started = perf_counter()

    def elapsed_ms(self) -> float:
        """Return elapsed milliseconds."""
        return (perf_counter() - self.started) * 1000.0
