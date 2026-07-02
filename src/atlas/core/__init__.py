"""Atlas Core.

Canonical runtime API for Atlas.

The Core package exposes the Canonical Structural Signature (CSS),
the compiler, exporter, and runtime loader.

Nothing outside Atlas should need to know where profile data is stored.
"""

from atlas.core.canonical_structural_signature import (
    CSS_VERSION,
    CanonicalStructuralSignature,
    CipherLayer,
    IdentityLayer,
    KameaLayer,
    PopulationLayer,
    ResearchLayer,
    TemporalLayer,
    ValidationLayer,
)

from atlas.core.compiler import (
    compile_profile,
    compile_profile_payload,
)

from atlas.core.css_exporter import (
    export_css_library,
    export_css_profile,
)

from atlas.core.css_loader import (
    css_exists,
    list_compiled_css,
    load_css,
    load_css_index,
    load_css_payload,
)

__all__ = [
    # CSS
    "CSS_VERSION",
    "CanonicalStructuralSignature",
    "IdentityLayer",
    "CipherLayer",
    "KameaLayer",
    "TemporalLayer",
    "ValidationLayer",
    "ResearchLayer",
    "PopulationLayer",

    # Compiler
    "compile_profile",
    "compile_profile_payload",

    # Exporter
    "export_css_library",
    "export_css_profile",

    # Runtime Loader
    "load_css",
    "load_css_payload",
    "load_css_index",
    "list_compiled_css",
    "css_exists",
]