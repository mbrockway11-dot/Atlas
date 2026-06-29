"""Birth data objects for Atlas profiles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BirthData:
    """Optional birth data attached to an Atlas entity."""

    date: str | None = None
    time: str | None = None
    location: str | None = None
    confidence: str = "unknown"
    notes: str | None = None


def birth_data_to_dict(birth_data: BirthData | None) -> dict:
    """Convert BirthData into JSON-safe dictionary."""
    if birth_data is None:
        return {
            "date": None,
            "time": None,
            "location": None,
            "confidence": "unknown",
            "notes": None,
        }

    return {
        "date": birth_data.date,
        "time": birth_data.time,
        "location": birth_data.location,
        "confidence": birth_data.confidence,
        "notes": birth_data.notes,
    }