"""Deterministic numerology and Gematria reports for Atlas profiles.

These calculations are reproducible symbolic transforms.  They are not
empirical personality measures, causal explanations, or clinical evidence.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from math import isqrt
import unicodedata
from typing import Any

from atlas.ciphers import run_all_ciphers


MASTER_NUMBERS = {11, 22, 33}
KARMIC_DEBT_NUMBERS = {13, 14, 16, 19}
VOWELS = set("AEIOU")

NUMBER_THEMES = {
    0: "an open or unexpressed symbolic field",
    1: "initiative, independence, and original construction",
    2: "cooperation, diplomacy, and relational calibration",
    3: "expression, imagination, and creative communication",
    4: "structure, reliability, and disciplined building",
    5: "adaptation, movement, freedom, and experimentation",
    6: "stewardship, responsibility, care, and harmonization",
    7: "analysis, inquiry, discernment, and interior depth",
    8: "organization, material execution, authority, and accountability",
    9: "integration, service, completion, and broad perspective",
    11: "inspiration, intuition, and heightened symbolic sensitivity",
    22: "large-scale construction, coordination, and practical vision",
    33: "teaching, responsibility, and compassionate service",
}


def build_numerology_profile(
    full_name: str,
    birth_date: str,
    *,
    as_of: date | None = None,
) -> dict[str, Any]:
    """Build a complete Pythagorean numerology profile."""
    parsed = parse_iso_date(birth_date)
    letters = normalize_letters(full_name)
    values = [pythagorean_value(char) for char in letters]
    vowel_values = [pythagorean_value(char) for char in letters if char in VOWELS]
    consonant_values = [pythagorean_value(char) for char in letters if char not in VOWELS]
    initials = [part[0] for part in normalized_name_parts(full_name) if part]
    initial_values = [pythagorean_value(char) for char in initials]

    core: dict[str, dict[str, Any]] = {}
    if parsed:
        date_total = sum(int(char) for char in parsed.isoformat() if char.isdigit())
        add_number(core, "life_path", date_total, "all digits in the recorded birth date")
        add_number(core, "birthday", parsed.day, "recorded day of birth")
        add_number(core, "attitude", parsed.month + parsed.day, "birth month + birth day")
        add_number(core, "birth_month", parsed.month, "recorded birth month")
        add_number(core, "birth_year", sum(int(char) for char in str(parsed.year)), "digits in birth year")
    if values:
        add_number(core, "expression", sum(values), "Pythagorean values of every name letter")
    if vowel_values:
        add_number(core, "soul_urge", sum(vowel_values), "Pythagorean values of A/E/I/O/U name vowels")
    if consonant_values:
        add_number(core, "personality", sum(consonant_values), "Pythagorean values of name consonants; Y is treated as a consonant")
    if initial_values:
        add_number(core, "balance", sum(initial_values), "Pythagorean values of name-part initials")
    if "life_path" in core and "expression" in core:
        add_number(
            core,
            "maturity",
            core["life_path"]["number"] + core["expression"]["number"],
            "reduced Life Path + reduced Expression",
        )

    frequencies = Counter(values)
    highest_frequency = max(frequencies.values(), default=0)
    hidden_passions = sorted(
        number for number, count in frequencies.items() if count == highest_frequency
    )
    karmic_lessons = [number for number in range(1, 10) if frequencies[number] == 0]

    pinnacles: list[dict[str, Any]] = []
    challenges: list[dict[str, Any]] = []
    cycles: dict[str, Any] = {}
    if parsed:
        month = reduce_number(parsed.month)
        day = reduce_number(parsed.day)
        year = reduce_number(sum(int(char) for char in str(parsed.year)))
        pinnacle_compounds = [month + day, day + year, reduce_number(month + day) + reduce_number(day + year), month + year]
        life_path = core["life_path"]["number"]
        first_end = max(0, 36 - (life_path if life_path < 10 else reduce_number(life_path, preserve_masters=False)))
        ranges = [f"birth-{first_end}", f"{first_end + 1}-{first_end + 9}", f"{first_end + 10}-{first_end + 18}", f"{first_end + 19}+" ]
        pinnacles = [
            number_record(compound, method=f"Pinnacle {index} formula", extra={"period": ranges[index - 1]})
            for index, compound in enumerate(pinnacle_compounds, start=1)
        ]
        challenge_compounds = [abs(month - day), abs(day - year), abs(reduce_number(abs(month - day), preserve_masters=False) - reduce_number(abs(day - year), preserve_masters=False)), abs(month - year)]
        challenges = [
            number_record(compound, method=f"Challenge {index} absolute-difference formula", preserve_masters=False)
            for index, compound in enumerate(challenge_compounds, start=1)
        ]
        current = as_of or date.today()
        personal_year_compound = parsed.month + parsed.day + sum(int(char) for char in str(current.year))
        personal_year = number_record(personal_year_compound, method=f"birth month + birth day + digits of {current.year}")
        personal_month = number_record(personal_year["number"] + current.month, method="Personal Year + calendar month")
        personal_day = number_record(personal_month["number"] + current.day, method="Personal Month + calendar day")
        cycles = {
            "as_of": current.isoformat(),
            "personal_year": personal_year,
            "personal_month": personal_month,
            "personal_day": personal_day,
        }

    debt_hits = sorted({
        item["compound"]
        for item in [*core.values(), *pinnacles]
        if item.get("compound") in KARMIC_DEBT_NUMBERS
    })
    return {
        "system": "Pythagorean numerology",
        "name_input": full_name,
        "birth_date_input": birth_date,
        "vowel_policy": "A, E, I, O, U are vowels; Y is treated as a consonant",
        "master_number_policy": "11, 22, and 33 are preserved in final reductions",
        "core_numbers": core,
        "hidden_passion_numbers": [themed_number(value) for value in hidden_passions],
        "karmic_lesson_numbers": [themed_number(value) for value in karmic_lessons],
        "karmic_debt_compounds_observed": debt_hits,
        "pinnacles": pinnacles,
        "challenges": challenges,
        "cycles": cycles,
        "letter_frequencies": {str(number): frequencies[number] for number in range(1, 10)},
        "available": bool(core),
    }


def build_gematria_profile(full_name: str) -> dict[str, Any]:
    """Analyze the name with Atlas's established Gematria/cipher systems."""
    systems = run_all_ciphers(full_name) if full_name else {}
    letters = normalize_letters(full_name)
    systems["reverse_ordinal"] = [27 - (ord(char) - 64) for char in letters]
    analyses = {
        system: analyze_gematria_sequence(system, sequence)
        for system, sequence in systems.items()
        if sequence
    }
    roots = [item["digital_root"] for item in analyses.values()]
    root_counts = Counter(roots)
    dominant_roots = sorted(
        root for root, count in root_counts.items() if count == max(root_counts.values(), default=0)
    )
    return {
        "name_input": full_name,
        "systems": analyses,
        "cross_system": {
            "system_count": len(analyses),
            "digital_roots": roots,
            "distinct_root_count": len(set(roots)),
            "dominant_roots": [themed_number(root) for root in dominant_roots],
            "exact_root_convergence": len(set(roots)) == 1 and bool(roots),
        },
        "methodology": {
            "ordinal": "A=1 through Z=26",
            "reverse_ordinal": "A=26 through Z=1",
            "hebrew_literal": "Atlas letter-for-letter English-to-Hebrew value mapping",
            "hebrew_phonetic": "Atlas phonetic-token mapping before single-letter Hebrew values",
        },
        "available": bool(analyses),
    }


