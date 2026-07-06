
"""Research Memory search."""

from __future__ import annotations

from typing import Any


def search_memory(memory: dict[str, Any], query: str, *, limit: int = 20) -> dict[str, Any]:
    """Search research memory by substring."""
    needle = query.lower().strip()
    results = []

    for collection_name in ["experiments", "evidence", "hypotheses"]:
        for item_id, item in (memory.get(collection_name, {}) or {}).items():
            haystack = str(item).lower()
            if needle in haystack:
                results.append(
                    {
                        "collection": collection_name,
                        "id": item_id,
                        "item": item,
                    }
                )

    for index, note in enumerate(memory.get("notes", []) or []):
        if needle in str(note).lower():
            results.append(
                {
                    "collection": "notes",
                    "id": f"note::{index}",
                    "item": note,
                }
            )

    return {
        "success": True,
        "query": query,
        "result_count": len(results),
        "results": results[:limit],
    }


def recall_recent_memory(memory: dict[str, Any], *, limit: int = 10) -> dict[str, Any]:
    """Recall recent memory notes and experiments."""
    experiments = list((memory.get("experiments", {}) or {}).values())
    evidence = list((memory.get("evidence", {}) or {}).values())
    hypotheses = list((memory.get("hypotheses", {}) or {}).values())

    combined = [
        *({"type": "experiment", **item} for item in experiments),
        *({"type": "evidence", **item} for item in evidence),
        *({"type": "hypothesis", **item} for item in hypotheses),
    ]

    combined.sort(key=lambda item: item.get("updated_at", item.get("created_at", "")), reverse=True)

    return {
        "success": True,
        "result_count": len(combined),
        "results": combined[:limit],
    }
