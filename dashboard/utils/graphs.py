"""Dashboard graph helpers."""

from atlas.kamea.projection import project_values_to_kamea
from atlas.topology.graph_builder import build_graph_from_kamea_path


def build_graph(values: list[int], kamea_name: str):
    """Build graph from values and Kamea name."""
    path = project_values_to_kamea(values, kamea_name)
    return build_graph_from_kamea_path(path)