"""Interpretation engine public API."""

from atlas.interpretation.identity import (
    IdentityInterpretation,
    identity_interpretation_to_dict,
    interpret_identity_vector,
)
from atlas.interpretation.profile import (
    ProfileInterpretation,
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.interpretation.rules import (
    interpret_amplifier,
    interpret_driver,
    interpret_motif,
    interpret_pattern,
    interpret_regulator,
    interpret_signature,
)

__all__ = [
    "ProfileInterpretation",
    "interpret_profile_summary",
    "profile_interpretation_to_dict",
    "IdentityInterpretation",
    "interpret_identity_vector",
    "identity_interpretation_to_dict",
    "interpret_driver",
    "interpret_amplifier",
    "interpret_regulator",
    "interpret_pattern",
    "interpret_motif",
    "interpret_signature",
]