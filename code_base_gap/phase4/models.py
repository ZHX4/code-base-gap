"""Canonical models for the Phase 4 program knowledge graph."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


NODE_KINDS = {
    "repository",
    "file",
    "symbol",
    "module",
    "endpoint",
    "query",
    "config",
    "integration",
    "test",
    "external_module",
}

EDGE_KINDS = {
    "CONTAINS",
    "DECLARES",
    "IMPORTS",
    "EXPORTS",
    "RESOLVES_TO",
    "EXPOSES",
    "EXECUTES_QUERY",
    "USES_CONFIG",
    "INTEGRATES_WITH",
    "TESTS",
    "LOCATED_IN",
}


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in NODE_KINDS:
            raise ValueError(f"unsupported graph node kind: {self.kind}")
        if not self.node_id:
            raise ValueError("graph node_id cannot be empty")
        if not self.label:
            raise ValueError("graph node label cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source: str
    target: str
    kind: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in EDGE_KINDS:
            raise ValueError(f"unsupported graph edge kind: {self.kind}")
        if not self.edge_id or not self.source or not self.target:
            raise ValueError("graph edge identifiers cannot be empty")
        if self.source == self.target and self.kind in {"RESOLVES_TO", "IMPORTS", "EXPORTS", "EXPOSES", "TESTS"}:
            raise ValueError(f"invalid self-loop for {self.kind}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProgramKnowledgeGraph:
    schema_version: str = "phase4.program-knowledge-graph.v1"
    repository_revision: str | None = None
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[str, GraphEdge] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        existing = self.nodes.get(node.node_id)
        if existing is not None and existing != node:
            raise ValueError(f"node ID collision with different content: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("graph edges must reference existing nodes")
        existing = self.edges.get(edge.edge_id)
        if existing is not None and existing != edge:
            raise ValueError(f"edge ID collision with different content: {edge.edge_id}")
        self.edges[edge.edge_id] = edge

    def validate(self) -> None:
        for edge in self.edges.values():
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError(f"orphan edge: {edge.edge_id}")
        for node_id, node in self.nodes.items():
            if node.node_id != node_id:
                raise ValueError(f"node map key mismatch: {node_id}")
        for edge_id, edge in self.edges.items():
            if edge.edge_id != edge_id:
                raise ValueError(f"edge map key mismatch: {edge_id}")

    def nodes_of_kind(self, kind: str) -> list[GraphNode]:
        if kind not in NODE_KINDS:
            raise ValueError(f"unsupported node kind: {kind}")
        return [node for node in self.nodes.values() if node.kind == kind]

    def edges_of_kind(self, kind: str) -> list[GraphEdge]:
        if kind not in EDGE_KINDS:
            raise ValueError(f"unsupported edge kind: {kind}")
        return [edge for edge in self.edges.values() if edge.kind == kind]

    def outgoing(self, node_id: str, kind: str | None = None) -> list[GraphEdge]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        return [
            edge for edge in self.edges.values()
            if edge.source == node_id and (kind is None or edge.kind == kind)
        ]

    def incoming(self, node_id: str, kind: str | None = None) -> list[GraphEdge]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        return [
            edge for edge in self.edges.values()
            if edge.target == node_id and (kind is None or edge.kind == kind)
        ]

    def neighbors(self, node_id: str, kind: str | None = None) -> list[GraphNode]:
        neighbor_ids = set()
        for edge in self.outgoing(node_id, kind):
            neighbor_ids.add(edge.target)
        for edge in self.incoming(node_id, kind):
            neighbor_ids.add(edge.source)
        return [self.nodes[item] for item in sorted(neighbor_ids)]

    def validate_and_normalize(self) -> None:
        self.nodes = dict(sorted(self.nodes.items()))
        self.edges = dict(sorted(self.edges.items()))
        self.limitations = sorted(set(self.limitations))
        self.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate_and_normalize()
        return {
            "schema_version": self.schema_version,
            "repository_revision": self.repository_revision,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "limitations": list(self.limitations),
            "stats": self.stats(),
        }

    def stats(self) -> dict[str, int]:
        result = {kind: len(self.nodes_of_kind(kind)) for kind in sorted(NODE_KINDS)}
        result.update({f"edge:{kind}": len(self.edges_of_kind(kind)) for kind in sorted(EDGE_KINDS)})
        result["nodes"] = len(self.nodes)
        result["edges"] = len(self.edges)
        return result

    @classmethod
    def from_records(
        cls,
        nodes: Iterable[GraphNode],
        edges: Iterable[GraphEdge],
        repository_revision: str | None = None,
        limitations: Iterable[str] = (),
    ) -> "ProgramKnowledgeGraph":
        graph = cls(repository_revision=repository_revision)
        graph.limitations.extend(limitations)
        for node in nodes:
            graph.add_node(node)
        for edge in edges:
            graph.add_edge(edge)
        graph.validate_and_normalize()
        return graph
