"""Topology plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext
from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.services.topology_service import get_population_topology_graph


@dataclass(frozen=True)
class TopologyCorePlugin:
    """Attach population topology report to ResearchContext."""

    name: str = "topology"
    order: int = 45
    depends_on: tuple[str, ...] = ("statistics",)

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Build and attach population topology section."""
        config = IntelligenceEngineConfig(**context.config)

        graph = get_population_topology_graph(
            threshold=config.topology_threshold,
            top_k=config.topology_top_k,
            metric=config.similarity_metric,
        )

        node = graph.get("nodes", {}).get(context.display_name)

        section = {
            "graph_summary": graph.get("summary", {}),
            "node": node,
            "node_available": node is not None,
            "node_lookup_name": context.display_name,
            "node_count": graph.get("node_count"),
            "edge_count": graph.get("edge_count"),
        }

        return (
            context.with_data("topology", section)
            .with_provenance(
                [
                    {
                        "section": "topology",
                        "source": "atlas.plugins.topology.TopologyCorePlugin",
                        "role": "Adds population topology graph summary and selected profile node.",
                    }
                ]
            )
        )