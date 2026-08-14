"""Small deterministic query helpers over the program knowledge graph."""
from __future__ import annotations

from .models import GraphNode, ProgramKnowledgeGraph


def find_nodes(graph: ProgramKnowledgeGraph, *, kind: str | None = None, label: str | None = None) -> list[GraphNode]:
    nodes = list(graph.nodes.values())
    if kind is not None:
        nodes = [node for node in nodes if node.kind == kind]
    if label is not None:
        nodes = [node for node in nodes if node.label == label]
    return sorted(nodes, key=lambda node: node.node_id)


def imports_from(graph: ProgramKnowledgeGraph, node_id: str) -> list[GraphNode]:
    edges = graph.outgoing(node_id, "IMPORTS")
    return [graph.nodes[edge.target] for edge in sorted(edges, key=lambda edge: edge.edge_id)]


def files_defining(graph: ProgramKnowledgeGraph, symbol_name: str) -> list[GraphNode]:
    symbols = [node for node in graph.nodes_of_kind("symbol") if node.label == symbol_name]
    file_ids = set()
    for symbol in symbols:
        for edge in graph.incoming(symbol.node_id, "DECLARES"):
            file_ids.add(edge.source)
    return [graph.nodes[node_id] for node_id in sorted(file_ids)]


def resolved_targets(graph: ProgramKnowledgeGraph, node_id: str) -> list[GraphNode]:
    edges = graph.outgoing(node_id, "RESOLVES_TO")
    return [graph.nodes[edge.target] for edge in sorted(edges, key=lambda edge: edge.edge_id)]


def exposed_endpoints(graph: ProgramKnowledgeGraph, file_node_id: str | None = None) -> list[GraphNode]:
    if file_node_id is not None:
        edges = graph.outgoing(file_node_id, "EXPOSES")
        return [graph.nodes[edge.target] for edge in sorted(edges, key=lambda edge: edge.edge_id)]
    return graph.nodes_of_kind("endpoint")
