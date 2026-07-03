"""
Atlas Interpretation Layer.

This package converts deterministic Atlas outputs into coherent,
human-readable explanations.

The interpretation layer does NOT perform analysis itself.
Instead, it synthesizes results produced by:

    • Identity Engine
    • Graph Intelligence
    • Temporal Intelligence
    • Relationship Intelligence
    • Population Intelligence
    • Civilization Intelligence
    • Market Intelligence (future)

This package should be the primary interface used by:

    • atlas_qa_service
    • Profile Report
    • Relationship Report
    • Narrative Intelligence
    • Atlas AI
    • Future LLM interfaces

Architecture

Compiler
    ↓
Deterministic Engines
    ↓
Interpretation Layer
    ↓
Narrative / QA / Dashboard
"""

from __future__ import annotations

#
# Existing interpretation modules
#

from .identity import *          # noqa: F401,F403
from .profile import *           # noqa: F401,F403
from .rules import *             # noqa: F401,F403

#
# New synthesis layer
#

from .synthesis import (
    synthesize_relationship_interpretation,
)

__version__ = "3.0"

__all__ = [
    "synthesize_relationship_interpretation",
]