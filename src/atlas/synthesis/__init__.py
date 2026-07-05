
"""Atlas synthesis package."""

from atlas.synthesis.collector import collect_structural_evidence, collect_structural_evidence_from_payload
from atlas.synthesis.consensus import (
    ConsensusReport,
    build_consensus_report,
    consensus_label,
    consensus_report_to_dict,
    strongest_theme_names,
)
from atlas.synthesis.fusion import (
    FusedTheme,
    SynthesisFusionResult,
    fused_theme_to_dict,
    fusion_result_to_dict,
    fuse_evidence_bundle,
)
from atlas.synthesis.report import build_synthesis_report, build_synthesis_report_from_payload
from atlas.synthesis.ontology import (
    CATEGORIES,
    FEATURES,
    FEATURE_TO_CATEGORY,
    SYNTHESIS_ONTOLOGY_VERSION,
    category_for_feature,
    describe_category,
    describe_feature,
)
from atlas.synthesis.evidence import (
    EvidenceBundle,
    StructuralEvidence,
    bundle_to_dict,
    evidence_from_dict,
    evidence_to_dict,
    make_evidence,
)

__all__ = [
    "build_synthesis_report",
    "build_synthesis_report_from_payload",
    "ConsensusReport",
    "build_consensus_report",
    "consensus_label",
    "consensus_report_to_dict",
    "strongest_theme_names",
    "FusedTheme",
    "SynthesisFusionResult",
    "fused_theme_to_dict",
    "fusion_result_to_dict",
    "fuse_evidence_bundle",
    "collect_structural_evidence",
    "collect_structural_evidence_from_payload",
    "CATEGORIES",
    "FEATURES",
    "FEATURE_TO_CATEGORY",
    "SYNTHESIS_ONTOLOGY_VERSION",
    "category_for_feature",
    "describe_category",
    "describe_feature",
    "EvidenceBundle",
    "StructuralEvidence",
    "bundle_to_dict",
    "evidence_from_dict",
    "evidence_to_dict",
    "make_evidence",
]
