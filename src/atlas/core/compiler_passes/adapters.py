"""CompilerPass adapters for existing CSS compiler passes.

These classes wrap the existing deterministic pass functions without changing
their internal business logic.
"""

from __future__ import annotations

from dataclasses import replace

from atlas.core.canonical_structural_signature import CanonicalStructuralSignature
from atlas.core.compiler_framework import CompilerContext, PassMetadata
from atlas.core.compiler_passes.cipher import build_cipher_layer
from atlas.core.compiler_passes.identity import build_identity_layer
from atlas.core.compiler_passes.kamea import build_kamea_layer
from atlas.core.compiler_passes.temporal import build_temporal_layer
from atlas.core.compiler_passes.astronomy import build_astronomy_layer
from atlas.core.compiler_passes.structural import build_structural_measurement_layer


class AstronomyPass:
    """Populate canonical physical measurements before symbolic transforms."""

    metadata = PassMetadata(name="astronomy", version="1.0", dependencies=("identity",))

    def run(self, css: CanonicalStructuralSignature, context: CompilerContext) -> CanonicalStructuralSignature:
        return replace(
            css,
            astronomy=build_astronomy_layer(profile_payload=context.profile_payload),
        )


class IdentityPass:
    """Populate css.identity."""

    metadata = PassMetadata(name="identity", version="1.0")

    def run(
        self,
        css: CanonicalStructuralSignature,
        context: CompilerContext,
    ) -> CanonicalStructuralSignature:
        return replace(
            css,
            identity=build_identity_layer(
                profile_key=context.profile_key,
                profile_payload=context.profile_payload,
            ),
        )


class CipherPass:
    """Populate css.cipher."""

    metadata = PassMetadata(name="cipher", version="1.0", dependencies=("identity",))

    def run(
        self,
        css: CanonicalStructuralSignature,
        context: CompilerContext,
    ) -> CanonicalStructuralSignature:
        return replace(
            css,
            cipher=build_cipher_layer(profile_payload=context.profile_payload),
        )


class KameaPass:
    """Populate css.kamea."""

    metadata = PassMetadata(
        name="kamea",
        version="2.0",
        dependencies=("identity", "astronomy", "cipher"),
    )

    def run(
        self,
        css: CanonicalStructuralSignature,
        context: CompilerContext,
    ) -> CanonicalStructuralSignature:
        return replace(
            css,
            kamea=build_kamea_layer(profile_payload=context.profile_payload),
        )


class TemporalPass:
    """Populate css.temporal."""

    metadata = PassMetadata(
        name="temporal",
        version="2.0",
        dependencies=("structural_measurement",),
    )

    def run(
        self,
        css: CanonicalStructuralSignature,
        context: CompilerContext,
    ) -> CanonicalStructuralSignature:
        return replace(
            css,
            temporal=build_temporal_layer(profile_payload=context.profile_payload),
        )


class StructuralMeasurementPass:
    """Assemble graph-of-graphs after astronomy and Kamea measurement."""

    metadata = PassMetadata(
        name="structural_measurement",
        version="1.0",
        dependencies=("astronomy", "kamea"),
    )

    def run(self, css: CanonicalStructuralSignature, context: CompilerContext) -> CanonicalStructuralSignature:
        return replace(
            css,
            structural_measurement=build_structural_measurement_layer(
                astronomy=css.astronomy.measurements,
                normalized_kamea_graphs=css.kamea.normalized_graphs,
            ),
        )
