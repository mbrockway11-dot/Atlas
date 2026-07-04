"""
Atlas Interpretation Package.

The interpretation layer transforms deterministic Atlas outputs into
human-understandable meaning.

This package never performs deterministic computation itself.
Instead, it converts deterministic outputs into semantic,
behavioral, narrative, and human-facing interpretations.

Architecture
------------

Compiler
    ↓
Deterministic Services
    ↓
Interpretation Layer
    ├── Semantic Engine
    ├── Vedic Behavior
    ├── Synthesis Engine
    ├── Narrative Engine
    └── Interpretive Composer
    ↓
Reasoning Kernel
    ↓
Atlas QA
"""

from __future__ import annotations

__version__ = "3.3.0"

###############################################################################
# Core Interpretation
###############################################################################

from .identity import *      # noqa: F401,F403
from .profile import *       # noqa: F401,F403
from .rules import *         # noqa: F401,F403

###############################################################################
# Semantic Interpretation
###############################################################################

from .semantic_engine import (
    build_semantic_profile,
    build_semantic_relationship,
)

###############################################################################
# Vedic Behavior
###############################################################################

from .vedic_behavior import (
    interpret_vedic_behavior,
)

###############################################################################
# Interpretation Synthesis
###############################################################################

from .synthesis import (
    synthesize_profile,
    synthesize_relationship,
    synthesize_relationship_interpretation,
)

###############################################################################
# Narrative Generation
###############################################################################

from .narrative import (
    compose_profile,
    compose_relationship,
    compose_population,
)

###############################################################################
# Human Interpretation Composer
###############################################################################

from .composer import (
    compose_interpretive_answer,
)

###############################################################################
# Public API
###############################################################################

__all__ = [

    #
    # Semantic
    #
    "build_semantic_profile",
    "build_semantic_relationship",

    #
    # Vedic Behavior
    #
    "interpret_vedic_behavior",

    #
    # Synthesis
    #
    "synthesize_profile",
    "synthesize_relationship",
    "synthesize_relationship_interpretation",

    #
    # Narrative
    #
    "compose_profile",
    "compose_relationship",
    "compose_population",

    #
    # Human Composer
    #
    "compose_interpretive_answer",
]

from atlas.interpretation.profile_classifier import classify_profile

__all__ = [name for name in globals() if not name.startswith("_")]
