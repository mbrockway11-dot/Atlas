
"""Atlas Core engine."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from atlas.core.context import AtlasContext
from atlas.core.node import NodeResult
from atlas.core.pipeline import Pipeline
from atlas.core.registry import NodeRegistry
from atlas.core.state import AtlasState


class AtlasEngine:
    def __init__(self, registry: NodeRegistry, context: AtlasContext | None = None) -> None:
        self.registry = registry
        self.context = context or AtlasContext()
        self.state = AtlasState()
        self.results: list[NodeResult] = []

    def run(self) -> dict[str, Any]:
        pipeline = Pipeline(self.registry)
        order = pipeline.execution_order()

        for node in order:
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

            if not result.success:
                break

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
        }
