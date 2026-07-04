"""Atlas QA service.

Thin wrapper around the Atlas cognition kernel.
"""

from __future__ import annotations

from typing import Any

from atlas.cognition import think


ATLAS_QA_SERVICE_VERSION = "3.1"


def answer_question(question: str) -> dict[str, Any]:
    """Answer a question using the Atlas cognition kernel."""
    payload = think(question)

    payload["qa_service_version"] = ATLAS_QA_SERVICE_VERSION

    return payload
