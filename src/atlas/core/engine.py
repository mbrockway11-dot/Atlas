
"""Atlas Core engine."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from atlas.core.audit import append_audit_event
from atlas.core.context import AtlasContext
from atlas.core.events import AtlasEvent
from atlas.core.node import NodeResult
from atlas.core.pipeline import Pipeline
from atlas.core.queue import ExecutionQueue
from atlas.core.registry import NodeRegistry
from atlas.core.state import AtlasState


class AtlasEngine:
    def __init__(self, registry: NodeRegistry, context: AtlasContext | None = None) -> None:
        self.registry = registry
        self.context = context or AtlasContext()
        self.state = AtlasState()
        self.results: list[NodeResult] = []
        self.events: list[AtlasEvent] = []
        self.queue = ExecutionQueue()

    def emit(self, name: str, payload: dict[str, Any] | None = None) -> None:
        event = AtlasEvent(name=name, payload=payload or {})
        self.events.append(event)
        append_audit_event({
            "run_id": self.context.run_id,
            "event": event.name,
            "timestamp": event.timestamp,
            "payload": event.payload,
        })

    def run(self) -> dict[str, Any]:
        pipeline = Pipeline(self.registry)
        order = pipeline.execution_order()

        self.emit("pipeline_started", {"node_count": len(order)})

        for node in order:
            self.queue.add(node.name, {"requires": node.requires, "provides": node.provides})
            self.emit("node_started", {"node": node.name})

            try:
                result = node.execute(self.state, self.context)
            except Exception as exc:
                result = NodeResult(
                    name=node.name,
                    success=False,
                    error=str(exc),
                )

            self.results.append(result)

            if result.success and result.output_key:
                self.state.set(result.output_key, result.output)

            self.emit(
                "node_completed" if result.success else "node_failed",
                {
                    "node": result.name,
                    "success": result.success,
                    "output_key": result.output_key,
                    "error": result.error,
                },
            )

            if not result.success:
                break

        self.emit("pipeline_completed", {"success": all(r.success for r in self.results)})
        return self.report()

    def report(self) -> dict[str, Any]:
        return {
            "success": all(r.success for r in self.results),
            "run_id": self.context.run_id,
            "mode": self.context.mode,
            "started_at": self.context.started_at,
            "ended_at": datetime.now(UTC).isoformat(),
            "node_count": len(self.results),
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "output_key": r.output_key,
                    "error": r.error,
                    "warnings": r.warnings,
                }
                for r in self.results
            ],
            "state_keys": list(self.state.to_dict().keys()),
            "event_count": len(self.events),
            "events": [
                {
                    "name": e.name,
                    "timestamp": e.timestamp,
                    "payload": e.payload,
                }
                for e in self.events
            ],
            "queue": self.queue.to_dict(),
        }
