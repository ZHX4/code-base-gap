from __future__ import annotations

import unittest

from code_base_gap.phase3.models import (
    EndpointRecord, ImportRecord, ParsedFile, Position, ReferenceRecord, SemanticIndex, Span, SymbolRecord,
)
from code_base_gap.phase4.builder import build_program_graph
from code_base_gap.phase4.models import GraphEdge, GraphNode, ProgramKnowledgeGraph
from code_base_gap.phase4.query import exposed_endpoints, find_nodes, files_defining, imports_from, resolved_targets


def span(start: int, end: int) -> Span:
    return Span(start, end, Position(1, start + 1), Position(1, end + 1))


class Phase4Tests(unittest.TestCase):
    def _index(self) -> SemanticIndex:
        user_symbol = SymbolRecord("user_fn", "get_user", "function", span(20, 60), span(24, 32))
        helper_symbol = SymbolRecord("helper_fn", "helper", "function", span(5, 15), span(5, 11))
        main = ParsedFile(
            path="app/main.py", language="python", source_sha256="a" * 64, byte_length=100,
            root_type="module", has_errors=False, error_count=0, ast_nodes=(),
            symbols=(user_symbol,), imports=(ImportRecord(".helpers", ("helper",), ("helper",), "static", span(0, 15)),),
            exports=(user_symbol,), references=(ReferenceRecord("helper", "identifier", span(35, 41), "user_fn", None),),
            endpoints=(EndpointRecord("fastapi", "GET", "/users/{id}", span(15, 20), None),),
            queries=(), configs=(), integrations=(), tests=(), limitations=(),
        )
        helper_file = ParsedFile(
            path="app/helpers.py", language="python", source_sha256="b" * 64, byte_length=50,
            root_type="module", has_errors=False, error_count=0, ast_nodes=(),
            symbols=(helper_symbol,), imports=(), exports=(), references=(), endpoints=(),
            queries=(), configs=(), integrations=(), tests=(), limitations=(),
        )
        index = SemanticIndex(repository_revision="c" * 40, files=[main, helper_file])
        index.finalize()
        return index

    def test_graph_integrity_and_cross_file_import(self) -> None:
        graph = build_program_graph(self._index())
        graph.validate()
        self.assertGreater(len(graph.nodes), 0)
        self.assertGreater(len(graph.edges), 0)
        files = find_nodes(graph, kind="file")
        self.assertEqual({node.label for node in files}, {"app/main.py", "app/helpers.py"})
        main_id = next(node.node_id for node in files if node.label == "app/main.py")
        imported = imports_from(graph, main_id)
        self.assertEqual([node.label for node in imported], ["app.helpers"])

    def test_unique_reference_resolution(self) -> None:
        graph = build_program_graph(self._index())
        targets = [node for node in graph.nodes_of_kind("symbol") if node.label == "helper"]
        self.assertEqual(len(targets), 1)
        main_symbol = next(node for node in graph.nodes_of_kind("symbol") if node.label == "get_user")
        resolved = resolved_targets(graph, main_symbol.node_id)
        self.assertEqual([node.label for node in resolved], ["helper"])

    def test_endpoint_and_export_edges(self) -> None:
        graph = build_program_graph(self._index())
        endpoints = exposed_endpoints(graph)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].label, "/users/{id}")
        user_symbol = next(node for node in graph.nodes_of_kind("symbol") if node.label == "get_user")
        self.assertTrue(graph.incoming(user_symbol.node_id, "EXPORTS"))

    def test_node_and_edge_collision_is_rejected(self) -> None:
        graph = ProgramKnowledgeGraph()
        node = GraphNode("file:x", "file", "x")
        graph.add_node(node)
        with self.assertRaises(ValueError):
            graph.add_node(GraphNode("file:x", "file", "different"))
        other = GraphNode("file:y", "file", "y")
        graph.add_node(other)
        edge = GraphEdge("edge:x", "file:x", "file:y", "CONTAINS")
        graph.add_edge(edge)
        with self.assertRaises(ValueError):
            graph.add_edge(GraphEdge("edge:x", "file:x", "file:y", "IMPORTS"))

    def test_queries_are_deterministic(self) -> None:
        graph = build_program_graph(self._index())
        first = [(n.node_id, n.label) for n in files_defining(graph, "helper")]
        second = [(n.node_id, n.label) for n in files_defining(graph, "helper")]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
