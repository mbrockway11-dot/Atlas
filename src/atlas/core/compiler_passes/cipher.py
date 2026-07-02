"""Cipher pass for the CSS compiler."""

from __future__ import annotations

from typing import Any

from atlas.core.canonical_structural_signature import CipherLayer
from atlas.core.compiler_passes.utils import extract_acf, first_dict


def build_cipher_layer(*, profile_payload: dict[str, Any]) -> CipherLayer:
    """Build CSS cipher layer from ACF/profile payload."""
    acf = extract_acf(profile_payload)

    cipher_matrix = first_dict(
        acf.get("cipher_matrix"),
        profile_payload.get("cipher_matrix"),
    )

    ciphers = first_dict(
        profile_payload.get("ciphers"),
        profile_payload.get("profile_summary", {}).get("ciphers")
        if isinstance(profile_payload.get("profile_summary"), dict)
        else None,
    )

    ordinal = first_dict(cipher_matrix.get("ordinal"), ciphers.get("ordinal"))

    hebrew_phonetic = first_dict(
        cipher_matrix.get("hebrew_phonetic"),
        cipher_matrix.get("hebrew"),
        ciphers.get("hebrew_phonetic"),
        ciphers.get("hebrew"),
    )

    hebrew_transliteration = first_dict(
        cipher_matrix.get("hebrew_transliteration"),
        cipher_matrix.get("hebrew_transliteral"),
        ciphers.get("hebrew_transliteration"),
        ciphers.get("hebrew_transliteral"),
    )

    gematria = first_dict(cipher_matrix.get("gematria"), ciphers.get("gematria"))

    fallback = {
        "cipher_matrix": cipher_matrix,
        "ciphers": ciphers,
        "cipher_status": "compiled_from_saved_profile",
    }

    return CipherLayer(
        ordinal=ordinal or {"source": fallback} if cipher_matrix or ciphers else {},
        hebrew_phonetic=hebrew_phonetic,
        hebrew_transliteration=hebrew_transliteration,
        gematria=gematria,
    )