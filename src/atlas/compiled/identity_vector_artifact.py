"""Serializable compiled identity-vector artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.ive import PlanetFeatureVector


COMPILED_IDENTITY_VECTOR_SCHEMA = "atlas.compiled.identity-vectors.v2"


@dataclass(frozen=True, slots=True)
class CompiledIdentityVectorArtifact:
    """Compiled raw planet-feature vectors for one Atlas profile."""

    schema_version: str
    profile_key: str
    profile_name: str
    entity_type: str

    compiler_name: str
    compiler_version: str
    compiler_git_commit: str
    compiled_at: str

    source_acf_path: str
    source_acf_sha256: str
    source_acf_size_bytes: int

    vector_count: int
    vectors: tuple[PlanetFeatureVector, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the artifact into JSON-safe primitive values."""
        return {
            "schema_version": self.schema_version,
            "profile_key": self.profile_key,
            "profile_name": self.profile_name,
            "entity_type": self.entity_type,
            "compiler": {
                "name": self.compiler_name,
                "version": self.compiler_version,
                "git_commit": self.compiler_git_commit,
                "compiled_at": self.compiled_at,
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

        compiler = payload["compiler"]
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

        return cls(
            schema_version=schema_version,
            profile_key=str(payload["profile_key"]),
            profile_name=str(payload["profile_name"]),
            entity_type=str(payload.get("entity_type", "person")),
            compiler_name=str(compiler["name"]),
            compiler_version=str(compiler["version"]),
            compiler_git_commit=str(compiler["git_commit"]),
            compiled_at=str(compiler["compiled_at"]),
            source_acf_path=str(source["acf_path"]),
            source_acf_sha256=source_hash,
            source_acf_size_bytes=int(source["acf_size_bytes"]),
            vector_count=expected_count,
            vectors=vectors,
        )
