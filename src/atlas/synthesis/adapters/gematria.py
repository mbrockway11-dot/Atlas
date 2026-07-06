
"""Gematria evidence adapter.

Converts Atlas cipher outputs into symbolic structural evidence.
"""

from __future__ import annotations

from math import isqrt
from typing import Any

from atlas.ciphers import run_all_ciphers
from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect gematria evidence from ordinal, Hebrew literal, and Hebrew phonetic systems."""
    identity = safe_dict(payload.get("identity"))
    name = (
        identity.get("full_name")
        or identity.get("display_name")
        or payload.get("name")
        or payload.get("profile_key")
        or ""
    )

    cipher_payload = safe_dict(payload.get("cipher"))
    systems = extract_cipher_systems(cipher_payload)

    if not systems and name:
        systems = run_all_ciphers(str(name))

    evidence: list[StructuralEvidence] = []

    normalized = {
        system: analyze_sequence(system, values)
        for system, values in systems.items()
        if values
    }

    for system, analysis in normalized.items():
        evidence.extend(evidence_from_analysis(system, analysis))

    evidence.extend(cross_system_evidence(normalized))

    return evidence


def extract_cipher_systems(cipher_payload: dict[str, Any]) -> dict[str, list[int]]:
    """Extract known cipher sequences from compiler payload."""
    systems: dict[str, list[int]] = {}

    candidates = cipher_payload.get("systems") or cipher_payload.get("ciphers") or cipher_payload

    if not isinstance(candidates, dict):
        return systems

    for key in ["ordinal", "hebrew_literal", "hebrew_phonetic"]:
        value = candidates.get(key)

        if isinstance(value, list):
            systems[key] = [int(item) for item in value if is_number(item)]
            continue

        if isinstance(value, dict):
            sequence = (
                value.get("sequence")
                or value.get("values")
                or value.get("numbers")
                or value.get("cipher_sequence")
            )
            if isinstance(sequence, list):
                systems[key] = [int(item) for item in sequence if is_number(item)]

    return systems


def analyze_sequence(system: str, values: list[int]) -> dict[str, Any]:
    """Analyze one gematria/cipher sequence."""
    total = sum(values)
    reduced = digital_root(total)
    compression = 1.0 - (reduced / max(total, 1))
    repeated_values = repeated_count(values)
    repeat_ratio = repeated_values / max(len(values), 1)

    return {
        "system": system,
        "values": values,
        "total": total,
        "digital_root": reduced,
        "is_prime_total": is_prime(total),
        "length": len(values),
        "unique_count": len(set(values)),
        "repeat_count": repeated_values,
        "repeat_ratio": repeat_ratio,
        "compression": compression,
        "parity": "even" if total % 2 == 0 else "odd",
    }


def evidence_from_analysis(system: str, analysis: dict[str, Any]) -> list[StructuralEvidence]:
    """Convert one cipher analysis into evidence."""
    evidence: list[StructuralEvidence] = []
    engine = f"gematria.{system}"

    if analysis["is_prime_total"]:
        evidence.append(make_record(engine, "prime_structure", analysis["total"], 0.78))

    if analysis["repeat_ratio"] >= 0.30:
        evidence.append(make_record(engine, "recursive_patterning", analysis["repeat_ratio"], 0.76))

    if analysis["compression"] >= 0.90:
        evidence.append(make_record(engine, "constraint_pattern", analysis["compression"], 0.74))

    if analysis["unique_count"] >= max(6, analysis["length"] * 0.75):
        evidence.append(make_record(engine, "information_routing", analysis["unique_count"], 0.72))

    if analysis["digital_root"] in {1, 4, 8}:
        evidence.append(make_record(engine, "persistent_architecture", analysis["digital_root"], 0.68))

    if analysis["digital_root"] in {3, 5}:
        evidence.append(make_record(engine, "expressive_catalysis", analysis["digital_root"], 0.66))

    if analysis["digital_root"] in {7, 9}:
        evidence.append(make_record(engine, "abstraction_pattern", analysis["digital_root"], 0.66))

    return evidence


def cross_system_evidence(normalized: dict[str, dict[str, Any]]) -> list[StructuralEvidence]:
    """Create evidence from cross-cipher convergence."""
    evidence: list[StructuralEvidence] = []

    if len(normalized) < 2:
        return evidence

    roots = [item["digital_root"] for item in normalized.values()]
    totals = [item["total"] for item in normalized.values()]
    prime_count = sum(1 for item in normalized.values() if item["is_prime_total"])

    if len(set(roots)) == 1:
        evidence.append(make_record("gematria.cross_system", "reduction_stability", roots[0], 0.86))
        evidence.append(make_record("gematria.cross_system", "symbolic_coherence", roots[0], 0.82))

    elif len(set(roots)) <= 2:
        evidence.append(make_record("gematria.cross_system", "symbolic_coherence", roots, 0.72))

    if prime_count >= 2:
        evidence.append(make_record("gematria.cross_system", "prime_structure", prime_count, 0.80))

    if divergence_ratio(totals) >= 0.60:
        evidence.append(make_record("gematria.cross_system", "information_routing", totals, 0.70))

    return evidence


def digital_root(value: int) -> int:
    """Compute digital root."""
    value = abs(int(value))
    if value == 0:
        return 0
    return 1 + ((value - 1) % 9)


def is_prime(value: int) -> bool:
    """Return whether value is prime."""
    value = int(value)
    if value < 2:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False

    for factor in range(3, isqrt(value) + 1, 2):
        if value % factor == 0:
            return False

    return True


def repeated_count(values: list[int]) -> int:
    """Count repeated values beyond first appearances."""
    seen = set()
    repeats = 0

    for value in values:
        if value in seen:
            repeats += 1
        else:
            seen.add(value)

    return repeats


def divergence_ratio(values: list[int]) -> float:
    """Approximate cross-system divergence."""
    if not values:
        return 0.0

    spread = max(values) - min(values)
    scale = max(max(values), 1)
    return spread / scale


def is_number(value: Any) -> bool:
    """Return whether value can become int."""
    try:
        int(value)
        return True
    except Exception:
        return False
