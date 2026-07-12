"""Atlas Research Knowledge Graph v1 reporting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from atlas.investment.research_knowledge_graph.builder import (
    build_knowledge_graph,
)
from atlas.investment.research_knowledge_graph.config import (
    EDGES_CSV,
    ENGINE_RELATIONSHIPS_CSV,
    GRAPH_INTEGRITY_CSV,
    GRAPH_METRICS_CSV,
    HYPOTHESIS_RELATIONSHIPS_CSV,
    NODES_CSV,
    OUTPUT_DIR,
    PORTFOLIO_LINEAGE_CSV,
    REPORT_JSON,
    REPORT_MD,
    RESEARCH_CYCLE_LINEAGE_CSV,
    SCHEMA_VERSION,
    SOURCE,
    STATE_JSON,
    VARIANT_LINEAGE_CSV,
    VERSION,
)
from atlas.investment.research_knowledge_graph.integrity import (
    build_graph_metrics,
    build_integrity_report,
)
from atlas.investment.research_knowledge_graph.loader import (
    load_graph_sources,
)
from atlas.investment.research_knowledge_graph.views import (
    build_lineage_views,
)


def build_knowledge_graph_report() -> dict[str, Any]:
    """Build and persist the Research Knowledge Graph."""
    sources = load_graph_sources()

    graph = build_knowledge_graph(
        sources
    )

    nodes = graph["nodes"]
    edges = graph["edges"]

    integrity = build_integrity_report(
        nodes,
        edges,
    )

    metrics = build_graph_metrics(
        nodes,
        edges,
    )

    views = build_lineage_views(
        nodes,
        edges,
    )

    integrity_passed = bool(
        integrity[
            "passed"
        ].astype(bool).all()
    ) if not integrity.empty else True

    node_type_counts = (
        nodes[
            "node_type"
        ].value_counts().to_dict()
        if not nodes.empty
        else {}
    )

    edge_type_counts = (
        edges[
            "relationship_type"
        ].value_counts().to_dict()
        if not edges.empty
        else {}
    )

    isolated_nodes = int(
        metrics[
            "is_isolated"
        ].astype(bool).sum()
    ) if not metrics.empty else 0

    report = {
        "success": integrity_passed,
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "state_hash": sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        ),
        "summary": (
            "Atlas Research Knowledge Graph v1 "
            f"contains {len(nodes)} node(s), "
            f"{len(edges)} edge(s), and "
            f"{isolated_nodes} isolated node(s)."
        ),
        "counts": {
            "nodes": int(len(nodes)),
            "edges": int(len(edges)),
            "isolated_nodes": (
                isolated_nodes
            ),
            "integrity_checks": int(
                len(integrity)
            ),
            "failed_integrity_checks": int(
                (
                    ~integrity[
                        "passed"
                    ].astype(bool)
                ).sum()
            )
            if not integrity.empty
            else 0,
        },
        "node_type_counts": (
            node_type_counts
        ),
        "edge_type_counts": (
            edge_type_counts
        ),
        "contract": {
            "read_only_sources": True,
            "execution_instruction": False,
            "changes_experiment_registry": False,
            "changes_compiled_state": False,
            "changes_engine_code": False,
            "production_eligible": False,
            "deterministic_given_sources": True,
            "referential_integrity_checked": True,
            "typed_nodes": True,
            "typed_edges": True,
        },
        "outputs": {
            "nodes_csv": str(NODES_CSV),
            "edges_csv": str(EDGES_CSV),
            "engine_relationships_csv": str(
                ENGINE_RELATIONSHIPS_CSV
            ),
            "hypothesis_relationships_csv": str(
                HYPOTHESIS_RELATIONSHIPS_CSV
            ),
            "variant_lineage_csv": str(
                VARIANT_LINEAGE_CSV
            ),
            "portfolio_lineage_csv": str(
                PORTFOLIO_LINEAGE_CSV
            ),
            "research_cycle_lineage_csv": str(
                RESEARCH_CYCLE_LINEAGE_CSV
            ),
            "integrity_csv": str(
                GRAPH_INTEGRITY_CSV
            ),
            "metrics_csv": str(
                GRAPH_METRICS_CSV
            ),
            "state_json": str(
                STATE_JSON
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_outputs(
        report=report,
        nodes=nodes,
        edges=edges,
        integrity=integrity,
        metrics=metrics,
        views=views,
    )

    return report


def write_outputs(
    *,
    report: dict,
    nodes,
    edges,
    integrity,
    metrics,
    views,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    nodes.to_csv(
        NODES_CSV,
        index=False,
    )

    edges.to_csv(
        EDGES_CSV,
        index=False,
    )

    views[
        "engine_relationships"
    ].to_csv(
        ENGINE_RELATIONSHIPS_CSV,
        index=False,
    )

    views[
        "hypothesis_relationships"
    ].to_csv(
        HYPOTHESIS_RELATIONSHIPS_CSV,
        index=False,
    )

    views[
        "variant_lineage"
    ].to_csv(
        VARIANT_LINEAGE_CSV,
        index=False,
    )

    views[
        "portfolio_lineage"
    ].to_csv(
        PORTFOLIO_LINEAGE_CSV,
        index=False,
    )

    views[
        "research_cycle_lineage"
    ].to_csv(
        RESEARCH_CYCLE_LINEAGE_CSV,
        index=False,
    )

    integrity.to_csv(
        GRAPH_INTEGRITY_CSV,
        index=False,
    )

    metrics.to_csv(
        GRAPH_METRICS_CSV,
        index=False,
    )

    state = {
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": report[
            "generated_at"
        ],
        "state_hash": report[
            "state_hash"
        ],
        "counts": report["counts"],
        "node_type_counts": report[
            "node_type_counts"
        ],
        "edge_type_counts": report[
            "edge_type_counts"
        ],
        "contract": report[
            "contract"
        ],
        "source": SOURCE,
    }

    STATE_JSON.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )


def build_markdown(
    report: dict,
) -> str:
    return "\n".join([
        "# Atlas Research Knowledge Graph v1",
        "",
        report["summary"],
        "",
        f"- Success: `{report['success']}`",
        (
            f"- State hash: "
            f"`{report['state_hash']}`"
        ),
        (
            f"- Integrity failures: "
            f"`{report['counts']['failed_integrity_checks']}`"
        ),
        "",
        "## Node Types",
        "",
        "```json",
        json.dumps(
            report["node_type_counts"],
            indent=2,
        ),
        "```",
        "",
        "## Edge Types",
        "",
        "```json",
        json.dumps(
            report["edge_type_counts"],
            indent=2,
        ),
        "```",
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            report["contract"],
            indent=2,
        ),
        "```",
        "",
    ])