def add_number(target: dict[str, dict[str, Any]], key: str, compound: int, method: str) -> None:
    target[key] = number_record(compound, method=method)


def number_record(
    compound: int,
    *,
    method: str,
    preserve_masters: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    number = reduce_number(compound, preserve_masters=preserve_masters)
    record = {
        "number": number,
        "compound": int(compound),
        "theme": NUMBER_THEMES.get(number, "an unresolved symbolic theme"),
        "method": method,
        "master_number": number in MASTER_NUMBERS,
        "karmic_debt_compound": compound if compound in KARMIC_DEBT_NUMBERS else None,
    }
    record.update(extra or {})
    return record


def themed_number(value: int) -> dict[str, Any]:
    return {"number": value, "theme": NUMBER_THEMES.get(value, "an unresolved symbolic theme")}


def analyze_gematria_sequence(system: str, values: list[int]) -> dict[str, Any]:
    total = sum(values)
    root = reduce_number(total, preserve_masters=False)
    return {
        "system": system,
        "sequence": values,
        "total": total,
        "digital_root": root,
        "root_theme": NUMBER_THEMES.get(root, "an unresolved symbolic theme"),
        "length": len(values),
        "unique_value_count": len(set(values)),
        "parity": "even" if total % 2 == 0 else "odd",
        "prime_total": is_prime(total),
    }


def reduce_number(value: int, *, preserve_masters: bool = True) -> int:
    value = abs(int(value))
    while value >= 10 and not (preserve_masters and value in MASTER_NUMBERS):
        value = sum(int(char) for char in str(value))
    return value


def pythagorean_value(character: str) -> int:
    return ((ord(character) - ord("A")) % 9) + 1


def normalize_letters(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in decomposed.upper() if "A" <= char <= "Z")


def normalized_name_parts(value: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return [
        "".join(char for char in part.upper() if "A" <= char <= "Z")
        for part in decomposed.split()
    ]


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        return None


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False
    return all(value % factor for factor in range(3, isqrt(value) + 1, 2))
