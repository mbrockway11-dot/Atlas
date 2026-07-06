
"""End-to-end synthesis report builder."""

from __future__ import annotations

from typing import Any

from atlas.synthesis.collector import (
    collect_structural_evidence,
    collect_structural_evidence_from_payload,
)
from atlas.synthesis.consensus import (
    build_consensus_report,
    consensus_report_to_dict,
    strongest_theme_names,
)
from atlas.synthesis.evidence import bundle_to_dict
from atlas.synthesis.inference_graph import (
    build_inference_graph,
    inference_graph_to_dict,
)
from atlas.synthesis.reasoning import (
    build_reasoning_report,
    reasoning_report_to_dict,
)
from atlas.synthesis.fusion import (
    fuse_evidence_bundle,
    fusion_result_to_dict,
)


SYNTHESIS_REPORT_VERSION = "1.0"


def build_synthesis_report(profile_key: str) -> dict[str, Any]:
    """Build full Atlas synthesis report for one profile."""

    bundle = collect_structural_evidence(profile_key)
    fusion = fuse_evidence_bundle(bundle)
    consensus = build_consensus_report(fusion)
    reasoning = build_reasoning_report(consensus)
    inference_graph = build_inference_graph(consensus)

    return {
        "success": True,
        "version": SYNTHESIS_REPORT_VERSION,
        "profile_key": profile_key,
        "summary": build_summary(profile_key, consensus, reasoning),
        "strongest_theme_names": strongest_theme_names(consensus),
        "evidence": bundle_to_dict(bundle),
        "fusion": fusion_result_to_dict(fusion),
        "consensus": consensus_report_to_dict(consensus),
        "reasoning": reasoning_report_to_dict(reasoning),
        "inference_graph": inference_graph_to_dict(inference_graph),
    }


def build_summary(profile_key: str, consensus, reasoning=None) -> str:
    """Build compact synthesis summary."""

    strongest = strongest_theme_names(consensus, limit=5)

    if not strongest:
        return (
            f"Atlas Synthesis collected evidence for {profile_key}, "
            "but no stable structural themes have crossed the current consensus threshold."
        )

    theme_text = ", ".join(strongest)
    inference_names = []

    if reasoning:
        inference_names = [
            item.inference
            for item in reasoning.strongest_inferences[:3]
        ]

    if inference_names:
        inference_text = ", ".join(inference_names)
        return (
            f"Atlas Synthesis identifies the strongest current structural themes for "
            f"{profile_key} as: {theme_text}. The reasoning layer derives higher-order "
            f"inferences from these themes, led by: {inference_text}."
        )

    return (
        f"Atlas Synthesis identifies the strongest current structural themes for "
        f"{profile_key} as: {theme_text}. These themes are derived from standardized "
        "evidence records, fused across available engines, and scored through the "
        "consensus layer."
    )



def build_synthesis_report_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build synthesis report from an already-compiled payload.

    This is safe to call inside the canonical compiler because it does not
    recursively call compile_canonical_profile().
    """

    profile_key = str(payload.get("profile_key") or "unknown")

    bundle = collect_structural_evidence_from_payload(profile_key, payload)

    fusion = fuse_evidence_bundle(bundle)
    consensus = build_consensus_report(fusion)
    reasoning = build_reasoning_report(consensus)
    inference_graph = build_inference_graph(consensus)

    return {
        "success": True,
        "version": SYNTHESIS_REPORT_VERSION,
        "profile_key": profile_key,
        "summary": build_summary(profile_key, consensus, reasoning),
        "strongest_theme_names": strongest_theme_names(consensus),
        "evidence": bundle_to_dict(bundle),
        "fusion": fusion_result_to_dict(fusion),
        "consensus": consensus_report_to_dict(consensus),
        "reasoning": reasoning_report_to_dict(reasoning),
        "inference_graph": inference_graph_to_dict(inference_graph),
    }
