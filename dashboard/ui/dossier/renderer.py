
"""Canonical Atlas dossier renderer."""

from __future__ import annotations

from typing import Any

from dashboard.ui.dossier.dossier_header import render_dossier_header
from dashboard.ui.dossier.executive_summary import render_executive_summary
from dashboard.ui.dossier.structural_synthesis_section import render_structural_synthesis_section
from dashboard.ui.dossier.classification_section import render_classification_section
from dashboard.ui.dossier.civilization_section import render_civilization_section
from dashboard.ui.dossier.relationship_section import render_relationship_section
from dashboard.ui.dossier.identity_section import render_identity_section
from dashboard.ui.dossier.graph_section import render_graph_section
from dashboard.ui.dossier.structural_genome import render_structural_genome_section
from dashboard.ui.dossier.kamea_section import render_kamea_section
from dashboard.ui.dossier.topology_section import render_topology_section
from dashboard.ui.dossier.resonance_section import render_resonance_section
from dashboard.ui.dossier.fingerprint_section import render_fingerprint_section
from dashboard.ui.dossier.temporal_section import render_temporal_section
from dashboard.ui.dossier.vedic_section import render_vedic_section
from dashboard.ui.dossier.semantic_section import render_semantic_section
from dashboard.ui.dossier.evidence_section import render_evidence_section
from dashboard.ui.dossier.metrics_section import render_metrics_section
from dashboard.ui.dossier.diagnostics_section import render_diagnostics_section


def render_dossier(profile: dict[str, Any]) -> None:
    """Render the full Atlas Structural Dossier in canonical order."""

    render_dossier_header(profile)
    render_executive_summary(profile)
    render_structural_synthesis_section(profile)

    render_classification_section(profile)
    render_civilization_section(profile)
    render_relationship_section(profile)

    render_identity_section(profile)

    render_graph_section(profile)
    render_structural_genome_section(profile)
    render_kamea_section(profile)
    render_topology_section(profile)
    render_resonance_section(profile)
    render_fingerprint_section(profile)

    render_temporal_section(profile)
    render_vedic_section(profile)

    render_semantic_section(profile)
    render_evidence_section(profile)
    render_metrics_section(profile)
    render_diagnostics_section(profile)
