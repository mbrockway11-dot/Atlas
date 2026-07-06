
"""Atlas Knowledge package."""

from atlas.knowledge.knowledge_base import (
    add_evidence,
    add_hypothesis,
    add_insight,
    add_relation,
    create_knowledge_base,
)
from atlas.knowledge.knowledge_graph import build_knowledge_graph_from_discovery

__all__ = [
    "add_evidence",
    "add_hypothesis",
    "add_insight",
    "add_relation",
    "create_knowledge_base",
    "build_knowledge_graph_from_discovery",
    "build_knowledge_interpretation",
]


from atlas.knowledge.interpreter import build_knowledge_interpretation
