"""Identity Graph Stack Audit Engine.

Audits graph-native IdentityGraphStack exports for structural anomalies.

This engine does not interpret personality. It checks whether the generated
stack looks internally healthy enough to trust for downstream analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


STACK_AUDIT_VERSION = "1.0"


@dataclass(frozen=True)
class StackAuditIssue:
    """Single stack audit issue."""

    code: str
    severity: str
    message: str
    details: dict[str, Any]


@dataclass(frozen=True)
class StackAudit:
    """Full stack audit result."""

    version: str
    valid: bool
    status: str
    issue_count: int
    warning_count: int
    error_count: int
    issues: list[StackAuditIssue]
    summary: dict[str, Any]


def audit_identity_stack(stack_data: dict[str, Any]) -> StackAudit:
    """Audit an identity stack dictionary."""
    issues: list[StackAuditIssue] = []

    issues.extend(audit_construction_passes(stack_data))
    issues.extend(audit_graph_connectivity(stack_data))
    issues.extend(audit_hub_ratio(stack_data))
    issues.extend(audit_edge_weight_distribution(stack_data))
    issues.extend(audit_reduction_strength(stack_data))

    error_count = count_severity(issues, "error")
    warning_count = count_severity(issues, "warning")

    valid = error_count == 0

    if error_count:
        status = "error"
    elif warning_count:
        status = "warning"
    else:
        status = "healthy"

    summary = {
        "version": STACK_AUDIT_VERSION,
        "status": status,
        "valid": valid,
        "issue_count": len(issues),
        "warning_count": warning_count,
        "error_count": error_count,
    }

    return StackAudit(
        version=STACK_AUDIT_VERSION,
        valid=valid,
        status=status,
        issue_count=len(issues),
        warning_count=warning_count,
        error_count=error_count,
        issues=issues,
        summary=summary,
    )


def audit_construction_passes(stack_data: dict[str, Any]) -> list[StackAuditIssue]:
    """Audit 21-layer construction pass integrity."""
    issues: list[StackAuditIssue] = []

    passes = (
        stack_data
        .get("cig", {})
        .get("analyzed_graph", {})
        .get("construction_passes", [])
    )

    if not passes:
        return [
            StackAuditIssue(
                code="missing_construction_passes",
                severity="error",
                message="No CIG construction passes found.",
                details={},
            )
        ]

    if len(passes) != 21:
        issues.append(
            StackAuditIssue(
                code="unexpected_layer_count",
                severity="error",
                message="Expected 21 construction layers.",
                details={
                    "expected": 21,
                    "actual": len(passes),
                },
            )
        )

    by_cipher: dict[str, list[int]] = {}

    for record in passes:
        cipher = str(record.get("cipher", "unknown"))
        visit_count = int(record.get("visit_count", 0))
        by_cipher.setdefault(cipher, []).append(visit_count)

    for cipher, counts in sorted(by_cipher.items()):
        if len(set(counts)) > 1:
            issues.append(
                StackAuditIssue(
                    code="within_cipher_visit_imbalance",
                    severity="warning",
                    message="Visit counts differ inside one cipher family.",
                    details={
                        "cipher": cipher,
                        "visit_counts": counts,
                        "minimum": min(counts),
                        "maximum": max(counts),
                    },
                )
            )

    all_counts = [
        int(record.get("visit_count", 0))
        for record in passes
    ]

    if all_counts and min(all_counts) != max(all_counts):
        issues.append(
            StackAuditIssue(
                code="cross_cipher_visit_imbalance",
                severity="warning",
                message="Construction layers do not all have equal visit counts.",
                details={
                    "minimum": min(all_counts),
                    "maximum": max(all_counts),
                    "counts_by_cipher": by_cipher,
                },
            )
        )

    return issues


def audit_graph_connectivity(stack_data: dict[str, Any]) -> list[StackAuditIssue]:
    """Audit CIG connectivity structure."""
    analysis = (
        stack_data
        .get("cig", {})
        .get("analyzed_graph", {})
        .get("analysis", {})
    )

    node_count = get_cig_node_count(stack_data)
    component_count = int(analysis.get("component_count", 0))
    bridge_count = int(analysis.get("bridge_count", 0))
    articulation_count = int(analysis.get("articulation_point_count", 0))
    leaf_count = int(analysis.get("leaf_count", 0))

    issues: list[StackAuditIssue] = []

    if node_count <= 0:
        issues.append(
            StackAuditIssue(
                code="empty_cig",
                severity="error",
                message="CIG has no nodes.",
                details={"node_count": node_count},
            )
        )
        return issues

    if component_count > 3:
        issues.append(
            StackAuditIssue(
                code="fragmented_graph",
                severity="warning",
                message="CIG has more connected components than expected.",
                details={
                    "component_count": component_count,
                },
            )
        )

    if node_count >= 20 and bridge_count <= 1 and articulation_count <= 1 and leaf_count <= 1:
        issues.append(
            StackAuditIssue(
                code="over_connected_graph",
                severity="warning",
                message=(
                    "CIG appears highly connected with very few bridges, "
                    "articulation points, or leaves."
                ),
                details={
                    "node_count": node_count,
                    "bridge_count": bridge_count,
                    "articulation_point_count": articulation_count,
                    "leaf_count": leaf_count,
                },
            )
        )

    return issues


def audit_hub_ratio(stack_data: dict[str, Any]) -> list[StackAuditIssue]:
    """Audit excessive hub density."""
    analysis = (
        stack_data
        .get("cig", {})
        .get("analyzed_graph", {})
        .get("analysis", {})
    )

    node_count = get_cig_node_count(stack_data)
    hub_count = int(analysis.get("hub_count", 0))

    if node_count <= 0:
        return []

    hub_ratio = hub_count / node_count

    if hub_ratio >= 0.30:
        return [
            StackAuditIssue(
                code="high_hub_ratio",
                severity="warning",
                message="CIG hub ratio is unusually high.",
                details={
                    "node_count": node_count,
                    "hub_count": hub_count,
                    "hub_ratio": round(hub_ratio, 6),
                },
            )
        ]

    return []


def audit_edge_weight_distribution(stack_data: dict[str, Any]) -> list[StackAuditIssue]:
    """Audit edge weight compression."""
    edges = (
        stack_data
        .get("cig", {})
        .get("analyzed_graph", {})
        .get("edges", {})
    )

    weights = [
        float(edge.get("weight", 0))
        for edge in edges.values()
    ]

    if not weights:
        return [
            StackAuditIssue(
                code="missing_edges",
                severity="error",
                message="CIG has no edges.",
                details={},
            )
        ]

    max_weight = max(weights)
    mean_weight = sum(weights) / len(weights)
    low_weight_ratio = len([weight for weight in weights if weight <= 1]) / len(weights)

    issues: list[StackAuditIssue] = []

    if max_weight <= 4 and len(weights) >= 30:
        issues.append(
            StackAuditIssue(
                code="compressed_edge_weights",
                severity="warning",
                message="Edge weights appear compressed into a narrow range.",
                details={
                    "edge_count": len(weights),
                    "max_weight": max_weight,
                    "mean_weight": round(mean_weight, 6),
                    "low_weight_ratio": round(low_weight_ratio, 6),
                },
            )
        )

    if low_weight_ratio >= 0.70:
        issues.append(
            StackAuditIssue(
                code="dominant_singleton_edges",
                severity="warning",
                message="Most edges are single-observation edges.",
                details={
                    "edge_count": len(weights),
                    "low_weight_ratio": round(low_weight_ratio, 6),
                },
            )
        )

    return issues


def audit_reduction_strength(stack_data: dict[str, Any]) -> list[StackAuditIssue]:
    """Audit whether structural reduction actually pruned much."""
    cig_nodes = get_cig_node_count(stack_data)
    stg_nodes = len(stack_data.get("stg", {}).get("nodes", {}))

    cig_edges = get_cig_edge_count(stack_data)
    stg_edges = len(stack_data.get("stg", {}).get("edges", {}))

    if cig_nodes <= 0 or cig_edges <= 0:
        return []

    node_retention = stg_nodes / cig_nodes
    edge_retention = stg_edges / cig_edges

    if node_retention >= 0.90 and edge_retention >= 0.90:
        return [
            StackAuditIssue(
                code="weak_structural_reduction",
                severity="warning",
                message=(
                    "Structural Truth Graph retains nearly all CIG structure. "
                    "Reduction may be too conservative."
                ),
                details={
                    "cig_nodes": cig_nodes,
                    "stg_nodes": stg_nodes,
                    "node_retention": round(node_retention, 6),
                    "cig_edges": cig_edges,
                    "stg_edges": stg_edges,
                    "edge_retention": round(edge_retention, 6),
                },
            )
        ]

    return []


def stack_audit_to_dict(audit: StackAudit) -> dict[str, Any]:
    """Convert StackAudit to JSON-safe dictionary."""
    return asdict(audit)


def count_severity(issues: list[StackAuditIssue], severity: str) -> int:
    """Count issues by severity."""
    return len(
        [
            issue
            for issue in issues
            if issue.severity == severity
        ]
    )


def get_cig_node_count(stack_data: dict[str, Any]) -> int:
    """Return CIG node count."""
    return len(
        stack_data
        .get("cig", {})
        .get("analyzed_graph", {})
        .get("nodes", {})
    )


def get_cig_edge_count(stack_data: dict[str, Any]) -> int:
    """Return CIG edge count."""
    return len(
        stack_data
        .get("cig", {})
        .get("analyzed_graph", {})
        .get("edges", {})
    )