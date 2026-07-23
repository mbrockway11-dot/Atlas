"""Serializable compiled identity-vector artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.compiled.compiler_identity import CompilerIdentity
from atlas.compiled.content_hash import compute_identity_content_hash
from atlas.ive import PlanetFeatureVector


COMPILED_IDENTITY_VECTOR_SCHEMA = "atlas.compiled.identity-vectors.v3"


@dataclass(frozen=True, slots=True)
class CompiledIdentityVectorArtifact:
    """Compiled raw planet-feature vectors for one Atlas profile.

    The ``feature_schema_hash`` fingerprints the meaning of a vector (planets,
    ciphers, features, builder, normalization). An artifact whose recorded
    hash no longer matches the current code was built against a different
    feature schema and must be rebuilt, even if its source ACF is unchanged.

    The ``content_hash`` fingerprints the semantic content only, excluding
    volatile provenance, so two runs of the same compiler over the same
    source produce identical content hashes.
    """

    schema_version: str
    profile_key: str
    profile_name: str
    entity_type: str

    feature_schema_hash: str
    compiler: CompilerIdentity

    source_acf_path: str
    source_acf_sha256: str
    source_acf_size_bytes: int

    vector_count: int
    vectors: tuple[PlanetFeatureVector, ...]

    @property
    def content_hash(self) -> str:
        """Return the deterministic content hash of this artifact."""
        return compute_identity_content_hash(
            profile_key=self.profile_key,
            profile_name=self.profile_name,
            entity_type=self.entity_type,
            source_acf_sha256=self.source_acf_sha256,
            feature_schema_hash=self.feature_schema_hash,
            vectors=self.vectors,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the artifact into JSON-safe primitive values."""
        compiler = self.compiler

        return {
            "schema_version": self.schema_version,
            "profile_key": self.profile_key,
            "profile_name": self.profile_name,
            "entity_type": self.entity_type,
            "feature_schema_hash": self.feature_schema_hash,
            "content_hash": self.content_hash,
            "compiler": {
                "name": compiler.name,
                "version": compiler.version,
                "git_commit": compiler.git_commit,
                "git_dirty": compiler.git_dirty,
                "python_version": compiler.python_version,
                "platform": compiler.platform,
                "atlas_version": compiler.atlas_version,
                "feature_schema_hash": compiler.feature_schema_hash,
                "command": compiler.command,
                "compiled_at": compiler.generated_at,
            },
            "source": {
                "acf_path": self.source_acf_path,
                "acf_sha256": self.source_acf_sha256,
                "acf_size_bytes": self.source_acf_size_bytes,
            },
            "vector_count": self.vector_count,
            "vectors": [asdict(vector) for vector in self.vectors],
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "CompiledIdentityVectorArtifact":
        """Reconstruct and validate an artifact from decoded JSON."""
        schema_version = str(payload["schema_version"])

        if schema_version != COMPILED_IDENTITY_VECTOR_SCHEMA:
            raise ValueError(
                "Unsupported compiled identity-vector schema: "
                f"{schema_version!r}"
            )

        compiler = CompilerIdentity.from_dict(payload["compiler"])
        source = payload["source"]

        vectors = tuple(
            PlanetFeatureVector(
                version=str(row["version"]),
                name=str(row["name"]),
                cipher=str(row["cipher"]),
                planet=str(row["planet"]),
                kamea=str(row["kamea"]),
                grid_size=int(row["grid_size"]),
                features={
                    str(feature): float(value)
                    for feature, value in row["features"].items()
                },
            )
            for row in payload["vectors"]
        )

        expected_count = int(payload["vector_count"])

        if len(vectors) != expected_count:
            raise ValueError(
                "Compiled artifact vector count mismatch: "
                f"expected {expected_count}, found {len(vectors)}"
            )

        source_hash = str(source["acf_sha256"])

        if len(source_hash) != 64:
            raise ValueError("Invalid source ACF SHA-256 digest.")

        artifact = cls(
            schema_version=schema_version,
            profile_key=str(payload["profile_key"]),
            profile_name=str(payload["profile_name"]),
            entity_type=str(payload.get("entity_type", "person")),
            feature_schema_hash=str(payload.get("feature_schema_hash", "")),
            compiler=compiler,
            source_acf_path=str(source["acf_path"]),
            source_acf_sha256=source_hash,
            source_acf_size_bytes=int(source["acf_size_bytes"]),
            vector_count=expected_count,
            vectors=vectors,
        )

        # A stored content hash that disagrees with the recomputed one means
        # the file was corrupted or hand-edited after it was written. Treat it
        # as damaged so the store's loader triggers a rebuild.
        stored_content_hash = payload.get("content_hash")

        if stored_content_hash and stored_content_hash != artifact.content_hash:
            raise ValueError(
                "Compiled artifact content hash mismatch: "
                f"{artifact.profile_key!r} was modified after compilation."
            )

        return artifact
