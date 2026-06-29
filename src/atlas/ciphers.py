"""Atlas cipher systems."""

import string


ENGLISH_ORDINAL = {
    letter: index + 1
    for index, letter in enumerate(string.ascii_uppercase)
}


HEBREW_LITERAL_VALUES = {
    "A": 1,      # Aleph
    "B": 2,      # Beth
    "C": 20,     # Kaph
    "D": 4,      # Daleth
    "E": 5,      # Heh
    "F": 80,     # Pe
    "G": 3,      # Gimel
    "H": 8,      # Cheth
    "I": 10,     # Yod
    "J": 10,     # Yod
    "K": 20,     # Kaph
    "L": 30,     # Lamed
    "M": 40,     # Mem
    "N": 50,     # Nun
    "O": 70,     # Ayin
    "P": 80,     # Pe
    "Q": 100,    # Qoph
    "R": 200,    # Resh
    "S": 60,     # Samekh
    "T": 400,    # Tav
    "U": 6,      # Vav
    "V": 6,      # Vav
    "W": 6,      # Vav
    "X": 60,     # Samekh
    "Y": 10,     # Yod
    "Z": 7,      # Zayin
}


PHONETIC_TOKENS = {
    # Three-letter sounds first
    "SCH": 300,   # Shin-like cluster
    "TCH": 90,    # Tsadi-like affricate

    # Two-letter sounds
    "PH": 80,     # Pe
    "TH": 400,    # Tav
    "SH": 300,    # Shin
    "CH": 20,     # Kaph default for English name work
    "CK": 20,     # Kaph
    "QU": 100,    # Qoph
    "WH": 6,      # Vav
    "NG": 50,     # Nun
}


def normalize_text(value: str) -> str:
    """Normalize text for Atlas cipher work."""
    return "".join(
        character
        for character in value.upper()
        if character.isalpha()
    )


def english_ordinal_sequence(value: str) -> list[int]:
    """Convert text to English ordinal values."""
    normalized = normalize_text(value)

    return [
        ENGLISH_ORDINAL[character]
        for character in normalized
        if character in ENGLISH_ORDINAL
    ]


def hebrew_literal_sequence(value: str) -> list[int]:
    """Convert text to Hebrew literal values.

    Literal mode is letter-for-letter.
    It does not combine sounds.
    """
    normalized = normalize_text(value)

    return [
        HEBREW_LITERAL_VALUES[character]
        for character in normalized
        if character in HEBREW_LITERAL_VALUES
    ]


def hebrew_phonetic_sequence(value: str) -> list[int]:
    """Convert text to Hebrew phonetic values.

    Phonetic mode scans sound groups before individual letters.
    This intentionally differs from Hebrew literal transliteration.
    """
    normalized = normalize_text(value)
    values = []
    index = 0

    token_lengths = sorted(
        {len(token) for token in PHONETIC_TOKENS},
        reverse=True,
    )

    while index < len(normalized):
        matched = False

        for token_length in token_lengths:
            token = normalized[index:index + token_length]

            if token in PHONETIC_TOKENS:
                values.append(PHONETIC_TOKENS[token])
                index += token_length
                matched = True
                break

        if matched:
            continue

        character = normalized[index]

        if character in HEBREW_LITERAL_VALUES:
            values.append(HEBREW_LITERAL_VALUES[character])

        index += 1

    return values


def run_all_ciphers(value: str) -> dict[str, list[int]]:
    """Run all Atlas cipher systems."""
    return {
        "ordinal": english_ordinal_sequence(value),
        "hebrew_literal": hebrew_literal_sequence(value),
        "hebrew_phonetic": hebrew_phonetic_sequence(value),
    }