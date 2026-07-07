
"""Research provenance report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.provenance.graph import build_provenance_graph
from atlas.autonomous.provenance.lineage import add_relation, create_lineage
from atlas.autonomous.provenance.registry import create_registry, register_object


PROVENANCE_VERSION = "1.0.0"


def build_provenance_report(autonomous_report: dict[str, Any]) -> dict[str, Any]:
    """Build provenance report from autonomous report."""
    registry = create_registry()
    lineage = create_lineage()

    director_id = register_object(
        registry,
        object_type="DIRECTOR",
        payload={"summary": autonomous_report.get("summary", "")},
        label="Autonomous Director Run",
    )
    registry = director_id["registry"]

    learning_id = register_object(
        registry,
        object_type="LEARNING",
        payload=autonomous_report.get("learning_update", {}) or {},
        label="Learning Update",
    )
    registry = learning_id["registry"]
    lineage = add_relation(lineage, learning_id["object_id"], director_id["object_id"], relation="feeds")

    confidence_id = register_object(
        registry,
        object_type="CONFIDENCE",
        payload=autonomous_report.get("scientific_confidence", {}) or {},
        label="Scientific Confidence",
    )
    registry = confidence_id["registry"]
    lineage = add_relation(lineage, confidence_id["object_id"], director_id["object_id"], relation="certifies")

    theory_ids = []
    for theory in (autonomous_report.get("theory", {}) or {}).get("theories", []) or []:
        result = register_object(
            registry,
            object_type="THEORY",
            payload=theory,
            label=theory.get("label", "Theory"),
        )
        registry = result["registry"]
        theory_ids.append(result["object_id"])
        lineage = add_relation(lineage, result["object_id"], learning_id["object_id"], relation="informs")

    evidence_ids = []
    evidence_records = (autonomous_report.get("evidence_registry", {}) or {}).get("records", {}) or {}
    for evidence in evidence_records.values():
        result = register_object(
            registry,
            object_type="EVIDENCE",
            payload=evidence,
            label=evidence.get("evidence_id", "Evidence"),
        )
        registry = result["registry"]
        evidence_ids.append(result["object_id"])

        for theory_id in theory_ids:
            lineage = add_relation(lineage, result["object_id"], theory_id, relation="supports")

    prediction = autonomous_report.get("prediction", {}) or {}
    prediction_id = register_object(
        registry,
        object_type="PREDICTION",
        payload=prediction,
        label="Prediction Benchmark",
    )
    registry = prediction_id["registry"]

    for theory_id in theory_ids:
        lineage = add_relation(lineage, theory_id, prediction_id["object_id"], relation="tested_by")

    falsification = autonomous_report.get("falsification", {}) or {}
    falsification_id = register_object(
        registry,
        object_type="FALSIFICATION",
        payload=falsification,
        label="Falsification Report",
    )
    registry = falsification_id["registry"]

    for theory_id in theory_ids:
        lineage = add_relation(lineage, theory_id, falsification_id["object_id"], relation="challenged_by")

    lineage = add_relation(lineage, prediction_id["object_id"], confidence_id["object_id"], relation="contributes_to")
    lineage = add_relation(lineage, falsification_id["object_id"], confidence_id["object_id"], relation="contributes_to")

    graph = build_provenance_graph(registry, lineage)

    return {
        "success": True,
        "version": PROVENANCE_VERSION,
        "registry": registry,
        "lineage": lineage,
        "graph": graph,
        "summary": build_summary(graph),
    }


def build_summary(graph: dict[str, Any]) -> str:
    """Build provenance summary."""
    summary = graph.get("summary", {}) or {}
    return (
        f"Provenance graph contains {summary.get('node_count', 0)} node(s) "
        f"and {summary.get('edge_count', 0)} edge(s)."
    )
