"""
Atlas Interpretation Package.

The interpretation layer is responsible for converting deterministic Atlas
outputs into coherent, human-readable understanding.

It does not perform deterministic analysis itself. Instead, it synthesizes
results from the Atlas engines into semantic and narrative explanations.

Primary inputs include:

    • Identity Intelligence
    • Kamea Topology
    • Natal Intelligence
    • Temporal Intelligence
    • Graph Intelligence
    • Relationship Intelligence
    • Population Intelligence
    • Civilization Intelligence
    • Market Intelligence (future)

Typical flow:

    Compiler
        ↓
    Deterministic Engines
        ↓
    Interpretation Layer
        ↓
    Atlas QA
    Profile Reports
    Relationship Reports
    Narrative Intelligence
    Dashboard
"""

from __future__ import annotations

__version__ = "3.0.0"

#
# Core interpretation modules
#

from .identity import *      # noqa: F401,F403
from .profile import *       # noqa: F401,F403
from .rules import *         # noqa: F401,F403

#
# High-level synthesis
#

from .synthesis import (
    synthesize_relationship_interpretation,
)

#
# Semantic interpretation engine
#

from .semantic_engine import (
    build_semantic_profile,
    build_semantic_relationship,
)

#
# Public API
#

__all__ = [
    "build_semantic_profile",
    "build_semantic_relationship",
    "synthesize_relationship_interpretation",
]